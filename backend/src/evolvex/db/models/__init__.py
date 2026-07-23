"""
EvolveX SQLAlchemy ORM models.

All domain models must be imported here so that ``Base.metadata`` is populated
before Alembic autogenerate inspects it.
"""

from evolvex.db.models.assignment import AssignmentStatus, DeviceAssignment
from evolvex.db.models.device import Device, DeviceAdminStatus, DeviceType
from evolvex.db.models.driver import Driver, DriverStatus
from evolvex.db.models.events import (
    DetectorStateEnum,
    DrivingEvent,
    EventDetectionState,
    EventSeverity,
    EventSource,
    EventStatus,
    EventTelemetryLink,
    EventType,
    EvidenceRole,
)
from evolvex.db.models.organization import Organization, OrganizationStatus
from evolvex.db.models.rules import (
    AccelerationRule,
    EventPenalty,
    EventSeverityBand,
    OverspeedRule,
    RiskBand,
    RuleSet,
    RuleSetVersion,
    RuleSetVersionStatus,
    TurningRule,
)
from evolvex.db.models.scores import (
    LedgerEntryType,
    RiskLevel,
    TripRiskHistory,
    TripScoreLedger,
    TripScoreState,
)
from evolvex.db.models.telemetry import TelemetryProcessingStatus, TelemetryRecord, TelemetrySource
from evolvex.db.models.trip import Trip, TripMode, TripStatus
from evolvex.db.models.user import User, UserRole, UserStatus
from evolvex.db.models.vehicle import Vehicle, VehicleStatus

__all__ = [
    "AccelerationRule",
    "AssignmentStatus",
    "DetectorStateEnum",
    "Device",
    "DeviceAdminStatus",
    "DeviceAssignment",
    "DeviceType",
    "Driver",
    "DriverStatus",
    "DrivingEvent",
    "EventDetectionState",
    "EventPenalty",
    "EventSeverity",
    "EventSeverityBand",
    "EventSource",
    "EventStatus",
    "EventTelemetryLink",
    "EventType",
    "EvidenceRole",
    "LedgerEntryType",
    "Organization",
    "OrganizationStatus",
    "OverspeedRule",
    "RiskBand",
    "RiskLevel",
    "RuleSet",
    "RuleSetVersion",
    "RuleSetVersionStatus",
    "TelemetryProcessingStatus",
    "TelemetryRecord",
    "TelemetrySource",
    "Trip",
    "TripMode",
    "TripRiskHistory",
    "TripScoreLedger",
    "TripScoreState",
    "TripStatus",
    "TurningRule",
    "User",
    "UserRole",
    "UserStatus",
    "Vehicle",
    "VehicleStatus",
]
