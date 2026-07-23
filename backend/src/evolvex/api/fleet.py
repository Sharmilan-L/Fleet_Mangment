"""
Fleet Management API Router.

Includes drivers, vehicles, devices, and device assignments endpoints
per docs/api-contract.md.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select

from evolvex.core.database import get_session_factory
from evolvex.db.models import (
    AssignmentStatus,
    Device,
    DeviceAdminStatus,
    DeviceAssignment,
    Driver,
    DriverStatus,
    Vehicle,
    VehicleStatus,
)

router = APIRouter(prefix="/api/v1", tags=["Fleet Management"])


@router.get("/drivers")
async def list_drivers(
    status_filter: Annotated[DriverStatus | None, Query(alias="status")] = None,
    search: str | None = None,
) -> JSONResponse:
    """List drivers in the organization."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(Driver)
        if status_filter:
            stmt = stmt.where(Driver.status == status_filter)
        if search:
            stmt = stmt.where(
                (Driver.first_name.ilike(f"%{search}%"))
                | (Driver.last_name.ilike(f"%{search}%"))
                | (Driver.employee_code.ilike(f"%{search}%"))
            )

        res = await session.execute(stmt)
        drivers = res.scalars().all()

        items: list[dict[str, Any]] = [
            {
                "id": str(d.id),
                "employeeCode": d.employee_code,
                "firstName": d.first_name,
                "lastName": d.last_name,
                "fullName": f"{d.first_name} {d.last_name}",
                "status": d.status,
                "licenseNumber": d.license_number,
                "phone": d.phone,
                "email": d.email,
            }
            for d in drivers
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": items},
        )


@router.get("/vehicles")
async def list_vehicles(
    status_filter: Annotated[VehicleStatus | None, Query(alias="status")] = None,
    search: str | None = None,
) -> JSONResponse:
    """List vehicles in the organization."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(Vehicle)
        if status_filter:
            stmt = stmt.where(Vehicle.status == status_filter)
        if search:
            stmt = stmt.where(
                (Vehicle.registration_number.ilike(f"%{search}%"))
                | (Vehicle.vehicle_code.ilike(f"%{search}%"))
                | (Vehicle.make.ilike(f"%{search}%"))
                | (Vehicle.model.ilike(f"%{search}%"))
            )

        res = await session.execute(stmt)
        vehicles = res.scalars().all()

        items: list[dict[str, Any]] = [
            {
                "id": str(v.id),
                "registrationNumber": v.registration_number,
                "vehicleCode": v.vehicle_code,
                "make": v.make,
                "model": v.model,
                "manufactureYear": v.manufacture_year,
                "status": v.status,
                "defaultSpeedLimitKmh": v.default_speed_limit_kmh,
            }
            for v in vehicles
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": items},
        )


@router.get("/devices")
async def list_devices(
    admin_status: Annotated[DeviceAdminStatus | None, Query(alias="administrativeStatus")] = None,
    search: str | None = None,
) -> JSONResponse:
    """List devices in the organization."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(Device)
        if admin_status:
            stmt = stmt.where(Device.administrative_status == admin_status)
        if search:
            stmt = stmt.where(
                (Device.device_code.ilike(f"%{search}%"))
                | (Device.display_name.ilike(f"%{search}%"))
            )

        res = await session.execute(stmt)
        devices = res.scalars().all()

        items: list[dict[str, Any]] = [
            {
                "id": str(d.id),
                "deviceCode": d.device_code,
                "displayName": d.display_name,
                "deviceType": d.device_type,
                "administrativeStatus": d.administrative_status,
                "firmwareVersion": d.firmware_version,
                "telemetrySchemaVersion": d.telemetry_schema_version,
            }
            for d in devices
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": items},
        )


@router.get("/device-assignments")
async def list_assignments(
    status_filter: Annotated[AssignmentStatus | None, Query(alias="status")] = None,
) -> JSONResponse:
    """List device assignments in the organization."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(DeviceAssignment)
        if status_filter:
            stmt = stmt.where(DeviceAssignment.status == status_filter)

        res = await session.execute(stmt)
        assignments = res.scalars().all()

        items: list[dict[str, Any]] = [
            {
                "id": str(a.id),
                "deviceId": str(a.device_id),
                "vehicleId": str(a.vehicle_id),
                "status": a.status,
                "assignedAt": a.assigned_at.isoformat() if a.assigned_at else None,
                "deviceCode": a.device.device_code if a.device else None,
                "vehicleRegistration": a.vehicle.registration_number if a.vehicle else None,
            }
            for a in assignments
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": items},
        )
