from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

STATIC_DIR = Path(__file__).parent / "static"


class ControlRequest(BaseModel):
    direction: Literal["F", "B", "L", "R", "S"]
    speed: int = Field(170, ge=0, le=255)


class ModeRequest(BaseModel):
    mode: Literal["manual", "follow"]
    target: str | None = Field(None, max_length=32)


@dataclass
class Deps:
    settings: Any
    car: Any
    db: Any
    pipeline: Any


def build_deps() -> Deps:
    """Create the real objects. Imported lazily so tests can inject fakes instead."""
    from .car import Car
    from .config import get_settings
    from .database import Database
    from .detector import Detector
    from .pipeline import Pipeline

    settings = get_settings()
    car = Car(settings.control_url)
    db = Database(settings.database_url)
    detector = Detector(settings.model, settings.conf, settings.imgsz)
    return Deps(settings, car, db, Pipeline(settings, detector, car, db))


def create_app(deps: Deps | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.deps = deps or build_deps()
        app.state.deps.pipeline.start()
        try:
            yield
        finally:
            app.state.deps.pipeline.stop()

    app = FastAPI(title="ESP32 AI RC Car", lifespan=lifespan)

    @app.get("/")
    def dashboard():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/video")
    def video():
        return StreamingResponse(
            app.state.deps.pipeline.mjpeg(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    @app.get("/api/status")
    def status():
        d = app.state.deps
        return {**d.pipeline.status(), "esp32_host": d.settings.esp32_host}

    @app.get("/api/detections")
    def detections():
        return app.state.deps.pipeline.latest_detections()

    @app.get("/api/history")
    def history(limit: int = Query(50, ge=1, le=500)):
        return app.state.deps.db.recent(limit)

    @app.post("/api/control")
    def control(req: ControlRequest):
        d = app.state.deps
        d.pipeline.set_mode("manual")  # a manual command always takes over from follow mode
        latency = d.car.send(req.direction, req.speed)
        if latency is None:
            raise HTTPException(
                status_code=502,
                detail="The ESP32 did not respond. Check that it is on the same Wi-Fi "
                "and that ESP32_HOST is correct.",
            )
        return {"ok": True, "latency_ms": round(latency, 1)}

    @app.post("/api/mode")
    def mode(req: ModeRequest):
        d = app.state.deps
        d.pipeline.set_mode(req.mode, req.target)
        return d.pipeline.status()

    return app


app = create_app()
