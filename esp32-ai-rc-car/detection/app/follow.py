from __future__ import annotations

from collections.abc import Sequence

from .schemas import Detection

Command = tuple[str, int]  # (direction, speed)


def follow_command(
    detections: Sequence[Detection],
    frame_w: int,
    frame_h: int,
    target: str,
    *,
    speed: int = 170,
    turn_speed: int = 150,
    deadband: float = 0.12,
    stop_area: float = 0.25,
) -> Command:
    """Decide how to drive so the car keeps `target` centred and at a safe distance.

    - target not visible          -> stop
    - target off to one side      -> turn toward it
    - target centred and far      -> drive forward
    - target centred and close    -> stop (box fills `stop_area` of the frame)
    """
    candidates = [d for d in detections if d.label == target]
    if not candidates:
        return ("S", 0)

    best = max(candidates, key=lambda d: d.area)

    offset = (best.x1 + best.x2) / 2 / frame_w - 0.5  # -0.5 (far left) .. +0.5 (far right)
    if abs(offset) > deadband:
        return ("R" if offset > 0 else "L", turn_speed)

    if best.area / (frame_w * frame_h) >= stop_area:
        return ("S", 0)
    return ("F", speed)
