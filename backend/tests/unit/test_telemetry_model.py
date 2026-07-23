"""
Unit tests for TelemetryRecord model and enums.
"""

import uuid

from sqlalchemy import inspect

from evolvex.db.models import (
    TelemetryProcessingStatus,
    TelemetryRecord,
    TelemetrySource,
)


class TestTelemetryRecordModel:
    """Verify TelemetryRecord model columns, table name, FKs, constraints, and enums."""

    def test_table_name(self) -> None:
        assert TelemetryRecord.__tablename__ == "telemetry_records"

    def test_columns(self) -> None:
        mapper = inspect(TelemetryRecord)
        cols = {c.key: c.type.python_type for c in mapper.columns}
        assert cols["id"] is uuid.UUID
        assert cols["organization_id"] is uuid.UUID
        assert cols["device_id"] is uuid.UUID
        assert cols["device_assignment_id"] is uuid.UUID
        assert cols["trip_id"] is uuid.UUID
        assert cols["boot_id"] is str
        assert cols["sequence_number"] is int
        assert cols["gps_valid"] is bool
        assert cols["sensor_valid"] is bool

    def test_fks(self) -> None:
        table = TelemetryRecord.__table__

        org_fk = list(table.c.organization_id.foreign_keys)[0]
        assert org_fk.target_fullname == "organizations.id"
        assert org_fk.ondelete == "CASCADE"

        dev_fk = list(table.c.device_id.foreign_keys)[0]
        assert dev_fk.target_fullname == "devices.id"
        assert dev_fk.ondelete == "RESTRICT"

        asgn_fk = list(table.c.device_assignment_id.foreign_keys)[0]
        assert asgn_fk.target_fullname == "device_assignments.id"
        assert asgn_fk.ondelete == "SET NULL"

        trip_fk = list(table.c.trip_id.foreign_keys)[0]
        assert trip_fk.target_fullname == "trips.id"
        assert trip_fk.ondelete == "SET NULL"

    def test_idempotency_unique_constraint(self) -> None:
        table = TelemetryRecord.__table__
        constrs = [c for c in table.constraints if hasattr(c, "columns")]
        uq = next((c for c in constrs if c.name == "uq_telemetry_records_idempotency"), None)
        assert uq is not None
        col_names = [c.name for c in uq.columns]
        assert col_names == ["device_id", "boot_id", "sequence_number"]

    def test_enums(self) -> None:
        assert set(TelemetrySource) == {"HARDWARE", "SIMULATOR", "REPLAY"}
        assert set(TelemetryProcessingStatus) == {
            "RECEIVED",
            "PROCESSED",
            "PARTIAL",
            "FAILED",
            "DUPLICATE",
            "REJECTED",
        }
