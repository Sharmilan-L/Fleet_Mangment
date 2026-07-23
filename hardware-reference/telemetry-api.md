# EvolveX Hardware Telemetry Integration Guide

This guide provides technical specifications for hardware developers, embedded engineers, and simulator integrators connecting devices directly to the EvolveX Telemetry Ingestion API.

---

## 1. Environment & Network Configuration

- **Local FastAPI Service Base URL**: `http://localhost:8000` (or `http://127.0.0.1:8000`)
- **Telemetry Ingestion Endpoint**: `POST /api/v1/device/telemetry`
- **Full Ingestion URL**: `http://localhost:8000/api/v1/device/telemetry`
- **Database Port**: PostgreSQL 16 Alpine operates on local port `5433` (`127.0.0.1:5433`).

---

## 2. Authentication & Headers

Hardware devices authenticate using custom HTTP request headers. Do **NOT** use human session cookies or Bearer tokens.

### Required Headers

| Header | Description | Example |
| :--- | :--- | :--- |
| `Content-Type` | MIME payload type | `application/json` |
| `X-Device-Code` | Unique hardware / simulator code registered in EvolveX | `HW-DEV-9001` |
| `X-Device-Key` | Secret API key associated with the device | `secret-hardware-api-key` |
| `X-Telemetry-Schema-Version` | Supported payload schema version | `1.0` |

> **Security Note**: Plain API keys must never be logged or transmitted over unencrypted HTTP in production environments (use HTTPS). The server compares the SHA-256 hash of `X-Device-Key` against the stored `api_key_hash`.

---

## 3. JSON Payload Contract

Version 1.0 JSON telemetry payload schema:

```json
{
  "boot_id": "boot-20260723-001",
  "sequence_number": 1024,
  "timestamp": 1721732160.125,
  "lat": 7.2906,
  "lng": 80.6337,
  "speed_kmh": 58.4,
  "accel_fwd": -0.7,
  "accel_lat": 0.3,
  "yaw_rate": 4.2,
  "harsh_accel": false,
  "harsh_brake": false,
  "harsh_corner": false,
  "overspeed": false
}
```

### Field Definitions

| Field | Type | Description | Valid Range |
| :--- | :--- | :--- | :--- |
| `boot_id` | `string` | Unique boot session ID generated when hardware powers up | Non-empty string |
| `sequence_number` | `integer` | Monotonically increasing sequence number per boot session | `0` to `2^63 - 1` |
| `timestamp` | `number` / `null` | Device timestamp (Unix epoch seconds or ms) | Optional |
| `lat` | `float` / `null` | WGS84 GPS latitude in decimal degrees | `-90.0` to `90.0` |
| `lng` | `float` / `null` | WGS84 GPS longitude in decimal degrees | `-180.0` to `180.0` |
| `speed_kmh` | `float` | Vehicle speed in km/h | `0.0` to `250.0` |
| `accel_fwd` | `float` | Longitudinal acceleration in m/s² (+ for acceleration, - for braking) | `-20.0` to `20.0` |
| `accel_lat` | `float` | Lateral acceleration in m/s² (+ for right turn, - for left turn) | `-20.0` to `20.0` |
| `yaw_rate` | `float` | Gyroscope yaw rate in degrees per second | `-360.0` to `360.0` |

---

## 4. Sample `curl` Requests & Responses

### A. Successful Telemetry Ingestion (Full GPS + Active Trip)

```bash
curl -X POST http://localhost:8000/api/v1/device/telemetry \
  -H "Content-Type: application/json" \
  -H "X-Device-Code: HW-DEV-9001" \
  -H "X-Device-Key: secret-hardware-api-key" \
  -H "X-Telemetry-Schema-Version: 1.0" \
  -d '{
    "boot_id": "boot-20260723-001",
    "sequence_number": 1024,
    "timestamp": 1721732160,
    "lat": 7.2906,
    "lng": 80.6337,
    "speed_kmh": 58.4,
    "accel_fwd": -0.7,
    "accel_lat": 0.3,
    "yaw_rate": 4.2
  }'
```

**Expected Success Response (HTTP 200 OK)**:

```json
{
  "success": true,
  "data": {
    "status": "ACCEPTED",
    "processingStatus": "PROCESSED",
    "telemetryId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "tripId": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
    "serverReceivedAt": "2026-07-23T06:15:00.125Z"
  }
}
```

---

### B. Duplicate Packet Transmit (Idempotency Triggered)

When a hardware device retransmits a packet with an identical `(device_code, boot_id, sequence_number)` combination:

```bash
curl -X POST http://localhost:8000/api/v1/device/telemetry \
  -H "Content-Type: application/json" \
  -H "X-Device-Code: HW-DEV-9001" \
  -H "X-Device-Key: secret-hardware-api-key" \
  -d '{
    "boot_id": "boot-20260723-001",
    "sequence_number": 1024,
    "speed_kmh": 58.4,
    "accel_fwd": -0.7,
    "accel_lat": 0.3,
    "yaw_rate": 4.2
  }'
```

**Expected Duplicate Response (HTTP 200 OK)**:

```json
{
  "success": true,
  "data": {
    "status": "DUPLICATE",
    "processingStatus": "DUPLICATE",
    "telemetryId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

---

### C. Missing / Unavailable GPS Fix

If GPS fix is lost (tunnel, underground parking), `lat` and `lng` may be `null` or omitted:

**Response (HTTP 200 OK - Partial Data Warning)**:

```json
{
  "success": true,
  "data": {
    "status": "ACCEPTED",
    "processingStatus": "PARTIAL",
    "telemetryId": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
    "warnings": [
      {
        "code": "GPS_UNAVAILABLE",
        "message": "Sensor telemetry was accepted without a valid GPS position."
      }
    ]
  }
}
```

---

### D. Error Responses

#### 1. Invalid Credentials or Disabled Device (HTTP 401 Unauthorized)

```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "Invalid device credentials or device is disabled."
  },
  "meta": {
    "requestId": "req_12345",
    "timestamp": "2026-07-23T06:15:00.000Z"
  }
}
```

#### 2. Extreme Sensor Out-of-Range (HTTP 400 Bad Request)

```json
{
  "success": false,
  "error": {
    "code": "TELEMETRY_VALIDATION_FAILED",
    "message": "The telemetry packet contains invalid values.",
    "details": [
      {
        "field": "speed_kmh",
        "message": "The value exceeds the permitted range."
      }
    ]
  },
  "meta": {
    "requestId": "req_12346",
    "timestamp": "2026-07-23T06:15:00.000Z"
  }
}
```
