"""
Rule configuration SQLAlchemy models.

Includes rule sets, rule set versions, behaviour rules, severity bands, penalties, and risk bands
(docs/database-design.md Sections 10, 11, 12, 13).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evolvex.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin


class RuleSetVersionStatus(enum.StrEnum):
    """Lifecycle status of a rule set version."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class RuleSet(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """
    Named collection of rules entity.

    Database design reference: docs/database-design.md Section 10.1
    """

    __tablename__ = "rule_sets"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization ownership foreign key",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Rule set display name",
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional rule set description",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
        comment="Rule set status",
    )

    organization = relationship("Organization", backref="rule_sets", lazy="selectin")
    versions = relationship(
        "RuleSetVersion",
        back_populates="rule_set",
        cascade="all, delete-orphan",
    )


class RuleSetVersion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """
    Immutable version of a rule set.

    Database design reference: docs/database-design.md Section 10.2
    """

    __tablename__ = "rule_set_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'RETIRED')",
            name="status",
        ),
        UniqueConstraint(
            "rule_set_id",
            "version_number",
            name="uq_rule_set_versions_rule_set_version",
        ),
    )

    rule_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rule_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent rule set foreign key",
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Monotonically increasing version index",
    )

    status: Mapped[RuleSetVersionStatus] = mapped_column(
        String(20),
        nullable=False,
        default=RuleSetVersionStatus.DRAFT,
        server_default=RuleSetVersionStatus.DRAFT.value,
        comment="Version lifecycle status (DRAFT, ACTIVE, RETIRED)",
    )

    effective_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when version becomes effective",
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when version was activated",
    )

    activated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who activated this version",
    )

    rule_set = relationship("RuleSet", back_populates="versions", lazy="selectin")
    acceleration_rules = relationship(
        "AccelerationRule",
        back_populates="rule_set_version",
        cascade="all, delete-orphan",
    )
    overspeed_rules = relationship(
        "OverspeedRule",
        back_populates="rule_set_version",
        cascade="all, delete-orphan",
    )
    turning_rules = relationship(
        "TurningRule",
        back_populates="rule_set_version",
        cascade="all, delete-orphan",
    )
    severity_bands = relationship(
        "EventSeverityBand",
        back_populates="rule_set_version",
        cascade="all, delete-orphan",
    )
    event_penalties = relationship(
        "EventPenalty",
        back_populates="rule_set_version",
        cascade="all, delete-orphan",
    )
    risk_bands = relationship(
        "RiskBand",
        back_populates="rule_set_version",
        cascade="all, delete-orphan",
    )


class AccelerationRule(UUIDPrimaryKeyMixin, Base):
    """
    Acceleration rule configuration (HARSH_BRAKING, SUDDEN_ACCELERATION).

    Database design reference: docs/database-design.md Section 11.1
    """

    __tablename__ = "acceleration_rules"
    __table_args__ = (
        CheckConstraint(
            "behaviour_type IN ('HARSH_BRAKING', 'SUDDEN_ACCELERATION')",
            name="behaviour_type",
        ),
    )

    rule_set_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rule_set_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    behaviour_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="HARSH_BRAKING or SUDDEN_ACCELERATION",
    )

    trigger_threshold_ms2: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Acceleration magnitude threshold in m/s^2",
    )

    release_threshold_ms2: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Acceleration hysteresis release threshold in m/s^2",
    )

    minimum_duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=500,
        server_default="500",
        comment="Minimum duration in milliseconds required to confirm event",
    )

    minimum_speed_kmh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=5.0,
        server_default="5.0",
        comment="Minimum vehicle speed in km/h for rule evaluation",
    )

    cooldown_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
        server_default="1000",
        comment="Cooldown window after event in milliseconds",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    rule_set_version = relationship(
        "RuleSetVersion",
        back_populates="acceleration_rules",
        lazy="selectin",
    )


class OverspeedRule(UUIDPrimaryKeyMixin, Base):
    """
    Overspeed rule configuration.

    Database design reference: docs/database-design.md Section 11.2
    """

    __tablename__ = "overspeed_rules"

    rule_set_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rule_set_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tolerance_kmh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=5.0,
        server_default="5.0",
        comment="Speed limit buffer / tolerance in km/h",
    )

    minimum_duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3000,
        server_default="3000",
        comment="Minimum sustained overspeed duration in milliseconds",
    )

    release_margin_kmh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=2.0,
        server_default="2.0",
        comment="Hysteresis margin below trigger speed for event release",
    )

    cooldown_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2000,
        server_default="2000",
        comment="Cooldown period after event release",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    rule_set_version = relationship(
        "RuleSetVersion",
        back_populates="overspeed_rules",
        lazy="selectin",
    )


class TurningRule(UUIDPrimaryKeyMixin, Base):
    """
    Sharp turning rule configuration.

    Database design reference: docs/database-design.md Section 11.3
    """

    __tablename__ = "turning_rules"

    rule_set_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rule_set_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    lateral_acceleration_threshold_ms2: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Lateral acceleration threshold in m/s^2",
    )

    yaw_rate_threshold_deg_s: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Yaw rate threshold in deg/s",
    )

    minimum_speed_kmh: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=10.0,
        server_default="10.0",
        comment="Minimum speed for sharp turn detection",
    )

    minimum_duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=500,
        server_default="500",
        comment="Minimum duration in milliseconds",
    )

    release_lateral_threshold_ms2: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Hysteresis release lateral accel threshold",
    )

    release_yaw_threshold_deg_s: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Hysteresis release yaw rate threshold",
    )

    cooldown_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
        server_default="1000",
        comment="Cooldown duration",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    rule_set_version = relationship(
        "RuleSetVersion",
        back_populates="turning_rules",
        lazy="selectin",
    )


class EventSeverityBand(UUIDPrimaryKeyMixin, Base):
    """
    Severity classification range for event types.

    Database design reference: docs/database-design.md Section 12.1
    """

    __tablename__ = "event_severity_bands"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')",
            name="severity",
        ),
    )

    rule_set_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rule_set_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    minimum_measure: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    maximum_measure: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    minimum_duration_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    priority_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    rule_set_version = relationship(
        "RuleSetVersion",
        back_populates="severity_bands",
        lazy="selectin",
    )


class EventPenalty(UUIDPrimaryKeyMixin, Base):
    """
    Score penalty allocation per event type and severity.

    Database design reference: docs/database-design.md Section 13.1
    """

    __tablename__ = "event_penalties"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')",
            name="severity",
        ),
        UniqueConstraint(
            "rule_set_version_id",
            "event_type",
            "severity",
            name="uq_event_penalties_version_type_severity",
        ),
    )

    rule_set_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rule_set_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    points_delta: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Negative score point deduction",
    )

    rule_set_version = relationship(
        "RuleSetVersion",
        back_populates="event_penalties",
        lazy="selectin",
    )


class RiskBand(UUIDPrimaryKeyMixin, Base):
    """
    Risk level band mapping from trip score.

    Database design reference: docs/database-design.md Section 13.3
    """

    __tablename__ = "risk_bands"
    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('LOW', 'MEDIUM', 'HIGH')",
            name="risk_level",
        ),
    )

    rule_set_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rule_set_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    minimum_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    maximum_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    priority_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    rule_set_version = relationship(
        "RuleSetVersion",
        back_populates="risk_bands",
        lazy="selectin",
    )
