"""
Trip SQLAlchemy model.

Represents a driving session (docs/database-design.md Section 14.1).
Includes database-enforced partial unique indexes enforcing one active trip per driver
and one active trip per device assignment.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evolvex.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin


class TripMode(enum.StrEnum):
    """Classification of trip purpose (OFFICIAL vs TEST/SIMULATION)."""

    OFFICIAL = "OFFICIAL"
    TEST = "TEST"


class TripStatus(enum.StrEnum):
    """Lifecycle status of a trip session."""

    ACTIVE = "ACTIVE"
    FINALIZING = "FINALIZING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FINALIZATION_FAILED = "FINALIZATION_FAILED"


class Trip(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """
    Trip driving session entity.

    Database design reference: docs/database-design.md Section 14.1
    """

    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint(
            "trip_mode IN ('OFFICIAL', 'TEST')",
            name="trip_mode",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'FINALIZING', 'COMPLETED', 'CANCELLED', 'FINALIZATION_FAILED')",
            name="status",
        ),
        # Database-enforced partial unique constraint: max 1 active/finalizing trip per driver
        Index(
            "uq_trips_active_driver",
            "driver_id",
            unique=True,
            postgresql_where=text("status IN ('ACTIVE', 'FINALIZING')"),
        ),
        # Database-enforced partial unique constraint: max 1 active/finalizing trip per assignment
        Index(
            "uq_trips_active_assignment",
            "device_assignment_id",
            unique=True,
            postgresql_where=text("status IN ('ACTIVE', 'FINALIZING')"),
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization ownership foreign key",
    )

    trip_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Globally unique trip code",
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("drivers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Driver operating the trip",
    )

    device_assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("device_assignments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Device assignment (device+vehicle relationship) for this trip",
    )

    rule_set_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="Applied rule set version UUID",
    )

    started_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who started the trip",
    )

    ended_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who ended the trip",
    )

    trip_mode: Mapped[TripMode] = mapped_column(
        String(20),
        nullable=False,
        default=TripMode.OFFICIAL,
        server_default=TripMode.OFFICIAL.value,
        comment="Trip mode (OFFICIAL or TEST)",
    )

    status: Mapped[TripStatus] = mapped_column(
        String(30),
        nullable=False,
        default=TripStatus.ACTIVE,
        server_default=TripStatus.ACTIVE.value,
        index=True,
        comment="Trip status (ACTIVE, COMPLETED, CANCELLED, FINALIZATION_FAILED)",
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when trip started",
    )

    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when trip ended",
    )

    applied_speed_limit_kmh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=60.0,
        server_default="60.0",
        comment="Speed limit applied to trip",
    )

    start_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional trip start justification",
    )

    end_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional trip end justification",
    )

    organization = relationship("Organization", backref="trips", lazy="selectin")
    driver = relationship("Driver", backref="trips", lazy="selectin")
    device_assignment = relationship("DeviceAssignment", backref="trips", lazy="selectin")
    started_by_user = relationship("User", foreign_keys=[started_by_user_id], lazy="selectin")
    ended_by_user = relationship("User", foreign_keys=[ended_by_user_id], lazy="selectin")
