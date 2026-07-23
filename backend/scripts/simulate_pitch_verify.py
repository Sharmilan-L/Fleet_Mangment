import json
import time
import urllib.request
import uuid

API_BASE = "http://127.0.0.1:8000/api/v1"


def api_post(url, payload, headers=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}{url}", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


def api_get(url):
    req = urllib.request.Request(f"{API_BASE}{url}", method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


def run_simulation_checks():
    print("\n--- Telemetry Ingestion, Auth, & Duplicate Verification ---")
    # Clear any active trips
    _, active_trips_data = api_get("/trips/active")
    for t in active_trips_data.get("data", []):
        trip_id = t["id"]
        print(f"Cleaning up active trip: {trip_id}")
        api_post(f"/trips/{trip_id}/end", {"endReason": "E2E cleanup"})

    # Get active driver, vehicle, and rule set
    _, start_opts = api_get("/trips/start-options")

    driver_id = None
    for d in start_opts["data"]["drivers"]:
        if d.get("employeeCode") == "DRV-DEMO-001" or "John" in d.get("name", ""):
            driver_id = d["id"]
            break

    vehicle_id = None
    for v in start_opts["data"]["vehicles"]:
        reg = v.get("registrationNumber", "")
        if v.get("vehicleCode") == "VEH-DEMO-001" or "EV-2026-SL" in reg:
            vehicle_id = v["id"]
            break

    if not driver_id:
        driver_id = start_opts["data"]["drivers"][0]["id"]
    if not vehicle_id:
        vehicle_id = start_opts["data"]["vehicles"][0]["id"]

    # Start Trip
    start_payload = {
        "driverId": driver_id,
        "vehicleId": vehicle_id,
        "tripMode": "TEST",
        "appliedSpeedLimitKmh": 60.0,
        "startReason": "Real E2E verification test",
    }
    status_code, trip_data = api_post("/trips", start_payload)
    print("Trip start status:", status_code, "Body:", trip_data)
    assert status_code == 201
    trip_id = trip_data["data"]["id"]
    print(f"Active E2E Trip Created: {trip_id}")

    # A. Invalid Auth key
    bad_headers = {
        "X-Device-Code": "SIM-DEVICE-001",
        "X-Device-Key": "invalid-key-xyz",
        "X-Telemetry-Schema-Version": "1.0",
    }
    bad_p = {
        "boot_id": "b-1",
        "sequence_number": 1,
        "speed_kmh": 40.0,
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }
    code, err_resp = api_post("/device/telemetry", bad_p, headers=bad_headers)
    print(f"Invalid key status (expected 401): {code}")
    assert code == 401

    headers = {
        "X-Device-Code": "SIM-DEVICE-001",
        "X-Device-Key": "demo-simulator-secret-key-2026",
        "X-Telemetry-Schema-Version": "1.0",
    }

    boot_id = f"boot-verify-{uuid.uuid4().hex[:6]}"

    # B. Missing GPS (should be partial warning / accepted)
    payload_no_gps = {
        "boot_id": boot_id,
        "sequence_number": 1,
        "speed_kmh": 40.0,
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }
    code, res_gps = api_post("/device/telemetry", payload_no_gps, headers=headers)
    p_status = res_gps["data"]["processingStatus"]
    print(f"Missing GPS status (expected 200/PARTIAL): {code} - Status: {p_status}")
    assert code == 200
    assert p_status == "PARTIAL"

    # C. Real Hardware Telemetry Ingestion (Full GPS)
    payload_gps = {
        "boot_id": boot_id,
        "sequence_number": 2,
        "timestamp": time.time(),
        "lat": 6.9271,
        "lng": 79.8612,
        "speed_kmh": 45.0,
        "accel_fwd": 0.0,
        "accel_lat": 0.0,
        "yaw_rate": 0.0,
    }
    code, res_gps_full = api_post("/device/telemetry", payload_gps, headers=headers)
    full_status = res_gps_full["data"]["processingStatus"]
    print(f"Ingestion status (expected 200/PROCESSED): {code} - Status: {full_status}")
    assert code == 200
    assert full_status == "PROCESSED"

    # D. Duplicate Ingestion
    code, res_dup = api_post("/device/telemetry", payload_gps, headers=headers)
    dup_status = res_dup["data"]["processingStatus"]
    print(f"Duplicate status (expected 200/DUPLICATE): {code} - Status: {dup_status}")
    assert code == 200
    assert dup_status == "DUPLICATE"

    print("\n--- Event Detection Checks ---")
    # Harsh braking sequence (accel_fwd <= -3.0 m/s^2 for > 500ms)
    t_start = time.time()
    braking_payloads = [
        {
            "boot_id": boot_id,
            "sequence_number": 3,
            "timestamp": t_start,
            "lat": 6.9271,
            "lng": 79.8612,
            "speed_kmh": 50.0,
            "accel_fwd": -3.8,
            "accel_lat": 0.0,
            "yaw_rate": 0.0,
        },
        {
            "boot_id": boot_id,
            "sequence_number": 4,
            "timestamp": t_start + 1.0,
            "lat": 6.9272,
            "lng": 79.8613,
            "speed_kmh": 40.0,
            "accel_fwd": -4.2,
            "accel_lat": 0.0,
            "yaw_rate": 0.0,
        },
        {
            "boot_id": boot_id,
            "sequence_number": 5,
            "timestamp": t_start + 2.0,
            "lat": 6.9273,
            "lng": 79.8614,
            "speed_kmh": 35.0,
            "accel_fwd": -0.5,
            "accel_lat": 0.0,
            "yaw_rate": 0.0,
        },
    ]
    for p in braking_payloads:
        api_post("/device/telemetry", p, headers=headers)

    _, snapshot = api_get(f"/trips/{trip_id}/live")
    events = snapshot["data"]["events"]
    print("Detected Events:", [e["eventType"] for e in events])
    assert any(e["eventType"] == "HARSH_BRAKING" for e in events)

    score_val = snapshot["data"]["score"]["currentScore"]
    risk = snapshot["data"]["score"]["riskLevel"]
    print(f"Safety Score (expected < 100): {score_val} - Risk Level: {risk}")
    assert score_val < 100.0

    # End trip
    code, res_end = api_post(f"/trips/{trip_id}/end", {"endReason": "E2E verification complete"})
    assert code == 200
    print("Trip closed successfully!")

    # Summary
    code, summary = api_get(f"/trips/{trip_id}/summary")
    assert code == 200
    dur = summary["data"]["durationSeconds"]
    f_score = summary["data"]["finalScore"]
    f_risk = summary["data"]["finalRiskLevel"]
    print(f"Trip Summary Details -> Duration: {dur}s, Score: {f_score}, Risk: {f_risk}")


if __name__ == "__main__":
    run_simulation_checks()
