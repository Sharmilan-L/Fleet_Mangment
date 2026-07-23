import asyncio
from sqlalchemy import delete
from evolvex.core.database import get_session_factory, close_engine
from evolvex.db.models import (
    Trip,
    TelemetryRecord,
    DrivingEvent,
    TripScoreLedger,
    DeviceAssignment,
    Vehicle,
    Driver,
    User,
    Organization,
    RuleSetVersion,
    RuleSet,
    AccelerationRule,
    TurningRule,
    OverspeedRule,
    EventPenalty,
    RiskBand
)
from evolvex.db.seed import run_seed

async def clean_and_reseed():
    print("Starting database clean & re-seed process...")
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        # Delete dependent data first
        print("Clearing telemetry, events, ledger and trips...")
        await session.execute(delete(TelemetryRecord))
        await session.execute(delete(DrivingEvent))
        await session.execute(delete(TripScoreLedger))
        await session.execute(delete(Trip))
        await session.execute(delete(DeviceAssignment))
        
        # Delete non-seed vehicles
        print("Clearing non-seed vehicles...")
        await session.execute(delete(Vehicle).where(Vehicle.vehicle_code != "VEH-DEMO-001"))
        
        # Delete non-seed drivers
        print("Clearing non-seed drivers...")
        await session.execute(delete(Driver).where(Driver.employee_code != "DRV-DEMO-001"))
        
        # Commit deletion
        await session.commit()
        
    print("Database cleaned. Now running idempotent seed...")
    await run_seed()
    print("Database re-seeded successfully with clean demo records!")

if __name__ == "__main__":
    try:
        asyncio.run(clean_and_reseed())
    finally:
        asyncio.run(close_engine())
