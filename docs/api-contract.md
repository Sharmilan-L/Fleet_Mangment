# EvolveX Driver Behaviour Intelligence Platform

## REST API Contract

**Document version:** 1.0  
**Project stage:** Pitching MVP  
**Backend:** FastAPI  
**Base path:** `/api/v1`  
**Data format:** JSON  
**Human authentication:** Secure HTTP-only cookie  
**Device authentication:** Device identifier and API key  

---

## 1. Purpose

This document defines the REST API contract between:

- React frontend and FastAPI backend
- Physical IoT device and FastAPI backend
- Virtual device simulator and FastAPI backend

It specifies:

- Endpoint paths
- HTTP methods
- Authentication
- Request bodies
- Response bodies
- Status codes
- Pagination
- Filtering
- Idempotency
- Business errors

The frontend and simulator must follow this contract.

---

## 2. REST Responsibilities

REST is used for:

- Login and logout
- Current-user information
- User management
- Driver management
- Vehicle management
- Device management
- Device assignment
- Trip creation and completion
- Telemetry upload
- Initial live-trip snapshots
- Historical records
- Events and evidence
- Patterns
- Alerts
- Rule configuration
- Monitoring settings
- Simulation controls
- Completed-trip reports
- Driver profiles
- Audit records

WebSocket is used separately for live updates after a page snapshot is loaded.

---

## 3. Base URLs

### Local development

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
API:      http://localhost:8000/api/v1
```

### Deployed pitch environment

```text
Frontend: https://demo-domain
API:      https://api-domain/api/v1
```

Production and pitch hostnames are configured through environment variables.

---

## 4. Content Type

Normal JSON requests use:

```http
Content-Type: application/json
```

Responses use:

```http
Content-Type: application/json
```

File upload endpoints are not required for the initial MVP.

---

## 5. Identifier Format

Primary identifiers are UUID strings.

Example:

```json
{
  "id": "6eeb936c-846d-4c90-b7d8-5301d684a5af"
}
```

Internal database IDs must not be exposed as predictable sequential identifiers.

---

## 6. Date and Time Format

API timestamps use ISO 8601 UTC format.

Example:

```text
2026-07-23T08:15:30.125Z
```

The backend stores and communicates official timestamps in UTC.

The frontend converts them into the organization or browser timezone for display.

---

## 7. Naming Convention

JSON fields use camelCase.

Example:

```json
{
  "currentScore": 94,
  "riskLevel": "LOW",
  "serverReceivedAt": "2026-07-23T08:15:30.125Z"
}
```

Database column names may use snake_case internally.

---

## 8. Standard Success Response

Single-resource success:

```json
{
  "success": true,
  "data": {
    "id": "resource-uuid"
  },
  "meta": {
    "requestId": "request-uuid",
    "timestamp": "2026-07-23T08:15:30.125Z"
  }
}
```

The `meta` object may be omitted for internal development responses, but should be included consistently before deployment.

---

## 9. Standard List Response

```json
{
  "success": true,
  "data": [
    {
      "id": "resource-uuid"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 54,
    "totalPages": 3
  },
  "meta": {
    "requestId": "request-uuid",
    "timestamp": "2026-07-23T08:15:30.125Z"
  }
}
```

---

## 10. Standard Error Response

```json
{
  "success": false,
  "error": {
    "code": "DRIVER_NOT_FOUND",
    "message": "The requested driver was not found.",
    "details": null
  },
  "meta": {
    "requestId": "request-uuid",
    "timestamp": "2026-07-23T08:15:30.125Z"
  }
}
```

Validation-error example:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid values.",
    "details": [
      {
        "field": "speedKmh",
        "message": "Value must be between 0 and 300."
      }
    ]
  },
  "meta": {
    "requestId": "request-uuid",
    "timestamp": "2026-07-23T08:15:30.125Z"
  }
}
```

Internal stack traces, SQL errors and secrets must not be returned to clients.

---

## 11. HTTP Status Codes

| Status | Meaning |
|---:|---|
| 200 | Successful read or update |
| 201 | Resource created |
| 202 | Accepted for asynchronous processing |
| 204 | Successful action with no response body |
| 400 | Invalid request or business rule violation |
| 401 | Authentication required or invalid |
| 403 | Authenticated but not authorized |
| 404 | Resource not found |
| 409 | Conflict or duplicate active resource |
| 422 | Request validation failed |
| 429 | Rate limit exceeded |
| 500 | Unexpected server error |
| 503 | Dependency temporarily unavailable |

Business-rule conflicts normally use `409`.

---

## 12. Human Authentication

Human users authenticate through email and password.

After login, the backend issues a secure HTTP-only authentication cookie.

The browser sends the cookie automatically with later requests.

Frontend requests must use credentials:

```javascript
fetch(url, {
  credentials: "include"
});
```

The authentication cookie should use:

```text
HttpOnly = true
Secure = true in deployed environments
SameSite = Lax or Strict
```

---

## 13. Human Authorization

Roles:

- `ADMIN`
- `FLEET_MANAGER`

Typical permissions:

| Action | Admin | Fleet Manager |
|---|:---:|:---:|
| View dashboard | Yes | Yes |
| Manage drivers | Yes | Yes |
| Manage vehicles | Yes | Yes |
| Register devices | Yes | Limited or No |
| Rotate device credentials | Yes | No |
| Start/end trips | Yes | Yes |
| View live trips | Yes | Yes |
| Manage rule versions | Yes | No |
| Run simulations | Yes | Configurable |
| Manage users | Yes | No |
| View audit logs | Yes | No |

The backend must enforce permissions.

Frontend visibility is not a security control.

---

## 14. Device Authentication

Device telemetry requests use headers such as:

```http
X-Device-Code: SIM-DEVICE-001
X-Device-Key: secret-device-key
X-Telemetry-Schema-Version: 1.0
```

The transmitted API key is validated against a secure stored representation.

The device must not use:

- Human-user cookies
- Manager JWTs
- PostgreSQL credentials

The endpoint may return `401` when credentials are invalid and `403` when the device is disabled or retired.

---

## 15. Idempotency

Important manager actions may include:

```http
Idempotency-Key: unique-client-generated-value
```

Use cases include:

- Starting a trip
- Ending a trip
- Starting a simulation
- Creating another important retryable resource

When the same valid key is used with the same request:

- The backend returns the original result.
- A duplicate resource is not created.

When the same key is used with a different request body:

```text
409 IDEMPOTENCY_KEY_REUSED
```

Device telemetry uses packet identity such as:

```text
deviceId + bootId + sequenceNumber
```

for duplicate detection.

---

# Health APIs

## 16. Backend Health

```http
GET /health
```

Authentication:

```text
None
```

Response:

```json
{
  "status": "healthy",
  "service": "evolvex-api",
  "timestamp": "2026-07-23T08:15:30.125Z"
}
```

---

## 17. Database Health

```http
GET /api/v1/health/database
```

Authentication:

```text
None or restricted in deployed production
```

Response:

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "database": "connected"
  }
}
```

The endpoint must not reveal credentials or internal host information.

---

# Authentication APIs

## 18. Login

```http
POST /api/v1/auth/login
```

Request:

```json
{
  "email": "admin@evolvex.demo",
  "password": "provided-through-secure-input"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user-uuid",
      "fullName": "Demo Administrator",
      "email": "admin@evolvex.demo",
      "role": "ADMIN",
      "organization": {
        "id": "organization-uuid",
        "name": "EvolveX Demo Fleet"
      }
    }
  }
}
```

Status codes:

- `200` successful
- `401` invalid credentials
- `403` user or organization disabled
- `429` too many attempts

---

## 19. Current User

```http
GET /api/v1/auth/me
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "user-uuid",
    "fullName": "Demo Administrator",
    "email": "admin@evolvex.demo",
    "role": "ADMIN",
    "status": "ACTIVE",
    "organization": {
      "id": "organization-uuid",
      "name": "EvolveX Demo Fleet"
    }
  }
}
```

---

## 20. Logout

```http
POST /api/v1/auth/logout
```

Response:

```json
{
  "success": true,
  "data": {
    "loggedOut": true
  }
}
```

The session is revoked or invalidated server-side where applicable.

---

# Dashboard APIs

## 21. Fleet Dashboard Overview

```http
GET /api/v1/dashboard/overview
```

Response includes:

```json
{
  "success": true,
  "data": {
    "activeTrips": 3,
    "onlineDevices": 7,
    "offlineDevices": 1,
    "unresolvedAlerts": 4,
    "riskDistribution": {
      "low": 2,
      "medium": 1,
      "high": 0
    },
    "recentAlerts": [],
    "activeTripSummaries": []
  }
}
```

Test-trip inclusion should be explicit through a query parameter.

Example:

```http
GET /api/v1/dashboard/overview?includeTestTrips=false
```

Default:

```text
includeTestTrips = false
```

---

## 22. Dashboard Trend

```http
GET /api/v1/dashboard/trends
```

Suggested query parameters:

```text
from
to
interval
includeTestTrips
```

Example:

```http
GET /api/v1/dashboard/trends?from=2026-07-01&to=2026-07-23&interval=day
```

Returns fleet-level event and score trends.

Official analytics exclude test trips by default.

---

# User APIs

## 23. List Users

```http
GET /api/v1/users
```

Authorization:

```text
ADMIN
```

Query parameters:

- `page`
- `pageSize`
- `search`
- `role`
- `status`

---

## 24. Create User

```http
POST /api/v1/users
```

Authorization:

```text
ADMIN
```

Request:

```json
{
  "fullName": "Fleet Manager One",
  "email": "manager@evolvex.demo",
  "role": "FLEET_MANAGER",
  "temporaryPassword": "temporary-secure-password"
}
```

The temporary password must be hashed before database storage.

---

## 25. Update User

```http
PATCH /api/v1/users/{userId}
```

Possible fields:

```json
{
  "fullName": "Updated Name",
  "role": "FLEET_MANAGER",
  "status": "ACTIVE"
}
```

---

# Driver APIs

## 26. List Drivers

```http
GET /api/v1/drivers
```

Query parameters:

- `page`
- `pageSize`
- `search`
- `status`
- `sortBy`
- `sortDirection`

Example:

```http
GET /api/v1/drivers?page=1&pageSize=20&status=ACTIVE
```

---

## 27. Create Driver

```http
POST /api/v1/drivers
```

Request:

```json
{
  "employeeCode": "DRV-001",
  "firstName": "Demo",
  "lastName": "Driver",
  "phone": "+94000000000",
  "email": "driver@example.com",
  "licenseNumber": "LIC-001"
}
```

Response status:

```text
201 Created
```

Possible errors:

- `DRIVER_EMPLOYEE_CODE_EXISTS`
- `DRIVER_LICENSE_EXISTS`
- `VALIDATION_ERROR`

---

## 28. Get Driver

```http
GET /api/v1/drivers/{driverId}
```

Returns the driver’s core record.

---

## 29. Update Driver

```http
PATCH /api/v1/drivers/{driverId}
```

Request example:

```json
{
  "phone": "+94111111111",
  "status": "ACTIVE"
}
```

---

## 30. Driver Profile

```http
GET /api/v1/drivers/{driverId}/profile
```

Returns:

- Core driver information
- Latest official performance snapshot
- Overall score
- Risk level
- Trend
- Confidence
- Primary concern
- Latest eligible trips
- Behaviour rates
- Manager-note summary

Test trips are not included in official performance calculations.

---

## 31. Driver Trips

```http
GET /api/v1/drivers/{driverId}/trips
```

Query parameters:

- `page`
- `pageSize`
- `status`
- `tripMode`
- `from`
- `to`

---

## 32. Driver Behaviour Metrics

```http
GET /api/v1/drivers/{driverId}/behaviour
```

Returns normalized behaviour metrics such as:

- Events per 100 kilometres
- Events per hour
- Weighted severity points
- Event-type breakdown

---

## 33. Driver Events

```http
GET /api/v1/drivers/{driverId}/events
```

This endpoint returns historical confirmed events with filters.

---

## 34. Driver Notes

```http
GET /api/v1/drivers/{driverId}/notes
POST /api/v1/drivers/{driverId}/notes
```

Create request:

```json
{
  "noteText": "Discussed repeated overspeeding behaviour."
}
```

---

# Vehicle APIs

## 35. List Vehicles

```http
GET /api/v1/vehicles
```

Query parameters:

- `page`
- `pageSize`
- `search`
- `status`
- `vehicleType`

---

## 36. Create Vehicle

```http
POST /api/v1/vehicles
```

Request:

```json
{
  "registrationNumber": "ABC-1234",
  "vehicleCode": "VEH-001",
  "make": "Demo Make",
  "model": "Demo Model",
  "manufactureYear": 2022,
  "vehicleType": "VAN",
  "defaultSpeedLimitKmh": 60
}
```

---

## 37. Get Vehicle

```http
GET /api/v1/vehicles/{vehicleId}
```

Returns vehicle details and current assignment summary.

---

## 38. Update Vehicle

```http
PATCH /api/v1/vehicles/{vehicleId}
```

---

## 39. Vehicle Trips

```http
GET /api/v1/vehicles/{vehicleId}/trips
```

---

## 40. Vehicle Live State

```http
GET /api/v1/vehicles/{vehicleId}/live
```

Returns:

- Current assignment
- Active trip if available
- Latest speed
- Latest location
- Connection status
- Last telemetry time

---

# Device APIs

## 41. List Devices

```http
GET /api/v1/devices
```

Filters:

- `deviceType`
- `administrativeStatus`
- `connectionStatus`
- `search`

---

## 42. Register Device

```http
POST /api/v1/devices
```

Authorization:

```text
ADMIN
```

Request:

```json
{
  "deviceCode": "SIM-DEVICE-001",
  "displayName": "Pitch Simulator Device",
  "deviceType": "SIMULATOR",
  "administrativeStatus": "TESTING",
  "firmwareVersion": "simulator-1.0",
  "telemetrySchemaVersion": "1.0"
}
```

Response includes the API key only once:

```json
{
  "success": true,
  "data": {
    "device": {
      "id": "device-uuid",
      "deviceCode": "SIM-DEVICE-001"
    },
    "apiKey": "one-time-visible-device-key"
  }
}
```

The plain key must not be returned again later.

---

## 43. Get Device

```http
GET /api/v1/devices/{deviceId}
```

Returns administrative and connection information but never returns the API key.

---

## 44. Update Device

```http
PATCH /api/v1/devices/{deviceId}
```

---

## 45. Rotate Device Credential

```http
POST /api/v1/devices/{deviceId}/rotate-credential
```

Authorization:

```text
ADMIN
```

Response returns the new key once.

The old key is invalidated according to the selected rotation strategy.

---

## 46. Device Diagnostics

```http
GET /api/v1/devices/{deviceId}/diagnostics
```

Returns:

- Last received telemetry time
- Connection status
- Firmware version
- Telemetry schema version
- Recent processing failures
- Current assignment
- Recent gaps

---

# Device Assignment APIs

## 47. List Assignments

```http
GET /api/v1/device-assignments
```

Filters:

- `vehicleId`
- `deviceId`
- `status`
- `from`
- `to`

---

## 48. Create Device Assignment

```http
POST /api/v1/device-assignments
```

Request:

```json
{
  "deviceId": "device-uuid",
  "vehicleId": "vehicle-uuid",
  "assignedAt": "2026-07-23T08:00:00Z",
  "notes": "Pitch simulator assignment"
}
```

Conflicts:

- Device already actively assigned
- Vehicle already has an active primary device
- Organization mismatch
- Device or vehicle inactive

---

## 49. End Device Assignment

```http
POST /api/v1/device-assignments/{assignmentId}/end
```

Request:

```json
{
  "unassignedAt": "2026-07-23T10:00:00Z",
  "notes": "Device removed"
}
```

An assignment used by an active trip must not be ended without controlled trip resolution.

---

# Trip APIs

## 50. Trip Start Options

```http
GET /api/v1/trips/start-options
```

Returns eligible:

- Drivers
- Vehicles
- Active device assignments
- Default speed limits
- Available trip modes
- Active rule version

Response example:

```json
{
  "success": true,
  "data": {
    "drivers": [],
    "vehicles": [],
    "tripModes": [
      "OFFICIAL",
      "TEST"
    ],
    "activeRuleVersion": {
      "id": "rule-version-uuid",
      "versionNumber": 1
    }
  }
}
```

---

## 51. Start Trip

```http
POST /api/v1/trips
```

Recommended header:

```http
Idempotency-Key: unique-start-trip-key
```

Request:

```json
{
  "driverId": "driver-uuid",
  "vehicleId": "vehicle-uuid",
  "tripMode": "TEST",
  "appliedSpeedLimitKmh": 60,
  "startReason": "Pitch demonstration"
}
```

The backend resolves the device assignment.

The client must not choose an arbitrary unassigned device.

Response:

```json
{
  "success": true,
  "data": {
    "id": "trip-uuid",
    "tripCode": "TRIP-2026-0001",
    "status": "ACTIVE",
    "tripMode": "TEST",
    "driver": {},
    "vehicle": {},
    "device": {},
    "startTime": "2026-07-23T08:15:30.125Z",
    "currentScore": 100,
    "riskLevel": "LOW",
    "ruleSetVersionId": "rule-version-uuid"
  }
}
```

Possible errors:

- `DRIVER_NOT_ACTIVE`
- `VEHICLE_NOT_ACTIVE`
- `DEVICE_NOT_AVAILABLE`
- `VEHICLE_HAS_NO_ACTIVE_DEVICE`
- `DRIVER_ALREADY_ON_ACTIVE_TRIP`
- `VEHICLE_ALREADY_ON_ACTIVE_TRIP`
- `DEVICE_ASSIGNMENT_ALREADY_ON_ACTIVE_TRIP`
- `ACTIVE_RULE_VERSION_NOT_FOUND`

---

## 52. List Trips

```http
GET /api/v1/trips
```

Filters:

- `page`
- `pageSize`
- `status`
- `tripMode`
- `driverId`
- `vehicleId`
- `riskLevel`
- `from`
- `to`

Test trips should be excluded from official-report screens unless requested.

---

## 53. Active Trips

```http
GET /api/v1/trips/active
```

Response contains compact active-trip summaries.

---

## 54. Get Trip

```http
GET /api/v1/trips/{tripId}
```

Returns trip identity, relationships and current status.

---

## 55. Live Trip Snapshot

```http
GET /api/v1/trips/{tripId}/live
```

This endpoint supplies the complete current state before WebSocket subscription.

Response should include:

```json
{
  "success": true,
  "data": {
    "trip": {
      "id": "trip-uuid",
      "tripCode": "TRIP-2026-0001",
      "status": "ACTIVE",
      "tripMode": "TEST",
      "startTime": "2026-07-23T08:15:30.125Z"
    },
    "driver": {},
    "vehicle": {},
    "device": {
      "connectionStatus": "ONLINE"
    },
    "telemetrySource": "SIMULATOR",
    "latestTelemetry": {
      "speedKmh": 54.2,
      "forwardAccelerationMs2": 0.4,
      "lateralAccelerationMs2": 0.3,
      "yawRateDegS": 2.1,
      "latitude": 7.2906,
      "longitude": 80.6337,
      "gpsValid": true,
      "serverReceivedAt": "2026-07-23T08:16:00.125Z"
    },
    "score": {
      "currentScore": 100,
      "riskLevel": "LOW"
    },
    "thresholds": {},
    "eventCounters": {},
    "activeEvents": [],
    "recentEvents": [],
    "activePatterns": [],
    "recentAlerts": [],
    "dataQuality": {
      "level": "GOOD"
    },
    "liveSequence": 105
  }
}
```

---

## 56. Recent Trip Telemetry

```http
GET /api/v1/trips/{tripId}/telemetry
```

Query parameters:

- `from`
- `to`
- `limit`
- `before`
- `downsample`

This endpoint is used for charts and recovery.

It must avoid returning an unlimited telemetry history in one request.

---

## 57. Trip Signal Series

```http
GET /api/v1/trips/{tripId}/series
```

Query parameters:

- `signal`
- `from`
- `to`
- `resolution`

Possible signals:

- `speed`
- `forwardAcceleration`
- `lateralAcceleration`
- `yawRate`

Response contains chart-ready points.

---

## 58. Trip Route

```http
GET /api/v1/trips/{tripId}/route
```

Query parameters:

- `from`
- `to`
- `resolution`

Returns valid GPS points and event-marker summaries.

---

## 59. End Trip

```http
POST /api/v1/trips/{tripId}/end
```

Recommended header:

```http
Idempotency-Key: unique-end-trip-key
```

Request:

```json
{
  "endReason": "Pitch demonstration completed"
}
```

Synchronous MVP response:

```json
{
  "success": true,
  "data": {
    "tripId": "trip-uuid",
    "status": "COMPLETED",
    "summaryAvailable": true
  }
}
```

If finalization becomes asynchronous:

```text
202 Accepted
```

with a finalization-status resource.

---

## 60. Cancel Trip

```http
POST /api/v1/trips/{tripId}/cancel
```

Request:

```json
{
  "reason": "Trip created by mistake"
}
```

Cancelled trips do not update official driver analytics.

---

## 61. Completed Trip Summary

```http
GET /api/v1/trips/{tripId}/summary
```

Returns:

- Duration
- Distance estimate
- Average and maximum speed
- Event counts
- Pattern counts
- Final score
- Final risk
- Score breakdown
- Data quality
- Primary concern
- Rule-based recommendation
- Analytics eligibility

---

## 62. Trip Score History

```http
GET /api/v1/trips/{tripId}/score-history
```

Response example:

```json
{
  "success": true,
  "data": [
    {
      "entryType": "INITIAL",
      "previousScore": 100,
      "pointsDelta": 0,
      "newScore": 100
    },
    {
      "entryType": "EVENT_PENALTY",
      "sourceEventId": "event-uuid",
      "previousScore": 100,
      "pointsDelta": -4,
      "newScore": 96
    }
  ]
}
```

---

## 63. Trip Review

```http
GET  /api/v1/trips/{tripId}/review
POST /api/v1/trips/{tripId}/review
```

Request:

```json
{
  "reviewStatus": "REVIEWED",
  "reviewNote": "Trip data checked.",
  "excludeFromDriverAnalytics": false
}
```

---

# Telemetry API

## 64. Submit Device Telemetry

```http
POST /api/v1/device/telemetry
```

Authentication headers:

```http
X-Device-Code: SIM-DEVICE-001
X-Device-Key: secret-device-key
X-Telemetry-Schema-Version: 1.0
```

Version 1 request example:

```json
{
  "boot_id": "boot-001",
  "sequence_number": 1024,
  "timestamp": 98500,
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

The adapter converts this into the standard internal telemetry model.

Accepted response:

```json
{
  "success": true,
  "data": {
    "status": "ACCEPTED",
    "processingStatus": "PROCESSED",
    "telemetryId": "telemetry-uuid",
    "tripId": "trip-uuid",
    "serverReceivedAt": "2026-07-23T08:16:00.125Z"
  }
}
```

Partial response:

```json
{
  "success": true,
  "data": {
    "status": "ACCEPTED",
    "processingStatus": "PARTIAL",
    "telemetryId": "telemetry-uuid",
    "warnings": [
      {
        "code": "GPS_UNAVAILABLE",
        "message": "Sensor telemetry was accepted without a valid GPS position."
      }
    ]
  }
}
```

Duplicate response:

```json
{
  "success": true,
  "data": {
    "status": "DUPLICATE",
    "processingStatus": "DUPLICATE",
    "telemetryId": "existing-telemetry-uuid"
  }
}
```

Invalid request:

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
  }
}
```

---

## 65. Telemetry Source Determination

The device does not choose an unrestricted source value.

The backend determines the source from:

- Device type
- Authenticated device record
- Replay context
- Controlled simulation context

Examples:

```text
Physical device → HARDWARE
Simulator device → SIMULATOR
Approved replay process → REPLAY
```

This prevents a physical device from pretending to be another source type.

---

## 66. Telemetry Without Active Trip

When no active trip exists:

- Packet may be stored as unassigned telemetry.
- Device latest state may be updated.
- Vehicle latest state may be updated if assignment exists.
- Official event and score processing does not run.
- No driver is assigned.

Response may contain:

```json
{
  "success": true,
  "data": {
    "status": "ACCEPTED",
    "processingStatus": "PROCESSED",
    "tripId": null,
    "assignmentStatus": "NO_ACTIVE_TRIP"
  }
}
```

---

# Event APIs

## 67. List Events

```http
GET /api/v1/events
```

Filters:

- `tripId`
- `driverId`
- `vehicleId`
- `eventType`
- `severity`
- `status`
- `from`
- `to`
- `page`
- `pageSize`

---

## 68. Get Event

```http
GET /api/v1/events/{eventId}
```

Returns:

- Event details
- Severity
- Measurements
- Thresholds
- Rule version
- Trip context
- Evidence summary
- Score impact
- Review status

---

## 69. Event Evidence

```http
GET /api/v1/events/{eventId}/evidence
```

Returns:

- Linked telemetry records
- Evidence roles
- Chart series
- Event start and end
- Threshold lines
- Peak measurement
- Location where available

---

## 70. Void Event

```http
POST /api/v1/events/{eventId}/void
```

Authorization:

```text
ADMIN or approved reviewer
```

Request:

```json
{
  "reason": "Confirmed invalid because of sensor calibration fault."
}
```

The backend must:

1. Mark the event voided.
2. Reverse active event penalty where applicable.
3. Recalculate score and risk.
4. Update dependent pattern validity where required.
5. Preserve original evidence.
6. Create an audit record.
7. Publish live updates after commit.

The event must not be deleted.

---

# Pattern APIs

## 71. List Patterns

```http
GET /api/v1/patterns
```

Filters:

- `tripId`
- `driverId`
- `patternType`
- `severity`
- `status`
- `from`
- `to`

---

## 72. Get Pattern

```http
GET /api/v1/patterns/{patternId}
```

Returns:

- Pattern type
- Severity
- Rolling window
- Included events
- Event weights
- Pattern points
- Score impact
- Status

---

# Alert APIs

## 73. List Alerts

```http
GET /api/v1/alerts
```

Filters:

- `status`
- `priority`
- `alertType`
- `tripId`
- `driverId`
- `vehicleId`
- `from`
- `to`
- `page`
- `pageSize`

---

## 74. Get Alert

```http
GET /api/v1/alerts/{alertId}
```

---

## 75. Mark Alert Read

```http
POST /api/v1/alerts/{alertId}/read
```

---

## 76. Acknowledge Alert

```http
POST /api/v1/alerts/{alertId}/acknowledge
```

Request:

```json
{
  "note": "Fleet manager contacted the driver."
}
```

---

## 77. Resolve Alert

```http
POST /api/v1/alerts/{alertId}/resolve
```

Request:

```json
{
  "resolutionNote": "Condition ended and follow-up completed."
}
```

---

# Rule Configuration APIs

## 78. List Rule Sets

```http
GET /api/v1/rule-sets
```

Authorization:

```text
ADMIN
```

---

## 79. Create Rule Set

```http
POST /api/v1/rule-sets
```

Request:

```json
{
  "name": "Default Fleet Safety Rules",
  "description": "Initial EvolveX pitching configuration"
}
```

---

## 80. List Rule Versions

```http
GET /api/v1/rule-sets/{ruleSetId}/versions
```

---

## 81. Create Draft Rule Version

```http
POST /api/v1/rule-sets/{ruleSetId}/versions
```

Request may copy an existing version:

```json
{
  "copyFromVersionId": "existing-version-uuid"
}
```

---

## 82. Get Rule Version

```http
GET /api/v1/rule-versions/{ruleVersionId}
```

Returns:

- Acceleration rules
- Overspeed rules
- Turning rules
- Pattern rules
- Severity bands
- Penalties
- Risk bands
- Assessment rules

---

## 83. Update Draft Rule Version

```http
PATCH /api/v1/rule-versions/{ruleVersionId}
```

Only a draft version may be changed.

Activated versions are immutable.

---

## 84. Validate Rule Version

```http
POST /api/v1/rule-versions/{ruleVersionId}/validate
```

Response:

```json
{
  "success": true,
  "data": {
    "valid": true,
    "errors": [],
    "warnings": []
  }
}
```

Validation checks include:

- Required event rules
- No overlapping invalid bands
- Complete risk score coverage
- Penalty values
- Release thresholds
- Duration values
- Pattern configurations

---

## 85. Activate Rule Version

```http
POST /api/v1/rule-versions/{ruleVersionId}/activate
```

Authorization:

```text
ADMIN
```

Existing active trips keep their original rule version.

Future trips use the newly active version.

---

# Monitoring Settings APIs

## 86. Get Monitoring Settings

```http
GET /api/v1/monitoring-settings
```

---

## 87. Update Monitoring Settings

```http
PATCH /api/v1/monitoring-settings
```

Authorization:

```text
ADMIN
```

Request example:

```json
{
  "deviceDelayedAfterSeconds": 5,
  "deviceOfflineAfterSeconds": 15,
  "websocketHeartbeatSeconds": 20,
  "liveTelemetryWindowSeconds": 120
}
```

Behaviour thresholds must not be placed here.

They belong to rule versions.

---

# Simulation APIs

## 88. List Simulation Scenarios

```http
GET /api/v1/simulation/scenarios
```

Returns enabled scenarios.

---

## 89. Start Simulation

```http
POST /api/v1/simulation/start
```

Recommended header:

```http
Idempotency-Key: unique-simulation-start-key
```

Request:

```json
{
  "tripId": "test-trip-uuid",
  "scenarioCode": "FULL_PITCH_DEMO",
  "packetIntervalMs": 1000,
  "randomSeed": 2026
}
```

Validation:

- Trip must exist.
- Trip mode must be `TEST`.
- Trip must be active.
- Assigned device must be a simulator device.
- No conflicting simulation may already be running.

Response:

```json
{
  "success": true,
  "data": {
    "simulationRunId": "simulation-run-uuid",
    "status": "RUNNING",
    "scenarioCode": "FULL_PITCH_DEMO"
  }
}
```

---

## 90. Get Simulation Status

```http
GET /api/v1/simulation/status
```

Optional query:

```text
tripId
simulationRunId
```

Response:

```json
{
  "success": true,
  "data": {
    "simulationRunId": "simulation-run-uuid",
    "status": "RUNNING",
    "currentStep": 42,
    "totalSteps": 110,
    "progressPercentage": 38.2
  }
}
```

---

## 91. Pause Simulation

```http
POST /api/v1/simulation/pause
```

Request:

```json
{
  "simulationRunId": "simulation-run-uuid"
}
```

---

## 92. Resume Simulation

```http
POST /api/v1/simulation/resume
```

---

## 93. Stop Simulation

```http
POST /api/v1/simulation/stop
```

Request:

```json
{
  "simulationRunId": "simulation-run-uuid",
  "reason": "Pitch scenario stopped by operator"
}
```

Stopping the simulator does not automatically end the trip unless explicitly configured.

---

# Audit APIs

## 94. List Audit Logs

```http
GET /api/v1/audit-logs
```

Authorization:

```text
ADMIN
```

Filters:

- `userId`
- `action`
- `targetType`
- `targetId`
- `from`
- `to`
- `page`
- `pageSize`

Sensitive values must be redacted.

---

# Pagination and Filtering

## 95. Pagination Rules

Default values:

```text
page = 1
pageSize = 20
```

Maximum page size:

```text
100
```

Large telemetry endpoints may use cursor-based pagination rather than page numbers.

---

## 96. Sorting

Suggested query parameters:

```text
sortBy
sortDirection
```

Allowed values must be explicitly whitelisted.

The client must not send arbitrary SQL field names.

---

## 97. Date Range Filters

Date filters use:

```text
from
to
```

Example:

```http
GET /api/v1/events?from=2026-07-01T00:00:00Z&to=2026-07-23T23:59:59Z
```

The backend validates:

```text
from <= to
```

---

# Business Error Codes

## 98. General Errors

```text
VALIDATION_ERROR
AUTHENTICATION_REQUIRED
INVALID_CREDENTIALS
PERMISSION_DENIED
RESOURCE_NOT_FOUND
ORGANIZATION_MISMATCH
CONFLICT
RATE_LIMIT_EXCEEDED
DATABASE_UNAVAILABLE
INTERNAL_SERVER_ERROR
```

---

## 99. Driver Errors

```text
DRIVER_NOT_FOUND
DRIVER_NOT_ACTIVE
DRIVER_EMPLOYEE_CODE_EXISTS
DRIVER_LICENSE_EXISTS
DRIVER_ALREADY_ON_ACTIVE_TRIP
```

---

## 100. Vehicle Errors

```text
VEHICLE_NOT_FOUND
VEHICLE_NOT_ACTIVE
VEHICLE_REGISTRATION_EXISTS
VEHICLE_HAS_NO_ACTIVE_DEVICE
VEHICLE_ALREADY_ON_ACTIVE_TRIP
```

---

## 101. Device Errors

```text
DEVICE_NOT_FOUND
DEVICE_CREDENTIAL_INVALID
DEVICE_DISABLED
DEVICE_SCHEMA_UNSUPPORTED
DEVICE_ALREADY_ASSIGNED
DEVICE_NOT_ASSIGNED
DEVICE_ASSIGNMENT_CONFLICT
DEVICE_ASSIGNMENT_ALREADY_ON_ACTIVE_TRIP
```

---

## 102. Trip Errors

```text
TRIP_NOT_FOUND
TRIP_NOT_ACTIVE
TRIP_ALREADY_COMPLETED
TRIP_ALREADY_CANCELLED
ACTIVE_RULE_VERSION_NOT_FOUND
TRIP_FINALIZATION_FAILED
TEST_TRIP_REQUIRED
OFFICIAL_TRIP_REQUIRED
```

---

## 103. Telemetry Errors

```text
TELEMETRY_VALIDATION_FAILED
TELEMETRY_SCHEMA_UNSUPPORTED
TELEMETRY_DUPLICATE
TELEMETRY_CONTEXT_UNAVAILABLE
TELEMETRY_PROCESSING_FAILED
TELEMETRY_VALUE_OUT_OF_RANGE
```

---

## 104. Rule Errors

```text
RULE_SET_NOT_FOUND
RULE_VERSION_NOT_FOUND
RULE_VERSION_NOT_DRAFT
RULE_VERSION_INVALID
RULE_VERSION_ALREADY_ACTIVE
RISK_BAND_COVERAGE_INVALID
SEVERITY_BAND_INVALID
```

---

## 105. Simulation Errors

```text
SIMULATION_SCENARIO_NOT_FOUND
SIMULATION_ALREADY_RUNNING
SIMULATION_NOT_RUNNING
SIMULATION_NOT_PAUSED
SIMULATOR_DEVICE_REQUIRED
TEST_TRIP_REQUIRED
SIMULATION_FAILED
```

---

# API Security Requirements

## 106. Organization Scope

Every organization-owned query must include organization authorization.

Example:

```text
Authenticated user organization
    must match
Requested trip organization
```

Guessing another UUID must not reveal another organization’s data.

---

## 107. Input Validation

All request bodies, path values and query values must use Pydantic validation.

Validation must occur before business processing.

---

## 108. Rate Limiting

Higher protection is recommended for:

- Login
- Device telemetry
- Credential rotation
- Simulation start
- Expensive historical queries

Rate-limit responses use:

```text
429 Too Many Requests
```

---

## 109. Sensitive Data

Responses must not expose:

- Password hashes
- Session token hashes
- Device API key hashes
- Database connection strings
- Internal exception traces
- Secret environment variables

---

# Frontend Page-to-API Mapping

## 110. Login Page

Uses:

```text
POST /auth/login
GET /auth/me
```

---

## 111. Fleet Dashboard

Uses:

```text
GET /dashboard/overview
GET /dashboard/trends
GET /trips/active
GET /alerts
```

WebSocket supplies later live changes.

---

## 112. Drivers Page

Uses:

```text
GET /drivers
POST /drivers
PATCH /drivers/{driverId}
```

---

## 113. Driver Profile Page

Uses:

```text
GET /drivers/{driverId}/profile
GET /drivers/{driverId}/trips
GET /drivers/{driverId}/behaviour
GET /drivers/{driverId}/events
GET /drivers/{driverId}/notes
```

---

## 114. Vehicles Page

Uses:

```text
GET /vehicles
POST /vehicles
PATCH /vehicles/{vehicleId}
GET /vehicles/{vehicleId}/live
```

---

## 115. Devices Page

Uses:

```text
GET /devices
POST /devices
PATCH /devices/{deviceId}
POST /devices/{deviceId}/rotate-credential
GET /devices/{deviceId}/diagnostics
```

---

## 116. Start Trip Page

Uses:

```text
GET /trips/start-options
POST /trips
```

---

## 117. Live Trip Page

Initial loading:

```text
GET /trips/{tripId}/live
GET /trips/{tripId}/telemetry
GET /trips/{tripId}/route
```

Actions:

```text
POST /trips/{tripId}/end
POST /simulation/start
POST /simulation/pause
POST /simulation/resume
POST /simulation/stop
```

Later changes arrive through WebSocket.

---

## 118. Completed Trip Page

Uses:

```text
GET /trips/{tripId}
GET /trips/{tripId}/summary
GET /trips/{tripId}/route
GET /trips/{tripId}/score-history
GET /events?tripId={tripId}
GET /patterns?tripId={tripId}
```

---

## 119. Alerts Page

Uses:

```text
GET /alerts
GET /alerts/{alertId}
POST /alerts/{alertId}/read
POST /alerts/{alertId}/acknowledge
POST /alerts/{alertId}/resolve
```

---

## 120. Rule Settings Page

Uses:

```text
GET /rule-sets
GET /rule-sets/{ruleSetId}/versions
GET /rule-versions/{ruleVersionId}
POST /rule-sets/{ruleSetId}/versions
PATCH /rule-versions/{ruleVersionId}
POST /rule-versions/{ruleVersionId}/validate
POST /rule-versions/{ruleVersionId}/activate
```

---

# REST Recovery Behaviour

## 121. WebSocket Recovery Snapshot

When WebSocket disconnects:

1. Frontend shows reconnecting state.
2. Frontend may poll `GET /trips/{tripId}/live`.
3. Frontend reconnects WebSocket.
4. Frontend loads a fresh live snapshot.
5. Frontend replaces stale local state.
6. Frontend resumes applying messages.

REST remains the authoritative recovery method.

---

# API Versioning

## 122. API Version

The initial API uses:

```text
/api/v1
```

Breaking contract changes require a new API version or controlled migration.

Adding optional response fields does not necessarily require a new major API version.

---

## 123. Telemetry Schema Version

API version and telemetry schema version are separate.

Example:

```text
API endpoint version: /api/v1
Telemetry schema: 1.0
```

A new hardware payload format may introduce telemetry schema `2.0` without immediately changing the complete REST API version.

---

# API Restrictions

## 124. Prohibited Behaviour

The implementation must not:

- Return raw database errors.
- Accept organization IDs from clients without authorization checks.
- Let the frontend calculate official scores.
- Let the frontend directly create events or patterns.
- Allow simulator control APIs to insert events directly.
- Trust telemetry source from an unrestricted request field.
- Allow hardware flags to become official events automatically.
- Allow test trips to update official analytics.
- Return plaintext device keys after initial creation or rotation.
- Allow updates to activated rule versions.
- Return unlimited telemetry records.
- Publish WebSocket updates before the database transaction commits.
- Use WebSocket as the only source for current page state.

---

# API Acceptance Criteria

## 125. Acceptance Criteria

The REST API contract is accepted when:

- All endpoints use `/api/v1` except the top-level health endpoint.
- Human and device authentication remain separate.
- Responses use consistent success and error envelopes.
- Validation errors identify affected fields safely.
- Organization authorization is enforced.
- Driver, vehicle and device management are supported.
- Device assignment history is supported.
- Trip start validates all active-resource conflicts.
- Trip start uses the active device assignment.
- Telemetry supports hardware, simulator and replay sources.
- Telemetry duplicate detection is supported.
- Missing GPS can produce partial processing.
- Telemetry without an active trip does not update driver scoring.
- Initial live state is available through REST.
- Historical telemetry queries are bounded.
- Events include evidence access.
- Score history is available.
- Event voiding preserves evidence and reverses score impact.
- Alert lifecycle actions are supported.
- Activated rule versions are immutable.
- Simulation works only with test trips and simulator devices.
- Test data is excluded from official analytics.
- Idempotency is supported for important retryable actions.
- Sensitive values are never returned.
- REST supports WebSocket reconnection recovery.