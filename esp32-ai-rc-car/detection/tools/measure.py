"""Measure control latency, stream frame rate and Wi-Fi signal at the car's current position.

Run it at several distances and the results are appended to docs/measurements.csv:

    python tools/measure.py --host 192.168.1.50 --distance 5
    python tools/measure.py --host 192.168.1.50 --distance 15

"Control latency" here is the HTTP round trip from this computer to the ESP32-CAM. It does
not include the UART hop, the Uno or the motors spinning up. For true end-to-end delay,
film the screen and the car in slow motion and count frames between press and movement.
"""
from __future__ import annotations

import argparse
import csv
import statistics
import time
from datetime import datetime
from pathlib import Path

import cv2
import requests

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "docs" / "measurements.csv"


def measure_latency(base: str, count: int) -> tuple[list[float], int]:
    session = requests.Session()
    times, failures = [], 0
    for _ in range(count):
        start = time.perf_counter()
        try:
            session.get(f"{base}/control", params={"dir": "S", "speed": 0}, timeout=1).raise_for_status()
        except requests.RequestException:
            failures += 1
            continue
        times.append((time.perf_counter() - start) * 1000)
        time.sleep(0.05)
    return times, failures


def measure_fps(stream_url: str, seconds: float) -> float:
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        return 0.0
    frames, start = 0, None
    while True:
        ok, _ = cap.read()
        if not ok:
            break
        if start is None:
            start = time.perf_counter()  # ignore connection setup time
            continue
        frames += 1
        if time.perf_counter() - start >= seconds:
            break
    cap.release()
    return frames / (time.perf_counter() - start) if start else 0.0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", required=True, help="ESP32-CAM IP address")
    p.add_argument("--distance", type=float, required=True, help="distance from the router in metres")
    p.add_argument("--count", type=int, default=100, help="number of control requests")
    p.add_argument("--seconds", type=float, default=10, help="how long to measure the stream")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = p.parse_args()

    base = f"http://{args.host}"
    try:
        rssi = requests.get(f"{base}/status", timeout=2).json().get("rssi")
    except (requests.RequestException, ValueError):
        rssi = None

    times, failures = measure_latency(base, args.count)
    fps = measure_fps(f"http://{args.host}:81/stream", args.seconds)
    if not times:
        raise SystemExit("No control requests succeeded. Check --host and that the ESP32 is reachable.")

    times.sort()
    row = {
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "distance_m": args.distance,
        "rssi_dbm": rssi,
        "latency_mean_ms": round(statistics.mean(times), 1),
        "latency_p95_ms": round(times[int(0.95 * (len(times) - 1))], 1),
        "failed_pct": round(100 * failures / args.count, 1),
        "stream_fps": round(fps, 1),
    }
    print(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    new_file = not args.out.exists()
    with args.out.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    print(f"Appended to {args.out}")


if __name__ == "__main__":
    main()
