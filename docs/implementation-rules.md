# EvolveX Driver Behaviour Intelligence Platform

## Implementation Rules

**Document version:** 1.0  
**Project stage:** Pitching MVP  
**Purpose:** Control AI-assisted implementation  
**Primary coding environment:** Antigravity  
**Implementation style:** Small reviewed phases  

---

## 1. Purpose

This document defines mandatory implementation rules for the EvolveX MVP.

It controls how developers and AI coding tools must:

- Read approved requirements
- Generate code
- Modify files
- Design modules
- Create database migrations
- Implement APIs
- Implement telemetry processing
- Implement WebSocket communication
- Implement simulation
- Write tests
- Handle secrets
- Commit changes
- Report completed work

This document prevents uncontrolled code generation and architectural drift.

---

## 2. Approved Source Documents

Before implementing any feature, the developer or AI tool must read the relevant approved documents.

The approved documents are:

```text
docs/product-requirements.md
docs/system-architecture.md
docs/database-design.md
docs/api-contract.md
docs/websocket-contract.md
docs/simulation-requirements.md
docs/deployment-plan.md
docs/implementation-rules.md
```

These documents are the project source of truth.

Implementation must not contradict them.

When two documents appear inconsistent:

1. Stop implementation.
2. Identify the contradiction.
3. Explain the affected sections.
4. Ask for a decision.
5. Update the approved document first.
6. Continue implementation only after approval.

The AI tool must not silently choose one interpretation.

---

## 3. Implementation Order

Implementation must follow the approved roadmap.

```text
Phase 0  → Documentation
Phase 1  → Backend and local PostgreSQL foundation
Phase 2  → Database migrations and seed data
Phase 3  → Authentication and authorization
Phase 4  → Driver, vehicle, device and assignment management
Phase 5  → Trip lifecycle
Phase 6  → Telemetry ingestion
Phase 7  → Simulator
Phase 8  → Driving-rule engine
Phase 9  → Patterns, scoring and risk
Phase 10 → Alerts and device-status worker
Phase 11 → WebSocket realtime communication
Phase 12 → Trip finalization and analytics
Phase 13 → React application foundation
Phase 14 → Live trip dashboard
Phase 15 → Completed trip and driver profile pages
Phase 16 → Complete testing
Phase 17 → Physical hardware integration
Phase 18 → Pitch deployment and offline backup
```

A later phase must not be implemented before its required earlier foundation exists.

Example:

```text
Do not implement the live dashboard
before the REST snapshot and WebSocket contracts exist in code.
```

---

## 4. One Task at a Time

Each implementation request must focus on one small deliverable.

Good task:

```text
Create the backend Python project foundation with FastAPI,
configuration loading and a health endpoint.
```

Bad task:

```text
Build the complete backend, database, simulator and frontend.
```

A task should normally modify only the files required for that task.

The AI tool must not create unrelated modules merely because they may be needed later.

---

## 5. Required Workflow for Every Task

Each coding task follows this workflow:

```text
1. Read relevant approved documents.

2. Inspect the existing repository.

3. Explain the intended change.

4. List files that will be created or modified.

5. Identify assumptions and risks.

6. Generate or modify code.

7. Run formatting and static checks.

8. Run relevant tests.

9. Report exact results.

10. Show Git diff summary.

11. Wait for review before beginning another major task.
```

The AI tool must not claim success without running the required checks.

---

## 6. Repository Inspection

Before editing code, inspect:

- Current directory structure
- Existing files
- Git status
- Existing dependencies
- Existing configuration
- Existing tests
- Relevant migrations
- Relevant approved documents

The tool must avoid creating duplicate files because it failed to inspect the repository.

Example:

```text
Do not create config_new.py
when config.py already exists and should be extended.
```

---

## 7. Git Working Tree Rule

Before beginning a new implementation task, check:

```bash
git status
```

The preferred state is:

```text
nothing to commit, working tree clean
```

When unrelated uncommitted changes exist:

- Do not overwrite them.
- Do not discard them.
- Report them.
- Limit changes to the approved task.

The AI tool must never run destructive commands such as:

```bash
git reset --hard
git clean -fd
```

unless the user explicitly approves the exact command and consequence.

---

## 8. Git Commit Rules

Each completed logical task should have one clear commit.

Examples:

```text
Initialize FastAPI backend foundation
Add initial PostgreSQL migration
Implement user authentication
Add driver management endpoints
Implement telemetry ingestion validation
```

Do not combine unrelated work into one commit.

Before committing:

```text
Formatting passes
Static checks pass
Tests pass
Git diff reviewed
Secrets not present
```

The AI tool must not rewrite Git history unless explicitly instructed.

---

## 9. No Unapproved Architecture Changes

The implementation must remain a modular monolith.

Do not introduce:

- Microservices
- Kubernetes
- Kafka
- RabbitMQ
- Redis
- MQTT
- Distributed task queues
- Multiple databases
- Separate analytics services

unless an approved later requirement explicitly needs them.

The pitching MVP uses:

- One React frontend
- One FastAPI backend application
- One PostgreSQL database
- One device-status worker
- One simulator worker

---

## 10. Backend Project Structure

The backend should follow a clear modular structure.

Recommended structure:

```text
backend/
├── pyproject.toml
├── alembic.ini
├── .env.example
├── src/
│   └── evolvex/
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── logging.py
│       │   ├── security.py
│       │   ├── exceptions.py
│       │   └── middleware.py
│       ├── db/
│       │   ├── base.py
│       │   ├── session.py
│       │   └── models/
│       ├── modules/
│       │   ├── auth/
│       │   ├── users/
│       │   ├── drivers/
│       │   ├── vehicles/
│       │   ├── devices/
│       │   ├── assignments/
│       │   ├── trips/
│       │   ├── telemetry/
│       │   ├── events/
│       │   ├── patterns/
│       │   ├── scoring/
│       │   ├── alerts/
│       │   ├── realtime/
│       │   ├── simulation/
│       │   └── analytics/
│       └── workers/
├── migrations/
├── scripts/
└── tests/
```

Only create modules when their implementation phase begins.

Do not create empty placeholder folders for every future module unless required by the current task.

---

## 11. Backend Layering

Standard business modules should use:

```text
Router
    ↓
Service
    ↓
Repository
    ↓
Database
```

### Router responsibility

- HTTP paths
- Authentication dependencies
- Request schemas
- Response schemas
- Status codes

### Service responsibility

- Business rules
- Authorization decisions
- Workflow coordination
- Transaction boundaries

### Repository responsibility

- SQLAlchemy queries
- Inserts and updates
- Row locking
- Database-specific operations

Routers must not contain substantial business logic.

Repositories must not decide business policy.

---

## 12. Python Coding Rules

Backend code should use:

- Type hints
- Async functions where database or network operations are asynchronous
- Clear names
- Small functions
- Explicit error handling
- Pydantic request and response models
- SQLAlchemy typed models
- Dependency injection through FastAPI
- Structured logging

Avoid:

- Global mutable application state
- Unexplained magic numbers
- Broad `except Exception` without logging and controlled handling
- Blocking network calls inside async endpoints
- Hidden side effects
- Circular imports
- Very large service files

---

## 13. Dependency Rules

Add a dependency only when the current task requires it.

Before adding a dependency:

1. Explain its purpose.
2. Confirm that an existing dependency cannot provide the feature.
3. Add it to the approved dependency file.
4. Update the lock file.
5. Run tests.

Do not add multiple libraries that perform the same responsibility.

Examples:

```text
Use one validation framework.
Use one ORM.
Use one password-hashing approach.
Use one frontend query approach.
```

---

## 14. Configuration Rules

Configuration must come from environment variables or controlled defaults.

Required principles:

- Development-safe defaults may exist.
- Secrets must never have committed real defaults.
- Configuration loading must fail clearly for missing required production values.
- Boolean and numeric settings must be validated.
- Environment-specific behaviour must be explicit.

Do not use environment checks scattered throughout the application.

Centralize configuration.

---

## 15. Secret Protection

Never commit:

- Database passwords
- Authentication secret keys
- Plain device API keys
- Session tokens
- Cloud credentials
- Private certificates
- Backup encryption keys

Before each commit, inspect:

```bash
git diff --cached
```

The repository must contain:

```text
.env.example
```

It must not contain:

```text
.env
```

Real secrets must not be printed in terminal output, tests or logs.

---

## 16. Database Access Rules

Only the FastAPI backend and approved workers may connect to PostgreSQL.

Prohibited:

```text
React → PostgreSQL
ESP32 → PostgreSQL
Simulator → PostgreSQL
```

Required:

```text
React → FastAPI → PostgreSQL
ESP32 → Telemetry API → PostgreSQL
Simulator → Telemetry API → PostgreSQL
```

The simulator may access its own run-control state through approved backend or worker architecture, but it must not insert telemetry-derived results directly.

---

## 17. Database Model Rules

Database models must follow the approved database design.

Each model should define:

- Primary key
- Foreign keys
- Nullability
- Unique constraints
- Check constraints
- Indexes
- Created and updated timestamps where required
- Enum handling
- Relationship loading strategy

Do not add a column only because it may be useful later.

Do not remove an approved field without document review.

---

## 18. Migration Rules

Every schema change requires an Alembic migration.

For each migration:

1. Review generated operations manually.
2. Confirm foreign keys.
3. Confirm index names.
4. Confirm unique constraints.
5. Confirm check constraints.
6. Confirm downgrade behaviour.
7. Run migration against an empty database.
8. Run migration against the current development database.
9. Run tests.

The AI tool must not trust Alembic autogeneration without review.

Migration filenames and revision messages must describe the change.

---

## 19. Database Constraint Rules

Critical business uniqueness must be enforced in PostgreSQL.

Examples:

- One active device assignment per vehicle
- One active assignment per device
- One active trip per driver
- One active trip per device assignment
- One telemetry packet per device, boot and sequence identity
- One active penalty per event
- One active penalty per pattern

Application validation alone is not sufficient.

Services should still validate first to provide understandable errors.

---

## 20. Database Transaction Rules

Related official changes must use a controlled transaction.

Telemetry transaction example:

```text
Store telemetry
    ↓
Update latest state
    ↓
Update event state
    ↓
Create or update event
    ↓
Create pattern
    ↓
Create score ledger entry
    ↓
Update score and risk
    ↓
Create alert
    ↓
Commit
```

Only after commit:

```text
Publish WebSocket messages
```

The implementation must not publish official state before commit.

---

## 21. Append-Only Evidence Rules

The following records should not be destructively edited during normal operation:

- Raw telemetry
- Score-ledger history
- Risk-transition history
- Audit records
- Historical device assignments
- Historical rule versions

Corrections use:

- Void status
- Reversal entry
- New version
- Controlled administrative adjustment

Do not delete evidence to make a test pass.

---

## 22. REST API Rules

REST endpoints must follow:

```text
docs/api-contract.md
```

Requirements:

- `/api/v1` prefix
- Camel-case JSON fields
- UUID identifiers
- UTC ISO 8601 timestamps
- Standard success envelope
- Standard error envelope
- Documented status codes
- Pydantic validation
- Organization authorization
- Bounded pagination
- Idempotency where specified

Do not invent a new path without checking the API contract.

---

## 23. API Response Rules

Response schemas must not expose:

- Password hashes
- Device API-key hashes
- Session hashes
- Database details
- Internal exceptions
- Secret environment variables

Do not return raw SQLAlchemy objects directly.

Convert data through approved response schemas.

---

## 24. Authentication Rules

Human authentication and device authentication remain separate.

### Human authentication

Uses:

- Email and password
- Secure password hashing
- Server-recognized session or approved token method
- HTTP-only cookie
- Role authorization
- Organization scope

### Device authentication

Uses:

- Device code
- Device API key
- Schema version
- Administrative-status validation

A device must never authenticate as a human user.

A human-user cookie must never be used as a device credential.

---

## 25. Authorization Rules

Every organization-owned query must enforce organization scope.

Bad:

```python
trip = get_trip(trip_id)
```

Required concept:

```python
trip = get_trip_for_organization(
    trip_id=trip_id,
    organization_id=current_user.organization_id,
)
```

The backend must not trust organization IDs sent by the frontend.

Authorization checks must occur in services or reusable dependencies, not only in UI visibility.

---

## 26. Telemetry Ingestion Rules

All physical, simulated and replay telemetry must enter through:

```http
POST /api/v1/device/telemetry
```

The ingestion pipeline must execute:

```text
Device authentication
    ↓
Schema adapter
    ↓
Validation
    ↓
Duplicate detection
    ↓
Context resolution
    ↓
Raw telemetry storage
    ↓
Rule processing
    ↓
Pattern processing
    ↓
Scoring
    ↓
Alerts
    ↓
Commit
    ↓
WebSocket publication
```

Do not create an alternative simulator-only ingestion path.

---

## 27. Telemetry Adapter Rules

Rule engines must consume a standardized internal telemetry model.

Firmware-specific field names must be handled by adapters.

Example:

```text
accel_fwd
→ forward_acceleration_ms2
```

Do not spread firmware field names throughout rule-engine services.

Each supported telemetry schema version must have:

- Explicit adapter
- Validation tests
- Mapping tests
- Unsupported-version error

---

## 28. Duplicate Telemetry Rules

Telemetry packet identity uses:

```text
device
+
boot identifier
+
sequence number
```

A retry of the same packet must not create:

- Duplicate telemetry
- Duplicate event
- Duplicate pattern
- Duplicate score penalty
- Duplicate alert

Duplicate handling must be tested under concurrent requests.

---

## 29. Missing and Invalid Telemetry

Missing GPS may produce partial telemetry.

Example:

```text
Valid speed and IMU
Missing GPS
```

Possible behaviour:

- Store telemetry
- Mark GPS invalid
- Continue allowed sensor processing
- Use last-known map location
- Reduce data-quality confidence

Invalid extreme values must not affect official calculations.

Validation behaviour must be explicit and tested.

---

## 30. Rule-Engine Rules

The MVP rule engine supports only:

- Harsh braking
- Sudden acceleration
- Overspeeding
- Sharp turning

Rules must come from the trip’s rule-set version.

Do not hard-code permanent thresholds directly inside detector code.

Detector state must support:

- Normal
- Candidate
- Active
- Cooldown

One continuous occurrence must create one event.

---

## 31. Event Explainability Rules

Each official event must store:

- Event type
- Start and end time
- Duration
- Severity
- Applied threshold
- Rule version
- Relevant measurements
- Evidence telemetry
- Source
- Status

The frontend must be able to show why the event was created.

Hardware flags remain supporting observations only.

---

## 32. Pattern Rules

Patterns must use confirmed backend events.

Supported MVP patterns:

- Repeated same behaviour
- Mixed aggressive behaviour

The simulator must not create a pattern directly.

The frontend must not infer an official pattern.

Pattern creation must be idempotent.

---

## 33. Score Rules

Each trip begins with:

```text
100
```

Every score change requires a ledger entry.

The current score must be reproducible from the ledger.

The implementation must not:

- Store only the final score
- Change a score without a ledger entry
- Reapply the same event penalty
- Let React calculate penalties
- Delete a penalty to reverse it

Corrections use reversal entries.

---

## 34. Risk Rules

Risk comes from configured score bands.

Initial suggested bands:

```text
80–100 → LOW
60–79  → MEDIUM
0–59   → HIGH
```

These are configuration, not hard-coded frontend logic.

Risk means behavioural risk level.

It must not be described as accident probability.

---

## 35. Alert Rules

Alerts require:

- Type
- Priority
- Status
- Source
- Deduplication key
- Organization context
- Trip context where applicable
- Lifecycle timestamps

A continuing condition must not create a new alert every processing cycle.

Alert wording must not claim:

- Accident detected
- Accident predicted
- Medical fatigue diagnosis

unless a future approved feature provides verified evidence.

---

## 36. WebSocket Rules

WebSocket implementation must follow:

```text
docs/websocket-contract.md
```

Required principles:

- Human-session authentication
- Origin validation
- Organization authorization
- Trip subscription validation
- Consistent message envelopes
- Message IDs
- Stream IDs
- Sequence numbers
- Heartbeats
- Reconnection support
- REST snapshot recovery
- Publication only after database commit

WebSocket is not used for physical telemetry upload.

---

## 37. WebSocket Connection Manager

The MVP may use one in-memory connection manager because the backend initially runs as one instance.

It must support:

- Connections by user
- Connections by organization
- Trip subscriptions
- Fleet subscriptions
- Unsubscribe
- Heartbeat
- Cleanup after disconnection

Do not add Redis merely for future scaling.

The limitation of one backend instance must be documented.

---

## 38. Frontend Rules

The frontend uses React and TypeScript.

Frontend responsibilities:

- Display data
- Submit actions
- Load REST snapshots
- Subscribe to WebSocket messages
- Display errors
- Display connection state
- Display test-data labels
- Render charts and route information

The frontend must not calculate official:

- Events
- Severity
- Patterns
- Scores
- Risk
- Alerts
- Driver performance

---

## 39. Frontend State Rules

Live trip state begins from:

```http
GET /api/v1/trips/{tripId}/live
```

Then WebSocket applies incremental updates.

After:

- Sequence gap
- New stream ID
- Reconnection
- Browser resume
- Server restart

the frontend reloads the REST snapshot.

The browser must not be the only location holding important trip state.

---

## 40. Frontend Component Rules

Components should remain focused.

Suggested separation:

```text
Page
├── Page-level data loading
├── Live state controller
├── Score card
├── Risk card
├── Telemetry cards
├── Chart components
├── Map component
├── Event timeline
├── Alert panel
└── Simulation controls
```

Do not place all live-page logic into one giant component.

Do not open separate WebSocket connections from each component.

---

## 41. Simulation Rules

Simulation implementation must follow:

```text
docs/simulation-requirements.md
```

The simulator:

- Uses a simulator device
- Uses a test trip
- Uses device authentication
- Sends the real telemetry payload
- Calls the real telemetry endpoint
- Produces deterministic scenarios
- Uses increasing sequence numbers
- Uses believable routes
- Records simulation-run state

The simulator must not force expected outcomes.

---

## 42. Official and Test Data Rules

The primary official-versus-test decision is:

```text
trip_mode
```

Official analytics queries must require:

```text
trip_mode = OFFICIAL
status = COMPLETED
eligible data quality
not excluded by review
```

Do not rely only on telemetry source.

A test trip may contain hardware telemetry and must still remain excluded from official analytics.

---

## 43. Worker Rules

Background workers must be separate from repeated API worker startup.

Required MVP workers:

- Device-status worker
- Simulator worker

Workers must use:

- Database locking or ownership
- Idempotent operations
- Structured logs
- Graceful shutdown
- Bounded retry
- Clear failure status

Do not run the same scheduler independently inside every Uvicorn worker.

---

## 44. Logging Rules

Logs should use structured fields.

Recommended fields:

- Timestamp
- Log level
- Request ID
- Organization ID
- User ID
- Device ID
- Trip ID
- Telemetry ID
- Event ID
- Simulation run ID
- Error code

Logs must not contain:

- Passwords
- Cookies
- Plain API keys
- Database passwords
- Complete secret values

Use exception logging internally while returning safe API errors.

---

## 45. Error Handling Rules

Errors should be classified as:

- Validation error
- Authentication error
- Authorization error
- Business conflict
- Not found
- Temporary dependency failure
- Unexpected internal failure

API responses must use documented error codes.

Do not expose Python tracebacks to clients.

Do not convert all errors into `500`.

---

## 46. Testing Rules

Every implemented module requires appropriate tests.

Testing layers:

```text
Unit tests
Integration tests
API tests
Database constraint tests
End-to-end tests
```

The tool must run the tests related to the changed code.

A feature is not complete merely because the application starts.

---

## 47. Unit Test Rules

Unit tests should cover:

- Pure business rules
- Validation
- Detector state transitions
- Severity calculation
- Pattern logic
- Score calculation
- Risk calculation
- Scenario generation
- Mapping and adapters

Unit tests should avoid unnecessary database access.

---

## 48. Integration Test Rules

Integration tests should use PostgreSQL where PostgreSQL-specific behaviour matters.

Do not replace every database test with SQLite when testing:

- Partial indexes
- JSONB
- PostgreSQL enums
- Row locking
- Concurrent constraints
- PostgreSQL-specific queries

Integration tests must use an isolated test database.

---

## 49. API Test Rules

API tests should verify:

- Success response
- Validation failure
- Authentication failure
- Authorization failure
- Organization isolation
- Not found
- Conflict
- Idempotency
- Safe response fields

Tests should verify both status code and response body.

---

## 50. Telemetry Test Rules

Telemetry tests must cover:

- Valid packet
- Missing GPS
- Invalid coordinate
- Invalid speed
- Unsupported schema
- Wrong device key
- Disabled device
- Duplicate packet
- No active trip
- Active official trip
- Active test trip
- Processing failure
- Retry behaviour

---

## 51. Rule and Score Test Rules

Tests must verify:

- Normal driving creates no false event
- Harsh braking creates one event
- Sudden acceleration creates one event
- Continuous overspeed creates one event
- Sharp turning creates one event
- Release and cooldown work
- Pattern uses confirmed events
- Event penalty is applied once
- Pattern penalty is applied once
- Ledger reproduces current score
- Risk transition is correct
- Voiding creates reversal behaviour

---

## 52. WebSocket Test Rules

Tests must cover:

- Valid connection
- Missing session
- Invalid origin
- Unauthorized trip
- Subscription confirmation
- Sequence ordering
- Duplicate messages
- Sequence gap recovery
- Stream restart recovery
- Commit-before-publish
- Device offline update
- Trip completion update

---

## 53. Simulation Test Rules

Tests must verify:

- Fixed seed is deterministic
- Scenario validation
- Gradual GPS route
- Packet interval
- Sequence identity
- Pause
- Resume
- Stop
- Retry
- Connection loss
- Reconnection
- Full pitch scenario
- Test-data exclusion from official analytics

---

## 54. Formatting and Static Checks

Backend checks should include:

```bash
uv run ruff check .
uv run ruff format --check .
```

When type checking is configured:

```bash
uv run mypy src
```

Frontend checks should include:

```bash
npm run lint
npm run typecheck
npm run build
```

Use the actual package-manager scripts defined in the repository.

Do not claim checks passed without running them.

---

## 55. Test Result Reporting

After implementation, report:

```text
Command executed
Exit result
Number of tests passed
Number of tests failed
Any warnings
```

Bad report:

```text
Everything should work.
```

Required report:

```text
uv run pytest tests/unit/test_health.py
1 test passed
```

When a check fails, report the failure honestly.

---

## 56. No Fake Implementation

Do not satisfy acceptance criteria with:

- Hard-coded API responses
- Direct frontend mock events
- Direct score insertion
- Static fake WebSocket data
- Simulator-created event rows
- Disabled authentication
- Catch-all success responses
- Tests that do not assert behaviour

Temporary mocks may be used only when explicitly approved and clearly marked.

---

## 57. No Silent Scope Expansion

Do not add unrequested features such as:

- Accident prediction
- Driver fatigue diagnosis
- Fuel consumption calculation
- Exact fuel-waste estimation
- Machine-learning models
- Mobile application
- Public driver portal
- Complex map routing service
- Multi-region infrastructure

The MVP must remain focused on the approved pitch scope.

---

## 58. AI and Machine-Learning Claims

The MVP is:

```text
Rule-based and AI-ready
```

It is not:

```text
Machine-learning powered
```

unless a real approved ML component is later implemented and validated.

Code, comments, UI text and documentation must not falsely claim current ML use.

---

## 59. Accident and Safety Wording

Approved language:

- Unsafe-driving event
- Aggressive-driving pattern
- Behavioural risk
- Device offline
- High-impact event requiring verification

Prohibited unsupported language:

- Accident predicted
- Accident detected
- Crash confirmed
- Driver medically fatigued
- Collision probability

Device communication loss is not evidence of an accident.

---

## 60. Documentation Updates

When implementation reveals a necessary contract change:

1. Stop coding.
2. Identify the document affected.
3. Propose the exact change.
4. Review the effect on other documents.
5. Update and approve documentation.
6. Commit the documentation change.
7. Resume implementation.

Code must not silently become the new source of truth.

---

## 61. Comment Rules

Comments should explain:

- Why a decision exists
- Why a constraint is important
- Why behaviour is not obvious
- Why a workaround is required

Avoid comments that merely repeat code.

Bad:

```python
# Increment sequence
sequence += 1
```

Useful:

```python
# Preserve the same packet identity across retries so the backend
# can safely detect a response-loss retransmission as a duplicate.
```

---

## 62. Naming Rules

Use domain names consistently.

Approved examples:

```text
trip
driver
vehicle
device
device assignment
telemetry
driving event
behaviour pattern
score ledger
risk level
alert
simulation run
```

Avoid inconsistent alternatives such as:

```text
journey
operator
car sensor
incident score
danger probability
```

unless the approved documents are updated.

---

## 63. Date and Time Rules

Store and exchange official timestamps in UTC.

Use timezone-aware datetime values.

Do not use naive local datetime values for:

- Telemetry arrival
- Trip start
- Event time
- Alert time
- Audit time
- Simulation run time

The frontend converts UTC for display.

---

## 64. Numeric Unit Rules

Internal and API units must remain explicit.

Examples:

```text
Speed → km/h
Acceleration → m/s²
Yaw rate → degrees/second
Duration → milliseconds or seconds as documented
Distance → kilometres
```

Field names should include the unit where ambiguity is possible.

Do not mix metres per second with kilometres per hour silently.

---

## 65. Data-Quality Rules

Data-quality failures must be stored and visible.

They must not automatically become driving penalties.

Examples:

```text
Missing GPS
Duplicate packet
Telemetry gap
Invalid sensor value
```

These affect:

- Confidence
- Diagnostics
- Analytics eligibility

They do not automatically prove unsafe driving.

---

## 66. Performance Rules

The MVP target is:

- One active simulator
- Approximately one packet per second
- One live dashboard
- Small fleet dataset

Optimize obvious query paths with approved indexes.

Do not prematurely introduce distributed infrastructure.

Avoid obvious performance mistakes such as:

- Loading unlimited telemetry
- Querying one row at a time inside large loops
- Sending full route history in every WebSocket message
- Recalculating all historical driver analytics for every packet

---

## 67. Deployment Rules

Do not deploy the pitch environment until:

- Local database migrations work
- Backend tests pass
- Telemetry integration works
- Simulator works
- Rule engine works
- WebSocket works
- Frontend works
- Full local end-to-end scenario passes

Deployment follows:

```text
docs/deployment-plan.md
```

The offline pitch environment must also be tested before the competition.

---

## 68. Antigravity Change Report

After each task, Antigravity should report:

```text
1. Summary of work completed
2. Files created
3. Files modified
4. Commands executed
5. Test results
6. Formatting and static-check results
7. Git status
8. Remaining limitations
9. Recommended next task
```

It must not hide failed commands.

---

## 69. Antigravity Pre-Implementation Response

Before editing code, Antigravity should return:

```text
Relevant documents read
Current repository state
Planned files
Implementation approach
Assumptions
Risks
```

Then implementation may proceed.

For destructive or architecture-changing actions, explicit approval is required first.

---

## 70. Prohibited Antigravity Actions

Antigravity must not:

- Generate the entire application in one operation
- Rewrite approved documents without permission
- Change architecture silently
- Add unnecessary frameworks
- Create duplicate modules
- Store secrets in code
- Delete user files
- Discard Git changes
- Reset Git history
- Skip tests and claim success
- Modify activated rule history destructively
- Create simulator-only event logic
- Calculate official frontend scores
- Publish WebSocket messages before commit
- Mix test data into official analytics
- Claim ML implementation when none exists
- Claim accident prediction
- Deploy external resources without explicit approval

---

## 71. Definition of Done

A coding task is complete only when:

- The approved requirement is implemented.
- The implementation follows architecture.
- Required files are present.
- Database migrations are reviewed where applicable.
- Formatting passes.
- Static checks pass.
- Relevant tests pass.
- No secrets are present.
- API contracts remain consistent.
- Git diff is reviewed.
- Remaining limitations are documented.
- The user approves moving to the next task.

---

## 72. Phase Gate Rule

At the end of each implementation phase:

1. Run the complete relevant test suite.
2. Review architecture alignment.
3. Review database changes.
4. Review API contract alignment.
5. Review security.
6. Review official-versus-test separation.
7. Commit the phase.
8. Tag only important stable milestones.
9. Begin the next phase only after approval.

---

## 73. Initial Implementation Prompt Template

Use this structure when asking Antigravity to implement a task:

```text
Read these documents completely:
- docs/implementation-rules.md
- [list relevant approved documents]

Inspect the current repository and Git status.

Task:
[one exact implementation task]

Before modifying files, report:
1. Relevant requirements
2. Existing files inspected
3. Files you plan to create or modify
4. Implementation approach
5. Assumptions and risks

Then implement only the requested task.

After implementation:
1. Run formatting
2. Run static checks
3. Run relevant tests
4. Show Git diff summary
5. Report any failures honestly
6. Do not commit unless explicitly instructed
7. Do not start another task
```

---

## 74. First Coding Task Boundary

The first implementation task after Phase 0 is limited to:

```text
Backend foundation
+
Local PostgreSQL foundation
```

It may include:

- Python project configuration
- FastAPI application creation
- Central settings
- Basic logging
- Database connection foundation
- Health endpoint
- Local PostgreSQL Docker Compose service
- Initial backend tests

It must not yet include:

- Complete database schema
- Authentication
- Driver CRUD
- Vehicle CRUD
- Telemetry ingestion
- Simulator
- Rule engine
- WebSocket
- React dashboard

Those belong to later tasks.

---

## 75. Implementation Acceptance Criteria

These implementation rules are accepted when:

- Approved documents remain the source of truth.
- Coding occurs one reviewed task at a time.
- Repository inspection occurs before changes.
- Git changes are protected.
- Architecture changes require approval.
- Backend modules follow router-service-repository separation.
- Database changes use reviewed migrations.
- Critical integrity is enforced by database constraints.
- Official updates commit before WebSocket publication.
- Human and device authentication remain separate.
- Organization authorization is enforced.
- All telemetry uses one ingestion pipeline.
- Hardware and simulation share backend processing.
- Simulator data remains test data.
- Frontend does not calculate official results.
- Every score change has a ledger entry.
- Unsupported ML and accident claims are prohibited.
- Relevant tests and checks run before completion.
- Failures are reported honestly.
- Secrets are never committed.
- Deployment occurs only after successful local integration.