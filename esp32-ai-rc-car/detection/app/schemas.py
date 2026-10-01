from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    """One detected object, in pixel coordinates of the source frame."""

    label: str
    conf: float
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def area(self) -> float:
        return max(self.x2 - self.x1, 0.0) * max(self.y2 - self.y1, 0.0)

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "conf": round(self.conf, 3),
            "box": [round(self.x1), round(self.y1), round(self.x2), round(self.y2)],
        }
