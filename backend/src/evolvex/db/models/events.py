"""
Driving Event and Detector State SQLAlchemy models.

Includes event detection states, driving events, and event-telemetry evidence links
(docs/database-design.md Sections 20, 21, 23).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evolvex.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin


class EventType(enum.StrEnum):
    """MVP Driving Event Types."""

    HARSH_BRAKING = "HARSH_BRAKING"
    SUDDEN_ACCELERATION = "SUDDEN_ACCELERATION"
    OVERSPEEDING = "OVERSPEEDING"
    SHARP_TURNING = "SHARP_TURNING"


class EventStatus(enum.StrEnum):
    """Lifecycle status of a driving event."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    VOIDED = "VOIDED"


class EventSeverity(enum.StrEnum):
    """Severity classification level."""

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventSource(enum.StrEnum):
    """Origin source of driving event."""

    BACKEND_RULE = "BACKEND_RULE"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class DetectorStateEnum(enum.StrEnum):
    """Rule engine state machine status for an event type."""

    NORMAL = "NORMAL"
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    COOLDOWN = "COOLDOWN"


class EvidenceRole(enum.StrEnum):
    """Role of a telemetry packet within event evidence timeline."""

    BEFORE = "BEFORE"
    TRIGGER = "TRIGGER"
    PEAK = "PEAK"
    DURING = "DURING"
    RELEASE = "RELEASE"
    AFTER = "AFTER"


class EventDetectionState(UUIDPrimaryKeyMixin, Base):
    """
    Detector state for recovering active rule evaluation across server restarts.

    Database design reference: docs/database-design.md Section 20.1
    """

    __tablename__ = "event_detection_states"
    __table_args__ = (
        CheckConstraint(
            "state IN ('NORMAL', 'CANDIDATE', 'ACTIVE', 'COOLDOWN')",
            name="state",
        ),
        UniqueConstraint("trip_id", "event_type", name="uq_event_detection_states_trip_event_type"),
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[EventType] = mapped_column(
        String(40),
        nullable=False,
    )

    state: Mapped[DetectorStateEnum] = mapped_column(
        String(20),
        nullable=False,
        default=DetectorStateEnum.NORMAL,
        server_default=DetectorStateEnum.NORMAL.value,
    )

    candidate_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    active_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("driving_events.id", ondelete="SET NULL"),
        nullable=True,
    )

    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cooldown_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    latest_telemetry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("telemetry_records.id", ondelete="SET NULL"),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    trip = relationship("Trip", backref="detector_states", lazy="selectin")
    active_event = relationship("DrivingEvent", foreign_keys=[active_event_id], lazy="selectin")


class DrivingEvent(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """
    Confirmed server-side driving event record.

    Database design reference: docs/database-design.md Section 21.1
    """

    __tablename__ = "driving_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ("
            "'HARSH_BRAKING', 'SUDDEN_ACCELERATION', 'OVERSPEEDING', 'SHARP_TURNING'"
            ")",
            name="event_type",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'COMPLETED', 'VOIDED')",
            name="status",
        ),
        CheckConstraint(
            "severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')",
            name="severity",
        ),
        CheckConstraint(
            "source IN ('BACKEND_RULE', 'MANUAL_REVIEW')",
            name="source",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[EventType] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    status: Mapped[EventStatus] = mapped_column(
        String(20),
        nullable=False,
        default=EventStatus.ACTIVE,
        server_default=EventStatus.ACTIVE.value,
        index=True,
    )

    severity: Mapped[EventSeverity] = mapped_column(
        String(20),
        nullable=False,
        default=EventSeverity.MODERATE,
        server_default=EventSeverity.MODERATE.value,
        index=True,
    )

    source: Mapped[EventSource] = mapped_column(
        String(30),
        nullable=False,
        default=EventSource.BACKEND_RULE,
        server_default=EventSource.BACKEND_RULE.value,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    rule_set_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rule_set_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    detection_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        String(100),
        nullable=True,
    )

    primary_measurement: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Peak measurement value (e.g. peak m/s^2 or peak km/h excess)",
    )

    threshold_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Trigger threshold value applied",
    )

    release_threshold_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Hysteresis release threshold applied",
    )

    maximum_speed_kmh: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    minimum_forward_acceleration_ms2: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_forward_acceleration_ms2: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_lateral_acceleration_ms2: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maximum_absolute_yaw_rate_deg_s: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    voided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    voided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    void_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    organization = relationship("Organization", backref="driving_events", lazy="selectin")
    trip = relationship("Trip", backref="driving_events", lazy="selectin")
    telemetry_links = relationship(
        "EventTelemetryLink", back_populates="event", cascade="all, delete-orphan"
    )


class EventTelemetryLink(UUIDPrimaryKeyMixin, Base):
    """
    Many-to-many link between driving event and supporting raw telemetry evidence.

    Database design reference: docs/database-design.md Section 23.1
    """

    __tablename__ = "event_telemetry_links"
    __table_args__ = (
        CheckConstraint(
            "evidence_role IN ('BEFORE', 'TRIGGER', 'PEAK', 'DURING', 'RELEASE', 'AFTER')",
            name="evidence_role",
        ),
        UniqueConstraint(
            "event_id", "telemetry_id", name="uq_event_telemetry_links_event_telemetry"
        ),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("driving_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    telemetry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("telemetry_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    evidence_role: Mapped[EvidenceRole] = mapped_column(
        String(20),
        nullable=False,
        default=EvidenceRole.DURING,
        server_default=EvidenceRole.DURING.value,
    )

    sequence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    event = relationship("DrivingEvent", back_populates="telemetry_links", lazy="selectin")
    telemetry = relationship("TelemetryRecord", backref="event_links", lazy="selectin")
