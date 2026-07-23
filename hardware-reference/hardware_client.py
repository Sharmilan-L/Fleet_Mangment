"""
EvolveX Physical Hardware Reference Client Simulator.

Simulates ESP32 device network socket transmission posting raw sensor telemetry
to the REST endpoint using raw HTTP packets and parsing server responses.
"""

import hashlib
import json
import time
import urllib.request
from typing import Any

DEVICE_CODE = "SIM-DEVICE-001"
DEVICE_KEY = "demo-simulator-secret-key-2026"
API_URL = "http://localhost:8000/api/v1/device/telemetry"


def send_telemetry_packet(packet: dict[str, Any]) -> dict[str, Any]:
    """Send a single telemetry packet over HTTP POST with custom headers."""
    data = json.dumps(packet).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Device-Code", DEVICE_CODE)
    req.add_header("X-Device-Key", DEVICE_KEY)
    req.add_header("X-Telemetry-Schema-Version", "1.0")

    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"success": False, "error": {"message": err.reason}}
    except Exception as exc:
        return {"success": False, "error": {"message": str(exc)}}


def run_reference_loop(limit: int = 5) -> None:
    """Generate and send a short sequence of telemetry records."""
    boot_id = f"hw-boot-{int(time.time())}"
    print(f"Starting hardware reference client run. Boot ID: {boot_id}")

    for seq in range(1, limit + 1):
        packet = {
            "boot_id": boot_id,
            "sequence_number": seq,
            "timestamp": time.time(),
            "lat": 6.9271 + (seq * 0.0001),
            "lng": 79.8612 + (seq * 0.0001),
            "speed_kmh": 45.0 + (seq * 2.0),
            "accel_fwd": 0.5,
            "accel_lat": 0.1,
            "yaw_rate": 1.2,
        }

        print(f"Sending packet #{seq}...")
        resp = send_telemetry_packet(packet)
        print("Response received:", resp)
        time.sleep(1.0)


if __name__ == "__main__":
    run_reference_loop()
