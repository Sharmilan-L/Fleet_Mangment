# EvolveX Driver Behaviour Intelligence Platform

EvolveX is an AI-ready, rule-based driver behaviour intelligence platform designed for fleet safety monitoring.

The MVP receives GPS and motion telemetry from either:

- A physical ESP32-based IoT device
- A controlled virtual-device simulator

Both sources use the same telemetry API and backend-processing pipeline.

## MVP Behaviour Detection

The system detects:

- Harsh braking
- Sudden acceleration
- Overspeeding
- Sharp turning
- Repeated aggressive-driving patterns

## System Outputs

The backend produces:

- Driving events
- Event severity
- Trip safety scores
- Risk levels
- Manager alerts
- Trip summaries
- Driver behaviour analytics

## Technology Stack

- Frontend: React and TypeScript
- Backend: Python and FastAPI
- Database: PostgreSQL
- Live updates: WebSocket
- Database migrations: Alembic
- Local environment: Docker Compose

## Quick Start — Local Development

Refer to [backend/README.md](file:///e:/Fleet_Manage/Fleet_Management/evolvex-mvp/backend/README.md) for detailed PowerShell setup steps.

```powershell
# 1. Start local PostgreSQL 16 container
docker compose -f deployment/docker-compose.local.yml up -d

# 2. Enter backend and sync dependencies
Push-Location backend
uv sync

# 3. Run FastAPI application
uv run uvicorn evolvex.main:app --reload --port 8000
```