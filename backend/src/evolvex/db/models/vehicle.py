"""
Vehicle SQLAlchemy model.

Represents fleet vehicles (docs/database-design.md Section 7.1).
"""

import enum
import uuid

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evolvex.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin


class VehicleStatus(enum.StrEnum):
    """Permitted statuses for a vehicle."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    RETIRED = "RETIRED"


class Vehicle(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """
    Fleet Vehicle entity.

    Database design reference: docs/database-design.md Section 7.1
    """

    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "registration_number", name="uq_vehicles_registration_number"
        ),
        UniqueConstraint("organization_id", "vehicle_code", name="uq_vehicles_vehicle_code"),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'MAINTENANCE', 'RETIRED')",
            name="status",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization ownership foreign key",
    )

    registration_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Official vehicle license plate or registration number",
    )

    vehicle_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Organization-scoped unique vehicle code",
    )

    make: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Vehicle manufacturer make (e.g. Toyota)",
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Vehicle model (e.g. Hilux)",
    )

    manufacture_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Year of manufacture",
    )

    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SEDAN",
        server_default="SEDAN",
        comment="Vehicle classification type (e.g. SEDAN, TRUCK, VAN)",
    )

    status: Mapped[VehicleStatus] = mapped_column(
        String(20),
        nullable=False,
        default=VehicleStatus.ACTIVE,
        server_default=VehicleStatus.ACTIVE.value,
        comment="Current vehicle status",
    )

    default_speed_limit_kmh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=60.0,
        server_default="60.0",
        comment="Default speed limit in km/h for overspeed calculations",
    )

    organization = relationship("Organization", backref="vehicles", lazy="selectin")
