from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    esp32_host: str
    control_port: int
    stream_port: int
    model: str
    conf: float
    imgsz: int
    database_url: str
    follow_target: str
    drive_speed: int
    turn_speed: int
    log_interval_s: float

    @property
    def stream_url(self) -> str:
        return f"http://{self.esp32_host}:{self.stream_port}/stream"

    @property
    def control_url(self) -> str:
        return f"http://{self.esp32_host}:{self.control_port}"


def get_settings() -> Settings:
    """Read settings from environment variables (see .env.example)."""
    env = os.environ.get
    return Settings(
        esp32_host=env("ESP32_HOST", "192.168.4.1"),
        control_port=int(env("ESP32_CONTROL_PORT", "80")),
        stream_port=int(env("ESP32_STREAM_PORT", "81")),
        model=env("YOLO_MODEL", "yolov8n.pt"),
        conf=float(env("DETECT_CONF", "0.4")),
        imgsz=int(env("DETECT_IMGSZ", "416")),
        database_url=env("DATABASE_URL", "sqlite:///detections.db"),
        follow_target=env("FOLLOW_TARGET", "person"),
        drive_speed=int(env("DRIVE_SPEED", "170")),
        turn_speed=int(env("TURN_SPEED", "150")),
        log_interval_s=float(env("LOG_INTERVAL_S", "5")),
    )
