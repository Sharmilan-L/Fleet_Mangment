"""
Unit tests for Rules, Events, and Scoring SQLAlchemy models.
"""

from sqlalchemy import inspect

from evolvex.db.models.events import DrivingEvent, EventDetectionState, EventTelemetryLink
from evolvex.db.models.rules import (
    AccelerationRule,
    OverspeedRule,
    RuleSet,
    RuleSetVersion,
    TurningRule,
)
from evolvex.db.models.scores import TripRiskHistory, TripScoreLedger, TripScoreState


def test_rule_table_names() -> None:
    assert RuleSet.__tablename__ == "rule_sets"
    assert RuleSetVersion.__tablename__ == "rule_set_versions"
    assert AccelerationRule.__tablename__ == "acceleration_rules"
    assert OverspeedRule.__tablename__ == "overspeed_rules"
    assert TurningRule.__tablename__ == "turning_rules"


def test_event_table_names() -> None:
    assert EventDetectionState.__tablename__ == "event_detection_states"
    assert DrivingEvent.__tablename__ == "driving_events"
    assert EventTelemetryLink.__tablename__ == "event_telemetry_links"


def test_score_table_names() -> None:
    assert TripScoreState.__tablename__ == "trip_score_states"
    assert TripScoreLedger.__tablename__ == "trip_score_ledger"
    assert TripRiskHistory.__tablename__ == "trip_risk_history"


def test_driving_event_columns() -> None:
    mapper = inspect(DrivingEvent)
    col_names = {c.key for c in mapper.columns}
    expected = {
        "id",
        "organization_id",
        "trip_id",
        "event_type",
        "status",
        "severity",
        "source",
        "started_at",
        "ended_at",
        "duration_ms",
        "rule_set_version_id",
        "detection_rule_id",
        "primary_measurement",
        "threshold_value",
        "release_threshold_value",
        "maximum_speed_kmh",
        "minimum_forward_acceleration_ms2",
        "maximum_forward_acceleration_ms2",
        "maximum_lateral_acceleration_ms2",
        "maximum_absolute_yaw_rate_deg_s",
        "voided_at",
        "voided_by_user_id",
        "void_reason",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(col_names)
