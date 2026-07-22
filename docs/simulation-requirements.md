# EvolveX Driver Behaviour Intelligence Platform

## Simulation Requirements Document

**Document version:** 1.0  
**Project stage:** Pitching MVP  
**Simulation type:** Controlled virtual IoT device  
**Telemetry transport:** REST  
**Live dashboard updates:** WebSocket  
**Simulation data classification:** TEST data  

---

## 1. Purpose

This document defines the requirements for the EvolveX virtual-device simulator.

The simulator is required because the physical sensor hardware is still being calibrated and may not consistently produce reliable values.

The simulator allows the team to:

- Develop the software without waiting for stable hardware
- Test the complete telemetry pipeline
- Demonstrate the MVP consistently during the pitch
- Reproduce specific driving behaviours
- Test event-detection thresholds
- Test score and alert behaviour
- Test device disconnection and recovery
- Perform repeatable regression testing

The simulator is an official MVP component.

It must not be implemented as a visual-only fake dashboard.

---

## 2. Simulation Principle

The simulator acts as a virtual IoT device.

```text
Virtual Device Simulator
        ↓
POST /api/v1/device/telemetry
        ↓
Device authentication
        ↓
Telemetry adapter
        ↓
Validation
        ↓
Raw telemetry storage
        ↓
Driving-rule engine
        ↓
Events
        ↓
Patterns
        ↓
Scores and risk
        ↓
Alerts
        ↓
Database commit
        ↓
WebSocket updates
        ↓
React dashboard
```

The simulator must use the same backend processing path as the physical ESP32 device.

---

## 3. Prohibited Simulation Behaviour

The simulator must not:

- Insert driving events directly into PostgreSQL
- Create score penalties directly
- Create behaviour patterns directly
- Create alerts directly
- Modify React dashboard state directly
- Call event detectors directly
- Call the score engine directly
- Bypass device authentication
- Bypass telemetry validation
- Bypass raw telemetry storage
- Pretend that simulated values are physical sensor values
- Update official driver or fleet analytics
- Use a production hardware credential
- Use an official trip unless explicitly approved for controlled testing

A simulation button must produce telemetry values, not final outcomes.

Correct:

```text
Trigger Harsh Braking Scenario
        ↓
Generate several telemetry packets
        ↓
Backend detects harsh braking
```

Incorrect:

```text
Trigger Harsh Braking Button
        ↓
Insert HARSH_BRAKING event
```

---

## 4. Simulation Data Classification

Every simulation must use all of the following protections:

```text
Simulator device
+
Device administrative status = TESTING
+
Trip mode = TEST
+
Telemetry source = SIMULATOR
+
Visible simulation badge
```

The dashboard must display:

```text
SIMULATION MODE — TEST DATA
```

Test-trip outputs may include:

- Telemetry
- Events
- Patterns
- Score changes
- Risk changes
- Alerts
- Route
- Trip summary
- Data-quality results

Test-trip outputs must not affect:

- Official driver score
- Driver ranking
- Driver trend
- Fleet average
- Official fleet reports
- Official driver-performance snapshots

---

## 5. Simulator Device

The development seed data must create a simulator device.

Suggested values:

```text
Device code: SIM-DEVICE-001
Display name: EvolveX Pitch Simulator
Device type: SIMULATOR
Administrative status: TESTING
Telemetry schema version: 1.0
Firmware version: simulator-1.0
```

The simulator authenticates using:

```http
X-Device-Code: SIM-DEVICE-001
X-Device-Key: simulator-device-key
X-Telemetry-Schema-Version: 1.0
```

The key must be stored through environment configuration or another secure local mechanism.

It must not be hard-coded in committed source code.

---

## 6. Simulator Vehicle and Driver

The pitch seed data should include:

```text
Driver: Demo Driver
Vehicle: Demo Vehicle
Device: SIM-DEVICE-001
```

The simulator device must have an active assignment to the demo vehicle.

Before running a scenario, the manager starts a test trip by selecting:

- Demo Driver
- Demo Vehicle
- `TEST` trip mode
- Applied speed limit

The backend resolves the simulator device through the active assignment.

---

## 7. Simulator Components

The simulator should contain the following internal components.

### 7.1 Simulation controller

Responsible for:

- Starting simulations
- Pausing simulations
- Resuming simulations
- Stopping simulations
- Tracking current status
- Preventing conflicting runs

### 7.2 Scenario loader

Responsible for:

- Loading scenario definitions
- Validating scenario structure
- Selecting scenario version
- Returning configured phases

### 7.3 Packet generator

Responsible for:

- Generating one telemetry packet at each interval
- Producing controlled variation
- Assigning sequence numbers
- Assigning device timestamps
- Preserving realistic relationships between values

### 7.4 Route generator

Responsible for:

- Moving the simulated vehicle through a predefined route
- Producing gradual GPS changes
- Avoiding impossible jumps
- Providing event locations

### 7.5 Telemetry client

Responsible for:

- Sending packets to the real telemetry endpoint
- Supplying device authentication headers
- Handling success, duplicate and retryable error responses
- Recording simulator-side failures

### 7.6 Simulation-run state manager

Responsible for:

- Current step
- Total steps
- Status
- Started time
- Paused time
- Completed time
- Failure state
- Random seed
- Current sequence number

---

## 8. Recommended Simulator Structure

```text
backend/
├── src/evolvex/
│   └── modules/
│       └── simulation/
│           ├── router.py
│           ├── schemas.py
│           ├── service.py
│           ├── repository.py
│           ├── controller.py
│           ├── scenario_loader.py
│           ├── packet_generator.py
│           ├── route_generator.py
│           ├── telemetry_client.py
│           └── scenarios/
│               ├── normal_driving.json
│               ├── harsh_braking.json
│               ├── sudden_acceleration.json
│               ├── overspeeding.json
│               ├── sharp_turning.json
│               ├── aggressive_pattern.json
│               ├── connection_loss.json
│               └── full_pitch_demo.json
│
└── scripts/
    └── simulate_device.py
```

The command-line script and API-controlled simulator may share the same simulator services.

---

## 9. Simulation States

A simulation run supports:

- `STOPPED`
- `RUNNING`
- `PAUSED`
- `COMPLETED`
- `FAILED`

State transitions:

```text
STOPPED
    ↓ start
RUNNING
    ↓ pause
PAUSED
    ↓ resume
RUNNING
    ↓ scenario ends
COMPLETED
```

Alternative transitions:

```text
RUNNING
    ↓ stop
STOPPED
```

```text
RUNNING or PAUSED
    ↓ unrecoverable error
FAILED
```

Invalid transitions must be rejected.

Examples:

- Resume a running simulation → rejected
- Pause a stopped simulation → rejected
- Start a second run for the same trip → rejected
- Resume a completed simulation → rejected

---

## 10. Simulation Control APIs

The simulator is controlled using the approved REST APIs.

### List scenarios

```http
GET /api/v1/simulation/scenarios
```

### Start

```http
POST /api/v1/simulation/start
```

Example:

```json
{
  "tripId": "test-trip-uuid",
  "scenarioCode": "FULL_PITCH_DEMO",
  "packetIntervalMs": 1000,
  "randomSeed": 2026
}
```

### Status

```http
GET /api/v1/simulation/status
```

### Pause

```http
POST /api/v1/simulation/pause
```

### Resume

```http
POST /api/v1/simulation/resume
```

### Stop

```http
POST /api/v1/simulation/stop
```

The control APIs manage simulator state.

Generated sensor packets still use:

```http
POST /api/v1/device/telemetry
```

---

## 11. Start Validation

Before a simulation starts, the backend must confirm:

- User is authenticated
- User has simulation permission
- Trip exists
- Trip belongs to the user’s organization
- Trip is active
- Trip mode is `TEST`
- Vehicle has the expected active assignment
- Assigned device type is `SIMULATOR`
- Device administrative status is `TESTING` or another approved simulation state
- Scenario exists
- Scenario is enabled
- Packet interval is within allowed limits
- No conflicting simulation is already active
- The trip is not being finalized
- An active rule-set version is attached to the trip

Failure must return a documented business error.

---

## 12. Simulation Scenario Definition

A scenario should be described using controlled phases.

Example structure:

```json
{
  "scenarioCode": "HARSH_BRAKING",
  "name": "Harsh Braking Demonstration",
  "version": 1,
  "estimatedDurationSeconds": 15,
  "defaultPacketIntervalMs": 1000,
  "routeCode": "PITCH_ROUTE_01",
  "phases": [
    {
      "phaseCode": "NORMAL_APPROACH",
      "durationSeconds": 5,
      "behaviour": "NORMAL",
      "speedRangeKmh": [48, 55],
      "forwardAccelerationRangeMs2": [-0.8, 0.5],
      "lateralAccelerationRangeMs2": [-0.4, 0.4],
      "yawRateRangeDegS": [-5, 5]
    },
    {
      "phaseCode": "BRAKING",
      "durationSeconds": 3,
      "behaviour": "HARSH_BRAKING",
      "speedRangeKmh": [35, 48],
      "forwardAccelerationRangeMs2": [-4.6, -4.0],
      "lateralAccelerationRangeMs2": [-0.4, 0.4],
      "yawRateRangeDegS": [-5, 5]
    },
    {
      "phaseCode": "RECOVERY",
      "durationSeconds": 7,
      "behaviour": "NORMAL",
      "speedRangeKmh": [30, 38],
      "forwardAccelerationRangeMs2": [-0.8, 0.5],
      "lateralAccelerationRangeMs2": [-0.4, 0.4],
      "yawRateRangeDegS": [-5, 5]
    }
  ]
}
```

The scenario definition describes sensor behaviour.

It does not define final event IDs, scores or alerts.

---

## 13. Deterministic Simulation

The pitch demonstration must produce predictable results.

Use a fixed random seed.

Suggested pitch seed:

```text
2026
```

Conceptually:

```text
Same scenario
+
Same seed
+
Same rule version
+
Same interval
=
Same telemetry sequence
```

This helps ensure:

- Events occur at expected times
- Scores are predictable
- Alerts appear consistently
- Demonstrations can be rehearsed
- Bugs can be reproduced

Random variation may exist inside configured ranges, but the fixed seed must make it repeatable.

---

## 14. Packet Interval

The default simulator interval is:

```text
1000 milliseconds
```

This approximates one telemetry packet per second.

The interval may be configurable within safe limits.

Suggested accepted range:

```text
250 ms to 5000 ms
```

The full pitch demo should normally use:

```text
1000 ms
```

A very short interval must not be used to overload the MVP backend.

---

## 15. Sequence Numbers

Each run must generate:

- One boot identifier
- Increasing sequence numbers

Example:

```text
bootId = simulation-run UUID
sequenceNumber = 1, 2, 3, 4...
```

A packet identity uses:

```text
device
+
bootId
+
sequenceNumber
```

This supports:

- Duplicate detection
- Retry safety
- Packet ordering
- Missing-sequence testing

Sequence numbers must not be reused inside one run.

---

## 16. Device Timestamp

The simulator provides a device-style timestamp.

The backend also records:

```text
serverReceivedAt
```

The server-received timestamp is the authoritative backend arrival time.

The simulator must support realistic timestamp progress.

It should not produce future timestamps or move backwards unless testing invalid-data handling.

---

## 17. Version 1 Telemetry Packet

The current simulation packet should match the approved hardware-compatible version 1 contract.

Example:

```json
{
  "boot_id": "simulation-run-uuid",
  "sequence_number": 42,
  "timestamp": 42000,
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

Hardware flags may optionally be generated for comparison.

The backend rules remain the official event source.

---

## 18. Standardized Telemetry Mapping

The telemetry adapter maps:

```text
accel_fwd
→ forwardAccelerationMs2

accel_lat
→ lateralAccelerationMs2

yaw_rate
→ yawRateDegS

speed_kmh
→ speedKmh

lat
→ latitude

lng
→ longitude
```

Simulation scenario definitions may use standardized internal names.

The telemetry client converts them into the selected outgoing schema version.

---

## 19. Realistic Value Generation

Values must change gradually unless a scenario intentionally produces an aggressive event.

Incorrect:

```text
Second 1: 20 km/h
Second 2: 180 km/h
Second 3: 5 km/h
```

Correct:

```text
Second 1: 45 km/h
Second 2: 48 km/h
Second 3: 52 km/h
Second 4: 55 km/h
```

The generator should preserve reasonable consistency between:

- Speed
- Forward acceleration
- Route progress
- Lateral acceleration
- Yaw rate

The values do not need to be a perfect physical vehicle model, but they must be believable and internally consistent for the demonstration.

---

## 20. Normal Driving Scenario

Scenario code:

```text
NORMAL_DRIVING
```

Purpose:

- Confirm normal values are accepted
- Confirm live map movement
- Confirm graphs update
- Confirm false events are not generated
- Confirm score remains near 100

Suggested example ranges:

```text
Speed: 35–55 km/h
Forward acceleration: -1.0 to +1.0 m/s²
Lateral acceleration: -0.8 to +0.8 m/s²
Yaw rate: -10 to +10 degrees/second
```

Expected outcome:

```text
No confirmed unsafe-driving event
No pattern
No behaviour alert
Score remains 100 unless another configured rule applies
Risk remains LOW
```

The exact event decision belongs to the configured backend rules.

---

## 21. Harsh Braking Scenario

Scenario code:

```text
HARSH_BRAKING
```

Example sequence:

| Second | Speed km/h | Forward acceleration m/s² |
|---:|---:|---:|
| 1 | 55 | -0.4 |
| 2 | 54 | -0.8 |
| 3 | 49 | -4.2 |
| 4 | 42 | -4.5 |
| 5 | 36 | -2.0 |
| 6 | 34 | -0.5 |

Example threshold:

```text
-3.5 m/s²
```

The threshold is an example and remains configurable.

Expected outcome:

- Candidate state starts
- Minimum duration is satisfied
- One harsh-braking event is confirmed
- Event closes after release condition
- One event penalty may be applied
- Live evidence appears

The scenario must not create one event per severe packet.

---

## 22. Sudden Acceleration Scenario

Scenario code:

```text
SUDDEN_ACCELERATION
```

Example:

| Second | Speed km/h | Forward acceleration m/s² |
|---:|---:|---:|
| 1 | 15 | 0.5 |
| 2 | 18 | 1.0 |
| 3 | 25 | 3.6 |
| 4 | 33 | 3.8 |
| 5 | 39 | 1.5 |
| 6 | 42 | 0.5 |

Example threshold:

```text
+3.0 m/s²
```

Expected outcome:

- One sudden-acceleration event
- Event evidence
- Severity classification
- Score impact according to configuration

---

## 23. Overspeeding Scenario

Scenario code:

```text
OVERSPEEDING
```

Example configuration:

```text
Applied speed limit = 60 km/h
Tolerance = 5 km/h
Detection threshold = 65 km/h
Release threshold = 62 km/h
```

Suggested phases:

```text
Normal speed
    ↓
Speed rises above 65 km/h
    ↓
Speed stays above threshold
    ↓
One active overspeed event
    ↓
Speed falls below release threshold
    ↓
Event closes
```

Expected outcome:

- One continuous event
- Duration updates
- Maximum speed updates
- Applied speed limit stored
- Score penalty applied once
- Event closes when release condition is reached

The simulator must not directly create the event.

---

## 24. Sharp Turning Scenario

Scenario code:

```text
SHARP_TURNING
```

Example values:

```text
Speed = 38 km/h
Lateral acceleration = 3.2 m/s²
Yaw rate = 38 degrees/second
```

Example thresholds:

```text
Lateral acceleration threshold = 2.8 m/s²
Yaw-rate threshold = 30 degrees/second
Minimum speed = 20 km/h
```

Expected outcome:

- Candidate state starts
- One sharp-turn event is confirmed
- Direction may be determined from signal sign
- Event evidence appears
- Score impact is applied according to severity

The exact thresholds remain backend configuration.

---

## 25. Repeated Aggressive Pattern Scenario

Scenario code:

```text
REPEATED_AGGRESSIVE_PATTERN
```

The scenario combines several event-producing phases.

Example timeline:

```text
Minute 1 → Harsh braking
Minute 2 → Overspeeding
Minute 4 → Sharp turning
Minute 5 → Sudden acceleration
Minute 7 → Overspeeding
```

Expected backend flow:

```text
Confirmed events
        ↓
Rolling-window evaluation
        ↓
Mixed aggressive-driving pattern
        ↓
Pattern severity
        ↓
Pattern penalty
        ↓
Possible alert
```

The simulator does not declare that a pattern has occurred.

It only generates the telemetry needed for the backend to determine it.

---

## 26. Connection-Loss Scenario

Scenario code:

```text
CONNECTION_LOSS
```

The scenario intentionally stops sending packets.

Expected flow:

```text
Packets arriving
        ↓
Device ONLINE
        ↓
Packets stop
        ↓
Device DELAYED
        ↓
More time passes
        ↓
Device OFFLINE
```

When packet sending resumes:

```text
Device OFFLINE
        ↓
New accepted packet
        ↓
Device ONLINE
```

Expected dashboard behaviour:

- Device status changes
- Last telemetry time is shown
- Last-known location remains visible
- Offline alert may appear
- Connection-restored update may appear

The dashboard must not display:

```text
Accident detected
```

---

## 27. GPS-Unavailable Scenario

An optional reliability scenario may send:

```json
{
  "lat": null,
  "lng": null,
  "speed_kmh": 42,
  "accel_fwd": 0.4,
  "accel_lat": 0.2,
  "yaw_rate": 3.0
}
```

Expected result:

- Sensor telemetry may be accepted as partial
- GPS validity becomes false
- Map uses last valid location
- Data-quality confidence may reduce
- Valid sensor processing may continue
- No unsafe event is created only because GPS is missing

---

## 28. Duplicate-Packet Scenario

An optional reliability scenario sends the same:

```text
bootId
+
sequenceNumber
```

more than once.

Expected result:

- First packet is accepted
- Repeated packet is identified as duplicate
- No duplicate raw accepted record where uniqueness prevents it
- No duplicate event
- No duplicate score penalty
- No duplicate alert

---

## 29. Invalid-Value Scenario

An optional scenario may send an invalid value:

```json
{
  "speed_kmh": 900
}
```

Expected result:

- Packet is rejected or marked invalid according to validation policy
- Value does not affect official event processing
- No score change occurs
- Failure is visible in diagnostics
- Simulator records the failed response

---

## 30. Full Pitch Demonstration Scenario

Scenario code:

```text
FULL_PITCH_DEMO
```

This is the primary competition scenario.

It must be deterministic.

Suggested timeline:

| Period | Scenario stage | Expected result |
|---:|---|---|
| 0–10 sec | Normal driving | Map moves, score remains 100 |
| 11–16 sec | Harsh braking | Harsh-braking event appears |
| 17–26 sec | Normal recovery | Event closes |
| 27–42 sec | Overspeeding | One continuous event |
| 43–49 sec | Normal recovery | Overspeed event closes |
| 50–55 sec | Sharp turning | Sharp-turn event |
| 56–62 sec | Sudden acceleration | Acceleration event |
| 63–80 sec | Additional aggressive events | Repeated pattern |
| 81–96 sec | Transmission stops | Delayed/offline status |
| 97–110 sec | Transmission resumes | Device returns online |
| End | Trip is ended by manager | Final summary |

The exact durations may be adjusted to match the configured thresholds.

---

## 31. Full Pitch Demo Expected Outputs

During the full scenario, the judges should see:

### Normal stage

- Vehicle moves on the map
- Speed changes
- Live graphs update
- Score remains near 100
- Risk remains LOW

### Harsh braking stage

- Forward-acceleration graph crosses threshold
- One event appears
- Event severity is displayed
- Score changes
- Evidence is available

### Overspeeding stage

- Speed crosses threshold
- Overspeed duration increases
- Maximum speed updates
- One continuous event is maintained

### Pattern stage

- Multiple confirmed events exist
- Aggressive pattern appears
- Pattern penalty is applied
- Risk may change
- Manager alert appears

### Connection-loss stage

- Status changes to DELAYED
- Status changes to OFFLINE
- Last-known location remains visible
- Alert may appear

### Recovery stage

- Telemetry resumes
- Status returns to ONLINE
- Live updates continue

### Completion stage

- Trip ends
- Final score appears
- Final risk appears
- Event and pattern breakdown appears
- Route and evidence remain available
- Data quality is shown
- Recommendation is generated

---

## 32. Simulated Route

The full pitch demo must use a predefined route.

Example route representation:

```json
{
  "routeCode": "PITCH_ROUTE_01",
  "points": [
    {
      "latitude": 7.2906,
      "longitude": 80.6337
    },
    {
      "latitude": 7.2912,
      "longitude": 80.6345
    },
    {
      "latitude": 7.2921,
      "longitude": 80.6357
    }
  ]
}
```

The route generator must interpolate between points.

The vehicle marker should move gradually.

It must not jump randomly across unrelated geographic locations.

---

## 33. Route and Speed Relationship

Route progress should be approximately consistent with vehicle speed and packet interval.

The MVP does not need an advanced physical navigation simulation.

However, it should avoid obvious contradictions such as:

```text
Speed = 0 km/h
Route moves several hundred metres per second
```

or:

```text
Speed = 80 km/h
Vehicle marker remains unchanged for the complete trip
```

---

## 34. Offline Map Consideration

The pitch system must have an offline fallback.

Possible MVP approaches:

- Bundle a static route background image
- Cache required local map tiles before the pitch
- Use a simplified coordinate-grid fallback
- Display the route on a locally stored schematic map

The core software demonstration must not fail completely because live online map tiles are unavailable.

The primary deployed demonstration may use normal online map tiles.

---

## 35. Pause Behaviour

When a simulation is paused:

- New telemetry packets stop
- Simulation status becomes `PAUSED`
- Current step is preserved
- Sequence number is preserved
- Route position is preserved
- Trip remains active

Important consequence:

A long pause may cause the device-status worker to classify the simulator as delayed or offline.

For manual demonstration pauses, the implementation may distinguish:

```text
Pause packet generation
```

from:

```text
Simulate connection loss
```

Recommended behaviour:

- A normal operator pause should update the simulation state but may still stop packets.
- The UI must warn that pausing long enough can trigger device-offline logic.
- The connection-loss scenario intentionally depends on this behaviour.

---

## 36. Resume Behaviour

When resumed:

- Status changes from `PAUSED` to `RUNNING`
- Packet generation continues from the preserved step
- Sequence numbers continue increasing
- Route continues from the preserved position
- Device may return to ONLINE after a new accepted packet

Resume must not restart the scenario from the beginning.

Restarting requires a separate new run.

---

## 37. Stop Behaviour

When stopped:

- New packets stop
- Status becomes `STOPPED`
- Current run remains available for audit
- Trip remains active unless the manager ends it
- Generated records are not deleted

Stopping a simulation must not automatically erase events, scores or telemetry.

---

## 38. Restarting a Scenario

To restart cleanly:

1. Stop the current run.
2. End or cancel the current test trip if required.
3. Start a new test trip.
4. Start a new simulation run.
5. Reset sequence and route state through the new run identity.

For the pitch, a demo reset script may restore a known database state.

---

## 39. Concurrency Rules

For the MVP:

- One active simulation run per trip
- One active simulation run per simulator device
- One active trip per device assignment
- One controller operation at a time for the same run

The backend must prevent:

- Two users starting the same scenario simultaneously
- Two workers producing packets for the same run
- Pause and stop being applied concurrently without control
- Repeated start requests creating duplicate runs

Use:

- Database constraints
- Row locks
- Idempotency keys
- Run status validation

---

## 40. Simulation Persistence

Simulation-run state must be stored in PostgreSQL.

The `simulation_runs` record stores:

- Scenario
- Trip
- Device
- Status
- Seed
- Packet interval
- Current step
- Start time
- Pause time
- Completion time
- Failure information

Scenario definitions may be stored:

- As version-controlled JSON files
- In the `simulation_scenarios` database table
- Or both, with a controlled synchronization strategy

For the first MVP, version-controlled scenario files plus seeded scenario metadata are acceptable.

---

## 41. Simulator Processing Location

For the pitching MVP, the simulator may run:

- Inside the backend process for simple development
- As a separate worker process
- As a command-line process controlled through shared database state

The preferred architecture is a separate simulator worker or controlled background task so that packet generation does not block normal API requests.

The simulator must still call the real telemetry HTTP endpoint.

---

## 42. Simulator Worker Restart

If the simulator process restarts:

- Active simulation runs must be identified
- They may be marked `FAILED`
- Automatic continuation is optional for the MVP
- The user may start a new controlled run

The system must not silently restart at an incorrect step and create unexpected duplicate events.

---

## 43. Telemetry Response Handling

The simulator telemetry client must handle:

### Accepted

```text
ACCEPTED / PROCESSED
```

Proceed to the next packet.

### Partial

```text
ACCEPTED / PARTIAL
```

Record warning and continue where appropriate.

### Duplicate

```text
DUPLICATE
```

Do not retry endlessly.

### Authentication failure

```text
401 or 403
```

Mark run failed and stop.

### Validation failure

```text
400 or 422
```

Record the response.

For normal scenarios, mark the run failed because scenario values should have been valid.

### Temporary server failure

```text
500 or 503
```

Retry according to a bounded strategy.

---

## 44. Retry Strategy

For a temporary telemetry upload failure, the simulator may retry.

Suggested approach:

```text
Attempt 1
    ↓ failure
Wait 1 second
    ↓
Attempt 2
    ↓ failure
Wait 2 seconds
    ↓
Attempt 3
```

Retries must use the same packet identity.

This allows the backend to recognize the packet if the original request succeeded but its response was lost.

Retries must be bounded.

---

## 45. Simulation Progress

Simulation progress is available through:

```http
GET /api/v1/simulation/status
```

The response may include:

- Run status
- Current step
- Total steps
- Current phase
- Progress percentage
- Last packet result
- Started time
- Estimated remaining time

For the MVP, the control panel may poll this endpoint every one or two seconds.

A dedicated WebSocket simulation-progress message may be added later if necessary.

Simulation-generated business results still arrive through normal WebSocket messages.

---

## 46. WebSocket Behaviour

The simulator does not publish directly to WebSocket.

Correct flow:

```text
Simulator
    ↓ REST
Telemetry endpoint
    ↓
Backend transaction
    ↓ commit
WebSocket publisher
    ↓
React dashboard
```

Simulation produces the same WebSocket message types as hardware:

- `TELEMETRY_UPDATED`
- `DRIVING_EVENT_CREATED`
- `DRIVING_EVENT_UPDATED`
- `BEHAVIOUR_PATTERN_CREATED`
- `BEHAVIOUR_PATTERN_UPDATED`
- `TRIP_SCORE_UPDATED`
- `ALERT_CREATED`
- `DEVICE_STATUS_CHANGED`
- `TRIP_STATUS_CHANGED`
- `TRIP_COMPLETED`

No fake simulation-specific event message is required.

---

## 47. Simulation Control Panel

The live test-trip page should include a simulation panel.

Required fields:

- Scenario selector
- Simulator device
- Current status
- Current phase
- Progress
- Start button
- Pause button
- Resume button
- Stop button

Example:

```text
┌─────────────────────────────────────────┐
│ Simulation Control                      │
│                                         │
│ Scenario: Full Pitch Demonstration      │
│ Device: SIM-DEVICE-001                  │
│ Status: RUNNING                         │
│ Phase: OVERSPEEDING                     │
│ Progress: 42 / 110                      │
│                                         │
│ [Start] [Pause] [Resume] [Stop]         │
└─────────────────────────────────────────┘
```

The panel must be hidden or disabled for official hardware trips.

---

## 48. Individual Scenario Controls

For judge questions, the UI may provide quick scenario options:

- Run normal driving
- Run harsh braking
- Run sudden acceleration
- Run overspeeding
- Run sharp turning
- Run repeated aggressive pattern
- Simulate connection loss
- Run complete pitch demo

Each option starts a controlled scenario.

It does not directly create the expected outcome.

---

## 49. Dashboard Identification

A running simulated trip must visibly show:

```text
TEST TRIP
SIMULATION MODE
SIMULATED TELEMETRY
Excluded from official analytics
```

Suggested header:

```text
SIMULATION MODE — TEST DATA
Driver: Demo Driver
Vehicle: Demo Vehicle
Device: SIM-DEVICE-001
```

The label must remain visible throughout the demo.

---

## 50. Pitch Explanation

Recommended team statement:

> For repeatable demonstration and software validation, the current MVP uses a controlled virtual IoT device. It sends realistic GPS and motion values through the same secured telemetry API used by our physical hardware. Every event, score, pattern and alert shown on the dashboard is calculated by the real backend and stored in the real database.

The team should not say:

> We generated random values because the hardware does not work.

A stronger explanation is:

> The sensor hardware is currently undergoing calibration, so the simulation layer allows independent and repeatable validation of the full software pipeline.

---

## 51. Pitch Demonstration Steps

### Step 1 — Login

The fleet manager logs in.

### Step 2 — Start test trip

Select:

```text
Demo Driver
Demo Vehicle
TEST mode
60 km/h applied limit
```

### Step 3 — Open live dashboard

Confirm:

- Simulation badge
- Score 100
- Risk LOW
- Device status

### Step 4 — Start full pitch scenario

Select:

```text
FULL_PITCH_DEMO
```

Press:

```text
Start Simulation
```

### Step 5 — Explain normal driving

Show:

- Moving map
- Live values
- No false events

### Step 6 — Explain harsh braking

Show:

- Acceleration graph
- Threshold
- Event
- Score change
- Evidence

### Step 7 — Explain overspeeding

Show:

- Speed limit
- Detection threshold
- Event duration
- Maximum speed
- One continuous event

### Step 8 — Explain repeated pattern

Show:

- Included events
- Pattern severity
- Pattern penalty
- Risk change
- Alert

### Step 9 — Explain disconnection

Show:

- DELAYED
- OFFLINE
- Last-known location

State clearly that offline means communication loss, not accident detection.

### Step 10 — Explain recovery

Show the device returning online.

### Step 11 — End trip

Show:

- Final score
- Final risk
- Event breakdown
- Pattern breakdown
- Route
- Data quality
- Recommendation

---

## 52. Test Expectations

Each scenario must define expected outcomes.

Example:

```json
{
  "scenarioCode": "HARSH_BRAKING",
  "expectedOutcomes": {
    "harshBrakingEvents": 1,
    "suddenAccelerationEvents": 0,
    "overspeedEvents": 0,
    "sharpTurnEvents": 0,
    "minimumScore": 0,
    "maximumScore": 100
  }
}
```

Expected values are used in automated tests.

They must not be used to force the backend result.

---

## 53. Scenario Validation

Before a scenario is enabled, validate:

- Unique scenario code
- Positive duration
- Positive packet interval
- Valid ranges
- Minimum value not greater than maximum
- Valid route reference
- Valid phase order
- At least one phase
- Supported telemetry fields
- Expected step count
- No unsupported direct outcome instruction

---

## 54. Unit Tests

Unit tests should cover:

- Scenario loading
- Invalid scenario rejection
- Deterministic seed
- Gradual value generation
- Route interpolation
- Sequence generation
- Timestamp generation
- Pause and resume
- Stop state
- Invalid state transitions
- Retry identity preservation

---

## 55. Integration Tests

Integration tests should verify:

```text
Simulator
    ↓
Real telemetry API
    ↓
PostgreSQL
```

Test:

- Device authentication
- Raw telemetry creation
- Trip linkage
- Source type
- Duplicate detection
- Missing GPS
- Validation failure
- Server retry
- Simulation-run status

---

## 56. Rule-Engine Scenario Tests

For each event scenario:

- Start a test trip
- Start the scenario
- Wait for completion
- Query events
- Confirm expected event type
- Confirm expected event count
- Confirm score ledger
- Confirm no duplicate penalties
- Confirm event evidence

Normal driving must not produce false event results.

---

## 57. Full Pitch End-to-End Test

The automated or rehearsed full test must verify:

- Test trip starts
- Simulator starts
- Telemetry is stored
- Live dashboard updates
- Harsh braking is detected
- Overspeeding is detected
- Sharp turning is detected
- Sudden acceleration is detected
- Repeated aggressive pattern is detected
- Score changes are explainable
- Risk changes correctly
- Alert appears
- Device becomes offline
- Device returns online
- Trip ends
- Summary is created
- Test trip remains excluded from official analytics

---

## 58. Failure Tests

Test:

- Wrong device key
- Disabled simulator device
- Official trip supplied to simulation start
- Missing active assignment
- Duplicate start request
- Invalid scenario code
- Invalid packet value
- Backend unavailable
- Database unavailable
- Worker restart
- Duplicate telemetry
- Pause during event phase
- Stop before completion
- Browser disconnection
- WebSocket recovery

---

## 59. Performance Expectations

For the pitch MVP:

- One simulator device is required
- One packet per second is expected
- One active full scenario is sufficient
- Dashboard updates should appear near-real-time
- Start and stop actions should respond without noticeable delay
- Scenario status should remain responsive

Multiple simultaneous simulated fleets are outside the initial requirement.

---

## 60. Logging

Simulation logs may include:

- Simulation run ID
- Scenario code
- Trip ID
- Device ID
- Current phase
- Current step
- Packet sequence
- Telemetry response status
- Retry count
- Failure code
- Start, pause, resume and stop actions

Logs must not contain:

- Plain device API keys
- User passwords
- Session tokens
- Database credentials

---

## 61. Audit Requirements

Important simulation actions should be audited:

- Simulation started
- Simulation paused
- Simulation resumed
- Simulation stopped
- Simulation failed
- Scenario selected
- User who performed the action

Audit records must link to:

- User
- Organization
- Trip
- Simulation run

---

## 62. Deployment Requirements

The pitch server must run:

- FastAPI backend
- PostgreSQL
- Simulator worker or background service
- Device-status worker
- React frontend
- WebSocket service

Environment configuration must include:

- Backend API URL
- Simulator device code
- Simulator device key
- Default packet interval
- Allowed scenarios
- Retry settings

The deployed simulator must call the deployed telemetry endpoint.

---

## 63. Local Offline Requirements

The complete simulator must work locally through Docker Compose.

```text
Laptop
├── PostgreSQL
├── FastAPI
├── Simulator
├── Worker
└── React frontend
```

The full pitch scenario must run without cloud access.

An offline route/map fallback must be available.

---

## 64. Hardware Replacement

When the physical hardware becomes stable:

```text
Simulator
    ↓ replaced by
ESP32
```

The following must remain unchanged:

- Telemetry endpoint
- Telemetry adapter interface
- Raw telemetry storage
- Rule engine
- Pattern engine
- Score engine
- Alert engine
- WebSocket messages
- React dashboard
- Trip summary

Only these may need adjustment:

- Hardware firmware
- Device credential
- Telemetry schema adapter
- Sensor calibration
- Packet frequency

This confirms that simulation is testing the real software architecture.

---

## 65. Future Replay Support

Future replay mode may read:

- CSV
- JSON
- Exported telemetry records

Replay flow:

```text
Recorded data
    ↓
Replay client
    ↓
Telemetry ingestion API
    ↓
Normal backend processing
```

Replay uses:

```text
sourceType = REPLAY
```

Replay must use a test trip unless a controlled research process explicitly allows another mode.

Replay is useful for:

- Calibration
- Regression testing
- Reproducing bugs
- Comparing rule versions
- Comparing firmware versions

---

## 66. Future Improvements

Possible future enhancements include:

- Multiple simultaneous simulator vehicles
- Custom route upload
- Scenario editor
- Adjustable simulation speed
- Hardware-recording replay
- Sensor noise modelling
- GPS drift modelling
- Offline packet buffering simulation
- Mobile-network latency simulation
- Dedicated simulation-progress WebSocket message
- Automated rule calibration tests

These are not required for the initial pitch MVP.

---

## 67. Simulation Restrictions

The implementation must not:

- Hide the fact that data is simulated
- Use simulation results in official analytics
- Insert final events directly
- Insert score changes directly
- Insert patterns directly
- Insert alerts directly
- Bypass device authentication
- Bypass telemetry validation
- Bypass raw telemetry storage
- Trust the scenario’s expected outcome as the actual outcome
- Create impossible uncontrolled random movement
- Generate unrelated random GPS positions
- Store simulator secrets in Git
- Run a simulation on an official trip
- Create two active runs for one simulator device
- Delete generated evidence when a run stops
- Describe device offline state as an accident
- Claim that the simulation is a machine-learning model

---

## 68. Simulation Acceptance Criteria

The simulation system is accepted when:

- A simulator device can be registered.
- The simulator device can be assigned to a vehicle.
- A test trip can be started.
- Simulation start rejects official trips.
- Simulation start rejects hardware devices.
- Scenarios can be listed.
- A scenario can be started.
- A scenario can be paused.
- A paused scenario can be resumed.
- A scenario can be stopped.
- Invalid state transitions are rejected.
- Scenario progress is available.
- Generated packets use the real telemetry API.
- Generated packets use device authentication.
- Raw telemetry is stored.
- Telemetry source is `SIMULATOR`.
- Trip mode is `TEST`.
- Simulation mode is visible on the dashboard.
- The fixed seed produces repeatable packets.
- GPS movement follows a believable route.
- Normal driving does not create false events.
- Harsh braking creates one correct event.
- Sudden acceleration creates one correct event.
- Overspeeding creates one continuous event.
- Sharp turning creates one correct event.
- Repeated aggressive driving creates the expected pattern.
- Score changes come from the backend score ledger.
- Alerts come from the backend alert engine.
- Connection loss produces delayed and offline status.
- Reconnection returns the device to online.
- Stopping simulation does not delete evidence.
- Ending the trip produces a summary.
- Simulated trips remain excluded from official analytics.
- The full pitch scenario runs predictably.
- The simulator works on the deployed server.
- The simulator works in the offline local environment.
- Physical hardware can later replace the simulator without redesigning the backend.