from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import Deps, create_app


class FakeCar:
    def __init__(self, latency=12.34):
        self.latency = latency
        self.sent = []
        self.last_latency_ms = latency

    def send(self, direction, speed):
        self.sent.append((direction, speed))
        return self.latency

    def stop(self):
        return self.send("S", 0)


class FakePipeline:
    def __init__(self, car):
        self.car = car
        self.mode = "manual"
        self.target = "person"
        self.started = self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def set_mode(self, mode, target=None):
        self.mode = mode
        if target:
            self.target = target

    def status(self):
        return {"mode": self.mode, "target": self.target, "fps": 12.0,
                "latency_ms": self.car.last_latency_ms, "stream_connected": True}

    def latest_detections(self):
        return [{"label": "person", "conf": 0.9, "box": [1, 2, 3, 4]}]

    def mjpeg(self):
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\nx\r\n"


class FakeDb:
    def recent(self, limit):
        return [{"id": 1, "label": "person", "confidence": 0.9, "created_at": "now"}][:limit]


@pytest.fixture
def setup():
    car = FakeCar()
    pipeline = FakePipeline(car)
    deps = Deps(SimpleNamespace(esp32_host="10.0.0.5"), car, FakeDb(), pipeline)
    with TestClient(create_app(deps)) as client:
        yield client, car, pipeline


def test_lifespan_starts_and_stops_pipeline():
    car = FakeCar()
    pipeline = FakePipeline(car)
    deps = Deps(SimpleNamespace(esp32_host="x"), car, FakeDb(), pipeline)
    with TestClient(create_app(deps)):
        assert pipeline.started
    assert pipeline.stopped


def test_control_forwards_command_and_reports_latency(setup):
    client, car, _ = setup
    r = client.post("/api/control", json={"direction": "F", "speed": 200})
    assert r.status_code == 200
    assert r.json() == {"ok": True, "latency_ms": 12.3}
    assert car.sent == [("F", 200)]


def test_control_rejects_bad_direction_and_speed(setup):
    client, car, _ = setup
    assert client.post("/api/control", json={"direction": "X", "speed": 100}).status_code == 422
    assert client.post("/api/control", json={"direction": "F", "speed": 999}).status_code == 422
    assert car.sent == []


def test_control_returns_502_when_esp32_unreachable(setup):
    client, car, _ = setup
    car.latency = None
    r = client.post("/api/control", json={"direction": "F", "speed": 100})
    assert r.status_code == 502
    assert "ESP32" in r.json()["detail"]


def test_manual_control_overrides_follow_mode(setup):
    client, _, pipeline = setup
    client.post("/api/mode", json={"mode": "follow", "target": "bottle"})
    assert pipeline.mode == "follow" and pipeline.target == "bottle"
    client.post("/api/control", json={"direction": "S", "speed": 0})
    assert pipeline.mode == "manual"


def test_status_detections_history(setup):
    client, _, _ = setup
    assert client.get("/api/status").json()["esp32_host"] == "10.0.0.5"
    assert client.get("/api/detections").json()[0]["label"] == "person"
    assert client.get("/api/history?limit=1").json()[0]["label"] == "person"


def test_dashboard_is_served(setup):
    client, _, _ = setup
    r = client.get("/")
    assert r.status_code == 200
    assert "ESP32 AI RC Car" in r.text
