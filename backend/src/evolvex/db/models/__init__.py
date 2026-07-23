"""
EvolveX SQLAlchemy ORM models.

All domain models must be imported here so that ``Base.metadata`` is populated
before Alembic autogenerate inspects it.
"""

from evolvex.db.models.assignment import AssignmentStatus, DeviceAssignment
from evolvex.db.models.device import Device, DeviceAdminStatus, DeviceType
from evolvex.db.models.driver import Driver, DriverStatus
from evolvex.db.models.organization import Organization, OrganizationStatus
from evolvex.db.models.trip import Trip, TripMode, TripStatus
from evolvex.db.models.user import User, UserRole, UserStatus
from evolvex.db.models.vehicle import Vehicle, VehicleStatus

__all__ = [
    "AssignmentStatus",
    "Device",
    "DeviceAdminStatus",
    "DeviceAssignment",
    "DeviceType",
    "Driver",
    "DriverStatus",
    "Organization",
    "OrganizationStatus",
    "Trip",
    "TripMode",
    "TripStatus",
    "User",
    "UserRole",
    "UserStatus",
    "Vehicle",
    "VehicleStatus",
]
