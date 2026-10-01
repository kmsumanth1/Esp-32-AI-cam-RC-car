from __future__ import annotations

import threading
import time

import requests


class Car:
    """Thin client for the ESP32-CAM /control endpoint."""

    def __init__(self, base_url: str, timeout: float = 0.4):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.last_latency_ms: float | None = None
        self._session = requests.Session()
        self._lock = threading.Lock()

    def send(self, direction: str, speed: int) -> float | None:
        """Send a drive command. Returns the HTTP round-trip in ms, or None if unreachable."""
        with self._lock:
            start = time.perf_counter()
            try:
                resp = self._session.get(
                    f"{self.base_url}/control",
                    params={"dir": direction, "speed": int(speed)},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
            except requests.RequestException:
                self.last_latency_ms = None
                return None
            self.last_latency_ms = (time.perf_counter() - start) * 1000
            return self.last_latency_ms

    def stop(self) -> float | None:
        return self.send("S", 0)
