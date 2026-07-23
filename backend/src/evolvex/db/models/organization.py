"""
Organization SQLAlchemy model.

Represents a fleet organization as defined in docs/database-design.md Section 4.1.
An Organization owns users, drivers, vehicles, devices, trips, and rules.
"""

import enum

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from evolvex.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin


class OrganizationStatus(enum.StrEnum):
    """Permitted statuses for an organization."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"


class Organization(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """
    Fleet organization.

    Database design reference: docs/database-design.md Section 4.1

    Fields
    ------
    id               : UUID primary key (from mixin)
    organization_code: Short unique business identifier (e.g. "FLEET-001")
    name             : Display name of the organization
    status           : OrganizationStatus enum (ACTIVE, SUSPENDED, INACTIVE)
    timezone         : IANA timezone string (e.g. "Asia/Kolkata")
    created_at       : Row insertion timestamp (from mixin)
    updated_at       : Last modification timestamp (from mixin)
    """

    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED', 'INACTIVE')",
            name="status",
        ),
    )

    organization_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Short unique business identifier",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Display name of the organization",
    )

    status: Mapped[OrganizationStatus] = mapped_column(
        String(20),
        nullable=False,
        default=OrganizationStatus.ACTIVE,
        server_default=OrganizationStatus.ACTIVE.value,
        comment="Current organization status",
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
        server_default="UTC",
        comment="IANA timezone identifier",
    )
