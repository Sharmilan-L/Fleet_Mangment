"""
Unit tests for the User SQLAlchemy model.

Validates table name, columns, types, foreign keys, constraints, indexes,
and enum values against docs/database-design.md Section 5.1.
No database connection required.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import inspect

from evolvex.db.models.user import User, UserRole, UserStatus

# -----------------------------------------------------------------------
# Table name
# -----------------------------------------------------------------------


class TestUserTableName:
    """Verify the User model maps to the correct table."""

    def test_tablename(self) -> None:
        assert User.__tablename__ == "users"


# -----------------------------------------------------------------------
# Column existence and types
# -----------------------------------------------------------------------

EXPECTED_COLUMNS = {
    "id": uuid.UUID,
    "organization_id": uuid.UUID,
    "email": str,
    "password_hash": str,
    "full_name": str,
    "role": str,
    "status": str,
    "last_login_at": datetime,
    "created_at": datetime,
    "updated_at": datetime,
}


class TestUserColumns:
    """Verify all approved columns exist with correct Python types."""

    def test_all_expected_columns_exist(self) -> None:
        mapper = inspect(User)
        actual = {c.key for c in mapper.columns}
        assert set(EXPECTED_COLUMNS.keys()) == actual

    @pytest.mark.parametrize("col_name,expected_type", list(EXPECTED_COLUMNS.items()))
    def test_column_python_type(self, col_name: str, expected_type: type) -> None:
        mapper = inspect(User)
        col = mapper.columns[col_name]
        assert col.type.python_type is expected_type

    def test_no_extra_columns(self) -> None:
        """Model must not define columns beyond the approved set."""
        mapper = inspect(User)
        actual = {c.key for c in mapper.columns}
        assert actual == set(EXPECTED_COLUMNS.keys())


# -----------------------------------------------------------------------
# Primary key and Foreign keys
# -----------------------------------------------------------------------


class TestUserKeysAndRelationships:
    """Verify primary key and organization foreign key."""

    def test_pk_is_id(self) -> None:
        mapper = inspect(User)
        pk_cols = [c.name for c in mapper.primary_key]
        assert pk_cols == ["id"]

    def test_pk_constraint_name(self) -> None:
        table = User.__table__
        assert table.primary_key.name == "pk_users"

    def test_organization_id_fk_exists(self) -> None:
        table = User.__table__
        fks = list(table.c.organization_id.foreign_keys)
        assert len(fks) == 1
        fk = fks[0]
        assert fk.target_fullname == "organizations.id"
        assert fk.ondelete == "CASCADE"

    def test_organization_relationship_exists(self) -> None:
        mapper = inspect(User)
        assert "organization" in mapper.relationships


# -----------------------------------------------------------------------
# Required fields and Nullability
# -----------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "id",
    "organization_id",
    "email",
    "password_hash",
    "full_name",
    "role",
    "status",
    "created_at",
    "updated_at",
]


class TestUserNullability:
    """Verify NOT NULL on required fields and NULL on last_login_at."""

    @pytest.mark.parametrize("col_name", REQUIRED_COLUMNS)
    def test_required_columns_not_nullable(self, col_name: str) -> None:
        table = User.__table__
        col = table.c[col_name]
        if col.primary_key:
            return
        assert col.nullable is False, f"{col_name} must be NOT NULL"

    def test_last_login_at_nullable(self) -> None:
        table = User.__table__
        assert table.c.last_login_at.nullable is True


# -----------------------------------------------------------------------
# Unique constraints and Indexes
# -----------------------------------------------------------------------


class TestUserConstraintsAndIndexes:
    """Verify unique constraints and indexes."""

    def test_email_unique(self) -> None:
        table = User.__table__
        assert table.c.email.unique is True

    def test_email_indexed(self) -> None:
        table = User.__table__
        assert table.c.email.index is True

    def test_organization_id_indexed(self) -> None:
        table = User.__table__
        assert table.c.organization_id.index is True


# -----------------------------------------------------------------------
# Check constraints
# -----------------------------------------------------------------------


class TestUserCheckConstraints:
    """Verify check constraints for role and status."""

    def test_role_check_constraint_exists(self) -> None:
        table = User.__table__
        checks = [c for c in table.constraints if hasattr(c, "sqltext")]
        ck = next((c for c in checks if c.name == "ck_users_role"), None)
        assert ck is not None, "ck_users_role check constraint must exist"
        assert "ADMIN" in str(ck.sqltext)
        assert "FLEET_MANAGER" in str(ck.sqltext)

    def test_status_check_constraint_exists(self) -> None:
        table = User.__table__
        checks = [c for c in table.constraints if hasattr(c, "sqltext")]
        ck = next((c for c in checks if c.name == "ck_users_status"), None)
        assert ck is not None, "ck_users_status check constraint must exist"
        assert "ACTIVE" in str(ck.sqltext)
        assert "DISABLED" in str(ck.sqltext)


# -----------------------------------------------------------------------
# Timestamps
# -----------------------------------------------------------------------


class TestUserTimestamps:
    """Verify created_at, updated_at, and last_login_at timezone awareness."""

    def test_created_at_is_timezone_aware(self) -> None:
        table = User.__table__
        assert table.c.created_at.type.timezone is True

    def test_updated_at_is_timezone_aware(self) -> None:
        table = User.__table__
        assert table.c.updated_at.type.timezone is True

    def test_last_login_at_is_timezone_aware(self) -> None:
        table = User.__table__
        assert table.c.last_login_at.type.timezone is True


# -----------------------------------------------------------------------
# Defaults & Enums
# -----------------------------------------------------------------------


class TestUserDefaultsAndEnums:
    """Verify column defaults and enum values."""

    def test_role_default_is_fleet_manager(self) -> None:
        table = User.__table__
        assert table.c.role.server_default.arg == UserRole.FLEET_MANAGER.value

    def test_status_default_is_active(self) -> None:
        table = User.__table__
        assert table.c.status.server_default.arg == UserStatus.ACTIVE.value

    def test_user_role_enum_values(self) -> None:
        expected = {"ADMIN", "FLEET_MANAGER"}
        actual = {r.value for r in UserRole}
        assert actual == expected

    def test_user_status_enum_values(self) -> None:
        expected = {"ACTIVE", "DISABLED"}
        actual = {s.value for s in UserStatus}
        assert actual == expected
