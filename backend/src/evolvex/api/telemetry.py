"""
Device Telemetry API endpoint router.

Implements POST /api/v1/device/telemetry per docs/api-contract.md §64.
"""

import hashlib
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from evolvex.core.database import get_session_factory
from evolvex.db.models import (
    AssignmentStatus,
    Device,
    DeviceAdminStatus,
    DeviceAssignment,
    TelemetryProcessingStatus,
    TelemetryRecord,
    TelemetrySource,
    Trip,
    TripStatus,
)

router = APIRouter(prefix="/api/v1/device", tags=["Device Telemetry"])


class TelemetryPacketRequest(BaseModel):
    """Telemetry packet version 1 payload."""

    boot_id: str = Field(..., description="Device boot instance identifier")
    sequence_number: int = Field(..., description="Monotonically increasing sequence number")
    timestamp: float | int | None = Field(None, description="Device timestamp")
    lat: float | None = Field(None, description="GPS latitude")
    lng: float | None = Field(None, description="GPS longitude")
    speed_kmh: float = Field(..., description="GPS speed in km/h")
    accel_fwd: float = Field(..., description="Forward acceleration in m/s^2")
    accel_lat: float = Field(..., description="Lateral acceleration in m/s^2")
    yaw_rate: float = Field(..., description="Yaw rate in deg/s")
    harsh_accel: bool | None = None
    harsh_brake: bool | None = None
    harsh_corner: bool | None = None
    overspeed: bool | None = None


def validate_sensor_ranges(body: TelemetryPacketRequest) -> list[dict[str, str]]:
    """Validate extreme sensor values to prevent garbage hardware telemetry."""
    details: list[dict[str, str]] = []

    if body.speed_kmh < 0.0 or body.speed_kmh > 250.0:
        details.append(
            {
                "field": "speed_kmh",
                "message": "The value exceeds the permitted range.",
            }
        )

    if body.accel_fwd < -20.0 or body.accel_fwd > 20.0:
        details.append(
            {
                "field": "accel_fwd",
                "message": "The value exceeds the permitted range.",
            }
        )

    if body.accel_lat < -20.0 or body.accel_lat > 20.0:
        details.append(
            {
                "field": "accel_lat",
                "message": "The value exceeds the permitted range.",
            }
        )

    if body.yaw_rate < -360.0 or body.yaw_rate > 360.0:
        details.append(
            {
                "field": "yaw_rate",
                "message": "The value exceeds the permitted range.",
            }
        )

    return details


@router.post("/telemetry")
async def submit_telemetry(
    body: TelemetryPacketRequest,
    request: Request,
    x_device_code: str | None = Header(None, alias="X-Device-Code"),
    x_device_key: str | None = Header(None, alias="X-Device-Key"),
    x_telemetry_schema_version: str | None = Header("1.0", alias="X-Telemetry-Schema-Version"),
) -> JSONResponse:
    """
    Submit hardware or simulator telemetry packet.
    """
    request_id = getattr(request.state, "request_id", "req_unknown")

    # 1. Header Validation
    if not x_device_code or not x_device_key:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "error": {
                    "code": "AUTHENTICATION_FAILED",
                    "message": "Missing X-Device-Code or X-Device-Key authentication headers.",
                },
                "meta": {"requestId": request_id, "timestamp": datetime.now(UTC).isoformat()},
            },
        )

    if x_telemetry_schema_version and x_telemetry_schema_version != "1.0":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": {
                    "code": "UNSUPPORTED_SCHEMA_VERSION",
                    "message": f"Schema version '{x_telemetry_schema_version}' is not supported.",
                },
                "meta": {"requestId": request_id, "timestamp": datetime.now(UTC).isoformat()},
            },
        )

    # 2. Sensor Range Validation (Requirement 7)
    validation_errors = validate_sensor_ranges(body)
    if validation_errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": {
                    "code": "TELEMETRY_VALIDATION_FAILED",
                    "message": "The telemetry packet contains invalid values.",
                    "details": validation_errors,
                },
                "meta": {"requestId": request_id, "timestamp": datetime.now(UTC).isoformat()},
            },
        )

    session_factory = get_session_factory()
    async with session_factory() as session:
        # 3. Authenticate Device
        stmt = select(Device).where(Device.device_code == x_device_code)
        result = await session.execute(stmt)
        device = result.scalar_one_or_none()

        if not device or device.administrative_status in (
            DeviceAdminStatus.DISABLED,
            DeviceAdminStatus.RETIRED,
        ):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "AUTHENTICATION_FAILED",
                        "message": "Invalid device credentials or device is disabled.",
                    },
                    "meta": {"requestId": request_id, "timestamp": datetime.now(UTC).isoformat()},
                },
            )

        # Check API Key Hash
        key_hash = hashlib.sha256(x_device_key.encode()).hexdigest()
        if (
            device.api_key_hash
            and device.api_key_hash != key_hash
            and device.api_key_hash != x_device_key
        ):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "AUTHENTICATION_FAILED",
                        "message": "Invalid device credentials.",
                    },
                    "meta": {"requestId": request_id, "timestamp": datetime.now(UTC).isoformat()},
                },
            )

        # 4. Duplicate Check (Requirement 3)
        dup_stmt = select(TelemetryRecord.id).where(
            TelemetryRecord.device_id == device.id,
            TelemetryRecord.boot_id == body.boot_id,
            TelemetryRecord.sequence_number == body.sequence_number,
        )
        dup_res = await session.execute(dup_stmt)
        existing_telemetry_id = dup_res.scalar_one_or_none()

        if existing_telemetry_id:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "data": {
                        "status": "DUPLICATE",
                        "processingStatus": "DUPLICATE",
                        "telemetryId": str(existing_telemetry_id),
                    },
                },
            )

        # 5. Resolve Active Assignment & Active/FINALIZING Trip
        asgn_stmt = select(DeviceAssignment).where(
            DeviceAssignment.device_id == device.id,
            DeviceAssignment.status == AssignmentStatus.ACTIVE,
        )
        asgn_res = await session.execute(asgn_stmt)
        active_assignment = asgn_res.scalar_one_or_none()

        active_trip: Trip | None = None
        if active_assignment:
            trip_stmt = select(Trip).where(
                Trip.device_assignment_id == active_assignment.id,
                Trip.status.in_([TripStatus.ACTIVE, TripStatus.FINALIZING]),
            )
            trip_res = await session.execute(trip_stmt)
            active_trip = trip_res.scalar_one_or_none()

        # 6. GPS Position Check
        is_gps_valid = (
            body.lat is not None
            and body.lng is not None
            and -90.0 <= body.lat <= 90.0
            and -180.0 <= body.lng <= 180.0
        )

        # Determine Telemetry Source Type
        source_type = (
            TelemetrySource.SIMULATOR
            if device.device_type == "SIMULATOR"
            else TelemetrySource.HARDWARE
        )

        # 7. Create Telemetry Record
        now_utc = datetime.now(UTC)
        if body.timestamp is not None:
            ts_val = body.timestamp / 1000.0 if body.timestamp > 1e11 else body.timestamp
            device_ts = datetime.fromtimestamp(ts_val, tz=UTC)
        else:
            device_ts = now_utc

        proc_status = (
            TelemetryProcessingStatus.PROCESSED
            if is_gps_valid
            else TelemetryProcessingStatus.PARTIAL
        )

        telemetry_rec = TelemetryRecord(
            organization_id=device.organization_id,
            device_id=device.id,
            device_assignment_id=active_assignment.id if active_assignment else None,
            trip_id=active_trip.id if active_trip else None,
            source_type=source_type,
            schema_version=x_telemetry_schema_version or "1.0",
            boot_id=body.boot_id,
            sequence_number=body.sequence_number,
            device_timestamp=device_ts,
            server_received_at=now_utc,
            latitude=body.lat if is_gps_valid else None,
            longitude=body.lng if is_gps_valid else None,
            gps_valid=is_gps_valid,
            sensor_valid=True,
            speed_kmh=body.speed_kmh,
            forward_acceleration_ms2=body.accel_fwd,
            lateral_acceleration_ms2=body.accel_lat,
            yaw_rate_deg_s=body.yaw_rate,
            processing_status=proc_status,
            raw_payload=body.model_dump(),
        )

        session.add(telemetry_rec)
        try:
            await session.flush()
            detected_events = []
            if active_trip:
                from evolvex.engine.rule_engine import RuleEngine

                rule_engine = RuleEngine(session)
                detected_events = await rule_engine.process_telemetry(
                    telemetry=telemetry_rec,
                    speed_limit_kmh=active_trip.applied_speed_limit_kmh,
                )
            await session.commit()
            await session.refresh(telemetry_rec)

            # WebSocket Broadcast (Post-Commit)
            if active_trip:
                from evolvex.core.websocket import manager as ws_manager

                trip_id_str = str(active_trip.id)
                # 1. Telemetry Snapshot
                await ws_manager.broadcast_to_trip(
                    trip_id_str,
                    "TELEMETRY_SNAPSHOT",
                    {
                        "speedKmh": telemetry_rec.speed_kmh,
                        "forwardAccelerationMs2": telemetry_rec.forward_acceleration_ms2,
                        "lateralAccelerationMs2": telemetry_rec.lateral_acceleration_ms2,
                        "yawRateDegS": telemetry_rec.yaw_rate_deg_s,
                        "latitude": telemetry_rec.latitude,
                        "longitude": telemetry_rec.longitude,
                        "gpsValid": telemetry_rec.gps_valid,
                        "sequenceNumber": telemetry_rec.sequence_number,
                        "serverReceivedAt": telemetry_rec.server_received_at.isoformat(),
                    },
                )

                # 2. Broadcast detected events
                for event in detected_events:
                    await ws_manager.broadcast_to_trip(
                        trip_id_str,
                        "EVENT_DETECTED",
                        {
                            "id": str(event.id),
                            "eventType": event.event_type.value,
                            "severity": event.severity.value,
                            "status": event.status.value,
                            "startedAt": event.started_at.isoformat() if event.started_at else now_utc.isoformat(),
                            "endedAt": event.ended_at.isoformat() if event.ended_at else None,
                            "durationMs": event.duration_ms,
                            "primaryMeasurement": event.primary_measurement,
                            "latitude": telemetry_rec.latitude,
                            "longitude": telemetry_rec.longitude,
                        }
                    )

                # 3. Broadcast updated safety score
                if detected_events:
                    from evolvex.db.models import TripScoreState
                    score_stmt = select(TripScoreState).where(TripScoreState.trip_id == active_trip.id)
                    score_res = await session.execute(score_stmt)
                    score_state = score_res.scalar_one_or_none()
                    if score_state:
                        await ws_manager.broadcast_to_trip(
                            trip_id_str,
                            "SCORE_UPDATED",
                            {
                                "newScore": score_state.current_score,
                                "currentRiskLevel": str(score_state.current_risk_level),
                            }
                        )
        except IntegrityError:
            await session.rollback()
            # Race condition duplicate check
            dup_res = await session.execute(dup_stmt)
            dup_id = dup_res.scalar_one_or_none()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "data": {
                        "status": "DUPLICATE",
                        "processingStatus": "DUPLICATE",
                        "telemetryId": str(dup_id) if dup_id else "duplicate",
                    },
                },
            )

        # 8. Build Response
        if is_gps_valid:
            resp_data: dict[str, Any] = {
                "status": "ACCEPTED",
                "processingStatus": "PROCESSED",
                "telemetryId": str(telemetry_rec.id),
                "serverReceivedAt": now_utc.isoformat(),
            }
            if active_trip:
                resp_data["tripId"] = str(active_trip.id)

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"success": True, "data": resp_data},
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "data": {
                        "status": "ACCEPTED",
                        "processingStatus": "PARTIAL",
                        "telemetryId": str(telemetry_rec.id),
                        "warnings": [
                            {
                                "code": "GPS_UNAVAILABLE",
                                "message": (
                                    "Sensor telemetry was accepted without a valid GPS position."
                                ),
                            }
                        ],
                    },
                },
            )
