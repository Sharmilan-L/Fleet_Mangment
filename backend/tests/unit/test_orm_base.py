"""
Unit tests for SQLAlchemy ORM base, naming conventions, and reusable mixins.

These tests verify the foundation that all domain models will inherit from.
No database connection is required — everything is validated against
SQLAlchemy metadata and column descriptors.
"""

import uuid
from datetime import datetime
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.orm import Mapped, mapped_column

from evolvex.db.base import (
    NAMING_CONVENTION,
    Base,
    CreatedAtMixin,
    UpdatedAtMixin,
    UUIDPrimaryKeyMixin,
)

# -----------------------------------------------------------------------
# Naming convention tests
# -----------------------------------------------------------------------


class TestNamingConvention:
    """Verify PostgreSQL naming convention attached to Base.metadata."""

    def test_metadata_has_naming_convention(self) -> None:
        """Base.metadata must carry the full naming convention dict."""
        meta = Base.metadata
        assert meta.naming_convention is not None
        assert isinstance(meta.naming_convention, dict)

    @pytest.mark.parametrize(
        "key,expected_template",
        [
            ("ix", "ix_%(column_0_label)s"),
            ("uq", "uq_%(table_name)s_%(column_0_name)s"),
            ("ck", "ck_%(table_name)s_%(constraint_name)s"),
            ("fk", "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"),
            ("pk", "pk_%(table_name)s"),
        ],
    )
    def test_naming_convention_templates(self, key: str, expected_template: str) -> None:
        """Each constraint type must use the approved template string."""
        assert NAMING_CONVENTION[key] == expected_template
        assert Base.metadata.naming_convention[key] == expected_template

    def test_naming_convention_has_all_five_keys(self) -> None:
        """Convention must cover ix, uq, ck, fk, pk."""
        required = {"ix", "uq", "ck", "fk", "pk"}
        assert required.issubset(set(NAMING_CONVENTION.keys()))


# -----------------------------------------------------------------------
# Helper model for mixin tests (not a real domain model)
# -----------------------------------------------------------------------


class _TestMixinModel(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """Throwaway model used only by unit tests to exercise mixins."""

    __tablename__ = "_test_mixin_model"

    label: Mapped[str] = mapped_column(nullable=False)


# -----------------------------------------------------------------------
# UUID primary key mixin tests
# -----------------------------------------------------------------------


class TestUUIDPrimaryKeyMixin:
    """Verify UUIDPrimaryKeyMixin produces correct column descriptor."""

    def test_id_column_exists(self) -> None:
        """Model must have an 'id' column."""
        mapper = inspect(_TestMixinModel)
        assert "id" in mapper.columns

    def test_id_is_primary_key(self) -> None:
        """The 'id' column must be the primary key."""
        mapper = inspect(_TestMixinModel)
        pk_cols = [c.name for c in mapper.primary_key]
        assert pk_cols == ["id"]

    def test_id_column_type_is_uuid(self) -> None:
        """The 'id' column Python type must be uuid.UUID."""
        mapper = inspect(_TestMixinModel)
        col = mapper.columns["id"]
        assert col.type.python_type is uuid.UUID

    def test_id_has_server_default(self) -> None:
        """The 'id' column must carry a server_default for gen_random_uuid()."""
        table = _TestMixinModel.__table__
        col = table.c.id
        assert col.server_default is not None
        rendered = col.server_default.arg.text
        assert "gen_random_uuid()" in rendered

    def test_id_has_python_default(self) -> None:
        """The 'id' column must also have a Python-side uuid4 default."""
        table = _TestMixinModel.__table__
        col = table.c.id
        assert col.default is not None


# -----------------------------------------------------------------------
# CreatedAtMixin tests
# -----------------------------------------------------------------------


class TestCreatedAtMixin:
    """Verify CreatedAtMixin produces correct column descriptor."""

    def test_created_at_column_exists(self) -> None:
        mapper = inspect(_TestMixinModel)
        assert "created_at" in mapper.columns

    def test_created_at_type_is_datetime(self) -> None:
        mapper = inspect(_TestMixinModel)
        col = mapper.columns["created_at"]
        assert col.type.python_type is datetime

    def test_created_at_not_nullable(self) -> None:
        table = _TestMixinModel.__table__
        assert table.c.created_at.nullable is False

    def test_created_at_has_server_default(self) -> None:
        table = _TestMixinModel.__table__
        assert table.c.created_at.server_default is not None

    def test_created_at_is_timezone_aware(self) -> None:
        table = _TestMixinModel.__table__
        assert table.c.created_at.type.timezone is True

    def test_created_at_no_onupdate(self) -> None:
        """created_at must NOT have onupdate — it is set once at insert."""
        table = _TestMixinModel.__table__
        assert table.c.created_at.onupdate is None


# -----------------------------------------------------------------------
# UpdatedAtMixin tests
# -----------------------------------------------------------------------


class TestUpdatedAtMixin:
    """Verify UpdatedAtMixin produces correct column descriptor."""

    def test_updated_at_column_exists(self) -> None:
        mapper = inspect(_TestMixinModel)
        assert "updated_at" in mapper.columns

    def test_updated_at_type_is_datetime(self) -> None:
        mapper = inspect(_TestMixinModel)
        col = mapper.columns["updated_at"]
        assert col.type.python_type is datetime

    def test_updated_at_is_timezone_aware(self) -> None:
        table = _TestMixinModel.__table__
        assert table.c.updated_at.type.timezone is True

    def test_updated_at_not_nullable(self) -> None:
        table = _TestMixinModel.__table__
        assert table.c.updated_at.nullable is False

    def test_updated_at_has_server_default(self) -> None:
        table = _TestMixinModel.__table__
        assert table.c.updated_at.server_default is not None

    def test_updated_at_has_onupdate(self) -> None:
        """updated_at must have onupdate so SQLAlchemy refreshes it on UPDATE."""
        table = _TestMixinModel.__table__
        assert table.c.updated_at.onupdate is not None


# -----------------------------------------------------------------------
# Primary key naming convention test
# -----------------------------------------------------------------------


class TestPrimaryKeyNaming:
    """Verify that the naming convention applies to the test model's PK."""

    def test_pk_constraint_name(self) -> None:
        """PK constraint must follow 'pk_%(table_name)s' template."""
        table = _TestMixinModel.__table__
        pk = table.primary_key
        assert pk.name == "pk__test_mixin_model"


# -----------------------------------------------------------------------
# Alembic target_metadata connection test
# -----------------------------------------------------------------------


class TestAlembicTargetMetadata:
    """Verify that migrations/env.py connects target_metadata to Base.metadata."""

    def test_env_py_imports_base(self) -> None:
        """migrations/env.py must contain 'from evolvex.db.base import Base'."""
        backend_dir = Path(__file__).resolve().parents[2]
        env_py = backend_dir / "migrations" / "env.py"
        assert env_py.is_file(), "migrations/env.py missing"
        content = env_py.read_text(encoding="utf-8")
        assert "from evolvex.db.base import Base" in content

    def test_env_py_sets_target_metadata(self) -> None:
        """migrations/env.py must set target_metadata = Base.metadata."""
        backend_dir = Path(__file__).resolve().parents[2]
        env_py = backend_dir / "migrations" / "env.py"
        content = env_py.read_text(encoding="utf-8")
        assert "target_metadata = Base.metadata" in content

    def test_alembic_config_loads_with_base_metadata(self) -> None:
        """Alembic Config must still load correctly after env.py update."""
        backend_dir = Path(__file__).resolve().parents[2]
        alembic_ini = backend_dir / "alembic.ini"
        assert alembic_ini.is_file()
        config = Config(str(alembic_ini))
        script_location = config.get_main_option("script_location")
        assert script_location is not None
        assert script_location.replace("\\", "/").endswith("migrations")
