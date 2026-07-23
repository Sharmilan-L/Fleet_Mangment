"""
TelemetryRecord SQLAlchemy model.

Represents raw telemetry packets received from devices or simulators
(docs/database-design.md Section 16.1).
Includes idempotency unique constraint on (device_id, boot_id, sequence_number).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evolvex.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class TelemetrySource(enum.StrEnum):
    """Origin source of telemetry data."""

    HARDWARE = "HARDWARE"
    SIMULATOR = "SIMULATOR"
    REPLAY = "REPLAY"


class TelemetryProcessingStatus(enum.StrEnum):
    """Processing status of a telemetry packet."""

    RECEIVED = "RECEIVED"
    PROCESSED = "PROCESSED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"
    REJECTED = "REJECTED"


class TelemetryRecord(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """
    Raw telemetry packet entity.

    Database design reference: docs/database-design.md Section 16.1
    """

    __tablename__ = "telemetry_records"
    __table_args__ = (
        UniqueConstraint(
            "device_id", "boot_id", "sequence_number", name="uq_telemetry_records_idempotency"
        ),
        CheckConstraint(
            "source_type IN ('HARDWARE', 'SIMULATOR', 'REPLAY')",
            name="source_type",
        ),
        CheckConstraint(
            "processing_status IN ("
            "'RECEIVED', 'PROCESSED', 'PARTIAL', 'FAILED', 'DUPLICATE', 'REJECTED'"
            ")",
            name="processing_status",
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
        comment="Device that produced the telemetry",
    )

    device_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("device_assignments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Resolved device assignment at time of packet",
    )

    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("trips.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Resolved active/finalizing trip at time of packet",
    )

    source_type: Mapped[TelemetrySource] = mapped_column(
        String(20),
        nullable=False,
        default=TelemetrySource.HARDWARE,
        server_default=TelemetrySource.HARDWARE.value,
        comment="Telemetry source (HARDWARE, SIMULATOR, REPLAY)",
    )

    schema_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0",
        server_default="1.0",
        comment="Telemetry payload schema version",
    )

    boot_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Device boot instance identifier",
    )

    sequence_number: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Monotonically increasing sequence number per boot",
    )

    device_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp reported by device clock",
    )

    server_received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp when server received packet",
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="GPS latitude in decimal degrees",
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="GPS longitude in decimal degrees",
    )

    gps_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Flag indicating valid GPS fix",
    )

    sensor_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Flag indicating valid IMU/sensor readings",
    )

    speed_kmh: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="GPS speed in km/h",
    )

    forward_acceleration_ms2: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Forward acceleration in m/s^2",
    )

    lateral_acceleration_ms2: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Lateral acceleration in m/s^2",
    )

    yaw_rate_deg_s: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Yaw rate in degrees per second",
    )

    processing_status: Mapped[TelemetryProcessingStatus] = mapped_column(
        String(30),
        nullable=False,
        default=TelemetryProcessingStatus.RECEIVED,
        server_default=TelemetryProcessingStatus.RECEIVED.value,
        index=True,
        comment="Telemetry packet processing status",
    )

    validation_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Validation outcome label",
    )

    processing_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="Number of processing attempts",
    )

    last_processing_error: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Error message if processing failed",
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when processing finished",
    )

    raw_payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Original unparsed JSON payload",
    )

    organization = relationship("Organization", backref="telemetry_records", lazy="selectin")
    device = relationship("Device", backref="telemetry_records", lazy="selectin")
    device_assignment = relationship(
        "DeviceAssignment", backref="telemetry_records", lazy="selectin"
    )
    trip = relationship("Trip", backref="telemetry_records", lazy="selectin")
