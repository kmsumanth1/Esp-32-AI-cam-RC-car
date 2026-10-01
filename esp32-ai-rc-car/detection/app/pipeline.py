from __future__ import annotations

import logging
import threading
import time

import cv2

from .follow import follow_command

log = logging.getLogger("pipeline")


class Pipeline:
    """Reads the ESP32 stream, runs detection, and optionally drives the car.

    Two threads: one reads frames as fast as they arrive and keeps only the newest
    (so a slow model never builds up a backlog / lag), the other runs detection on it.
    """

    def __init__(self, settings, detector, car, db):
        self.settings = settings
        self.detector = detector
        self.car = car
        self.db = db

        self.mode = "manual"  # "manual" or "follow"
        self.target = settings.follow_target
        self.fps = 0.0
        self.stream_connected = False

        self._lock = threading.Lock()
        self._frame = None
        self._frame_id = 0
        self._jpeg: bytes | None = None
        self._jpeg_id = 0
        self._detections: list = []
        self._last_logged: dict[str, float] = {}
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    # ---- lifecycle -------------------------------------------------------------------
    def start(self) -> None:
        for fn in (self._grab_loop, self._detect_loop):
            thread = threading.Thread(target=fn, daemon=True)
            thread.start()
            self._threads.append(thread)

    def stop(self) -> None:
        self._stop.set()
        for thread in self._threads:
            thread.join(timeout=2)
        self.car.stop()

    # ---- public state ----------------------------------------------------------------
    def set_mode(self, mode: str, target: str | None = None) -> None:
        if target:
            self.target = target.strip().lower()
        was_following = self.mode == "follow"
        self.mode = mode
        if was_following and mode != "follow":
            self.car.stop()

    def latest_detections(self) -> list[dict]:
        with self._lock:
            return [d.to_dict() for d in self._detections]

    def status(self) -> dict:
        return {
            "mode": self.mode,
            "target": self.target,
            "fps": round(self.fps, 1),
            "latency_ms": None
            if self.car.last_latency_ms is None
            else round(self.car.last_latency_ms, 1),
            "stream_connected": self.stream_connected,
        }

    def mjpeg(self):
        """Generator of multipart MJPEG chunks for the annotated video."""
        last = -1
        while not self._stop.is_set():
            with self._lock:
                jpeg, jpeg_id = self._jpeg, self._jpeg_id
            if jpeg is None or jpeg_id == last:
                time.sleep(0.02)
                continue
            last = jpeg_id
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                + str(len(jpeg)).encode()
                + b"\r\n\r\n"
                + jpeg
                + b"\r\n"
            )

    # ---- worker threads --------------------------------------------------------------
    def _grab_loop(self) -> None:
        while not self._stop.is_set():
            cap = cv2.VideoCapture(self.settings.stream_url)
            if not cap.isOpened():
                self.stream_connected = False
                self._stop.wait(2.0)
                continue
            self.stream_connected = True
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok:
                    break
                with self._lock:
                    self._frame = frame
                    self._frame_id += 1
            cap.release()
            self.stream_connected = False
            self._stop.wait(1.0)

    def _detect_loop(self) -> None:
        last_id = 0
        last_time = time.perf_counter()
        while not self._stop.is_set():
            with self._lock:
                frame, frame_id = self._frame, self._frame_id
            if frame is None or frame_id == last_id:
                time.sleep(0.005)
                continue
            last_id = frame_id

            try:
                detections, annotated = self.detector.detect(frame)
                height, width = frame.shape[:2]
                if self.mode == "follow":
                    self.car.send(
                        *follow_command(
                            detections,
                            width,
                            height,
                            self.target,
                            speed=self.settings.drive_speed,
                            turn_speed=self.settings.turn_speed,
                        )
                    )
                self._log_detections(detections)
                ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            except Exception:
                log.exception("detection step failed")
                time.sleep(0.2)
                continue

            now = time.perf_counter()
            instant = 1.0 / max(now - last_time, 1e-6)
            last_time = now
            self.fps = instant if self.fps == 0 else 0.9 * self.fps + 0.1 * instant

            with self._lock:
                self._detections = detections
                if ok:
                    self._jpeg = buf.tobytes()
                    self._jpeg_id += 1

    def _log_detections(self, detections) -> None:
        """Store at most one row per label every `log_interval_s` seconds."""
        now = time.monotonic()
        for det in detections:
            if now - self._last_logged.get(det.label, -1e9) < self.settings.log_interval_s:
                continue
            self._last_logged[det.label] = now
            try:
                self.db.log(det.label, det.conf)
            except Exception:
                log.exception("could not write detection to database")
