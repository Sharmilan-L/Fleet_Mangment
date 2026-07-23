"""
Device SQLAlchemy model.

Represents physical and simulated telemetry devices (docs/database-design.md Section 8.1).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evolvex.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin


class DeviceType(enum.StrEnum):
    """Telemetry device hardware/software type."""

    HARDWARE = "HARDWARE"
    SIMULATOR = "SIMULATOR"


class DeviceAdminStatus(enum.StrEnum):
    """Administrative status of a device."""

    ACTIVE = "ACTIVE"
    TESTING = "TESTING"
    DISABLED = "DISABLED"
    RETIRED = "RETIRED"


class Device(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """
    Device entity (Hardware IoT device or Simulator).

    Database design reference: docs/database-design.md Section 8.1
    """

    __tablename__ = "devices"
    __table_args__ = (
        CheckConstraint(
            "device_type IN ('HARDWARE', 'SIMULATOR')",
            name="device_type",
        ),
        CheckConstraint(
            "administrative_status IN ('ACTIVE', 'TESTING', 'DISABLED', 'RETIRED')",
            name="administrative_status",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization ownership foreign key",
    )

    device_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Globally unique hardware/simulator device code",
    )

    display_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Human-readable device display name",
    )

    device_type: Mapped[DeviceType] = mapped_column(
        String(30),
        nullable=False,
        default=DeviceType.HARDWARE,
        server_default=DeviceType.HARDWARE.value,
        comment="Device category type (HARDWARE or SIMULATOR)",
    )

    administrative_status: Mapped[DeviceAdminStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DeviceAdminStatus.ACTIVE,
        server_default=DeviceAdminStatus.ACTIVE.value,
        comment="Current administrative status",
    )

    firmware_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Device firmware version string",
    )

    telemetry_schema_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="v1",
        server_default="v1",
        comment="Supported telemetry payload schema version",
    )

    api_key_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Hashed device API key credential",
    )

    last_credential_rotation_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last API key rotation",
    )

    organization = relationship("Organization", backref="devices", lazy="selectin")
