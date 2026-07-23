# EvolveX Backend Service

The backend component of the EvolveX Driver Behaviour Intelligence Platform built with FastAPI and Python 3.12.

## Prerequisites

- **Python 3.12**
- **uv** package manager
- **Docker Desktop** (for local PostgreSQL 16 database)

## Local Development Setup (PowerShell)

### 1. Launch Local PostgreSQL Service

```powershell
docker compose -f ../deployment/docker-compose.local.yml up -d
docker compose -f ../deployment/docker-compose.local.yml ps
```

### 2. Install Dependencies with uv

```powershell
Push-Location backend
uv sync
```

### 3. Run Database Migration Commands (Alembic)

```powershell
# Check current migration revision
uv run alembic current

# Check revision heads
uv run alembic heads
```

### 4. Run FastAPI Application

```powershell
uv run uvicorn evolvex.main:app --reload --port 8000
```

- **Process Liveness:** `http://localhost:8000/health`
- **Database Readiness:** `http://localhost:8000/api/v1/health/database`

### 5. Run Unit Tests (Fast, No Docker Required)

```powershell
uv run pytest tests/unit
```

### 6. Run Real PostgreSQL Integration Test

```powershell
uv run pytest -m integration
```

### 7. Run Formatting and Linting Checks

```powershell
uv run ruff check .
uv run ruff format --check .
```
