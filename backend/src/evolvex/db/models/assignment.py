"""
DeviceAssignment SQLAlchemy model.

Represents periods when a Device is attached to a Vehicle (docs/database-design.md Section 9.1).
Includes database-enforced partial unique constraints guaranteeing one active assignment
per vehicle and one active assignment per device.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evolvex.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class AssignmentStatus(enum.StrEnum):
    """Permitted statuses for a device assignment."""

    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class DeviceAssignment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """
    DeviceAssignment entity.

    Database design reference: docs/database-design.md Section 9.1
    """

    __tablename__ = "device_assignments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'ENDED')",
            name="status",
        ),
        # Database-enforced partial unique constraint: only 1 active assignment per vehicle
        Index(
            "uq_device_assignments_active_vehicle",
            "vehicle_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
        # Database-enforced partial unique constraint: only 1 active assignment per device
        Index(
            "uq_device_assignments_active_device",
            "device_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization ownership foreign key",
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Foreign key to assigned device",
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Foreign key to assigned vehicle",
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when assignment began",
    )

    unassigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when assignment ended (NULL for ACTIVE)",
    )

    status: Mapped[AssignmentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=AssignmentStatus.ACTIVE,
        server_default=AssignmentStatus.ACTIVE.value,
        index=True,
        comment="Assignment status (ACTIVE or ENDED)",
    )

    assigned_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who performed the assignment",
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Optional administrative notes",
    )

    organization = relationship("Organization", backref="device_assignments", lazy="selectin")
    device = relationship("Device", backref="assignments", lazy="selectin")
    vehicle = relationship("Vehicle", backref="assignments", lazy="selectin")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by_user_id], lazy="selectin")
