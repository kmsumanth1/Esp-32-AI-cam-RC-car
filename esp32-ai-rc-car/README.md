# ESP32 AI RC Car

A Wi-Fi controlled RC car with a live camera and AI object detection. An ESP32-CAM streams
video and receives drive commands, an Arduino Uno drives the motors, and a Python server runs
YOLOv8 on the video, serves a web dashboard, and can make the car follow an object on its own.

**Demo:** _add your YouTube link here_

## How it works

```
 phone / laptop browser
        |  http://<server>:8000  (dashboard: video, drive pad, mode, detections)
        v
 +---------------------------+        MJPEG stream (port 81)        +-----------------+
 |  Detection server         | <----------------------------------- |   ESP32-CAM     |
 |  FastAPI + YOLOv8 + OpenCV|                                      |  OV2640, VGA    |
 |  MySQL / SQLite log       | -----------------------------------> |                 |
 +---------------------------+     GET /control?dir=F&speed=170     +--------+--------+
                                                                             | UART 9600
                                                                    +--------v--------+
                                                                    |  Arduino Uno    |
                                                                    |  L298N + motors |
                                                                    +-----------------+
```

- **ESP32-CAM** streams 640x480 MJPEG and exposes `/control`, `/status`, `/capture`.
- **Arduino Uno** drives two motors through an L298N and stops them if no command arrives for 500 ms.
- **Detection server** reads the stream, runs YOLOv8n, draws boxes, logs detections to a database,
  and exposes a REST API plus the dashboard.
- **Follow mode** steers toward the largest detected object of a chosen class (default: person)
  and stops when it fills a quarter of the frame or leaves the view.

## Repository layout

```
esp32_cam/     ESP32-CAM firmware (camera stream + Wi-Fi control)
arduino_uno/   Uno motor controller with failsafe
detection/     Python server: YOLOv8 detection, follow mode, REST API, dashboard, tests, tools
docs/          Wiring guide, photos, demo GIF, measurements.csv
```

## Hardware

ESP32-CAM (AI Thinker), Arduino Uno, L298N motor driver, 2-wheel (or 4-wheel) chassis with DC
motors, battery pack, separate 5 V supply for the ESP32-CAM. Wiring: [docs/wiring.md](docs/wiring.md).

## Setup

### 1. Flash the ESP32-CAM
1. In Arduino IDE install the **esp32 by Espressif** board package.
2. Copy `esp32_cam/secrets.h.example` to `esp32_cam/secrets.h` and enter your Wi-Fi name and password.
3. Select board **AI Thinker ESP32-CAM** and upload `esp32_cam/esp32_cam.ino`.
4. Open the Serial Monitor at 115200 baud and note the IP address it prints.

### 2. Flash the Arduino Uno
Upload `arduino_uno/arduino_uno.ino`.

### 3. Run the detection server

```bash
cd detection
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ESP32_HOST=192.168.1.50 uvicorn app.main:app --host 0.0.0.0 --port 8000
```
(Windows PowerShell: `$env:ESP32_HOST="192.168.1.50"; uvicorn app.main:app --host 0.0.0.0 --port 8000`)

Open <http://localhost:8000>. The YOLOv8n weights download automatically on first run.

Or with Docker and MySQL:

```bash
cp .env.example .env      # set ESP32_HOST
docker compose up --build
```

### Settings (environment variables)

| Variable          | Default              | Meaning                                          |
| ----------------- | -------------------- | ------------------------------------------------ |
| `ESP32_HOST`      | `192.168.4.1`        | IP of the ESP32-CAM                              |
| `YOLO_MODEL`      | `yolov8n.pt`         | Any ultralytics weights file                     |
| `DETECT_CONF`     | `0.4`                | Minimum detection confidence                     |
| `DETECT_IMGSZ`    | `416`                | Inference size (smaller is faster)               |
| `DATABASE_URL`    | `sqlite:///detections.db` | SQLAlchemy URL, e.g. `mysql+pymysql://...`  |
| `FOLLOW_TARGET`   | `person`             | Default object to follow                         |
| `DRIVE_SPEED`     | `170`                | Follow-mode forward speed (0-255)                |
| `TURN_SPEED`      | `150`                | Follow-mode turning speed (0-255)                |

## REST API

| Method | Path             | Body / query                          | Returns                                   |
| ------ | ---------------- | ------------------------------------- | ----------------------------------------- |
| GET    | `/video`         |                                       | Annotated MJPEG stream                    |
| GET    | `/api/status`    |                                       | mode, target, fps, control latency, link  |
| GET    | `/api/detections`|                                       | Objects in the current frame              |
| GET    | `/api/history`   | `limit` (1-500)                       | Logged detections, newest first           |
| POST   | `/api/control`   | `{"direction": "F", "speed": 170}`    | `{"ok": true, "latency_ms": 41.2}`        |
| POST   | `/api/mode`      | `{"mode": "follow", "target": "cup"}` | Updated status                            |

`direction` is one of `F`, `B`, `L`, `R`, `S`. Interactive docs are at `/docs`.

## Safety

- The Uno stops the motors 500 ms after the last command, so a dropped Wi-Fi link, a closed
  browser tab or a crashed server all stop the car.
- Test on a stand or with the wheels off the ground first, especially follow mode.

## Results

Run `python detection/tools/measure.py --host <esp32-ip> --distance <metres>` at a few
distances. It appends control latency, signal strength and stream frame rate to
`docs/measurements.csv`. Paste your real numbers here:

| Distance | Wi-Fi signal | Control latency (mean / p95) | Stream fps | Detection fps |
| -------- | ------------ | ---------------------------- | ---------- | ------------- |
| _fill in_ |             |                              |            |               |

Detection fps is shown live on the dashboard. Latency here is the HTTP round trip to the
ESP32; for true end-to-end delay, film the screen and the car in slow motion.

## Tests

```bash
cd detection
pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover the follow-mode decision logic, the REST API (with a fake car and pipeline) and the
database layer. CI (GitHub Actions) runs them with ruff, and compiles both firmware sketches.
