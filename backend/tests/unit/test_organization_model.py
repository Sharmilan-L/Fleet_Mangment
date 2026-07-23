"""
Unit tests for the Organization SQLAlchemy model.

Validates table name, columns, types, constraints, indexes,
and enum values against docs/database-design.md Section 4.1.
No database connection required.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import inspect

from evolvex.db.models.organization import Organization, OrganizationStatus

# -----------------------------------------------------------------------
# Table name
# -----------------------------------------------------------------------


class TestOrganizationTableName:
    """Verify the Organization model maps to the correct table."""

    def test_tablename(self) -> None:
        assert Organization.__tablename__ == "organizations"


# -----------------------------------------------------------------------
# Column existence and types
# -----------------------------------------------------------------------

# Expected columns from database-design.md Section 4.1
EXPECTED_COLUMNS = {
    "id": uuid.UUID,
    "organization_code": str,
    "name": str,
    "status": str,  # stored as VARCHAR, Python enum on the model
    "timezone": str,
    "created_at": datetime,
    "updated_at": datetime,
}


class TestOrganizationColumns:
    """Verify all approved columns exist with correct Python types."""

    def test_all_expected_columns_exist(self) -> None:
        mapper = inspect(Organization)
        actual = {c.key for c in mapper.columns}
        assert set(EXPECTED_COLUMNS.keys()) == actual

    @pytest.mark.parametrize("col_name,expected_type", list(EXPECTED_COLUMNS.items()))
    def test_column_python_type(self, col_name: str, expected_type: type) -> None:
        mapper = inspect(Organization)
        col = mapper.columns[col_name]
        assert col.type.python_type is expected_type

    def test_no_extra_columns(self) -> None:
        """Model must not define columns beyond the approved set."""
        mapper = inspect(Organization)
        actual = {c.key for c in mapper.columns}
        assert actual == set(EXPECTED_COLUMNS.keys())


# -----------------------------------------------------------------------
# UUID primary key
# -----------------------------------------------------------------------


class TestOrganizationPrimaryKey:
    """Verify UUID primary key from mixin."""

    def test_pk_is_id(self) -> None:
        mapper = inspect(Organization)
        pk_cols = [c.name for c in mapper.primary_key]
        assert pk_cols == ["id"]

    def test_pk_type_is_uuid(self) -> None:
        mapper = inspect(Organization)
        assert mapper.columns["id"].type.python_type is uuid.UUID

    def test_pk_has_server_default(self) -> None:
        table = Organization.__table__
        assert table.c.id.server_default is not None
        rendered = table.c.id.server_default.arg.text
        assert "gen_random_uuid()" in rendered

    def test_pk_constraint_name(self) -> None:
        """PK name must follow naming convention: pk_organizations."""
        table = Organization.__table__
        assert table.primary_key.name == "pk_organizations"


# -----------------------------------------------------------------------
# Required fields (NOT NULL)
# -----------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "id",
    "organization_code",
    "name",
    "status",
    "timezone",
    "created_at",
    "updated_at",
]


class TestOrganizationRequiredFields:
    """All approved fields are NOT NULL."""

    @pytest.mark.parametrize("col_name", REQUIRED_COLUMNS)
    def test_column_not_nullable(self, col_name: str) -> None:
        table = Organization.__table__
        col = table.c[col_name]
        # Primary key is implicitly NOT NULL
        if col.primary_key:
            return
        assert col.nullable is False, f"{col_name} must be NOT NULL"


# -----------------------------------------------------------------------
# Unique constraints
# -----------------------------------------------------------------------


class TestOrganizationUniqueConstraints:
    """Verify unique constraints on approved columns."""

    def test_organization_code_unique(self) -> None:
        table = Organization.__table__
        assert table.c.organization_code.unique is True


# -----------------------------------------------------------------------
# Check constraints
# -----------------------------------------------------------------------


class TestOrganizationCheckConstraints:
    """Verify check constraints on Organization model."""

    def test_status_check_constraint_exists(self) -> None:
        table = Organization.__table__
        checks = [c for c in table.constraints if hasattr(c, "sqltext")]
        assert len(checks) >= 1
        ck = next((c for c in checks if c.name == "ck_organizations_status"), None)
        assert ck is not None, "ck_organizations_status check constraint must exist"
        assert "ACTIVE" in str(ck.sqltext)
        assert "SUSPENDED" in str(ck.sqltext)
        assert "INACTIVE" in str(ck.sqltext)


# -----------------------------------------------------------------------
# Indexes
# -----------------------------------------------------------------------


class TestOrganizationIndexes:
    """Verify indexes on approved columns."""

    def test_organization_code_indexed(self) -> None:
        table = Organization.__table__
        assert table.c.organization_code.index is True


# -----------------------------------------------------------------------
# Timestamps (from mixins)
# -----------------------------------------------------------------------


class TestOrganizationTimestamps:
    """Verify created_at and updated_at from mixins."""

    def test_created_at_has_server_default(self) -> None:
        table = Organization.__table__
        assert table.c.created_at.server_default is not None

    def test_created_at_no_onupdate(self) -> None:
        table = Organization.__table__
        assert table.c.created_at.onupdate is None

    def test_updated_at_has_server_default(self) -> None:
        table = Organization.__table__
        assert table.c.updated_at.server_default is not None

    def test_updated_at_has_onupdate(self) -> None:
        table = Organization.__table__
        assert table.c.updated_at.onupdate is not None


# -----------------------------------------------------------------------
# Defaults
# -----------------------------------------------------------------------


class TestOrganizationDefaults:
    """Verify column defaults."""

    def test_status_default_is_active(self) -> None:
        table = Organization.__table__
        assert table.c.status.server_default.arg == OrganizationStatus.ACTIVE.value

    def test_timezone_default_is_utc(self) -> None:
        table = Organization.__table__
        assert table.c.timezone.server_default.arg == "UTC"


# -----------------------------------------------------------------------
# OrganizationStatus enum
# -----------------------------------------------------------------------


class TestOrganizationStatusEnum:
    """Verify OrganizationStatus enum values."""

    def test_enum_values(self) -> None:
        expected = {"ACTIVE", "SUSPENDED", "INACTIVE"}
        actual = {s.value for s in OrganizationStatus}
        assert actual == expected

    def test_enum_is_str_subclass(self) -> None:
        """Enum must subclass str for direct VARCHAR storage."""
        assert issubclass(OrganizationStatus, str)
