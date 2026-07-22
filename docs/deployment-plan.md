# EvolveX Driver Behaviour Intelligence Platform

## Deployment Plan

**Document version:** 1.0  
**Project stage:** Pitching MVP  
**Application architecture:** Modular monolith  
**Frontend:** React and TypeScript  
**Backend:** FastAPI and Python  
**Database:** PostgreSQL  
**Local orchestration:** Docker Compose  
**Live communication:** WebSocket  

---

## 1. Purpose

This document defines how the EvolveX system will run in:

1. Local development
2. Automated testing
3. The deployed pitch environment
4. The offline pitch backup environment
5. A future production environment

It also defines:

- Database creation
- Database migrations
- Environment variables
- HTTPS and secure WebSocket configuration
- Application startup
- Health checks
- Logging
- Backups
- Restore procedures
- Demo reset procedures
- Deployment validation
- Pitch-day fallback arrangements

This document does not select a permanent production cloud provider.

The MVP must remain deployable on a normal Linux server or compatible container-hosting environment.

---

## 2. Deployment Environments

EvolveX requires three separate environments.

### 2.1 Local development

Used by team members while building and testing.

```text
Developer laptop
├── React frontend
├── FastAPI backend
├── PostgreSQL
├── Device-status worker
├── Simulator worker
└── Optional reverse proxy
```

Suggested local addresses:

```text
Frontend:   http://localhost:5173
Backend:    http://localhost:8000
API:        http://localhost:8000/api/v1
WebSocket:  ws://localhost:8000/ws
PostgreSQL: localhost:5432
```

Local data may be deleted and reseeded.

It must never be confused with pitch or future production data.

### 2.2 Pitch or staging environment

Used during the competition and final rehearsals.

```text
Internet browser
    ↓ HTTPS / WSS
Reverse proxy
    ├── React frontend
    ├── FastAPI backend
    ├── Device-status worker
    ├── Simulator worker
    └── PostgreSQL
```

This environment contains:

- Demo organization
- Demo administrator
- Demo fleet manager
- Demo driver
- Demo vehicle
- Simulator device
- Active simulator assignment
- Approved rule configuration
- Simulation scenarios
- Test trips only unless otherwise required

### 2.3 Offline pitch backup

Runs entirely on the team’s laptop.

```text
Pitch laptop
├── React frontend
├── FastAPI backend
├── PostgreSQL
├── Simulator worker
├── Device-status worker
└── Offline map or route fallback
```

This environment must support the full demonstration without cloud access.

---

## 3. Future Production Separation

A future production system must use:

- Separate database
- Separate secrets
- Separate device credentials
- Separate user accounts
- Separate storage
- Separate backups
- Separate domain names

The pitch database must never become the official production database.

```text
Development database
≠ Pitch database
≠ Production database
```

---

## 4. Local Docker Compose Services

The local Docker Compose configuration should include:

```text
postgres
api
device-status-worker
simulator-worker
frontend
```

An optional reverse-proxy service may be added later.

Conceptual structure:

```yaml
services:
  postgres:
    image: postgres

  api:
    build: ./backend
    depends_on:
      - postgres

  device-status-worker:
    build: ./backend
    depends_on:
      - postgres

  simulator-worker:
    build: ./backend
    depends_on:
      - postgres
      - api

  frontend:
    build: ./frontend
    depends_on:
      - api
```

The exact Compose file is created during implementation.

---

## 5. Database Creation

PostgreSQL tables must be created through Alembic migrations.

Correct process:

```text
Start PostgreSQL
    ↓
Create empty database
    ↓
Configure DATABASE_URL
    ↓
Run Alembic migrations
    ↓
Run seed script
    ↓
Start application services
```

Example commands:

```bash
uv run alembic upgrade head
uv run python scripts/seed_development.py
```

For the pitch environment:

```bash
uv run alembic upgrade head
uv run python scripts/seed_pitch_demo.py
```

Tables must not be manually recreated through a graphical database tool.

---

## 6. Migration Requirements

Every database change must have an Alembic migration.

Deployment must verify:

- Migration history is valid
- Required PostgreSQL extensions exist
- All tables exist
- Foreign keys exist
- Unique constraints exist
- Check constraints exist
- Required indexes exist
- Views exist
- Triggers or database functions exist where approved

The backend must not start in the pitch environment when required migrations are missing.

A migration check should compare the database revision with the application’s expected Alembic revision.

---

## 7. Seed Data

### 7.1 Development seed

May create:

- Development organization
- Administrator
- Fleet manager
- Drivers
- Vehicles
- Hardware-reference device
- Simulator device
- Rule sets
- Monitoring settings
- Simulation scenarios

### 7.2 Pitch seed

Must create predictable demonstration data:

```text
Organization: EvolveX Demo Fleet
Administrator: Demo Administrator
Manager: Demo Fleet Manager
Driver: Demo Driver
Vehicle: Demo Vehicle
Device: SIM-DEVICE-001
Trip mode: TEST
Rule version: Approved pitch rules
Scenario: FULL_PITCH_DEMO
```

Passwords and device keys must come from environment variables or be generated securely.

They must not be committed to Git.

---

## 8. Environment Variables

The project must provide `.env.example` files.

Actual `.env` files remain outside Git.

Backend variables may include:

```env
APP_ENV=development
APP_NAME=EvolveX
APP_HOST=0.0.0.0
APP_PORT=8000

DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/evolvex

AUTH_SECRET_KEY=replace-me
AUTH_COOKIE_NAME=evolvex_session
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax
SESSION_EXPIRE_MINUTES=60

FRONTEND_ORIGIN=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173

DEVICE_KEY_PEPPER=replace-me

SIMULATOR_DEVICE_CODE=SIM-DEVICE-001
SIMULATOR_DEVICE_KEY=replace-me
SIMULATOR_API_BASE_URL=http://api:8000/api/v1
SIMULATOR_DEFAULT_INTERVAL_MS=1000

LOG_LEVEL=INFO
```

Frontend variables may include:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WEBSOCKET_URL=ws://localhost:8000/ws
VITE_APP_NAME=EvolveX
```

Deployed values use HTTPS and WSS.

---

## 9. Secret Management

The system must not commit:

- Database passwords
- Authentication secrets
- Session tokens
- Device API keys
- Device key hashes
- Private certificates
- Cloud credentials
- Backup encryption keys

Secrets must be supplied through:

- Server environment variables
- Deployment-platform secret storage
- Protected environment files
- Approved secret-management service in future production

Logs must not print secrets.

---

## 10. Backend Container

The FastAPI backend container should:

1. Install locked Python dependencies.
2. Copy application code.
3. Run as a non-root user where practical.
4. Expose the backend port.
5. Start Uvicorn.
6. Support health checks.
7. Avoid embedding secrets inside the image.

Conceptual startup:

```bash
uv run uvicorn evolvex.main:app \
  --host 0.0.0.0 \
  --port 8000
```

The first MVP may use one backend process.

Multiple workers require careful WebSocket and background-task planning.

---

## 11. Frontend Build

The React frontend is built into static production files.

Conceptual process:

```text
Install locked dependencies
    ↓
Run TypeScript validation
    ↓
Run frontend tests
    ↓
Create production build
    ↓
Serve static files
```

The frontend must use environment-provided API and WebSocket URLs.

It must not contain database credentials or device secrets.

---

## 12. Background Workers

The pitch environment requires:

### Device-status worker

Responsible for:

- Detecting delayed devices
- Detecting offline devices
- Restoring online status
- Creating and resolving related alerts

### Simulator worker

Responsible for:

- Running simulation scenarios
- Sending telemetry through the real HTTP endpoint
- Managing pause, resume and stop state
- Recording failures

These workers should not be started separately in every API worker.

That could create duplicated jobs and alerts.

---

## 13. Reverse Proxy

The deployed environment should place a reverse proxy in front of the application.

Responsibilities:

- HTTPS termination
- Frontend delivery
- API routing
- WebSocket upgrade routing
- Request-size limits
- Security headers
- Optional rate limiting

Conceptual routes:

```text
/
→ React frontend

/api/
→ FastAPI backend

/ws
→ FastAPI WebSocket endpoint
```

The proxy must support WebSocket upgrade headers.

Otherwise, REST may work while live updates fail.

---

## 14. HTTPS and WSS

Local development may use:

```text
HTTP
WS
```

The pitch server must use:

```text
HTTPS
WSS
```

Conceptually:

```text
https://demo-domain
https://api-domain/api/v1
wss://api-domain/ws
```

Authentication cookies in the deployed environment should use:

```text
HttpOnly = true
Secure = true
SameSite = Lax or Strict
```

---

## 15. Cross-Origin Configuration

The backend must allow only configured frontend origins.

Local example:

```text
http://localhost:5173
```

Pitch example:

```text
https://demo-domain
```

CORS must allow credentials for authenticated REST requests.

WebSocket origin validation must also be applied separately.

Do not use unrestricted origins together with credentialed requests.

---

## 16. Startup Order

Recommended startup sequence:

```text
1. Start PostgreSQL.

2. Wait for database health.

3. Run Alembic migrations.

4. Run required seed process.

5. Start FastAPI.

6. Wait for API health.

7. Start device-status worker.

8. Start simulator worker.

9. Start frontend or reverse proxy.

10. Run deployment verification.
```

The simulator must not begin sending packets before:

- Backend is healthy
- Database is available
- Simulator device exists
- Device assignment exists
- A test trip is active
- Simulation run is started by an authorized user

---

## 17. Health Checks

Required endpoints:

```http
GET /health
GET /api/v1/health/database
```

The health system should verify:

### Backend health

- Process is running
- HTTP endpoint responds

### Database health

- Connection succeeds
- Basic query succeeds

Future checks may include:

- Migration revision
- Worker heartbeat
- Simulator worker status
- WebSocket service status

Health endpoints must not expose database hostnames, credentials or internal stack traces.

---

## 18. Readiness and Liveness

### Liveness

Answers:

> Is the backend process alive?

### Readiness

Answers:

> Is the backend ready to accept application traffic?

The backend may be alive but not ready when:

- Database is unavailable
- Migrations are missing
- Required configuration is invalid

The pitch deployment should not route traffic until readiness succeeds.

---

## 19. Logging

Application logs should use structured records.

Useful fields:

- Timestamp
- Environment
- Request ID
- User ID where available
- Organization ID
- Device ID
- Trip ID
- Simulation run ID
- Message type
- Error code
- Log level

Logs must not contain:

- Passwords
- Plain device API keys
- Authentication cookies
- Database passwords
- Full secret environment variables

Pitch logs should be retained long enough to debug rehearsal and demonstration issues.

---

## 20. Request Correlation

Each REST request should receive a request ID.

Related telemetry-processing records and logs should preserve that identifier where useful.

WebSocket messages may include:

```text
transactionId
messageId
```

This assists debugging:

```text
Telemetry request
    ↓
Database transaction
    ↓
Event and score
    ↓
WebSocket message
```

---

## 21. Error Handling

Deployment-level failures must have clear behaviour.

### Database unavailable

- API readiness fails
- Telemetry request returns retryable error
- No false successful processing response
- No official WebSocket update is sent

### Worker unavailable

- Main API may remain available
- Health monitoring reports degraded state
- Offline-device detection or simulation may pause
- Team is notified during rehearsal

### WebSocket unavailable

- REST remains available
- Frontend uses polling fallback
- Frontend shows connection status

### Simulator unavailable

- Hardware-independent demo cannot run
- Existing stored data remains safe
- Simulator is restarted without modifying official data

---

## 22. Database Backup

Before the competition, create a database backup.

Example:

```bash
pg_dump -Fc evolvex_demo > evolvex_demo.dump
```

The backup must contain:

- Approved rule configuration
- Demo users
- Demo driver
- Demo vehicle
- Simulator device
- Device assignment
- Simulation scenarios
- Required reference data

Plain secrets should not be included unnecessarily.

Backup files must not be committed to Git.

---

## 23. Database Restore

The team must test restoration before the pitch.

Conceptual process:

```text
Create clean database
    ↓
Restore backup
    ↓
Verify migration revision
    ↓
Start application
    ↓
Run health checks
    ↓
Run full simulation scenario
```

A backup is not considered reliable until restore has been tested.

---

## 24. Demo Reset

The pitch environment must be resettable.

A controlled reset may:

1. Stop the simulator.
2. End or clear active test runs.
3. Restore the clean pitch database or run a reset script.
4. Reapply migrations if needed.
5. Recreate seed data.
6. Start services.
7. Verify health.
8. Start a fresh test trip.
9. Run the scenario.

A reset must never be run against a future production database.

The reset script must check the environment name before destructive actions.

---

## 25. Deployment Scripts

Recommended files:

```text
deployment/
├── docker-compose.local.yml
├── docker-compose.pitch.yml
├── reverse-proxy.conf
├── deploy.sh
├── migrate.sh
├── seed_pitch.sh
├── backup_database.sh
├── restore_database.sh
├── reset_pitch_demo.sh
└── verify_deployment.sh
```

PowerShell equivalents may also be provided for Windows-based local use.

Scripts must stop immediately when a critical command fails.

---

## 26. Deployment Verification

After deployment, verify:

### Infrastructure

- Database container or service is healthy
- Backend is healthy
- Frontend loads
- Device-status worker runs
- Simulator worker runs
- Reverse proxy routes correctly

### Authentication

- Login works
- Logout works
- Unauthorized APIs reject access
- WebSocket authentication works

### Database

- Migration revision is current
- Seed data exists
- Active rule version exists
- Simulator assignment exists

### Telemetry

- Simulator authenticates
- Telemetry is stored
- Active trip is resolved
- Duplicate detection works

### Live system

- REST snapshot loads
- WebSocket connects through WSS
- Telemetry appears live
- Event appears
- Score changes
- Alert appears
- Device status updates

### Completion

- Trip ends
- Summary is created
- Test trip remains excluded from official analytics

---

## 27. Pitch Rehearsal

The full deployed demonstration must be rehearsed several times.

Rehearsal should confirm:

- Login credentials are available securely
- Demo database is clean
- Test trip starts
- Simulator starts
- Full scenario completes
- Events appear at predictable times
- Score and risk changes are understood
- Device disconnection appears
- Device reconnects
- Trip summary appears
- Team members know the explanation
- Reset works after the run

The pitch should not be the first complete deployed test.

---

## 28. Offline Map Fallback

Online map tiles may fail when internet access is unreliable.

The offline system must provide one of:

- Bundled static map image
- Cached route tiles
- Locally stored schematic route
- Coordinate-grid route display

The fallback must still show:

- Vehicle movement
- Route progress
- Event locations
- Last-known location

The core event and scoring demonstration must not depend on online maps.

---

## 29. Offline Pitch Procedure

Before the competition:

1. Install Docker or the approved local runtime.
2. Pull or build all required images.
3. Store dependencies locally.
4. Prepare the offline map fallback.
5. Restore or seed the demo database.
6. Start all services.
7. Disconnect internet.
8. Run the full scenario.
9. Confirm all essential features still work.

The team should carry:

- Source-code repository
- Locked dependency files
- Built container images where practical
- Database backup
- Environment template
- Offline reset instructions
- Demo credentials stored securely

---

## 30. Deployment Security Checklist

Before deployment:

- Replace default passwords.
- Generate strong application secrets.
- Generate simulator device credential.
- Enable HTTPS.
- Enable WSS.
- Enable secure cookies.
- Restrict CORS.
- Validate WebSocket origin.
- Restrict database network access.
- Disable debug mode.
- Hide stack traces.
- Configure rate limiting.
- Verify organization authorization.
- Confirm secrets are not in Git history.
- Confirm backup files are not public.
- Confirm health endpoints reveal no secrets.

---

## 31. Data Separation Checklist

Verify:

```text
Local data
≠ Pitch data
≠ Future production data
```

Pitch simulation uses:

```text
Simulator device
+
TEST trip
+
SIMULATOR telemetry source
```

Official analytics queries must continue excluding test trips after deployment.

The pitch database should contain synthetic or approved demo data only.

---

## 32. Deployment Monitoring

For the pitching MVP, lightweight monitoring is sufficient.

Monitor:

- API availability
- Database connectivity
- API error rate
- Telemetry-processing failures
- Worker availability
- Device last-seen time
- WebSocket connection failures
- Simulator failures
- Disk space
- Database backup success

A complex observability platform is not required initially.

---

## 33. Performance Expectations

The initial pitch deployment must support:

- One organization
- A small number of users
- One active simulated vehicle
- Approximately one telemetry packet per second
- One live dashboard
- Normal REST usage
- One simulator worker
- One device-status worker

The system does not initially require:

- Kubernetes
- Automatic horizontal scaling
- Distributed message brokers
- Multi-region deployment
- Thousands of devices
- Multiple database replicas

---

## 34. Future Scaling

Future growth may introduce:

- Managed PostgreSQL
- Database partitioning
- Redis for WebSocket distribution
- Task queue
- MQTT ingestion
- Multiple API instances
- Transactional outbox
- Object storage
- Monitoring platform
- Automated CI/CD deployment
- Database replicas

These are deferred until scale requires them.

---

## 35. Rollback Plan

A deployment rollback must be possible when a new version fails.

Possible rollback process:

```text
Stop new application version
    ↓
Start previous application version
    ↓
Verify database compatibility
    ↓
Run health checks
    ↓
Resume traffic
```

Database migrations must be reviewed before deployment.

Destructive migrations require:

- Backup
- Tested downgrade or forward-fix plan
- Maintenance decision
- Clear approval

The pitch deployment should avoid risky schema changes immediately before the competition.

---

## 36. Release Freeze

A release freeze should begin before the final pitch.

During the freeze:

- No architecture changes
- No unreviewed migrations
- No major dependency upgrades
- No new rule thresholds
- No new simulation scenarios
- No large frontend redesign

Only verified critical fixes should be accepted.

A final release tag should identify the pitch version.

Example:

```text
v0.1.0-pitch
```

---

## 37. Git and Release Requirements

Before a pitch release:

```text
Working tree clean
All required documents committed
Tests passing
Migration revision recorded
Environment templates current
Release notes prepared
Git tag created
```

Do not deploy directly from uncommitted local changes.

---

## 38. Deployment Phases

### Deployment Phase A — Local development

- Create Docker Compose
- Run PostgreSQL locally
- Run migrations
- Run seed
- Develop API and frontend

### Deployment Phase B — Local integration

- Run complete stack
- Test REST
- Test telemetry
- Test WebSocket
- Test workers
- Test simulator

### Deployment Phase C — Pitch server

- Create empty database
- Configure secrets
- Run migrations
- Seed demo data
- Deploy backend
- Deploy workers
- Deploy frontend
- Configure HTTPS and WSS

### Deployment Phase D — Deployed verification

- Run health checks
- Run full scenario
- Verify reset
- Verify backup
- Verify WebSocket recovery

### Deployment Phase E — Offline fallback

- Build local images
- Restore local demo database
- Test without internet
- Verify offline map
- Rehearse full flow

---

## 39. Actual Implementation Roadmap Position

Database creation begins during backend foundation:

```text
Phase 1
→ Local PostgreSQL service

Phase 2
→ Alembic migrations and seed data
```

Pitch-server deployment occurs only after the main system works locally:

```text
Backend
+
Database
+
Simulator
+
Rule engine
+
WebSocket
+
Frontend
+
Local end-to-end tests
        ↓
Pitch server deployment
```

This prevents the team from debugging basic application problems directly on the pitch server.

---

## 40. Deployment Restrictions

The implementation must not:

- Commit secrets to Git.
- Use the pitch database as future production.
- Manually recreate production tables.
- Skip Alembic migrations.
- Deploy before local integration tests pass.
- Use HTTP or plain WS for the public pitch environment.
- Expose PostgreSQL publicly without strong restrictions.
- Run duplicate workers unintentionally.
- Run destructive reset scripts without environment checks.
- Depend completely on venue internet.
- Depend completely on online map tiles.
- Publish WebSocket updates before database commit.
- Allow simulator data into official analytics.
- Return internal stack traces publicly.
- Deploy uncommitted changes.
- Introduce unnecessary Kubernetes or microservices for the MVP.

---

## 41. Deployment Acceptance Criteria

The deployment design is accepted when:

- Local PostgreSQL runs through Docker Compose.
- Alembic can create the complete schema.
- Development seed data can be created.
- Pitch seed data can be created.
- Secrets are supplied outside Git.
- Backend and database health checks work.
- The FastAPI container starts successfully.
- The React production build works.
- The device-status worker runs once.
- The simulator worker runs once.
- HTTPS works in the pitch environment.
- WSS works in the pitch environment.
- REST authentication cookies work securely.
- CORS and WebSocket origin rules are restricted.
- The simulator reaches the deployed telemetry endpoint.
- Raw telemetry is stored remotely.
- Events, scores and alerts appear through WebSocket.
- The full pitch scenario completes remotely.
- The trip summary is generated.
- Test data remains excluded from official analytics.
- A database backup can be created.
- The backup can be restored successfully.
- The pitch environment can be reset.
- The complete system can run locally without internet.
- An offline route or map fallback exists.
- Deployment verification can be repeated before the competition.