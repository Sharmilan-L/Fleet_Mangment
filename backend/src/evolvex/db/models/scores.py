"""
Trip Score State, Score Ledger, and Risk History SQLAlchemy models.

Includes trip score state, score ledger entries with uniqueness constraints, and risk history
(docs/database-design.md Sections 25, 26, 27).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evolvex.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class RiskLevel(enum.StrEnum):
    """Behavioral risk classification level."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class LedgerEntryType(enum.StrEnum):
    """Score ledger entry classification."""

    INITIAL = "INITIAL"
    EVENT_PENALTY = "EVENT_PENALTY"
    PATTERN_PENALTY = "PATTERN_PENALTY"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"
    REVERSAL = "REVERSAL"


class TripScoreState(UUIDPrimaryKeyMixin, Base):
    """
    Current trip score and risk status optimization table.

    Database design reference: docs/database-design.md Section 25.1
    """

    __tablename__ = "trip_score_states"
    __table_args__ = (
        CheckConstraint(
            "current_score >= 0.0 AND current_score <= 100.0",
            name="ck_trip_score_states_score_range",
        ),
        CheckConstraint(
            "current_risk_level IN ('LOW', 'MEDIUM', 'HIGH')",
            name="ck_trip_score_states_risk_level",
        ),
        UniqueConstraint("trip_id", name="uq_trip_score_states_trip_id"),
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    initial_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=100.0,
        server_default="100.0",
    )

    current_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=100.0,
        server_default="100.0",
        index=True,
    )

    current_risk_level: Mapped[RiskLevel] = mapped_column(
        String(20),
        nullable=False,
        default=RiskLevel.LOW,
        server_default=RiskLevel.LOW.value,
        index=True,
    )

    last_ledger_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("trip_score_ledger.id", ondelete="SET NULL"),
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

    trip = relationship("Trip", backref="score_state", lazy="selectin")
    last_ledger_entry = relationship(
        "TripScoreLedger",
        foreign_keys=[last_ledger_entry_id],
        lazy="selectin",
    )


class TripScoreLedger(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """
    Audit ledger of all trip score adjustments.

    Database design reference: docs/database-design.md Section 26.1
    """

    __tablename__ = "trip_score_ledger"
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ("
            "'INITIAL', 'EVENT_PENALTY', 'PATTERN_PENALTY', 'MANUAL_ADJUSTMENT', 'REVERSAL'"
            ")",
            name="entry_type",
        ),
        # Unique constraint preventing duplicate active event penalty per event
        Index(
            "uq_trip_score_ledger_source_event",
            "trip_id",
            "source_event_id",
            unique=True,
            postgresql_where=text("source_event_id IS NOT NULL AND entry_type = 'EVENT_PENALTY'"),
        ),
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    entry_type: Mapped[LedgerEntryType] = mapped_column(
        String(30),
        nullable=False,
        default=LedgerEntryType.EVENT_PENALTY,
        server_default=LedgerEntryType.EVENT_PENALTY.value,
    )

    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("driving_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    source_pattern_id: Mapped[uuid.UUID | None] = mapped_column(
        String(100),
        nullable=True,
    )

    reverses_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("trip_score_ledger.id", ondelete="SET NULL"),
        nullable=True,
    )

    rule_set_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rule_set_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    penalty_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        String(100),
        nullable=True,
    )

    previous_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    points_delta: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    new_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    trip = relationship("Trip", backref="score_ledger_entries", lazy="selectin")
    source_event = relationship("DrivingEvent", foreign_keys=[source_event_id], lazy="selectin")


class TripRiskHistory(UUIDPrimaryKeyMixin, Base):
    """
    History of behavioral risk level transitions for a trip.

    Database design reference: docs/database-design.md Section 27.1
    """

    __tablename__ = "trip_risk_history"
    __table_args__ = (
        CheckConstraint(
            "new_risk_level IN ('LOW', 'MEDIUM', 'HIGH')",
            name="new_risk_level",
        ),
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    previous_risk_level: Mapped[RiskLevel | None] = mapped_column(
        String(20),
        nullable=True,
    )

    new_risk_level: Mapped[RiskLevel] = mapped_column(
        String(20),
        nullable=False,
    )

    score_at_transition: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    risk_band_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("risk_bands.id", ondelete="SET NULL"),
        nullable=True,
    )

    triggering_ledger_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("trip_score_ledger.id", ondelete="SET NULL"),
        nullable=True,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    trip = relationship("Trip", backref="risk_history_entries", lazy="selectin")
