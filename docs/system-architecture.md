# EvolveX Driver Behaviour Intelligence Platform

## System Architecture Document

**Document version:** 1.0  
**Project stage:** Pitching MVP  
**Architecture type:** Modular monolith  
**Frontend:** React and TypeScript  
**Backend:** FastAPI and Python  
**Database:** PostgreSQL  
**Realtime communication:** WebSocket  

---

## 1. Purpose

This document explains how all EvolveX components are connected and how data moves through the system.

It defines the responsibilities of:

- Physical IoT hardware
- Virtual device simulator
- Telemetry ingestion API
- Backend processing modules
- PostgreSQL database
- REST APIs
- WebSocket communication
- React dashboard
- Background workers
- Local and deployed environments

This document is the approved source of truth for system-level architecture.

Application code must follow this architecture unless the architecture is formally reviewed and updated.

---

## 2. Product Architecture Summary

EvolveX is implemented as a modular monolith.

The MVP consists of:

1. One React frontend
2. One FastAPI backend application
3. One PostgreSQL database
4. One background worker process
5. One physical or simulated telemetry source

The internal backend is divided into modules, but all modules are deployed as one backend application.

```text
Physical ESP32 Device
          │
          │
          ├──────────────┐
          │              │
          ▼              ▼
Telemetry API      Virtual Device Simulator
          │              │
          └──────┬───────┘
                 │
                 ▼
          FastAPI Backend
                 │
        ┌────────┼────────┐
        │        │        │
        ▼        ▼        ▼
   PostgreSQL   REST   WebSocket
        │        │        │
        └────────┴────────┘
                 │
                 ▼
          React Dashboard
```

The physical device and simulator use the same telemetry ingestion endpoint.

The backend does not maintain separate event-processing logic for hardware and simulation.

---

## 3. Architecture Principles

The system must follow these principles.

### 3.1 One official backend processing path

All telemetry must pass through:

```text
Authentication
    ↓
Schema adaptation
    ↓
Validation
    ↓
Context resolution
    ↓
Raw storage
    ↓
Rule processing
    ↓
Pattern processing
    ↓
Scoring
    ↓
Alerts
    ↓
Database commit
    ↓
WebSocket publication
```

No frontend component, simulator component or hardware flag may directly create an official event or score.

### 3.2 Backend is the source of truth

The backend is responsible for official:

- Event detection
- Severity classification
- Behaviour-pattern detection
- Score calculation
- Risk calculation
- Alert creation
- Trip finalization
- Driver analytics

The frontend only displays backend results.

### 3.3 PostgreSQL is the persistent evidence store

PostgreSQL stores:

- Raw telemetry
- Trip context
- Rule versions
- Events
- Event evidence
- Patterns
- Score changes
- Alerts
- Trip summaries
- Driver analytics
- Audit history

### 3.4 REST and WebSocket have separate responsibilities

REST is used for:

- One-time actions
- Data creation and updates
- Telemetry uploads
- Initial page snapshots
- Historical records
- Recovery after disconnection

WebSocket is used for:

- Immediate live updates
- Event notifications
- Score changes
- Alerts
- Device status changes
- Trip status changes

### 3.5 Test data must remain separated

Simulation must use:

- A simulator device
- A test trip
- `SIMULATOR` telemetry source
- Visible test-data labels

Test trips must not update official driver or fleet analytics.

### 3.6 Configuration must be versioned

Event thresholds, penalties, severity bands and risk bands must be stored in versioned backend configuration.

A trip must keep the rule version selected when the trip started.

Changing a rule later must not silently change the historical explanation of a completed trip.

---

## 4. High-Level Component Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                    TELEMETRY SOURCES                       │
│                                                            │
│  ┌─────────────────────┐  ┌─────────────────────────────┐ │
│  │ Physical IoT Device │  │ Virtual Device Simulator    │ │
│  │ ESP32 + GPS + IMU   │  │ Controlled test scenarios  │ │
│  └──────────┬──────────┘  └──────────────┬──────────────┘ │
└─────────────┼─────────────────────────────┼────────────────┘
              │ HTTP/HTTPS telemetry POST  │
              └──────────────┬──────────────┘
                             ▼
┌────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                        │
│                                                            │
│  Device authentication                                    │
│          ↓                                                 │
│  Telemetry adapter                                         │
│          ↓                                                 │
│  Validation and duplicate detection                        │
│          ↓                                                 │
│  Device, vehicle and trip context resolution               │
│          ↓                                                 │
│  Raw telemetry storage                                     │
│          ↓                                                 │
│  Driving-rule engine                                       │
│          ↓                                                 │
│  Pattern engine                                            │
│          ↓                                                 │
│  Score and risk engine                                     │
│          ↓                                                 │
│  Alert engine                                              │
│          ↓                                                 │
│  Transaction commit                                        │
│          ↓                                                 │
│  WebSocket publication                                     │
└───────────────┬─────────────────┬──────────────────────────┘
                │                 │
                ▼                 ▼
       ┌────────────────┐  ┌───────────────────┐
       │ PostgreSQL     │  │ React Dashboard   │
       │ Persistent data│  │ REST + WebSocket  │
       └────────────────┘  └───────────────────┘
```

---

## 5. Telemetry Source Layer

The system supports three telemetry source types:

- `HARDWARE`
- `SIMULATOR`
- `REPLAY`

### 5.1 Physical IoT device

The physical hardware may include:

- ESP32
- GPS module
- IMU or gyroscope
- Communication module
- Power source
- Optional local storage

Hardware responsibilities:

- Read sensors
- Read GPS
- Create telemetry packets
- Authenticate with the backend
- Send packets
- Retry failed transmission where supported

Hardware must not be responsible for the official:

- Event result
- Event severity
- Trip score
- Risk level
- Behaviour pattern
- Manager alert

Hardware flags may be stored only as supporting observations.

### 5.2 Virtual device simulator

The simulator acts as a virtual IoT device.

It must:

- Use device authentication
- Use the real telemetry endpoint
- Send realistic multi-packet sequences
- Follow a predefined route
- Run repeatable scenarios
- Mark data as simulated
- Operate only with test trips

The simulator must not:

- Insert events directly
- Insert score penalties directly
- Modify dashboard state directly
- Bypass telemetry validation
- Bypass database storage
- Call the rule engine directly

### 5.3 Replay source

Replay is used to send previously recorded data through the ingestion pipeline.

Replay supports:

- Regression testing
- Threshold calibration
- Firmware comparison
- Bug reproduction
- Recorded-trip analysis

Replay data must remain clearly marked and must not silently affect official driver performance.

---

## 6. Telemetry Contract and Adapter Layer

Hardware versions may use different field names.

For example:

```text
Firmware field: accel_fwd
Standard field: forward_acceleration_ms2
```

The telemetry adapter converts device-specific packets into one internal standard model.

```text
Device packet
    ↓
Schema-version selection
    ↓
Telemetry adapter
    ↓
Standard telemetry object
```

Example internal standard fields:

- Device identifier
- Schema version
- Device timestamp
- Server-received timestamp
- Sequence number
- Boot identifier
- Latitude
- Longitude
- GPS validity
- Speed in kilometres per hour
- Forward acceleration in metres per second squared
- Lateral acceleration in metres per second squared
- Yaw rate in degrees per second
- Hardware observation flags
- Telemetry source

The rule engine must use only standardized fields.

It must not depend directly on firmware-specific names.

---

## 7. Telemetry Ingestion API

The device and simulator send telemetry to:

```http
POST /api/v1/device/telemetry
```

The endpoint performs:

1. Device authentication
2. Administrative-status check
3. Schema-version validation
4. Adapter selection
5. Field validation
6. Duplicate detection
7. Context resolution
8. Raw telemetry storage
9. Processing
10. Response generation

The telemetry endpoint must remain separate from manager-user APIs.

Human-user authentication and device authentication are different security mechanisms.

---

## 8. Device Authentication

Each physical or simulated device must have:

- Device code or identifier
- Device API key
- Administrative status
- Supported schema version
- Organization ownership

The API key must be stored securely.

Devices must never receive:

- PostgreSQL credentials
- Manager authentication tokens
- Direct database access
- Internal service secrets

A disabled, retired or invalid device must not submit accepted official telemetry.

---

## 9. Telemetry Validation

Validation occurs before official processing.

Validation checks may include:

- Required fields
- Numeric field types
- Latitude range
- Longitude range
- Speed range
- Acceleration range
- Yaw-rate range
- Schema version
- Duplicate packet identity
- Delayed timestamp
- Missing GPS
- Invalid or unrealistic values

Possible outcomes include:

- `PROCESSED`
- `PARTIAL`
- `FAILED`
- `DUPLICATE`
- `REJECTED`

Missing GPS does not always require rejecting the complete packet.

Example:

```text
Valid acceleration
Valid speed
Missing GPS
```

The packet may be stored as partial telemetry.

The map may continue showing the last valid location while sensor-based behaviour processing continues with reduced data-quality confidence.

---

## 10. Context Resolution

After a device is authenticated, the backend determines its context.

```text
Device
    ↓
Active device assignment
    ↓
Vehicle
    ↓
Active trip
    ↓
Driver
```

The hardware packet does not need to declare the official driver.

The manager selects the driver and vehicle when the trip begins.

The backend resolves the active driver through the trip.

### 10.1 Assigned active trip

When an active trip exists:

- Telemetry is stored
- Telemetry is linked to the trip
- Rule processing runs
- Score and alert logic may run

### 10.2 No active trip

When no active trip exists:

- Telemetry may still be stored as unassigned
- Latest device state may be updated
- Official trip scoring does not run
- Official driver analytics do not change

This prevents telemetry from being assigned to an incorrect driver.

---

## 11. Raw Telemetry Storage

Each accepted packet creates a raw telemetry record.

Raw telemetry is evidence and should remain immutable.

The record must preserve:

- Device identity
- Trip linkage where available
- Device assignment linkage
- Server-received time
- Device time
- Source type
- Sensor values
- GPS values
- Validation result
- Processing status
- Hardware observations
- Schema version
- Duplicate identity fields

If rule processing fails after raw storage:

- The raw packet remains stored
- Processing status becomes failed
- A retry mechanism may reprocess it
- The system must avoid applying duplicate events or penalties

---

## 12. Latest-State Storage

Historical telemetry and current state serve different purposes.

Raw telemetry stores every packet.

Latest-state records store the most recent known state for:

- Device
- Vehicle
- Trip

Example latest state:

```text
Current speed
Current location
Latest telemetry time
Device connection status
Current score
Current risk
Current active event state
```

The live dashboard can obtain its initial state efficiently from these latest-state records.

Latest-state records do not replace raw telemetry.

---

## 13. Driving-Rule Engine

The rule engine processes standardized telemetry.

The MVP contains four official detectors:

- Harsh braking
- Sudden acceleration
- Overspeeding
- Sharp turning

Each detector manages a state lifecycle:

```text
NORMAL
    ↓
CANDIDATE
    ↓
CONFIRMED ACTIVE EVENT
    ↓
RELEASED
    ↓
COOLDOWN
    ↓
NORMAL
```

This lifecycle prevents one continuous occurrence from creating one event per packet.

### 13.1 Harsh braking

Uses:

- Forward acceleration
- Minimum duration
- Minimum applicable speed
- Release threshold
- Cooldown

### 13.2 Sudden acceleration

Uses:

- Forward acceleration
- Minimum duration
- Release threshold
- Cooldown

### 13.3 Overspeeding

Uses:

- Current speed
- Applied trip speed limit
- Allowed tolerance
- Minimum duration
- Release threshold or hysteresis

One continuous overspeed occurrence must remain one event.

### 13.4 Sharp turning

Uses:

- Lateral acceleration
- Yaw rate
- Minimum vehicle speed
- Minimum duration
- Release conditions
- Cooldown

The exact official thresholds come from the trip’s rule-version configuration.

---

## 14. Driving Event Storage

A confirmed event must store:

- Organization
- Trip
- Driver context
- Vehicle context
- Event type
- Event status
- Start time
- End time
- Duration
- Severity
- Maximum or minimum measured values
- Applied thresholds
- Rule version
- Detection source
- Supporting telemetry references
- Review or void status

Events must be linked to evidence.

A manager should be able to understand why the event was created.

---

## 15. Event Severity

Severity is calculated by the backend.

Possible levels:

- LOW
- MODERATE
- HIGH
- CRITICAL

Severity may depend on:

- Distance beyond threshold
- Event duration
- Maximum value
- Minimum value
- Speed at the time
- Rule configuration

Severity must not be calculated independently by the frontend.

---

## 16. Behaviour-Pattern Engine

The pattern engine evaluates confirmed events within a rolling trip window.

The MVP supports:

- Repeated same behaviour
- Mixed aggressive behaviour

Example:

```text
Harsh braking
    +
Overspeeding
    +
Sharp turning
    +
Sudden acceleration
    ↓
Mixed aggressive-driving pattern
```

Patterns must use confirmed backend events only.

A pattern must store:

- Trip
- Pattern type
- Start and end time
- Rolling-window configuration
- Included events
- Pattern severity
- Pattern score or weight
- Rule version
- Status

Pattern detection does not mean accident prediction.

It means that the configured repeated unsafe-behaviour condition has been satisfied.

---

## 17. Score Engine

Each trip begins with:

```text
Trip score = 100
```

The official score is calculated from a score ledger.

```text
Current score =
maximum of zero and
initial score plus all valid ledger changes
```

Every score change must store:

- Source type
- Source identifier
- Previous score
- Points changed
- New score
- Penalty or adjustment rule
- Timestamp
- Reversal state where applicable

Possible score sources include:

- Driving event
- Behaviour pattern
- Controlled correction
- Reversal of a voided event

The current score must always be explainable from the ledger.

The frontend must not calculate the official score.

---

## 18. Risk Engine

The risk engine converts the current score into a configured risk band.

Suggested initial bands:

```text
80–100 → LOW
60–79  → MEDIUM
0–59   → HIGH
```

The official values are stored in the backend rule configuration.

When the score crosses a risk-band boundary:

- Trip risk state changes
- A score-update message may be published
- An alert may be created
- The transition is preserved in history

HIGH behavioural risk must not be presented as an accident prediction.

---

## 19. Alert Engine

Alerts may be created for:

- Severe driving event
- Repeated aggressive pattern
- Trip entering HIGH risk
- Device becoming offline during an active trip
- Optional high-impact event requiring verification

Alert priorities:

- INFO
- WARNING
- CRITICAL

Alert states:

- UNREAD
- READ
- ACKNOWLEDGED
- RESOLVED

Alerts must include deduplication logic.

A continuing condition must not create repeated identical alerts every second.

---

## 20. Device-Status Worker

Device connection status is inferred from telemetry arrival time.

Example lifecycle:

```text
Recent packet
    ↓
ONLINE

No packet beyond delayed threshold
    ↓
DELAYED

No packet beyond offline threshold
    ↓
OFFLINE
```

When telemetry resumes:

```text
OFFLINE
    ↓
ONLINE
```

The worker may:

- Update device state
- Update vehicle state
- Publish a WebSocket status message
- Create or resolve an alert

Offline status means communication was interrupted.

It must not be described as an accident.

---

## 21. Database Transaction Boundary

Processing one telemetry packet may create or update:

- Raw telemetry
- Latest device state
- Latest vehicle state
- Latest trip state
- Event candidate state
- Driving event
- Behaviour pattern
- Score-ledger entry
- Trip score
- Risk state
- Alert

Related official changes should occur inside a controlled database transaction.

Recommended sequence:

```text
Begin transaction
    ↓
Store raw telemetry
    ↓
Update context and state
    ↓
Process events
    ↓
Process patterns
    ↓
Process score and risk
    ↓
Process alerts
    ↓
Commit transaction
    ↓
Publish WebSocket messages
```

WebSocket messages must not be treated as the persistent source of truth.

They are notifications about committed state.

---

## 22. REST API Architecture

REST APIs provide request-response communication.

```text
Client request
    ↓
Backend validation and processing
    ↓
Backend response
```

REST is used for:

- Login and logout
- Current-user information
- Driver management
- Vehicle management
- Device management
- Device assignments
- Starting trips
- Ending trips
- Cancelling trips
- Telemetry uploads
- Initial live-trip snapshots
- Historical trips
- Event details
- Score history
- Alerts
- Settings
- Simulation controls
- Completed-trip reports
- Driver profiles

The physical device and simulator also use REST to upload telemetry.

---

## 23. WebSocket Architecture

WebSocket provides a persistent connection between the backend and frontend.

```text
React frontend opens connection
    ↓
Connection remains active
    ↓
Backend pushes committed changes
```

Required message types include:

- `TELEMETRY_UPDATED`
- `DRIVING_EVENT_CREATED`
- `DRIVING_EVENT_UPDATED`
- `BEHAVIOUR_PATTERN_CREATED`
- `BEHAVIOUR_PATTERN_UPDATED`
- `TRIP_SCORE_UPDATED`
- `ALERT_CREATED`
- `ALERT_UPDATED`
- `DEVICE_STATUS_CHANGED`
- `TRIP_STATUS_CHANGED`
- `TRIP_COMPLETED`

WebSocket is not the only mechanism used to load page state.

REST is still required for complete snapshots and historical information.

---

## 24. Live Dashboard Opening Sequence

When a manager opens a live trip:

```text
1. React requests the current snapshot through REST.

2. FastAPI returns:
   - Trip details
   - Driver
   - Vehicle
   - Device
   - Current telemetry
   - Current score
   - Current risk
   - Existing events
   - Existing patterns
   - Latest alerts
   - Applied thresholds

3. React renders the page.

4. React opens an authenticated WebSocket connection.

5. React subscribes to the trip.

6. FastAPI pushes later changes.

7. React updates only the relevant components.
```

Conceptually:

```text
REST
→ Complete current state

WebSocket
→ New changes after that state
```

---

## 25. WebSocket Reconnection

A WebSocket connection may fail because of:

- Network interruption
- Laptop sleep
- Server restart
- Reverse-proxy interruption
- Temporary internet loss

Recovery process:

```text
WebSocket disconnects
    ↓
Frontend shows reconnecting state
    ↓
Frontend may use REST polling fallback
    ↓
Frontend reconnects
    ↓
Frontend requests a fresh REST snapshot
    ↓
Frontend replaces stale state
    ↓
Frontend resumes WebSocket updates
```

Sequence numbers may be used to detect missing live messages.

PostgreSQL remains the authoritative source for recovery.

---

## 26. Frontend Architecture

The frontend is implemented using React and TypeScript.

The frontend responsibilities are:

- Display information
- Submit manager actions
- Load snapshots and history
- Subscribe to live updates
- Render maps and charts
- Show validation errors
- Show connection status
- Display simulation mode clearly

The frontend must not officially calculate:

- Driving events
- Event severity
- Patterns
- Scores
- Risk levels
- Alerts
- Driver performance

Suggested frontend data flow:

```text
React component
    ↓
API client or query layer
    ↓
REST API
```

For live data:

```text
WebSocket client
    ↓
Central live-trip state
    ↓
Relevant dashboard components
```

---

## 27. Backend Module Architecture

The backend is divided into business modules.

Recommended modules:

- Authentication
- Users
- Organizations
- Drivers
- Vehicles
- Devices
- Device assignments
- Trips
- Telemetry
- Driving events
- Behaviour patterns
- Scoring
- Alerts
- Realtime communication
- Trip summaries
- Driver analytics
- Rule configuration
- Simulation
- Audit records

Each standard module should separate:

```text
Router
    ↓
Service
    ↓
Repository
    ↓
Database
```

### Router

Responsible for:

- HTTP details
- Input schema
- Authentication dependency
- Response schema
- Status code

### Service

Responsible for:

- Business rules
- Workflow coordination
- Authorization decisions
- Transaction coordination

### Repository

Responsible for:

- Database queries
- Inserts
- Updates
- Locks
- Database-specific access

Business logic must not be placed directly inside routers.

---

## 28. Trip Lifecycle Architecture

### 28.1 Before trip start

The system must have:

- Active driver
- Active vehicle
- Enabled device
- Active device assignment
- Active rule version

### 28.2 Trip start

The manager selects:

- Driver
- Vehicle
- Trip mode
- Applied speed limit where required

The backend resolves the active device assignment.

It then creates:

- Trip record
- Initial score state
- Initial risk state
- Live trip state

### 28.3 Active trip

During an active trip:

- Telemetry is linked to the trip
- Rule engine processes packets
- Patterns are detected
- Score and risk change
- Alerts are generated
- WebSocket updates are published

### 28.4 Trip ending

When ending a trip:

```text
Stop new telemetry assignment
    ↓
Close active event states
    ↓
Finalize patterns
    ↓
Verify score ledger
    ↓
Calculate statistics
    ↓
Calculate data quality
    ↓
Create summary
    ↓
Generate rule-based recommendations
    ↓
Update official driver analytics where eligible
```

### 28.5 Trip constraints

Only one active trip is allowed for the same:

- Driver
- Vehicle
- Device assignment

---

## 29. Official and Test Data Architecture

### Official trip

May affect:

- Driver score
- Driver trend
- Driver profile
- Fleet average
- Driver ranking
- Official reports

### Test trip

Used for:

- Simulation
- Pitch demonstrations
- Software testing
- Rule testing
- Calibration

A test trip may create complete system outputs, but it must not affect official analytics.

Test-data markers must exist at multiple levels:

```text
Testing device
    +
TEST trip
    +
SIMULATOR or REPLAY telemetry source
    +
Visible dashboard badge
```

---

## 30. Simulation Architecture

Simulation controls are manager-facing REST actions.

Example:

```text
Manager selects FULL_PITCH_DEMO
    ↓
Frontend calls simulation start API
    ↓
Simulation service starts virtual device
    ↓
Virtual device generates packet
    ↓
Virtual device posts to telemetry API
    ↓
Normal telemetry processing occurs
    ↓
Backend publishes live updates
    ↓
Dashboard changes
```

The control API and telemetry API have different purposes.

```text
Simulation control API
→ Controls simulator state

Telemetry ingestion API
→ Receives generated sensor packets
```

Required simulation states:

- STOPPED
- RUNNING
- PAUSED
- COMPLETED
- FAILED

The full pitch scenario should be deterministic and repeatable.

---

## 31. Trip Finalization and Analytics

The completed-trip process calculates:

- Duration
- Estimated distance
- Average speed
- Maximum speed
- Overspeed duration
- Event counts
- Event rates
- Pattern counts
- Final score
- Final risk
- Data quality
- Primary concern
- Rule-based recommendation

Official driver analytics must use eligible completed official trips only.

Test trips, incomplete trips and insufficient-quality trips must not silently change official driver performance.

---

## 32. Security Boundaries

### Browser to backend

Uses:

- HTTPS
- Secure authentication cookie
- Role authorization
- Organization ownership checks

### Device to backend

Uses:

- HTTPS
- Device identifier
- Device API key
- Device status validation
- Schema-version validation

### Backend to database

Uses:

- Private database credentials
- Environment variables
- Restricted database user
- Transaction management

### Frontend to database

Direct access is prohibited.

```text
React
    ↓
FastAPI
    ↓
PostgreSQL
```

---

## 33. Organization Isolation

All organization-owned records must belong to an organization.

Users may access only records authorized for their organization.

Examples include:

- Drivers
- Vehicles
- Devices
- Trips
- Events
- Alerts
- Rules
- Reports

Organization checks must occur in the backend.

Hiding information in the frontend is not sufficient authorization.

---

## 34. Auditability

Important administrative and operational actions should create audit records.

Examples:

- User login
- Driver creation
- Vehicle creation
- Device registration
- Device assignment
- Device credential rotation
- Trip start
- Trip end
- Rule-version activation
- Event voiding
- Score correction
- Alert acknowledgement

Audit records should identify:

- Organization
- User
- Action
- Target type
- Target identifier
- Time
- Relevant metadata

---

## 35. Data-Quality Architecture

The system monitors:

- Missing GPS
- Invalid GPS
- Missing sensor values
- Unrealistic sensor values
- Duplicate packets
- Delayed packets
- Telemetry gaps
- Device disconnection
- Processing failures
- Low sample count

Possible assessment classifications:

- GOOD
- ACCEPTABLE
- LIMITED
- INSUFFICIENT

Data quality influences:

- Trip assessment confidence
- Recommendation wording
- Eligibility for official driver analytics

Data-quality problems should not automatically be interpreted as unsafe driver behaviour.

---

## 36. Failure Handling

### 36.1 Invalid device credential

Result:

- Request rejected
- No official processing
- Security log may be created

### 36.2 Invalid telemetry value

Result may be:

- Request rejected
- Packet stored as rejected
- Packet accepted as partial
- Field excluded from rule processing

### 36.3 Database failure

Result:

- Transaction rolls back
- Device receives a retryable error where appropriate
- No WebSocket update is published
- Device or simulator may retry

### 36.4 Rule-processing failure

Result:

- Raw telemetry remains stored where possible
- Processing status becomes failed
- Retry worker may reprocess
- Idempotency prevents duplicate outcomes

### 36.5 WebSocket failure

Result:

- Committed database data remains safe
- Frontend reconnects
- REST snapshot restores state

### 36.6 Simulator failure

Result:

- Simulation state becomes failed
- Test trip remains clearly marked
- Official analytics remain unaffected

---

## 37. Idempotency and Duplicate Protection

The same packet may be sent more than once because of network retries.

Duplicate identity may use:

- Device identifier
- Boot identifier
- Sequence number

The system must prevent duplicate:

- Telemetry records
- Events
- Pattern penalties
- Score-ledger entries
- Alerts

Trip-start and trip-end actions may also use idempotency protection where appropriate.

---

## 38. Local Development Architecture

Local development uses Docker Compose.

```text
Developer computer
│
├── React frontend
├── FastAPI backend
├── Background worker
├── Simulator
└── PostgreSQL
```

Typical local addresses:

```text
Frontend:   http://localhost:5173
Backend:    http://localhost:8000
PostgreSQL: localhost:5432
WebSocket:  ws://localhost:8000/ws
```

Local development data must not be confused with deployed pitch data.

---

## 39. Pitch Server Architecture

The deployed pitch environment contains:

- React frontend
- FastAPI backend
- PostgreSQL database
- Device-status worker
- Simulation service
- HTTPS reverse proxy
- Secure WebSocket support

```text
Browser
    ↓ HTTPS / WSS
Reverse proxy
    ↓
FastAPI and React
    ↓
PostgreSQL
```

The deployed environment must use:

- HTTPS
- WSS
- Environment-based secrets
- Database migrations
- Demo seed data
- Health checks
- Backup procedure

---

## 40. Offline Pitch Backup

The project must support a complete offline local demonstration.

```text
Pitch laptop
│
├── React frontend
├── FastAPI backend
├── PostgreSQL
├── Worker
└── Simulator
```

The offline fallback must not require external internet for the core demonstration.

A locally available map method or prepared map fallback may be required if live map tiles depend on internet access.

---

## 41. Deployment Database Procedure

The database must be created through migrations.

Correct deployment sequence:

```text
Create empty PostgreSQL database
    ↓
Configure DATABASE_URL
    ↓
Run Alembic migrations
    ↓
Run pitch seed script
    ↓
Start backend
    ↓
Run health checks
```

The server must not depend on manually creating tables through a graphical database interface.

---

## 42. Health Checks

Required health endpoints include:

```http
GET /health
GET /api/v1/health/database
```

Health checks should identify:

- Backend process availability
- Database connectivity

Future health checks may include:

- Worker activity
- WebSocket service
- Migration state
- Simulator service

---

## 43. Scaling Boundary

The MVP uses one backend application instance and one PostgreSQL database.

The following are not required initially:

- Microservices
- Kubernetes
- Kafka
- RabbitMQ
- Distributed event streaming
- Redis-based WebSocket scaling
- Multiple independent rule-engine services

Future scaling may introduce:

- Redis for shared live-state or WebSocket distribution
- Message queue for background processing
- MQTT for large device fleets
- Separate analytics services
- Read replicas
- Telemetry partitioning

These additions must not be introduced before there is a proven requirement.

---

## 44. End-to-End Example: Harsh Braking

```text
1. Simulator sends telemetry:
   forward acceleration = -4.2 m/s²

2. Telemetry API authenticates the simulator device.

3. Adapter converts fields to the standard model.

4. Validator accepts the packet.

5. Backend resolves:
   device → assignment → vehicle → active test trip → driver

6. Raw telemetry is stored.

7. Harsh-braking detector enters candidate state.

8. Additional packets satisfy minimum duration.

9. One harsh-braking event is confirmed.

10. Severity is classified.

11. Event penalty is added to the score ledger.

12. Trip score is updated.

13. Risk is recalculated.

14. Alert logic runs.

15. Transaction commits.

16. WebSocket publishes:
    - driving event
    - score update
    - possible alert

17. React updates:
    - acceleration graph
    - event counter
    - event timeline
    - score card
    - alert panel
```

---

## 45. End-to-End Example: Overspeeding

```text
1. Applied trip limit is 60 km/h.

2. Tolerance is 5 km/h.

3. Detection threshold is 65 km/h.

4. Telemetry reports speed above 65 km/h.

5. Overspeed candidate begins.

6. Speed remains above threshold for the required duration.

7. One overspeed event is confirmed.

8. Later packets update:
   - duration
   - maximum speed
   - evidence

9. Speed drops below the release threshold.

10. The event closes.

11. Only one continuous event is stored.
```

---

## 46. End-to-End Example: Device Disconnection

```text
1. Device sends telemetry normally.

2. Device status is ONLINE.

3. Telemetry stops.

4. Device-status worker detects delayed threshold.

5. Device changes to DELAYED.

6. More time passes.

7. Device changes to OFFLINE.

8. Offline alert is created.

9. WebSocket updates the dashboard.

10. The dashboard shows the last valid location.

11. Telemetry resumes.

12. Device returns to ONLINE.

13. Connection-restored update is published.

14. Offline alert may be resolved.
```

Offline status alone does not indicate an accident.

---

## 47. End-to-End Example: Live Page Recovery

```text
1. Manager opens an active trip.

2. React loads complete state using REST.

3. React connects to WebSocket.

4. Live updates arrive.

5. Internet connection drops.

6. WebSocket disconnects.

7. React shows RECONNECTING.

8. React may poll the REST snapshot.

9. WebSocket reconnects.

10. React reloads the latest REST snapshot.

11. React resumes live updates.

12. No official data is lost because PostgreSQL stored committed results.
```

---

## 48. Architecture Restrictions

The implementation must not:

- Connect React directly to PostgreSQL
- Calculate official scores in React
- Create official events from hardware flags alone
- Insert simulator events directly
- Publish WebSocket updates before database commit
- Allow test trips to update official analytics
- Store secrets in source code
- Give devices database credentials
- Describe device disconnection as an accident
- Claim accident prediction
- Claim machine learning is already implemented
- Use multiple independent processing paths for hardware and simulation
- Introduce unnecessary microservices for the MVP

---

## 49. Architecture Acceptance Criteria

The architecture is correctly implemented when:

- Hardware and simulator use the same telemetry API.
- Device packets are converted into a standard internal model.
- Raw telemetry is stored before official derived results are finalized.
- Device, vehicle, trip and driver context are resolved by the backend.
- Events are created by backend rules.
- Continuous behaviour creates one event rather than one per packet.
- Patterns use confirmed events.
- Every score change is represented in the score ledger.
- Risk is calculated by the backend.
- Alerts use deduplication.
- Database commits occur before WebSocket publication.
- REST loads complete snapshots and history.
- WebSocket delivers later live changes.
- Reconnection reloads a fresh REST snapshot.
- Test data is clearly separated.
- Official analytics exclude test trips.
- The system runs locally and in the deployed pitch environment.
- An offline local demonstration is available.
- Real hardware can replace the simulator without redesigning backend processing.