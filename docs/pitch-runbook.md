# EvolveX MVP Pitch Runbook and Walkthrough

This document contains instructions, setup procedures, and verification details for running and demonstrating the EvolveX MVP Driver Behaviour Platform.

## 1. Setup and Startup Guide

### Prerequisites
- **Python**: 3.12+ (managed with `uv`)
- **Node.js**: 18+ (with `npm`)
- **Docker**: For running PostgreSQL development database

### A. Database Setup
Ensure that the PostgreSQL Docker container is running on port `5433`:
```bash
docker compose -f deployment/docker-compose.local.yml up -d
```
Verify container status:
```bash
docker compose -f deployment/docker-compose.local.yml ps
```

### B. Backend Setup
1. Navigate to `backend/`
2. Sync dependencies:
   ```bash
   uv sync
   ```
3. Run Alembic migrations:
   ```bash
   uv run alembic upgrade head
   ```
4. Run the seed data process:
   ```bash
   uv run python -m evolvex.db.seed
   ```
5. Start the FastAPI local server:
   ```bash
   uv run uvicorn evolvex.main:app --reload --host 127.0.0.1 --port 8000
   ```

### C. Frontend Setup
1. Navigate to `frontend/`
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to `http://localhost:3000`.

---

## 2. Walkthrough and Pitch Demonstration Flow

To showcase the platform's capabilities during a pitch, follow this flow:

1. **Access the Dashboard**: Open `http://localhost:3000`. The browser shows a sleek dark mode dashboard displaying real-time telemetry metrics, a driver safety score gauge, and an empty event timeline.
2. **Start a TEST Trip**: In the Trip Setup card on the left column, choose "John Doe" and "EV-2026-SL", then click **Start Trip**. This will create an active test trip session.
3. **Execute Telemetry Simulator**: In the Scenario Simulator card, select a scenario (e.g. `PITCH_DEMO_REPLAY` or `HARSH_BRAKING_EVENT`) and click **Start Scenario**.
4. **Watch Live Telemetry and WebSocket Stream**:
   - The live coordinates, speed, forward/lateral acceleration, and yaw rate metrics will update in real-time.
   - Any detected aggressive behaviors (e.g. Harsh Braking, Overspeeding) will be streamed via WebSocket, adding cards dynamically to the event timeline.
   - The Driver Safety Score will dynamically decrease based on the severity of the events, with color-coded risk bands (Green, Yellow, Red).
5. **Complete/End the Trip**: Click **End Trip** to finalize the test trip session and retrieve a completed summary analysis.

---

## 3. Reference and Troubleshooting

### Ports Mapping
- **FastAPI API Server**: `http://localhost:8000`
- **React Frontend**: `http://localhost:3000`
- **PostgreSQL Database**: `127.0.0.1:5433`

### Common Issues
- **401 Unauthorized Telemetry Ingestion**: Ensure the simulated hardware client uses the correct device code `SIM-DEVICE-001` and header `X-Device-Key` matches the environment configured key.
- **Multiple active trips error**: End any existing active trips for the vehicle or driver first using the API or by restarting the database seed.
