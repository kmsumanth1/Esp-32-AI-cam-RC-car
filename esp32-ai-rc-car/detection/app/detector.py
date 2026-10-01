from __future__ import annotations

import numpy as np

from .schemas import Detection


class Detector:
    """YOLOv8 object detector. ultralytics is imported lazily so tests don't need it."""

    def __init__(self, model_path: str, conf: float = 0.4, imgsz: int = 416):
        from ultralytics import YOLO

        self.model = YOLO(model_path)  # downloads yolov8n.pt on first run
        self.conf = conf
        self.imgsz = imgsz

    def detect(self, frame: np.ndarray) -> tuple[list[Detection], np.ndarray]:
        """Run detection on a BGR frame. Returns (detections, frame with boxes drawn)."""
        result = self.model.predict(frame, conf=self.conf, imgsz=self.imgsz, verbose=False)[0]
        names = result.names
        detections = []
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append(
                Detection(names[int(box.cls[0])], float(box.conf[0]), x1, y1, x2, y2)
            )
        return detections, result.plot()
