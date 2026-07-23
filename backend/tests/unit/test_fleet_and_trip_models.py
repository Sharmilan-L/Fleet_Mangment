"""
Focused unit tests for Driver, Vehicle, Device, DeviceAssignment, and Trip models.

Validates table names, columns, foreign keys, constraints, partial unique indexes,
and enums against docs/database-design.md.
"""

import uuid
from datetime import datetime

from sqlalchemy import inspect

from evolvex.db.models import (
    AssignmentStatus,
    Device,
    DeviceAdminStatus,
    DeviceAssignment,
    DeviceType,
    Driver,
    DriverStatus,
    Trip,
    TripMode,
    TripStatus,
    Vehicle,
    VehicleStatus,
)


class TestFleetAndTripTableNames:
    """Verify table names for all core fleet and trip entities."""

    def test_table_names(self) -> None:
        assert Driver.__tablename__ == "drivers"
        assert Vehicle.__tablename__ == "vehicles"
        assert Device.__tablename__ == "devices"
        assert DeviceAssignment.__tablename__ == "device_assignments"
        assert Trip.__tablename__ == "trips"


class TestDriverModel:
    """Verify Driver model structure, foreign keys, constraints, and enums."""

    def test_driver_columns(self) -> None:
        mapper = inspect(Driver)
        cols = {c.key: c.type.python_type for c in mapper.columns}
        assert cols["id"] is uuid.UUID
        assert cols["organization_id"] is uuid.UUID
        assert cols["employee_code"] is str
        assert cols["first_name"] is str
        assert cols["last_name"] is str
        assert cols["status"] is str

    def test_driver_fk(self) -> None:
        table = Driver.__table__
        fks = list(table.c.organization_id.foreign_keys)
        assert len(fks) == 1
        assert fks[0].target_fullname == "organizations.id"
        assert fks[0].ondelete == "CASCADE"

    def test_driver_check_constraint(self) -> None:
        table = Driver.__table__
        checks = [c for c in table.constraints if hasattr(c, "sqltext")]
        ck = next((c for c in checks if c.name == "ck_drivers_status"), None)
        assert ck is not None
        assert "ACTIVE" in str(ck.sqltext)

    def test_driver_status_enum(self) -> None:
        assert set(DriverStatus) == {"ACTIVE", "INACTIVE", "SUSPENDED"}


class TestVehicleModel:
    """Verify Vehicle model structure, foreign keys, constraints, and enums."""

    def test_vehicle_columns(self) -> None:
        mapper = inspect(Vehicle)
        cols = {c.key: c.type.python_type for c in mapper.columns}
        assert cols["id"] is uuid.UUID
        assert cols["organization_id"] is uuid.UUID
        assert cols["registration_number"] is str
        assert cols["vehicle_code"] is str
        assert cols["default_speed_limit_kmh"] is float

    def test_vehicle_fk(self) -> None:
        table = Vehicle.__table__
        fks = list(table.c.organization_id.foreign_keys)
        assert len(fks) == 1
        assert fks[0].target_fullname == "organizations.id"
        assert fks[0].ondelete == "CASCADE"

    def test_vehicle_check_constraint(self) -> None:
        table = Vehicle.__table__
        checks = [c for c in table.constraints if hasattr(c, "sqltext")]
        ck = next((c for c in checks if c.name == "ck_vehicles_status"), None)
        assert ck is not None
        assert "MAINTENANCE" in str(ck.sqltext)

    def test_vehicle_status_enum(self) -> None:
        assert set(VehicleStatus) == {"ACTIVE", "INACTIVE", "MAINTENANCE", "RETIRED"}


class TestDeviceModel:
    """Verify Device model structure, foreign keys, constraints, and enums."""

    def test_device_columns(self) -> None:
        mapper = inspect(Device)
        cols = {c.key: c.type.python_type for c in mapper.columns}
        assert cols["id"] is uuid.UUID
        assert cols["organization_id"] is uuid.UUID
        assert cols["device_code"] is str
        assert cols["device_type"] is str
        assert cols["administrative_status"] is str
        assert cols["last_credential_rotation_at"] is datetime

    def test_device_fk(self) -> None:
        table = Device.__table__
        fks = list(table.c.organization_id.foreign_keys)
        assert len(fks) == 1
        assert fks[0].target_fullname == "organizations.id"
        assert fks[0].ondelete == "CASCADE"

    def test_device_enums(self) -> None:
        assert set(DeviceType) == {"HARDWARE", "SIMULATOR"}
        assert set(DeviceAdminStatus) == {"ACTIVE", "TESTING", "DISABLED", "RETIRED"}


class TestDeviceAssignmentModel:
    """Verify DeviceAssignment foreign keys, delete rules, and partial unique indexes."""

    def test_assignment_fks(self) -> None:
        table = DeviceAssignment.__table__

        org_fk = list(table.c.organization_id.foreign_keys)[0]
        assert org_fk.target_fullname == "organizations.id"
        assert org_fk.ondelete == "CASCADE"

        dev_fk = list(table.c.device_id.foreign_keys)[0]
        assert dev_fk.target_fullname == "devices.id"
        assert dev_fk.ondelete == "RESTRICT"

        veh_fk = list(table.c.vehicle_id.foreign_keys)[0]
        assert veh_fk.target_fullname == "vehicles.id"
        assert veh_fk.ondelete == "RESTRICT"

        user_fk = list(table.c.assigned_by_user_id.foreign_keys)[0]
        assert user_fk.target_fullname == "users.id"
        assert user_fk.ondelete == "SET NULL"

    def test_active_assignment_partial_unique_indexes(self) -> None:
        table = DeviceAssignment.__table__
        indexes = {idx.name: idx for idx in table.indexes}

        assert "uq_device_assignments_active_vehicle" in indexes
        idx_veh = indexes["uq_device_assignments_active_vehicle"]
        assert idx_veh.unique is True
        assert "status = 'ACTIVE'" in str(idx_veh.dialect_options["postgresql"]["where"])

        assert "uq_device_assignments_active_device" in indexes
        idx_dev = indexes["uq_device_assignments_active_device"]
        assert idx_dev.unique is True
        assert "status = 'ACTIVE'" in str(idx_dev.dialect_options["postgresql"]["where"])

    def test_assignment_status_enum(self) -> None:
        assert set(AssignmentStatus) == {"ACTIVE", "ENDED"}


class TestTripModel:
    """Verify Trip model foreign keys, delete rules, and partial unique indexes."""

    def test_trip_fks(self) -> None:
        table = Trip.__table__

        org_fk = list(table.c.organization_id.foreign_keys)[0]
        assert org_fk.target_fullname == "organizations.id"
        assert org_fk.ondelete == "CASCADE"

        drv_fk = list(table.c.driver_id.foreign_keys)[0]
        assert drv_fk.target_fullname == "drivers.id"
        assert drv_fk.ondelete == "RESTRICT"

        asgn_fk = list(table.c.device_assignment_id.foreign_keys)[0]
        assert asgn_fk.target_fullname == "device_assignments.id"
        assert asgn_fk.ondelete == "RESTRICT"

    def test_active_trip_partial_unique_indexes(self) -> None:
        table = Trip.__table__
        indexes = {idx.name: idx for idx in table.indexes}

        assert "uq_trips_active_driver" in indexes
        idx_drv = indexes["uq_trips_active_driver"]
        assert idx_drv.unique is True
        assert "status IN ('ACTIVE', 'FINALIZING')" in str(
            idx_drv.dialect_options["postgresql"]["where"]
        )

        assert "uq_trips_active_assignment" in indexes
        idx_asgn = indexes["uq_trips_active_assignment"]
        assert idx_asgn.unique is True
        assert "status IN ('ACTIVE', 'FINALIZING')" in str(
            idx_asgn.dialect_options["postgresql"]["where"]
        )

    def test_trip_enums(self) -> None:
        assert set(TripMode) == {"OFFICIAL", "TEST"}
        assert set(TripStatus) == {
            "ACTIVE",
            "FINALIZING",
            "COMPLETED",
            "CANCELLED",
            "FINALIZATION_FAILED",
        }
