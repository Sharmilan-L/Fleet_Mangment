"""
SQLAlchemy DeclarativeBase, PostgreSQL naming conventions, and reusable column mixins.

All ORM models in the EvolveX project must inherit from ``Base`` defined here.
The naming convention ensures that Alembic autogenerate produces deterministic,
PostgreSQL-safe constraint names across all migrations.

Mixins
------
- ``UUIDPrimaryKeyMixin``  — ``id: Mapped[uuid.UUID]`` server-default ``gen_random_uuid()``
- ``CreatedAtMixin``       — ``created_at: Mapped[datetime]`` server-default ``now()``
- ``UpdatedAtMixin``       — ``updated_at: Mapped[datetime]`` server-default ``now()``, onupdate
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, MetaData, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ---------------------------------------------------------------------------
# PostgreSQL-safe naming convention
# ---------------------------------------------------------------------------
# Guarantees deterministic constraint names for indexes, unique constraints,
# check constraints, foreign keys, and primary keys.
# Reference: https://alembic.sqlalchemy.org/en/latest/naming.html

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# ---------------------------------------------------------------------------
# DeclarativeBase
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """
    Project-wide SQLAlchemy DeclarativeBase.

    All EvolveX ORM models must inherit from this class.
    The ``metadata`` carries the PostgreSQL naming convention so that every
    constraint created by model definitions or Alembic autogenerate receives
    a predictable, framework-managed name.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ---------------------------------------------------------------------------
# Reusable column mixins
# ---------------------------------------------------------------------------


class UUIDPrimaryKeyMixin:
    """
    Provides a UUID ``id`` column as the primary key.

    Uses PostgreSQL ``gen_random_uuid()`` as the server-side default so that
    the database generates the value when the application does not supply one.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class CreatedAtMixin:
    """
    Provides a ``created_at`` column with a server-side ``now()`` default.

    The value is set once when the row is inserted and never updated afterward.
    Uses DateTime(timezone=True) to generate TIMESTAMPTZ columns in PostgreSQL.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UpdatedAtMixin:
    """
    Provides an ``updated_at`` column with server-side ``now()`` default
    and automatic ``onupdate`` refresh.

    SQLAlchemy sets ``onupdate`` on the Python side; an additional database
    trigger may be added later for writes that bypass the ORM.
    Uses DateTime(timezone=True) to generate TIMESTAMPTZ columns in PostgreSQL.
    """

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
