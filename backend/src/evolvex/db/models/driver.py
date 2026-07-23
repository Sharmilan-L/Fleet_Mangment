"""
Driver SQLAlchemy model.

Represents drivers managed by an Organization (docs/database-design.md Section 6.1).
"""

import enum
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evolvex.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin


class DriverStatus(enum.StrEnum):
    """Permitted statuses for a driver."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class Driver(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """
    Driver entity.

    Database design reference: docs/database-design.md Section 6.1
    """

    __tablename__ = "drivers"
    __table_args__ = (
        UniqueConstraint("organization_id", "employee_code", name="uq_drivers_employee_code"),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')",
            name="status",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization ownership foreign key",
    )

    employee_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Organization-scoped unique employee identifier",
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Driver first name",
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Driver last name",
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="Contact phone number",
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Driver email address",
    )

    license_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Driving license number",
    )

    status: Mapped[DriverStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DriverStatus.ACTIVE,
        server_default=DriverStatus.ACTIVE.value,
        comment="Current driver status (ACTIVE, INACTIVE, SUSPENDED)",
    )

    organization = relationship("Organization", backref="drivers", lazy="selectin")
