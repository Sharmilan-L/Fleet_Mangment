"""
Unit and integration tests for EvolveX seed database script.
"""

import pytest

from evolvex.db.seed import run_seed


@pytest.mark.asyncio
async def test_run_seed_idempotent() -> None:
    """Verify run_seed creates demo data and is fully idempotent."""
    res1 = await run_seed()
    assert res1["admin_email"] == "admin@evolvex.demo"
    assert res1["manager_email"] == "manager@evolvex.demo"
    assert res1["device_code"] == "SIM-DEVICE-001"

    # Re-running must not raise errors
    res2 = await run_seed()
    assert res2["organization_id"] == res1["organization_id"]
    assert res2["driver_id"] == res1["driver_id"]
    assert res2["vehicle_id"] == res1["vehicle_id"]
