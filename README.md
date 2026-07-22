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

## Project Structure

- `docs/` — Approved requirements and architecture
- `backend/` — FastAPI backend
- `frontend/` — React dashboard
- `hardware-reference/` — Existing hardware code
- `deployment/` — Server and deployment configuration

## Important MVP Scope

The current MVP is rule-based and AI-ready.

It does not claim:

- Accident prediction
- Medical fatigue detection
- Exact fuel-consumption measurement
- Machine-learning-based decisions