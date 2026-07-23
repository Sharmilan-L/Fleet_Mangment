"""
Trip Management API Router.

Includes trip lifecycle management (start, get active, live snapshot, end, summary,
events, score history) per docs/api-contract.md.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from evolvex.core.database import get_session_factory
from evolvex.db.models import (
    AssignmentStatus,
    DeviceAdminStatus,
    DeviceAssignment,
    Driver,
    DriverStatus,
    DrivingEvent,
    RuleSetVersion,
    RuleSetVersionStatus,
    TelemetryRecord,
    Trip,
    TripMode,
    TripScoreLedger,
    TripStatus,
    Vehicle,
    VehicleStatus,
)

router = APIRouter(prefix="/api/v1/trips", tags=["Trip Management"])


class StartTripRequest(BaseModel):
    """Request payload for starting a trip."""

    driver_id: uuid.UUID = Field(..., alias="driverId")
    vehicle_id: uuid.UUID = Field(..., alias="vehicleId")
    trip_mode: TripMode = Field(default=TripMode.OFFICIAL, alias="tripMode")
    applied_speed_limit_kmh: float = Field(default=60.0, alias="appliedSpeedLimitKmh")
    start_reason: str | None = Field(default="Pitch demo", alias="startReason")


class EndTripRequest(BaseModel):
    """Request payload for ending a trip."""

    end_reason: str | None = Field(default="Trip completed", alias="endReason")


@router.get("/start-options")
async def get_start_options() -> JSONResponse:
    """Return available drivers, vehicles, assignments, and rule versions for starting a trip."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Active drivers
        dr_stmt = select(Driver).where(Driver.status == DriverStatus.ACTIVE)
        dr_res = await session.execute(dr_stmt)
        drivers = dr_res.scalars().all()

        # Active vehicles with active device assignment
        asgn_stmt = select(DeviceAssignment).where(
            DeviceAssignment.status == AssignmentStatus.ACTIVE
        )
        asgn_res = await session.execute(asgn_stmt)
        assignments = asgn_res.scalars().all()

        v_ids = [a.vehicle_id for a in assignments]
        vh_stmt = select(Vehicle).where(
            Vehicle.id.in_(v_ids), Vehicle.status == VehicleStatus.ACTIVE
        )
        vh_res = await session.execute(vh_stmt)
        vehicles = vh_res.scalars().all()

        # Active rule set version
        rv_stmt = select(RuleSetVersion).where(RuleSetVersion.status == RuleSetVersionStatus.ACTIVE)
        rv_res = await session.execute(rv_stmt)
        active_rv = rv_res.scalars().first()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "drivers": [
                        {
                            "id": str(d.id),
                            "name": f"{d.first_name} {d.last_name}",
                            "employeeCode": d.employee_code,
                        }
                        for d in drivers
                    ],
                    "vehicles": [
                        {
                            "id": str(v.id),
                            "registrationNumber": v.registration_number,
                            "speedLimit": v.default_speed_limit_kmh,
                        }
                        for v in vehicles
                    ],
                    "tripModes": ["OFFICIAL", "TEST"],
                    "activeRuleVersion": (
                        {
                            "id": str(active_rv.id),
                            "versionNumber": active_rv.version_number,
                        }
                        if active_rv
                        else None
                    ),
                },
            },
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def start_trip(payload: StartTripRequest) -> JSONResponse:
    """Start a new driving trip session with full domain validation."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        # 1. Validate Driver
        driver = await session.get(Driver, payload.driver_id)
        if not driver or driver.status != DriverStatus.ACTIVE:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "code": "DRIVER_NOT_ACTIVE",
                        "message": "Selected driver is not active.",
                    },
                },
            )

        # Check existing active trip for driver
        dr_trip_stmt = select(Trip).where(
            Trip.driver_id == payload.driver_id,
            Trip.status.in_([TripStatus.ACTIVE, TripStatus.FINALIZING]),
        )
        if (await session.execute(dr_trip_stmt)).scalar_one_or_none():
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "success": False,
                    "error": {
                        "code": "DRIVER_ALREADY_ON_ACTIVE_TRIP",
                        "message": "Driver is already on an active trip.",
                    },
                },
            )

        # 2. Validate Vehicle
        vehicle = await session.get(Vehicle, payload.vehicle_id)
        if not vehicle or vehicle.status != VehicleStatus.ACTIVE:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "code": "VEHICLE_NOT_ACTIVE",
                        "message": "Selected vehicle is not active.",
                    },
                },
            )

        # 3. Validate Device Assignment
        asgn_stmt = (
            select(DeviceAssignment)
            .options(selectinload(DeviceAssignment.device))
            .where(
                DeviceAssignment.vehicle_id == payload.vehicle_id,
                DeviceAssignment.status == AssignmentStatus.ACTIVE,
            )
        )
        assignment = (await session.execute(asgn_stmt)).scalar_one_or_none()
        if not assignment:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "code": "VEHICLE_HAS_NO_ACTIVE_DEVICE",
                        "message": "Vehicle has no active device assignment.",
                    },
                },
            )

        # Validate Device Eligibility
        if assignment.device.administrative_status in (
            DeviceAdminStatus.DISABLED,
            DeviceAdminStatus.RETIRED,
        ):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "code": "DEVICE_NOT_AVAILABLE",
                        "message": "Assigned device is disabled or retired.",
                    },
                },
            )

        # Check existing active trip for device assignment
        asgn_trip_stmt = select(Trip).where(
            Trip.device_assignment_id == assignment.id,
            Trip.status.in_([TripStatus.ACTIVE, TripStatus.FINALIZING]),
        )
        if (await session.execute(asgn_trip_stmt)).scalar_one_or_none():
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "success": False,
                    "error": {
                        "code": "DEVICE_ASSIGNMENT_ALREADY_ON_ACTIVE_TRIP",
                        "message": "Device assignment is already on an active trip.",
                    },
                },
            )

        # 4. Resolve Active Rule Set Version
        rv_stmt = select(RuleSetVersion).where(RuleSetVersion.status == RuleSetVersionStatus.ACTIVE)
        active_rv = (await session.execute(rv_stmt)).scalars().first()

        # Create Trip
        now_utc = datetime.now(UTC)
        trip_code = f"TRIP-{now_utc.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        trip = Trip(
            organization_id=driver.organization_id,
            trip_code=trip_code,
            driver_id=driver.id,
            device_assignment_id=assignment.id,
            rule_set_version_id=active_rv.id if active_rv else None,
            trip_mode=payload.trip_mode,
            status=TripStatus.ACTIVE,
            start_time=now_utc,
            applied_speed_limit_kmh=payload.applied_speed_limit_kmh,
            start_reason=payload.start_reason,
        )
        session.add(trip)
        await session.flush()

        # Initialize Score State & Initial Ledger Entry
        from evolvex.engine.rule_engine import RuleEngine

        rule_engine = RuleEngine(session)
        score_state = await rule_engine.initialize_trip_score_if_needed(trip.id)

        await session.commit()
        await session.refresh(trip)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "data": {
                    "id": str(trip.id),
                    "tripCode": trip.trip_code,
                    "status": trip.status,
                    "tripMode": trip.trip_mode,
                    "driver": {
                        "id": str(driver.id),
                        "name": f"{driver.first_name} {driver.last_name}",
                    },
                    "vehicle": {
                        "id": str(vehicle.id),
                        "registrationNumber": vehicle.registration_number,
                    },
                    "device": {
                        "id": str(assignment.device_id),
                        "deviceCode": assignment.device.device_code,
                    },
                    "startTime": trip.start_time.isoformat(),
                    "currentScore": score_state.current_score,
                    "riskLevel": score_state.current_risk_level,
                    "ruleSetVersionId": (
                        str(trip.rule_set_version_id) if trip.rule_set_version_id else None
                    ),
                },
            },
        )


@router.get("/active")
async def list_active_trips() -> JSONResponse:
    """List current active or finalizing trips."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = (
            select(Trip)
            .options(
                selectinload(Trip.driver),
                selectinload(Trip.device_assignment).selectinload(DeviceAssignment.vehicle),
                selectinload(Trip.device_assignment).selectinload(DeviceAssignment.device),
                selectinload(Trip.score_state),
            )
            .where(Trip.status.in_([TripStatus.ACTIVE, TripStatus.FINALIZING]))
        )
        res = await session.execute(stmt)
        trips = res.scalars().all()

        items: list[dict[str, Any]] = []
        for t in trips:
            score = t.score_state[0].current_score if t.score_state else 100.0
            risk = t.score_state[0].current_risk_level if t.score_state else "LOW"
            d_name = f"{t.driver.first_name} {t.driver.last_name}" if t.driver else "Unknown"
            v_reg = (
                t.device_assignment.vehicle.registration_number
                if t.device_assignment and t.device_assignment.vehicle
                else "Unknown"
            )
            dev_code = (
                t.device_assignment.device.device_code
                if t.device_assignment and t.device_assignment.device
                else "Unknown"
            )
            items.append(
                {
                    "id": str(t.id),
                    "tripCode": t.trip_code,
                    "status": t.status,
                    "tripMode": t.trip_mode,
                    "driverName": d_name,
                    "vehicleRegistration": v_reg,
                    "deviceCode": dev_code,
                    "startTime": t.start_time.isoformat(),
                    "currentScore": score,
                    "riskLevel": risk,
                }
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": items},
        )


@router.get("/{trip_id}")
async def get_trip_detail(trip_id: uuid.UUID) -> JSONResponse:
    """Get single trip details."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = (
            select(Trip)
            .options(
                selectinload(Trip.driver),
                selectinload(Trip.device_assignment).selectinload(DeviceAssignment.vehicle),
                selectinload(Trip.device_assignment).selectinload(DeviceAssignment.device),
                selectinload(Trip.score_state),
            )
            .where(Trip.id == trip_id)
        )
        res = await session.execute(stmt)
        trip = res.scalar_one_or_none()
        if not trip:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "error": {"code": "TRIP_NOT_FOUND", "message": "Trip not found."},
                },
            )

        score = trip.score_state[0].current_score if trip.score_state else 100.0
        risk = trip.score_state[0].current_risk_level if trip.score_state else "LOW"

        driver_info = (
            {"id": str(trip.driver_id), "name": f"{trip.driver.first_name} {trip.driver.last_name}"}
            if trip.driver
            else None
        )
        vehicle_info = (
            {
                "id": str(trip.device_assignment.vehicle_id),
                "registration": trip.device_assignment.vehicle.registration_number,
            }
            if trip.device_assignment and trip.device_assignment.vehicle
            else None
        )
        device_info = (
            {
                "id": str(trip.device_assignment.device_id),
                "code": trip.device_assignment.device.device_code,
            }
            if trip.device_assignment and trip.device_assignment.device
            else None
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "id": str(trip.id),
                    "tripCode": trip.trip_code,
                    "status": trip.status,
                    "tripMode": trip.trip_mode,
                    "startTime": trip.start_time.isoformat(),
                    "endTime": trip.end_time.isoformat() if trip.end_time else None,
                    "appliedSpeedLimitKmh": trip.applied_speed_limit_kmh,
                    "driver": driver_info,
                    "vehicle": vehicle_info,
                    "device": device_info,
                    "currentScore": score,
                    "riskLevel": risk,
                },
            },
        )


@router.get("/{trip_id}/live")
async def get_live_trip_snapshot(trip_id: uuid.UUID) -> JSONResponse:
    """Get complete live snapshot of an active trip for frontend restoration."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = (
            select(Trip)
            .options(
                selectinload(Trip.driver),
                selectinload(Trip.device_assignment).selectinload(DeviceAssignment.vehicle),
                selectinload(Trip.device_assignment).selectinload(DeviceAssignment.device),
                selectinload(Trip.score_state),
            )
            .where(Trip.id == trip_id)
        )
        res = await session.execute(stmt)
        trip = res.scalar_one_or_none()
        if not trip:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "error": {"code": "TRIP_NOT_FOUND", "message": "Trip not found."},
                },
            )

        # Get latest telemetry
        tel_stmt = (
            select(TelemetryRecord)
            .where(TelemetryRecord.trip_id == trip_id)
            .order_by(desc(TelemetryRecord.sequence_number))
            .limit(1)
        )
        tel_res = await session.execute(tel_stmt)
        latest_tel = tel_res.scalar_one_or_none()

        # Get events
        ev_stmt = (
            select(DrivingEvent)
            .where(DrivingEvent.trip_id == trip_id)
            .order_by(desc(DrivingEvent.started_at))
        )
        ev_res = await session.execute(ev_stmt)
        events = ev_res.scalars().all()

        score = trip.score_state[0].current_score if trip.score_state else 100.0
        risk = trip.score_state[0].current_risk_level if trip.score_state else "LOW"

        latest_tel_data = {
            "speedKmh": latest_tel.speed_kmh if latest_tel else 0.0,
            "forwardAccelerationMs2": latest_tel.forward_acceleration_ms2 if latest_tel else 0.0,
            "lateralAccelerationMs2": latest_tel.lateral_acceleration_ms2 if latest_tel else 0.0,
            "yawRateDegS": latest_tel.yaw_rate_deg_s if latest_tel else 0.0,
            "latitude": latest_tel.latitude if latest_tel else None,
            "longitude": latest_tel.longitude if latest_tel else None,
            "gpsValid": latest_tel.gps_valid if latest_tel else False,
            "sequenceNumber": latest_tel.sequence_number if latest_tel else 0,
            "serverReceivedAt": latest_tel.server_received_at.isoformat() if latest_tel else None,
        }

        event_items = [
            {
                "id": str(e.id),
                "eventType": e.event_type,
                "severity": e.severity,
                "status": e.status,
                "startedAt": e.started_at.isoformat(),
                "endedAt": e.ended_at.isoformat() if e.ended_at else None,
                "primaryMeasurement": e.primary_measurement,
            }
            for e in events
        ]

        driver_data = (
            {"id": str(trip.driver_id), "name": f"{trip.driver.first_name} {trip.driver.last_name}"}
            if trip.driver
            else {}
        )
        vehicle_data = (
            {
                "id": str(trip.device_assignment.vehicle_id),
                "registrationNumber": trip.device_assignment.vehicle.registration_number,
            }
            if trip.device_assignment and trip.device_assignment.vehicle
            else {}
        )
        device_data = (
            {
                "id": str(trip.device_assignment.device_id),
                "deviceCode": trip.device_assignment.device.device_code,
                "deviceType": trip.device_assignment.device.device_type,
                "connectionStatus": "ONLINE" if latest_tel else "UNKNOWN",
            }
            if trip.device_assignment and trip.device_assignment.device
            else {}
        )
        tel_src = (
            trip.device_assignment.device.device_type
            if trip.device_assignment and trip.device_assignment.device
            else "HARDWARE"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "trip": {
                        "id": str(trip.id),
                        "tripCode": trip.trip_code,
                        "status": trip.status,
                        "tripMode": trip.trip_mode,
                        "startTime": trip.start_time.isoformat(),
                    },
                    "driver": driver_data,
                    "vehicle": vehicle_data,
                    "device": device_data,
                    "telemetrySource": tel_src,
                    "latestTelemetry": latest_tel_data,
                    "score": {"currentScore": score, "riskLevel": risk},
                    "events": event_items,
                    "eventCount": len(events),
                },
            },
        )


@router.post("/{trip_id}/end")
async def end_trip(trip_id: uuid.UUID, payload: EndTripRequest) -> JSONResponse:
    """Complete an active trip session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        trip = await session.get(Trip, trip_id)
        if not trip:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "error": {"code": "TRIP_NOT_FOUND", "message": "Trip not found."},
                },
            )

        if trip.status not in (TripStatus.ACTIVE, TripStatus.FINALIZING):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {"code": "TRIP_NOT_ACTIVE", "message": "Trip is not active."},
                },
            )

        now_utc = datetime.now(UTC)
        trip.status = TripStatus.COMPLETED
        trip.end_time = now_utc
        trip.end_reason = payload.end_reason

        await session.commit()
        await session.refresh(trip)

        from evolvex.core.websocket import manager as ws_manager

        await ws_manager.broadcast_to_trip(
            str(trip.id),
            "TRIP_STATUS_CHANGED",
            {
                "status": trip.status,
                "endTime": trip.end_time.isoformat(),
                "endReason": trip.end_reason,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "tripId": str(trip.id),
                    "status": trip.status,
                    "endTime": trip.end_time.isoformat(),
                    "summaryAvailable": True,
                },
            },
        )


@router.get("/{trip_id}/summary")
async def get_completed_trip_summary(trip_id: uuid.UUID) -> JSONResponse:
    """Get completed trip summary and performance statistics."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(Trip).options(selectinload(Trip.score_state)).where(Trip.id == trip_id)
        res = await session.execute(stmt)
        trip = res.scalar_one_or_none()
        if not trip:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "error": {"code": "TRIP_NOT_FOUND", "message": "Trip not found."},
                },
            )

        # Get telemetry count and speed stats
        tel_stmt = select(TelemetryRecord).where(TelemetryRecord.trip_id == trip_id)
        tel_res = await session.execute(tel_stmt)
        telemetry_records = tel_res.scalars().all()

        duration_seconds = (
            int((trip.end_time - trip.start_time).total_seconds()) if trip.end_time else 0
        )
        speeds = [t.speed_kmh for t in telemetry_records if t.speed_kmh is not None]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
        max_speed = max(speeds) if speeds else 0.0

        # Get events
        ev_stmt = select(DrivingEvent).where(DrivingEvent.trip_id == trip_id)
        ev_res = await session.execute(ev_stmt)
        events = ev_res.scalars().all()

        score = trip.score_state[0].current_score if trip.score_state else 100.0
        risk = trip.score_state[0].current_risk_level if trip.score_state else "LOW"

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "tripId": str(trip.id),
                    "tripCode": trip.trip_code,
                    "status": trip.status,
                    "tripMode": trip.trip_mode,
                    "startTime": trip.start_time.isoformat(),
                    "endTime": trip.end_time.isoformat() if trip.end_time else None,
                    "durationSeconds": duration_seconds,
                    "totalPackets": len(telemetry_records),
                    "averageSpeedKmh": round(avg_speed, 1),
                    "maximumSpeedKmh": round(max_speed, 1),
                    "totalEvents": len(events),
                    "finalScore": score,
                    "finalRiskLevel": risk,
                    "officialAnalyticsEligible": trip.trip_mode == TripMode.OFFICIAL,
                },
            },
        )


@router.get("/{trip_id}/events")
async def list_trip_events(trip_id: uuid.UUID) -> JSONResponse:
    """List confirmed driving events for a trip."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = (
            select(DrivingEvent)
            .where(DrivingEvent.trip_id == trip_id)
            .order_by(DrivingEvent.started_at)
        )
        res = await session.execute(stmt)
        events = res.scalars().all()

        items = [
            {
                "id": str(e.id),
                "eventType": e.event_type,
                "status": e.status,
                "severity": e.severity,
                "startedAt": e.started_at.isoformat(),
                "endedAt": e.ended_at.isoformat() if e.ended_at else None,
                "durationMs": e.duration_ms,
                "primaryMeasurement": e.primary_measurement,
                "thresholdValue": e.threshold_value,
            }
            for e in events
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": items},
        )


@router.get("/{trip_id}/score-history")
async def get_trip_score_history(trip_id: uuid.UUID) -> JSONResponse:
    """Get complete score ledger timeline for explainability."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = (
            select(TripScoreLedger)
            .where(TripScoreLedger.trip_id == trip_id)
            .order_by(TripScoreLedger.created_at)
        )
        res = await session.execute(stmt)
        entries = res.scalars().all()

        items = [
            {
                "id": str(e.id),
                "entryType": e.entry_type,
                "sourceEventId": str(e.source_event_id) if e.source_event_id else None,
                "previousScore": e.previous_score,
                "pointsDelta": e.points_delta,
                "newScore": e.new_score,
                "reason": e.reason,
                "createdAt": e.created_at.isoformat(),
            }
            for e in entries
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": items},
        )
