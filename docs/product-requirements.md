# EvolveX Driver Behaviour Intelligence Platform

## Product Requirements Document

**Document version:** 1.1  
**Project stage:** Pitching MVP  
**Product type:** AI-ready, rule-based IoT fleet-safety platform  
**Team:** EvolveX  

---

## 1. Product Overview

EvolveX is a driver-behaviour intelligence platform designed for fleet managers.

The system receives vehicle movement and location telemetry from either:

1. A physical ESP32-based IoT device
2. A controlled virtual-device simulator

Both sources use the same telemetry API and backend-processing pipeline.

The MVP analyses telemetry using configurable rules to detect unsafe driving behaviours, calculate trip safety scores, identify repeated aggressive-driving patterns and notify fleet managers through a live dashboard.

The current MVP is rule-based. It is designed so that machine-learning models can be added later without replacing the core system architecture.

---

## 2. Problem Statement

Fleet managers often lack objective and near-real-time information about how vehicles are being driven.

Common unsafe behaviours include:

- Harsh braking
- Sudden acceleration
- Overspeeding
- Sharp turning
- Repeated aggressive-driving actions

Without a monitoring platform, managers may depend on driver complaints, accident reports, manual supervision, vehicle damage, delayed feedback and subjective observations. These methods normally identify problems only after an incident or operational loss has already occurred.

EvolveX converts vehicle telemetry into understandable evidence such as:

- Driving events
- Event severity
- Trip scores
- Risk levels
- Alerts
- Behaviour patterns
- Driver trends
- Recommendations

---

## 3. Target Users

### 3.1 Administrator

The administrator manages:

- Organization information
- User accounts
- Drivers
- Vehicles
- IoT devices
- Device assignments
- Rule configurations
- Monitoring settings
- Simulation access
- Audit records

### 3.2 Fleet Manager

The fleet manager can:

- Start and end trips
- Select the driver and vehicle
- Monitor active trips
- View vehicle location
- View driving events
- View trip scores and risk levels
- Receive alerts
- Review completed trips
- Review driver behaviour history
- Add notes and reviews

### 3.3 IoT Device

The IoT device:

- Collects sensor and GPS values
- Packages telemetry
- Authenticates with the backend
- Sends telemetry to the ingestion API
- Receives an acceptance or rejection response

The device does not calculate the official trip score.

### 3.4 Virtual Device Simulator

The virtual device:

- Produces realistic telemetry
- Uses the same telemetry endpoint as the physical device
- Authenticates using a simulator-device credential
- Runs repeatable test scenarios
- Supports the pitch demonstration

---

## 4. MVP Objectives

The MVP must demonstrate that the system can:

1. Register drivers, vehicles and devices.
2. Assign a device to a vehicle.
3. Start a trip by selecting a driver and vehicle.
4. Receive telemetry from hardware or a simulator.
5. Validate and store raw telemetry.
6. Detect unsafe-driving events.
7. Classify event severity.
8. Detect repeated aggressive-driving patterns.
9. Calculate an explainable trip safety score.
10. Assign a trip risk level.
11. Create manager alerts.
12. Update the live dashboard through WebSocket.
13. Display the route and event evidence.
14. Finalize a trip and create a summary.
15. Separate simulated data from official data.
16. Operate both locally and on a deployed pitch server.
17. Produce rule-based recommendations from completed-trip evidence.
18. Produce driver trends from valid completed official trips only.

---

## 5. MVP Behaviour Detection

The official MVP detects four primary behaviours.

### 5.1 Harsh Braking

Harsh braking occurs when forward acceleration falls below the configured negative threshold for the required minimum duration.

Example:

- Measured forward acceleration: `-4.2 m/s^2`
- Configured threshold: `-3.5 m/s^2`
- Result: harsh-braking candidate

The event is confirmed only when the configured duration and other validation conditions are satisfied.

The system must avoid producing one event for every telemetry packet during the same braking action.

### 5.2 Sudden Acceleration

Sudden acceleration occurs when forward acceleration rises above the configured positive threshold for the required minimum duration.

Example:

- Measured forward acceleration: `+3.7 m/s^2`
- Configured threshold: `+3.0 m/s^2`
- Result: sudden-acceleration candidate

The system must use cooldown and release conditions to prevent duplicate events.

### 5.3 Overspeeding

Overspeeding occurs when vehicle speed remains above the applied speed threshold for the configured duration.

Example:

- Trip speed limit: `60 km/h`
- Allowed tolerance: `5 km/h`
- Detection threshold: `65 km/h`
- Measured speed: `76 km/h`

The system must create one continuous overspeeding event rather than creating one event every second.

The event must store:

- Event start time
- Event end time
- Duration
- Maximum speed
- Applied speed limit
- Detection threshold

### 5.4 Sharp Turning

Sharp turning is detected using:

- Lateral acceleration
- Yaw rate
- Minimum vehicle speed

Example:

- Vehicle speed: `38 km/h`
- Lateral acceleration: `3.2 m/s^2`
- Yaw rate: `38 degrees/second`

The event is confirmed only when the configured conditions are satisfied.

---

## 6. Repeated Aggressive-Driving Patterns

The system must analyse confirmed events within a configurable rolling time window.

The MVP supports:

### 6.1 Repeated Same Behaviour

Example:

- Four harsh-braking events within ten minutes

### 6.2 Mixed Aggressive Behaviour

Example:

- Harsh braking
- Overspeeding
- Sharp turning
- Sudden acceleration

occurring within the same configured rolling window.

The pattern engine must operate only on confirmed backend events. Hardware-generated flags must not independently create an official behaviour pattern.

---

## 7. Trip Safety Score

Each trip begins with:

```text
Safety score = 100
```

Confirmed events and patterns may reduce the score according to configured penalty rules.

Conceptually:

```text
Current score = maximum of 0 and initial score plus all score-ledger changes
```

Example:

| Reason | Score change |
|---|---:|
| Initial score | 100 |
| High harsh-braking event | -4 |
| Moderate overspeed event | -2 |
| Repeated aggressive pattern | -8 |
| Final score | 86 |

Every score change must be explainable.

Each score-ledger entry must identify:

- Source type
- Source event or pattern
- Severity
- Penalty rule
- Previous score
- Points added or removed
- New score
- Time of change

The frontend must not calculate the official score.

---

## 8. Trip Risk Levels

The MVP uses configurable risk bands.

Initial suggested bands are:

| Score | Risk |
|---:|---|
| 80-100 | LOW |
| 60-79 | MEDIUM |
| 0-59 | HIGH |

The exact values must be stored in backend configuration.

When a trip moves into a new risk band, the backend updates the trip state and may create an alert.

The system does not interpret HIGH risk as an accident prediction. It means that detected driving behaviour has entered the configured high-risk behavioural range.

---

## 9. Event Severity

Event severity is determined by backend configuration.

Suggested levels are:

- LOW
- MODERATE
- HIGH
- CRITICAL

Severity may depend on:

- Threshold exceedance
- Event duration
- Maximum value
- Applied rule version
- Vehicle speed

The event record must preserve:

- Measured values
- Threshold values
- Rule version
- Severity result
- Supporting telemetry evidence

---

## 10. Alerts

The MVP may create alerts for:

- Severe driving events
- Repeated aggressive-driving patterns
- Trip transition into HIGH risk
- Device becoming offline during an active trip
- Optional high-impact event requiring verification

Alert priorities are:

- INFO
- WARNING
- CRITICAL

Alert states are:

- UNREAD
- READ
- ACKNOWLEDGED
- RESOLVED

The system must prevent repeated alerts for the same continuing condition.

Device offline status must not be described as an accident.

---

## 11. Trip Lifecycle

### 11.1 Starting a Trip

The manager selects:

- Driver
- Vehicle
- Trip mode
- Applied speed limit where required

The backend determines the currently assigned device through the active device assignment.

The system validates that:

- Driver is active
- Vehicle is active
- Device is enabled
- Vehicle has an active device assignment
- Driver has no other active trip
- Vehicle has no other active trip
- Device assignment has no other active trip
- An active rule version exists

### 11.2 Active Trip

During an active trip, the system processes:

- Telemetry
- Location
- Device status
- Events
- Patterns
- Scores
- Alerts
- Data-quality conditions

### 11.3 Ending a Trip

When the manager ends the trip, the backend:

1. Stops assigning new telemetry to the trip.
2. Closes active events where appropriate.
3. Finalizes active patterns.
4. Verifies the score ledger.
5. Calculates trip statistics.
6. Calculates data quality.
7. Creates the trip summary.
8. Determines the primary concern.
9. Generates recommendations.
10. Updates driver performance for eligible official trips.

### 11.4 Active-Trip Restrictions

Only one active trip is allowed for the same:

- Driver
- Vehicle
- Device assignment

---

## 12. Trip Modes and Data Separation

### 12.1 Official Trip

Official trips may affect:

- Driver overall score
- Driver trend
- Fleet analytics
- Driver ranking
- Official reports

### 12.2 Test Trip

Test trips are used for:

- Simulation
- System testing
- Demonstrations
- Threshold testing
- Software validation

Test trips may still create:

- Telemetry
- Events
- Patterns
- Scores
- Alerts
- Summaries

However, they must not update official fleet or driver performance.

### 12.3 Required Data Separation Rules

A simulated run must satisfy all of the following:

- `trip_mode = TEST`
- `telemetry_source = SIMULATOR`
- The device is registered as a simulator or testing device
- The dashboard displays a visible test-data label
- Test trips are excluded from official driver, fleet and ranking queries

---

## 13. Telemetry Sources

Every telemetry record must identify its source.

Supported sources are:

- `HARDWARE`
- `SIMULATOR`
- `REPLAY`

### Hardware

Telemetry received from the physical IoT device.

### Simulator

Telemetry produced by the virtual device during controlled scenarios.

### Replay

Previously recorded telemetry sent through the ingestion pipeline again for testing or calibration.

---

## 14. Telemetry Processing

Each telemetry packet passes through:

```text
Device authentication
        ↓
Schema adapter
        ↓
Validation
        ↓
Duplicate detection
        ↓
Device and trip context resolution
        ↓
Raw telemetry storage
        ↓
Latest-state update
        ↓
Rule engine
        ↓
Event generation
        ↓
Pattern engine
        ↓
Score engine
        ↓
Alert engine
        ↓
Database commit
        ↓
WebSocket publication
```

The backend must preserve raw telemetry even when later rule processing fails.

Processing status must identify whether the packet is:

- RECEIVED
- PROCESSED
- PARTIAL
- FAILED
- DUPLICATE
- REJECTED

---

## 15. Hardware Responsibilities

The physical device may contain:

- ESP32
- GPS module
- IMU or gyroscope
- Communication module
- Power supply
- Prototype board
- Optional local storage

The hardware is responsible for:

- Reading sensors
- Creating telemetry packets
- Identifying the device
- Sending telemetry
- Retrying failed transmission where supported

Hardware behaviour flags may be stored as supporting observations. They are not the official source for backend event creation.

---

## 16. Simulation Mode

Simulation Mode is an official MVP feature. It is not a visual-only fake dashboard.

The simulator acts as a virtual IoT device and sends telemetry through:

```text
POST /api/v1/device/telemetry
```

Simulation must use:

- Simulator device
- Test trip
- `SIMULATOR` telemetry source
- Real device authentication
- Real telemetry validation
- Real rule engine
- Real database storage
- Real WebSocket updates

Required scenarios are:

- Normal driving
- Harsh braking
- Sudden acceleration
- Overspeeding
- Sharp turning
- Repeated aggressive behaviour
- Connection loss
- Full pitch demonstration

The dashboard must clearly display:

```text
SIMULATION MODE - TEST DATA
```

Simulated trips must be excluded from official analytics.

---

## 17. Full Pitch Demonstration Scenario

The main pitch scenario must be repeatable.

Suggested flow:

| Stage | Behaviour | Expected result |
|---|---|---|
| 1 | Normal driving | Map moves, score stays near 100 |
| 2 | Harsh braking | Event and evidence appear |
| 3 | Normal driving | Event closes |
| 4 | Overspeeding | One continuous event appears |
| 5 | Sharp turning | Turning event appears |
| 6 | Sudden acceleration | Acceleration event appears |
| 7 | Multiple events | Aggressive pattern detected |
| 8 | Risk transition | Manager alert appears |
| 9 | Telemetry stops | Device becomes delayed/offline |
| 10 | Telemetry resumes | Device returns online |
| 11 | Trip ends | Final summary is generated |

The scenario should use a fixed seed or predetermined values so that the result is predictable during the competition.

---

## 18. Live Dashboard

The active-trip dashboard must show:

- Driver
- Vehicle
- Device
- Trip mode
- Telemetry source
- Trip status
- Device connection status
- Current safety score
- Current risk level
- Current speed
- Forward acceleration
- Lateral acceleration
- Yaw rate
- Current location
- Live route
- Sensor graphs
- Applied thresholds
- Event counters
- Event timeline
- Behaviour patterns
- Alerts
- Simulation controls for test trips
- End Trip action

The live dashboard must use:

- REST for the initial complete snapshot
- WebSocket for subsequent changes

---

## 19. REST API Responsibilities

REST APIs are used for:

- Login and logout
- User management
- Driver management
- Vehicle management
- Device management
- Device assignment
- Starting and ending trips
- Telemetry uploads
- Loading live snapshots
- Loading historical trips
- Loading summaries
- Loading settings
- Alert actions
- Simulation controls

REST follows:

```text
Client request
        ↓
Backend response
```

---

## 20. WebSocket Responsibilities

WebSocket is used to push live updates from the backend to the dashboard.

Required live message types include:

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

WebSocket messages must only be published after the related database transaction commits successfully.

When WebSocket disconnects, the frontend must:

1. Show reconnecting status.
2. Use polling fallback where necessary.
3. Reconnect.
4. Load a new REST snapshot.
5. Resume live updates.

---

## 21. Completed Trip Summary

The completed-trip report must contain:

- Trip start and end
- Driver
- Vehicle
- Device assignment
- Trip mode
- Duration
- Estimated distance
- Average speed
- Maximum speed
- Overspeed duration
- Event counts
- Event-rate metrics
- Pattern counts
- Final safety score
- Final risk level
- Score breakdown
- Route
- Event markers
- Telemetry evidence
- Data quality
- Primary concern
- Recommendations

The system may provide a rule-based eco-driving indicator.

It must not claim an exact fuel-consumption or fuel-waste value unless reliable fuel measurements are available.

---

## 22. Driver Performance

Driver performance is based on valid completed official trips.

The initial MVP driver score uses the latest five valid trips with greater weight given to recent trips.

Example weighting:

| Trip | Weight |
|---|---:|
| Most recent | 5 |
| Second most recent | 4 |
| Third | 3 |
| Fourth | 2 |
| Fifth | 1 |

Driver performance may show:

- Overall score
- Risk level
- Trend
- Latest valid trips
- Normalized event rates
- Primary concern
- Recommendations
- Manager notes
- Review history

Test trips must not affect these results.

---

## 23. Data Quality

The system must monitor:

- Missing GPS
- Invalid sensor values
- Delayed packets
- Duplicate packets
- Telemetry gaps
- Unrealistic speed
- Missing fields
- Processing failures
- Device disconnection

Data quality may be classified as:

- GOOD
- ACCEPTABLE
- LIMITED
- INSUFFICIENT

Poor data quality must reduce assessment confidence.

The system must not present an unreliable trip assessment as highly confident.

---

## 24. Security Requirements

### 24.1 Human Users

The MVP must support:

- Email and password authentication
- Secure password hashing
- HTTP-only authentication cookie
- Organization isolation
- Role-based authorization

### 24.2 Devices

The MVP must support:

- Device identifier
- Device API key
- Device administrative status
- Credential rotation
- Telemetry schema version

Devices must never receive direct PostgreSQL credentials.

Secrets must be stored in environment variables and excluded from Git.

---

## 25. Database Requirements

The database must use PostgreSQL.

The schema must be reviewed for:

- First Normal Form
- Second Normal Form
- Third Normal Form
- BCNF where appropriate
- Foreign-key integrity
- Unique constraints
- Check constraints
- Indexing
- Assignment history
- Rule versioning
- Auditability

Raw telemetry must remain immutable after storage, except for controlled processing metadata.

The frontend must never connect directly to PostgreSQL.

---

## 26. Technology Stack

### Frontend

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- Recharts
- Leaflet

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy Async
- asyncpg
- Alembic

### Database

- PostgreSQL

### Realtime Communication

- WebSocket

### Development and Testing

- Docker Compose
- pytest
- Ruff
- Git
- Antigravity

---

## 27. Deployment Environments

The project must support:

### 27.1 Local Development

- React frontend
- FastAPI backend
- PostgreSQL Docker container
- Simulator
- Worker process

### 27.2 Pitch or Staging Server

- HTTPS frontend
- HTTPS backend
- Secure WebSocket connection
- PostgreSQL database
- Simulator
- Device-status worker
- Demo seed data

### 27.3 Offline Pitch Backup

The complete system must also run locally through Docker Compose in case the competition venue has unreliable internet.

---

## 28. Out of Scope for the MVP

The following are not part of the initial MVP:

- Accident prediction
- Accident-probability percentage
- Medical fatigue diagnosis
- Camera-based facial fatigue detection
- Exact fuel-consumption measurement
- Exact fuel-waste calculation
- Machine-learning event classification
- Automatic road speed limits from live maps
- Multiple simultaneous hardware models
- Native mobile application
- Complex route optimization
- Automatic emergency-service dispatch
- Insurance pricing decisions
- Payroll or disciplinary automation
- Kubernetes
- Microservice deployment
- Kafka
- RabbitMQ
- Production-scale MQTT infrastructure

---

## 29. AI-Ready Meaning

The product may be described as AI-ready because it preserves:

- Raw telemetry
- Confirmed event labels
- Event evidence
- Driver and trip context
- Rule-version information
- Data-quality information
- Outcome history

This data may later support machine-learning models for:

- Improved event classification
- Personalized thresholds
- Behaviour clustering
- Anomaly detection
- Risk trend analysis

The current MVP must not claim that these future models are already implemented.

---

## 30. Pitch-Safe Product Statement

The team should describe the product as:

> EvolveX is an AI-ready IoT driver-behaviour intelligence platform that converts GPS and motion telemetry into explainable driving events, safety scores, behaviour patterns and manager alerts.

The team should not say:

> The system predicts accidents.

A safer statement is:

> The system identifies high-risk driving behaviour and repeated unsafe patterns so fleet managers can intervene earlier.

---

## 31. MVP Acceptance Criteria

The pitching MVP is accepted when:

- A user can log in.
- A driver can be created.
- A vehicle can be created.
- A simulator device can be registered.
- The device can be assigned to the vehicle.
- A test trip can be started.
- The simulator can send telemetry.
- Raw telemetry is stored.
- The live map and measurements update.
- Normal driving does not create false events.
- Harsh braking creates one correct event.
- Sudden acceleration creates one correct event.
- Overspeeding creates one continuous event.
- Sharp turning creates one correct event.
- Repeated events create an aggressive-driving pattern.
- Event and pattern penalties update the score.
- The risk level changes according to configured bands.
- Relevant alerts are created.
- WebSocket updates appear on the dashboard.
- Device disconnection and reconnection are displayed.
- The trip can be ended.
- A final summary is generated.
- Score deductions are explainable.
- Test data is visibly marked.
- Test trips are excluded from official analytics.
- The same system can run locally and on the pitch server.
