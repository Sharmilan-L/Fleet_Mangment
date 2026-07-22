# EvolveX Driver Behaviour Intelligence Platform

## WebSocket Realtime Communication Contract

**Document version:** 1.0  
**Project stage:** Pitching MVP  
**Backend:** FastAPI  
**Frontend:** React and TypeScript  
**Local endpoint:** `ws://localhost:8000/ws`  
**Deployed endpoint:** `wss://api-domain/ws`  
**Message format:** JSON  

---

## 1. Purpose

This document defines the realtime communication contract between the FastAPI backend and the React frontend.

WebSocket is used to deliver committed live changes such as:

- Telemetry updates
- Driving events
- Behaviour patterns
- Score changes
- Risk changes
- Alerts
- Device status changes
- Trip status changes
- Trip completion

WebSocket does not replace REST.

REST remains responsible for:

- Initial complete page snapshots
- Historical data
- Manager actions
- Telemetry uploads
- Reconnection recovery

---

## 2. Communication Summary

```text
ESP32 or Simulator
        ↓
REST telemetry upload
        ↓
FastAPI processing
        ↓
PostgreSQL commit
        ↓
WebSocket publication
        ↓
React live dashboard
```

The hardware device and simulator do not send sensor telemetry through the frontend WebSocket connection.

They send telemetry through:

```http
POST /api/v1/device/telemetry
```

---

## 3. Why WebSocket Is Used

REST can imitate live updates by polling repeatedly.

Example:

```text
Frontend asks every second:
“Is there new information?”
```

This creates repeated requests even when nothing has changed.

WebSocket keeps one connection open:

```text
Frontend opens connection
        ↓
Backend keeps connection active
        ↓
Backend sends changes when they occur
```

This provides:

- Faster live updates
- Fewer repeated HTTP requests
- Immediate event notifications
- Immediate score changes
- Immediate device-status changes

---

## 4. WebSocket Responsibilities

WebSocket is used for:

- Current telemetry changes
- Live map movement
- Driving-event creation
- Driving-event updates
- Behaviour-pattern creation
- Behaviour-pattern updates
- Trip score updates
- Trip risk changes
- New alerts
- Alert status changes
- Device online, delayed and offline changes
- Trip status changes
- Trip completion notifications
- Data-quality warnings where useful

---

## 5. WebSocket Restrictions

WebSocket must not be used as the only mechanism for:

- Loading an active trip
- Loading historical telemetry
- Loading completed-trip summaries
- Creating drivers
- Registering vehicles
- Starting trips
- Ending trips
- Uploading hardware telemetry
- Managing rule configurations
- Recovering after a connection gap

These operations use REST.

---

## 6. WebSocket Endpoint

### Local development

```text
ws://localhost:8000/ws
```

### Deployed pitch environment

```text
wss://api-domain/ws
```

The deployed connection must use secure WebSocket:

```text
WSS
```

The reverse proxy must permit WebSocket connection upgrades.

---

## 7. Authentication

The WebSocket connection uses the authenticated human-user session.

The browser includes the secure authentication cookie during the WebSocket handshake.

Conceptually:

```text
Authenticated browser session
        ↓
WebSocket upgrade request
        ↓
FastAPI validates session
        ↓
Connection accepted or rejected
```

The frontend must not send the password through a WebSocket message.

---

## 8. Connection Rejection

The backend must reject the connection when:

- Authentication cookie is missing
- Session is invalid
- Session is expired
- User is disabled
- Organization is disabled
- Request origin is not allowed

Possible close codes:

| Code | Meaning |
|---:|---|
| 1008 | Policy violation or authorization failure |
| 1011 | Unexpected server failure |
| 4001 | Authentication required |
| 4002 | Session expired |
| 4003 | Permission denied |
| 4004 | Organization disabled |

Application-defined close codes should remain documented and stable.

---

## 9. Origin Validation

The backend must validate the browser origin during the WebSocket handshake.

Allowed origins come from environment configuration.

Examples:

```text
http://localhost:5173
https://demo-domain
```

An authenticated cookie alone is not sufficient when the request originates from an unapproved website.

---

## 10. Connection Lifecycle

```text
DISCONNECTED
    ↓
CONNECTING
    ↓
CONNECTED
    ↓
AUTHENTICATED
    ↓
SUBSCRIBED
    ↓
RECONNECTING
    ↓
CONNECTED
```

Possible frontend connection states:

- `DISCONNECTED`
- `CONNECTING`
- `CONNECTED`
- `SUBSCRIBED`
- `RECONNECTING`
- `FAILED`

The dashboard should visibly show the live-connection state.

---

## 11. Connection-Accepted Message

After successful authentication, the server sends:

```json
{
  "type": "CONNECTION_ACCEPTED",
  "messageId": "message-uuid",
  "occurredAt": "2026-07-23T08:15:30.125Z",
  "publishedAt": "2026-07-23T08:15:30.130Z",
  "payload": {
    "connectionId": "connection-uuid",
    "userId": "user-uuid",
    "organizationId": "organization-uuid",
    "heartbeatIntervalSeconds": 20,
    "serverTime": "2026-07-23T08:15:30.130Z"
  }
}
```

The connection is authenticated but not yet subscribed to any trip.

---

## 12. Client Message Envelope

Client-to-server messages use:

```json
{
  "type": "MESSAGE_TYPE",
  "requestId": "client-generated-uuid",
  "sentAt": "2026-07-23T08:15:31.000Z",
  "payload": {}
}
```

Fields:

| Field | Purpose |
|---|---|
| `type` | Requested operation |
| `requestId` | Correlates response with client request |
| `sentAt` | Client message time |
| `payload` | Operation-specific content |

---

## 13. Server Message Envelope

Server-to-client live messages use:

```json
{
  "type": "TELEMETRY_UPDATED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 106,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:16:00.125Z",
  "publishedAt": "2026-07-23T08:16:00.150Z",
  "payload": {}
}
```

### Field meanings

| Field | Meaning |
|---|---|
| `type` | Message type |
| `messageId` | Unique message identity |
| `streamId` | Identifies the current server message stream |
| `sequence` | Ordering value within a subscribed channel |
| `organizationId` | Organization scope |
| `tripId` | Related trip where applicable |
| `transactionId` | Groups messages from one committed transaction |
| `occurredAt` | Time the business event occurred |
| `publishedAt` | Time the message was sent |
| `payload` | Type-specific data |

---

## 14. Stream Identifier

The backend generates a `streamId`.

The stream identifier may change when:

- Backend restarts
- WebSocket publishing service restarts
- Subscription is rebuilt
- Server deployment occurs

When the frontend observes a new stream identifier, it must reload the relevant REST snapshot.

This prevents the frontend from assuming that sequence values from a previous server process are still continuous.

---

## 15. Sequence Numbers

Each subscribed channel receives monotonically increasing sequence numbers during the active stream.

Example:

```text
105
106
107
108
```

If the frontend receives:

```text
105
106
108
```

then sequence `107` may have been missed.

The frontend must:

1. Stop trusting incremental state.
2. Load a fresh REST snapshot.
3. Replace stale local state.
4. Resume applying later messages.

Sequence values support gap detection.

They are not the permanent business record.

PostgreSQL remains the authoritative source.

---

## 16. Message Identity

Every server message has a unique `messageId`.

The frontend should remember recently handled message IDs.

If the same message is received again after reconnection, it should not apply the same UI update twice.

This is especially important for:

- Event counters
- Alert counters
- Score animations
- Notification toasts

---

## 17. Transaction Identifier

Messages created by one committed backend transaction may share the same `transactionId`.

Example:

```text
One harsh-braking transaction
    ↓
DRIVING_EVENT_CREATED
TRIP_SCORE_UPDATED
ALERT_CREATED
```

The shared transaction ID helps debugging and ordering.

The frontend does not use the transaction ID to calculate official results.

---

## 18. Subscribe to Trip

Client sends:

```json
{
  "type": "SUBSCRIBE_TRIP",
  "requestId": "request-uuid",
  "sentAt": "2026-07-23T08:15:31.000Z",
  "payload": {
    "tripId": "trip-uuid",
    "snapshotSequence": 105
  }
}
```

`snapshotSequence` is obtained from:

```http
GET /api/v1/trips/{tripId}/live
```

The backend verifies:

- Trip exists
- Trip belongs to the user’s organization
- User has permission to view the trip
- Trip subscription limit is not exceeded

---

## 19. Trip Subscription Confirmation

Server responds:

```json
{
  "type": "SUBSCRIPTION_CONFIRMED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 106,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "occurredAt": "2026-07-23T08:15:31.020Z",
  "publishedAt": "2026-07-23T08:15:31.025Z",
  "payload": {
    "requestId": "request-uuid",
    "channel": "TRIP",
    "tripId": "trip-uuid",
    "currentSequence": 106,
    "snapshotSequence": 105,
    "snapshotRefreshRequired": true
  }
}
```

When:

```text
currentSequence > snapshotSequence
```

the frontend reloads the REST live snapshot before processing further incremental updates.

This reduces the race between snapshot loading and WebSocket subscription.

---

## 20. Unsubscribe from Trip

Client sends:

```json
{
  "type": "UNSUBSCRIBE_TRIP",
  "requestId": "request-uuid",
  "sentAt": "2026-07-23T08:20:00.000Z",
  "payload": {
    "tripId": "trip-uuid"
  }
}
```

The backend removes the connection from that trip channel.

This should occur when:

- User leaves the live-trip page
- User opens another trip
- Trip monitoring is no longer required

---

## 21. Subscribe to Fleet Channel

The main fleet dashboard may subscribe to organization-level summaries.

Client sends:

```json
{
  "type": "SUBSCRIBE_FLEET",
  "requestId": "request-uuid",
  "sentAt": "2026-07-23T08:15:31.000Z",
  "payload": {}
}
```

The backend derives the organization from the authenticated user.

The client must not select an unrestricted organization ID.

---

## 22. Fleet Subscription Use

The fleet channel may publish compact updates such as:

- Active-trip score changed
- Active-trip risk changed
- Device became offline
- New critical alert
- Trip started
- Trip completed

It should not send every detailed sensor sample for every vehicle unless the dashboard specifically requires it.

Detailed telemetry belongs to trip-specific subscriptions.

---

## 23. Subscription Error

Example:

```json
{
  "type": "SUBSCRIPTION_REJECTED",
  "messageId": "message-uuid",
  "occurredAt": "2026-07-23T08:15:31.020Z",
  "publishedAt": "2026-07-23T08:15:31.025Z",
  "payload": {
    "requestId": "request-uuid",
    "code": "TRIP_SUBSCRIPTION_FORBIDDEN",
    "message": "You are not authorized to monitor this trip."
  }
}
```

Possible codes:

- `TRIP_NOT_FOUND`
- `TRIP_SUBSCRIPTION_FORBIDDEN`
- `ORGANIZATION_MISMATCH`
- `SUBSCRIPTION_LIMIT_REACHED`
- `INVALID_SUBSCRIPTION_REQUEST`

---

# Heartbeat

## 24. Heartbeat Message

The server periodically sends:

```json
{
  "type": "HEARTBEAT",
  "messageId": "message-uuid",
  "occurredAt": "2026-07-23T08:16:20.000Z",
  "publishedAt": "2026-07-23T08:16:20.000Z",
  "payload": {
    "serverTime": "2026-07-23T08:16:20.000Z"
  }
}
```

The client responds:

```json
{
  "type": "HEARTBEAT_ACK",
  "requestId": "request-uuid",
  "sentAt": "2026-07-23T08:16:20.050Z",
  "payload": {
    "receivedMessageId": "message-uuid"
  }
}
```

---

## 25. Heartbeat Timeout

The backend may close a connection when heartbeat acknowledgements are repeatedly missing.

The frontend should treat this as a disconnected connection and begin reconnection.

Heartbeat settings come from monitoring configuration.

Example:

```text
heartbeat interval = 20 seconds
connection timeout = 60 seconds
```

---

# Live Message Types

## 26. Telemetry Updated

Message type:

```text
TELEMETRY_UPDATED
```

Example:

```json
{
  "type": "TELEMETRY_UPDATED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 107,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:16:00.125Z",
  "publishedAt": "2026-07-23T08:16:00.150Z",
  "payload": {
    "telemetryId": "telemetry-uuid",
    "sourceType": "SIMULATOR",
    "speedKmh": 58.4,
    "forwardAccelerationMs2": -0.7,
    "lateralAccelerationMs2": 0.3,
    "yawRateDegS": 4.2,
    "latitude": 7.2906,
    "longitude": 80.6337,
    "gpsValid": true,
    "processingStatus": "PROCESSED",
    "serverReceivedAt": "2026-07-23T08:16:00.125Z"
  }
}
```

Frontend updates:

- Current measurement cards
- Live charts
- Map marker
- Route
- Latest-update time
- Connection indicator

The frontend must not use the values to independently create official events.

---

## 27. Driving Event Created

Message type:

```text
DRIVING_EVENT_CREATED
```

Example:

```json
{
  "type": "DRIVING_EVENT_CREATED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 108,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:16:03.000Z",
  "publishedAt": "2026-07-23T08:16:03.025Z",
  "payload": {
    "eventId": "event-uuid",
    "eventType": "HARSH_BRAKING",
    "status": "ACTIVE",
    "severity": "HIGH",
    "startedAt": "2026-07-23T08:16:01.000Z",
    "primaryMeasurement": -4.2,
    "measurementUnit": "m/s²",
    "thresholdValue": -3.5,
    "location": {
      "latitude": 7.2906,
      "longitude": 80.6337,
      "gpsValid": true
    }
  }
}
```

Frontend updates:

- Event counter
- Timeline
- Event panel
- Map marker
- Optional notification

---

## 28. Driving Event Updated

Message type:

```text
DRIVING_EVENT_UPDATED
```

Used when an active event changes or closes.

Example:

```json
{
  "type": "DRIVING_EVENT_UPDATED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 109,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:16:05.000Z",
  "publishedAt": "2026-07-23T08:16:05.020Z",
  "payload": {
    "eventId": "event-uuid",
    "eventType": "HARSH_BRAKING",
    "status": "COMPLETED",
    "severity": "HIGH",
    "endedAt": "2026-07-23T08:16:05.000Z",
    "durationMs": 4000,
    "peakMeasurement": -4.5
  }
}
```

---

## 29. Behaviour Pattern Created

Message type:

```text
BEHAVIOUR_PATTERN_CREATED
```

Example:

```json
{
  "type": "BEHAVIOUR_PATTERN_CREATED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 120,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:20:00.000Z",
  "publishedAt": "2026-07-23T08:20:00.025Z",
  "payload": {
    "patternId": "pattern-uuid",
    "patternType": "MIXED_AGGRESSIVE",
    "status": "ACTIVE",
    "severity": "HIGH",
    "windowSeconds": 600,
    "eventCount": 5,
    "patternPoints": 12,
    "includedEventIds": [
      "event-uuid-1",
      "event-uuid-2",
      "event-uuid-3"
    ]
  }
}
```

The frontend displays:

- Pattern card
- Pattern timeline item
- Included-event count
- Severity
- Possible alert relationship

---

## 30. Behaviour Pattern Updated

Message type:

```text
BEHAVIOUR_PATTERN_UPDATED
```

Used when:

- Pattern receives another included event
- Severity changes
- Pattern closes
- Pattern becomes voided after review

---

## 31. Trip Score Updated

Message type:

```text
TRIP_SCORE_UPDATED
```

Example:

```json
{
  "type": "TRIP_SCORE_UPDATED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 121,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:20:00.000Z",
  "publishedAt": "2026-07-23T08:20:00.030Z",
  "payload": {
    "ledgerEntryId": "ledger-entry-uuid",
    "entryType": "PATTERN_PENALTY",
    "sourcePatternId": "pattern-uuid",
    "previousScore": 86,
    "pointsDelta": -8,
    "currentScore": 78,
    "previousRiskLevel": "LOW",
    "currentRiskLevel": "MEDIUM",
    "reason": "High-severity mixed aggressive-driving pattern"
  }
}
```

The frontend displays the official backend score.

It must not apply its own penalty calculation.

---

## 32. Alert Created

Message type:

```text
ALERT_CREATED
```

Example:

```json
{
  "type": "ALERT_CREATED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 122,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:20:00.000Z",
  "publishedAt": "2026-07-23T08:20:00.035Z",
  "payload": {
    "alertId": "alert-uuid",
    "alertType": "HIGH_RISK_TRANSITION",
    "priority": "CRITICAL",
    "status": "UNREAD",
    "title": "Trip entered high behavioural risk",
    "message": "The trip score entered the configured high-risk behavioural range.",
    "sourceEventId": null,
    "sourcePatternId": "pattern-uuid",
    "createdAt": "2026-07-23T08:20:00.000Z"
  }
}
```

The alert wording must not claim that an accident occurred or will occur.

---

## 33. Alert Updated

Message type:

```text
ALERT_UPDATED
```

Used when the alert becomes:

- Read
- Acknowledged
- Resolved

Example:

```json
{
  "type": "ALERT_UPDATED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 130,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:22:00.000Z",
  "publishedAt": "2026-07-23T08:22:00.020Z",
  "payload": {
    "alertId": "alert-uuid",
    "previousStatus": "UNREAD",
    "status": "ACKNOWLEDGED",
    "acknowledgedBy": {
      "id": "user-uuid",
      "fullName": "Demo Administrator"
    },
    "acknowledgedAt": "2026-07-23T08:22:00.000Z"
  }
}
```

---

## 34. Device Status Changed

Message type:

```text
DEVICE_STATUS_CHANGED
```

Example:

```json
{
  "type": "DEVICE_STATUS_CHANGED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 140,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:25:00.000Z",
  "publishedAt": "2026-07-23T08:25:00.020Z",
  "payload": {
    "deviceId": "device-uuid",
    "deviceCode": "SIM-DEVICE-001",
    "previousStatus": "DELAYED",
    "currentStatus": "OFFLINE",
    "lastTelemetryAt": "2026-07-23T08:24:45.000Z",
    "reason": "No telemetry received within the configured offline threshold"
  }
}
```

The frontend may display:

```text
Device offline
Displaying last-known location
```

It must not display:

```text
Accident detected
```

unless a separate verified feature exists in the future.

---

## 35. Trip Status Changed

Message type:

```text
TRIP_STATUS_CHANGED
```

Example:

```json
{
  "type": "TRIP_STATUS_CHANGED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 150,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:30:00.000Z",
  "publishedAt": "2026-07-23T08:30:00.020Z",
  "payload": {
    "previousStatus": "ACTIVE",
    "currentStatus": "FINALIZING",
    "reason": "Trip end requested"
  }
}
```

Possible trip states include:

- `ACTIVE`
- `FINALIZING`
- `COMPLETED`
- `CANCELLED`
- `FINALIZATION_FAILED`

---

## 36. Trip Completed

Message type:

```text
TRIP_COMPLETED
```

Example:

```json
{
  "type": "TRIP_COMPLETED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 151,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:30:03.000Z",
  "publishedAt": "2026-07-23T08:30:03.025Z",
  "payload": {
    "status": "COMPLETED",
    "endTime": "2026-07-23T08:30:00.000Z",
    "summaryAvailable": true,
    "finalScore": 78,
    "finalRiskLevel": "MEDIUM",
    "dataQualityLevel": "GOOD",
    "summaryUrl": "/api/v1/trips/trip-uuid/summary"
  }
}
```

After this message, the frontend may:

1. Stop the active-trip subscription.
2. Load the completed summary through REST.
3. Navigate to the completed-trip page.

---

## 37. Data Quality Updated

Optional but recommended message type:

```text
DATA_QUALITY_UPDATED
```

Example:

```json
{
  "type": "DATA_QUALITY_UPDATED",
  "messageId": "message-uuid",
  "streamId": "stream-uuid",
  "sequence": 145,
  "organizationId": "organization-uuid",
  "tripId": "trip-uuid",
  "transactionId": "transaction-uuid",
  "occurredAt": "2026-07-23T08:27:00.000Z",
  "publishedAt": "2026-07-23T08:27:00.020Z",
  "payload": {
    "previousLevel": "GOOD",
    "currentLevel": "ACCEPTABLE",
    "gpsValid": false,
    "recentGapSeconds": 4,
    "confidenceReduced": true,
    "reason": "GPS signal temporarily unavailable"
  }
}
```

Data-quality warnings do not automatically represent unsafe driving.

---

# Message Ordering

## 38. Publish Only After Commit

The required rule is:

```text
Database transaction commits
        ↓
WebSocket messages are published
```

The backend must never publish an official update before the related database transaction commits.

Incorrect:

```text
Publish score = 90
        ↓
Database transaction fails
```

This would show data that does not exist in the database.

Correct:

```text
Commit score = 90
        ↓
Publish score update
```

---

## 39. Message Order Within One Transaction

When one telemetry transaction creates several outputs, use deterministic ordering.

Recommended order:

1. `TELEMETRY_UPDATED`
2. `DRIVING_EVENT_CREATED` or `DRIVING_EVENT_UPDATED`
3. `BEHAVIOUR_PATTERN_CREATED` or `UPDATED`
4. `TRIP_SCORE_UPDATED`
5. `ALERT_CREATED`
6. `DATA_QUALITY_UPDATED`
7. `DEVICE_STATUS_CHANGED`
8. `TRIP_STATUS_CHANGED`
9. `TRIP_COMPLETED`

Only messages actually produced by the transaction are sent.

---

## 40. Frontend Must Tolerate Delayed Messages

The frontend must not assume that internet delivery is perfectly immediate.

It should use:

- Message sequence
- Message ID
- Resource ID
- Occurred time
- Current backend state

Example:

A delayed telemetry message must not overwrite a newer telemetry value.

The frontend should compare sequence values before applying updates.

---

# Reconnection

## 41. Reconnection Strategy

When disconnected, the frontend reconnects using increasing delays.

Suggested sequence:

```text
1 second
2 seconds
4 seconds
8 seconds
15 seconds
30 seconds maximum
```

After a successful connection, the delay resets.

---

## 42. Reconnection Flow

```text
Connection lost
    ↓
Frontend state = RECONNECTING
    ↓
Show connection warning
    ↓
Start REST polling fallback where required
    ↓
Attempt WebSocket reconnection
    ↓
Receive CONNECTION_ACCEPTED
    ↓
Load fresh REST snapshot
    ↓
Subscribe using snapshot sequence
    ↓
Stop fallback polling
    ↓
Resume live updates
```

The frontend must not assume that no changes occurred during disconnection.

---

## 43. REST Polling Fallback

While WebSocket is unavailable, the live page may periodically call:

```http
GET /api/v1/trips/{tripId}/live
```

Suggested MVP fallback interval:

```text
5 seconds
```

Polling should stop after WebSocket recovery.

The fallback ensures that the dashboard still updates during a temporary WebSocket problem.

---

## 44. Browser Refresh Recovery

When the user refreshes the page:

1. React reloads.
2. Authentication is checked through REST.
3. Live-trip snapshot is loaded through REST.
4. New WebSocket connection is opened.
5. Trip subscription is created.
6. Incremental live updates resume.

No live business state should exist only inside the browser.

---

## 45. Server Restart Recovery

When the backend restarts:

- Existing WebSocket connections close.
- Frontend begins reconnection.
- New `streamId` is created.
- Frontend reloads a REST snapshot.
- Frontend subscribes again.

Committed trip, event, score and alert data remains in PostgreSQL.

---

# Rate and Payload Control

## 46. Telemetry Update Frequency

The current hardware and simulator are expected to send approximately one telemetry packet per second.

One WebSocket telemetry update per accepted packet is suitable for the MVP.

If future hardware sends much faster data, the backend may:

- Coalesce display telemetry
- Publish a reduced live rate
- Preserve full raw telemetry in PostgreSQL

The backend must not drop:

- Confirmed event messages
- Score changes
- Alerts
- Trip-status changes

---

## 47. Payload Size

WebSocket payloads should remain compact.

Do not send:

- Entire trip history with every message
- Hundreds of route points in one telemetry update
- Complete event evidence on event creation
- Complete alert history on each alert

Detailed history remains available through REST.

---

## 48. Batching

The MVP may send one message at a time.

Future versions may support controlled batching:

```json
{
  "type": "MESSAGE_BATCH",
  "payload": {
    "messages": []
  }
}
```

Batching is not required for the first pitch version.

---

# Simulation Behaviour

## 49. Simulation Uses Normal WebSocket Messages

Simulation must not use special fake dashboard messages.

The flow is:

```text
Simulation control REST API
        ↓
Simulator creates telemetry
        ↓
Simulator posts to telemetry REST API
        ↓
Backend processes normally
        ↓
Backend publishes normal WebSocket messages
```

A simulated harsh-braking event produces:

```text
DRIVING_EVENT_CREATED
```

not:

```text
FAKE_HARSH_BRAKING
```

---

## 50. Simulation Identification

Telemetry messages for simulated trips include:

```json
{
  "sourceType": "SIMULATOR"
}
```

The trip snapshot also identifies:

```text
tripMode = TEST
```

The frontend must display:

```text
SIMULATION MODE — TEST DATA
```

Simulation messages must not be mixed into official driver-performance screens.

---

# Security

## 51. Organization Isolation

A connection may receive messages only for its authenticated organization.

The client cannot subscribe to another organization by guessing:

- Trip UUID
- Device UUID
- Alert UUID

The backend must verify ownership on every subscription.

---

## 52. Role Authorization

Examples:

| Subscription | Admin | Fleet Manager |
|---|:---:|:---:|
| Own organization fleet channel | Yes | Yes |
| Own organization active trip | Yes | Yes |
| Rule-administration stream | Yes | No |
| Audit stream | Yes | No |

Rule and audit streams are not required for the initial MVP.

---

## 53. Sensitive Values

WebSocket messages must never contain:

- Passwords
- Password hashes
- Device API keys
- Device API-key hashes
- Session tokens
- Database credentials
- Environment secrets
- Internal exception traces

---

## 54. Logging

WebSocket logs may include:

- Connection ID
- User ID
- Organization ID
- Subscription type
- Trip ID
- Message type
- Message ID
- Sequence
- Close code
- Error code

Logs must not contain passwords or secret keys.

---

# Error Messages

## 55. Client Message Error

Example:

```json
{
  "type": "CLIENT_MESSAGE_ERROR",
  "messageId": "message-uuid",
  "occurredAt": "2026-07-23T08:15:31.020Z",
  "publishedAt": "2026-07-23T08:15:31.025Z",
  "payload": {
    "requestId": "request-uuid",
    "code": "INVALID_MESSAGE",
    "message": "The WebSocket message could not be processed.",
    "details": [
      {
        "field": "payload.tripId",
        "message": "A valid trip identifier is required."
      }
    ]
  }
}
```

---

## 56. WebSocket Error Codes

Possible application error codes:

```text
INVALID_MESSAGE
UNSUPPORTED_MESSAGE_TYPE
AUTHENTICATION_REQUIRED
SESSION_EXPIRED
PERMISSION_DENIED
ORGANIZATION_MISMATCH
TRIP_NOT_FOUND
TRIP_SUBSCRIPTION_FORBIDDEN
SUBSCRIPTION_LIMIT_REACHED
HEARTBEAT_TIMEOUT
SERVER_TEMPORARILY_UNAVAILABLE
```

Detailed stack traces must not be returned.

---

# Frontend Handling

## 57. Central WebSocket Client

The React application should have one centralized WebSocket client.

It manages:

- Connection
- Authentication result
- Reconnection
- Heartbeat
- Subscription
- Sequence tracking
- Duplicate message detection
- Dispatch to frontend state

Individual chart components should not independently open their own connections.

---

## 58. Live Trip State

The frontend should maintain a central live-trip state containing:

- Current telemetry
- Current location
- Current score
- Current risk
- Device status
- Event counters
- Active events
- Recent events
- Patterns
- Alerts
- Data quality
- Last sequence
- Stream ID
- Connection state

The state begins from a REST snapshot.

WebSocket messages update that state incrementally.

---

## 59. Message Handling Rules

For each incoming message:

1. Validate required envelope fields.
2. Check the stream ID.
3. Check the sequence.
4. Check whether the message ID was already handled.
5. Confirm the trip ID matches the active subscription.
6. Apply the update.
7. Record the latest sequence.

When validation fails, request a new REST snapshot.

---

## 60. UI Connection Indicator

Suggested states:

```text
LIVE
RECONNECTING
POLLING FALLBACK
OFFLINE
```

Example:

```text
LIVE
Last update: 1 second ago
```

When disconnected:

```text
RECONNECTING
Showing the latest confirmed data
```

---

# Testing Requirements

## 61. Connection Tests

Test:

- Valid session connects
- Missing session is rejected
- Expired session is rejected
- Disabled user is rejected
- Invalid origin is rejected

---

## 62. Subscription Tests

Test:

- Authorized trip subscription succeeds
- Other-organization trip subscription fails
- Missing trip fails
- Unsubscribe stops updates
- Fleet subscription receives only permitted summaries

---

## 63. Message Tests

Test:

- Telemetry message updates current values
- Event-created message updates event count
- Event-updated message closes the event
- Pattern message appears
- Score message updates official score
- Alert message appears
- Device status message updates connection state
- Trip-completed message causes summary loading

---

## 64. Ordering Tests

Test:

- Sequence numbers increase
- Duplicate message is ignored
- Sequence gap triggers snapshot reload
- New stream ID triggers snapshot reload
- Delayed old telemetry does not overwrite newer telemetry

---

## 65. Commit-Boundary Tests

Test:

```text
Database transaction succeeds
→ WebSocket message appears
```

and:

```text
Database transaction fails
→ No official WebSocket message appears
```

---

## 66. Reconnection Tests

Test:

- Network disconnect
- Server restart
- Browser sleep and resume
- Reconnection backoff
- REST polling fallback
- Snapshot reload
- Resubscription
- Duplicate message protection

---

## 67. Simulation Tests

Test:

- Simulation telemetry creates normal telemetry messages
- Simulation event creates normal event messages
- Test-trip badge remains visible
- Test messages do not update official analytics
- Connection-loss scenario produces device status updates

---

# End-to-End Example

## 68. Harsh-Braking Live Flow

```text
1. Simulator sends packet through REST.

2. Telemetry is validated and stored.

3. Rule engine begins harsh-braking candidate.

4. Additional packet confirms event.

5. Event, ledger and score are stored.

6. Database transaction commits.

7. Backend publishes:
   TELEMETRY_UPDATED
   DRIVING_EVENT_CREATED
   TRIP_SCORE_UPDATED
   optional ALERT_CREATED

8. React receives messages in sequence.

9. React updates:
   acceleration graph
   event counter
   event timeline
   score card
   alert panel
```

---

## 69. Device Offline Live Flow

```text
1. Telemetry stops.

2. Device worker detects delayed condition.

3. Device state changes to DELAYED.

4. Transaction commits.

5. DEVICE_STATUS_CHANGED is published.

6. More time passes.

7. Device changes to OFFLINE.

8. Offline alert is stored.

9. Transaction commits.

10. DEVICE_STATUS_CHANGED and ALERT_CREATED are published.

11. Dashboard shows last-known location.

12. Telemetry resumes.

13. Device returns ONLINE.

14. Connection-restored update is published.
```

Offline status alone is not an accident.

---

## 70. Trip Completion Live Flow

```text
1. Manager ends trip through REST.

2. Backend marks trip finalizing.

3. TRIP_STATUS_CHANGED may be published.

4. Backend closes active states.

5. Summary and data quality are calculated.

6. Trip becomes completed.

7. Database transaction commits.

8. TRIP_COMPLETED is published.

9. React loads completed summary through REST.
```

---

# Implementation Boundary

## 71. MVP Connection Manager

For the first MVP, one backend instance may use an in-memory connection manager.

It manages:

- Active connections
- Organization channels
- Trip channels
- Heartbeat state

This is acceptable for:

```text
One FastAPI backend instance
```

---

## 72. Future Multi-Instance Scaling

When multiple backend instances are introduced, an in-memory manager is insufficient because one server cannot see connections held by another server.

Future scaling may use:

- Redis pub/sub
- Redis Socket.IO adapter
- Message broker
- Transactional outbox
- Shared sequence service

These are not required for the pitching MVP.

---

## 73. Transactional Outbox

A transactional outbox is recommended for a later production version.

It would store publishable messages in the same database transaction as business changes.

A separate publisher then sends them to WebSocket clients.

The pitching MVP may publish directly after a successful commit.

If direct publication fails:

- Database data remains correct.
- Frontend recovers through a REST snapshot.
- The failed live message does not alter the official result.

---

# Prohibited Behaviour

## 74. Restrictions

The implementation must not:

- Upload hardware telemetry through the browser WebSocket.
- Use WebSocket as the only source of page state.
- Publish before database commit.
- Trust client-provided organization scope.
- Allow unauthorized trip subscriptions.
- Send secrets in messages.
- Calculate official events in React.
- Calculate official scores in React.
- Insert simulator events directly.
- Create special fake simulation dashboard messages.
- Treat sequence numbers as permanent business records.
- Assume WebSocket delivery is guaranteed.
- Ignore sequence gaps.
- Continue showing stale data without a connection warning.
- Describe device disconnection as an accident.
- Allow test-trip messages to affect official analytics.

---

# Acceptance Criteria

## 75. WebSocket Acceptance Criteria

The WebSocket contract is accepted when:

- The browser authenticates using the human-user session.
- Invalid sessions are rejected.
- Origin validation is applied.
- Users can subscribe only to authorized organization resources.
- The initial trip state is loaded through REST.
- A trip subscription is confirmed.
- Message envelopes use consistent fields.
- Message IDs support duplicate protection.
- Stream IDs support restart detection.
- Sequence numbers support gap detection.
- Telemetry updates appear live.
- Driving events appear live.
- Pattern updates appear live.
- Score and risk changes appear live.
- Alerts appear live.
- Device status changes appear live.
- Trip completion appears live.
- All official messages are published only after database commit.
- The frontend reloads a REST snapshot after sequence gaps.
- The frontend reloads a REST snapshot after stream changes.
- Reconnection uses controlled backoff.
- REST polling fallback works.
- Browser refresh restores state.
- Server restart recovery works.
- Simulation uses the normal processing and message path.
- Test data remains visibly marked.
- Sensitive values are never sent.
- The system works locally through `ws://`.
- The deployed pitch environment works through `wss://`.