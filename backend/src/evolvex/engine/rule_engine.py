"""
EvolveX Server-Side Telemetry Rule Engine & Scoring Engine.

Implements rule detection, detector state machine, event creation,
score ledger writing, and risk transitions according to:
- docs/system-architecture.md
- docs/database-design.md
- Milestone 3 specifications
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from evolvex.db.models.events import (
    DetectorStateEnum,
    DrivingEvent,
    EventDetectionState,
    EventSeverity,
    EventSource,
    EventStatus,
    EventTelemetryLink,
    EventType,
    EvidenceRole,
)
from evolvex.db.models.scores import (
    LedgerEntryType,
    RiskLevel,
    TripRiskHistory,
    TripScoreLedger,
    TripScoreState,
)
from evolvex.db.models.telemetry import TelemetryRecord

DEFAULT_PENALTIES = {
    EventType.HARSH_BRAKING: -4.0,
    EventType.SUDDEN_ACCELERATION: -3.0,
    EventType.OVERSPEEDING: -5.0,
    EventType.SHARP_TURNING: -3.0,
}


def calculate_risk_level(score: float) -> RiskLevel:
    """Determine risk band from current trip score."""
    if score >= 80.0:
        return RiskLevel.LOW
    elif score >= 60.0:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.HIGH


def calculate_event_severity(event_type: EventType, primary_measurement: float) -> EventSeverity:
    """Calculate event severity level based on peak measurement."""
    val = abs(primary_measurement)
    if event_type == EventType.HARSH_BRAKING:
        if val >= 6.0:
            return EventSeverity.CRITICAL
        elif val >= 4.5:
            return EventSeverity.HIGH
        elif val >= 3.5:
            return EventSeverity.MODERATE
        else:
            return EventSeverity.LOW
    elif event_type == EventType.SUDDEN_ACCELERATION:
        if val >= 6.0:
            return EventSeverity.CRITICAL
        elif val >= 4.5:
            return EventSeverity.HIGH
        elif val >= 3.5:
            return EventSeverity.MODERATE
        else:
            return EventSeverity.LOW
    elif event_type == EventType.OVERSPEEDING:
        if val >= 30.0:
            return EventSeverity.CRITICAL
        elif val >= 20.0:
            return EventSeverity.HIGH
        elif val >= 10.0:
            return EventSeverity.MODERATE
        else:
            return EventSeverity.LOW
    elif event_type == EventType.SHARP_TURNING:
        if val >= 8.0:
            return EventSeverity.CRITICAL
        elif val >= 6.0:
            return EventSeverity.HIGH
        elif val >= 4.5:
            return EventSeverity.MODERATE
        else:
            return EventSeverity.LOW
    return EventSeverity.MODERATE


class RuleEngine:
    """Evaluates telemetry packets against active trip rules and updates score ledger."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def initialize_trip_score_if_needed(self, trip_id) -> TripScoreState:
        """Ensure initial score state (100.0 points) and initial ledger entry exist for a trip."""
        stmt = select(TripScoreState).where(TripScoreState.trip_id == trip_id)
        res = await self.session.execute(stmt)
        score_state = res.scalar_one_or_none()

        if not score_state:
            # Create initial score ledger entry
            initial_ledger = TripScoreLedger(
                trip_id=trip_id,
                entry_type=LedgerEntryType.INITIAL,
                previous_score=100.0,
                points_delta=0.0,
                new_score=100.0,
                reason="Initial trip starting score",
            )
            self.session.add(initial_ledger)
            await self.session.flush()

            score_state = TripScoreState(
                trip_id=trip_id,
                initial_score=100.0,
                current_score=100.0,
                current_risk_level=RiskLevel.LOW,
                last_ledger_entry_id=initial_ledger.id,
            )
            self.session.add(score_state)
            await self.session.flush()

        return score_state

    async def apply_penalty_and_update_score(
        self,
        trip_id,
        event: DrivingEvent,
        rule_set_version_id=None,
    ) -> TripScoreState:
        """Deduct score points, write ledger entry, and record risk history."""
        score_state = await self.initialize_trip_score_if_needed(trip_id)

        # Check if penalty already logged for this event
        dup_chk = select(TripScoreLedger).where(
            TripScoreLedger.trip_id == trip_id,
            TripScoreLedger.source_event_id == event.id,
            TripScoreLedger.entry_type == LedgerEntryType.EVENT_PENALTY,
        )
        dup_res = await self.session.execute(dup_chk)
        if dup_res.scalar_one_or_none():
            return score_state

        points_delta = DEFAULT_PENALTIES.get(event.event_type, -3.0)
        previous_score = score_state.current_score
        new_score = max(0.0, min(100.0, previous_score + points_delta))

        ledger_entry = TripScoreLedger(
            trip_id=trip_id,
            entry_type=LedgerEntryType.EVENT_PENALTY,
            source_event_id=event.id,
            rule_set_version_id=rule_set_version_id,
            previous_score=previous_score,
            points_delta=points_delta,
            new_score=new_score,
            reason=f"{event.event_type.value} ({event.severity.value}) severity penalty",
        )
        self.session.add(ledger_entry)
        await self.session.flush()

        # Check risk level transition
        prev_risk = score_state.current_risk_level
        new_risk = calculate_risk_level(new_score)

        if prev_risk != new_risk:
            risk_hist = TripRiskHistory(
                trip_id=trip_id,
                previous_risk_level=prev_risk,
                new_risk_level=new_risk,
                score_at_transition=new_score,
                triggering_ledger_entry_id=ledger_entry.id,
            )
            self.session.add(risk_hist)

        score_state.current_score = new_score
        score_state.current_risk_level = new_risk
        score_state.last_ledger_entry_id = ledger_entry.id
        score_state.version_number += 1
        await self.session.flush()

        return score_state

    async def process_telemetry(
        self, telemetry: TelemetryRecord, speed_limit_kmh: float = 60.0
    ) -> list[DrivingEvent]:
        """
        Evaluate single telemetry record against four MVP driving rules.
        """
        if not telemetry.trip_id:
            return []

        packet_time = (
            telemetry.device_timestamp or telemetry.server_received_at or datetime.now(UTC)
        )
        created_events: list[DrivingEvent] = []

        # Rule evaluation conditions
        # 1. HARSH_BRAKING: accel_fwd <= -3.0 m/s^2, min_speed 5 km/h
        hb_condition = (
            telemetry.sensor_valid
            and telemetry.forward_acceleration_ms2 is not None
            and telemetry.speed_kmh is not None
            and telemetry.speed_kmh >= 5.0
            and telemetry.forward_acceleration_ms2 <= -3.0
        )
        hb_meas = abs(telemetry.forward_acceleration_ms2 or 0.0)
        e1 = await self._evaluate_event_type(
            telemetry=telemetry,
            event_type=EventType.HARSH_BRAKING,
            condition_met=hb_condition,
            primary_measurement=hb_meas,
            threshold_val=3.0,
            packet_time=packet_time,
            min_duration_ms=500,
            cooldown_ms=1000,
        )
        if e1:
            created_events.append(e1)

        # 2. SUDDEN_ACCELERATION: accel_fwd >= 3.0 m/s^2, min_speed 5 km/h
        sa_condition = (
            telemetry.sensor_valid
            and telemetry.forward_acceleration_ms2 is not None
            and telemetry.speed_kmh is not None
            and telemetry.speed_kmh >= 5.0
            and telemetry.forward_acceleration_ms2 >= 3.0
        )
        sa_meas = abs(telemetry.forward_acceleration_ms2 or 0.0)
        e2 = await self._evaluate_event_type(
            telemetry=telemetry,
            event_type=EventType.SUDDEN_ACCELERATION,
            condition_met=sa_condition,
            primary_measurement=sa_meas,
            threshold_val=3.0,
            packet_time=packet_time,
            min_duration_ms=500,
            cooldown_ms=1000,
        )
        if e2:
            created_events.append(e2)

        # 3. OVERSPEEDING: speed_kmh > speed_limit + 5.0, requires valid GPS
        over_threshold = speed_limit_kmh + 5.0
        os_condition = (
            telemetry.gps_valid
            and telemetry.speed_kmh is not None
            and telemetry.speed_kmh > over_threshold
        )
        excess_speed = max(0.0, (telemetry.speed_kmh or 0.0) - speed_limit_kmh)
        e3 = await self._evaluate_event_type(
            telemetry=telemetry,
            event_type=EventType.OVERSPEEDING,
            condition_met=os_condition,
            primary_measurement=excess_speed,
            threshold_val=over_threshold,
            packet_time=packet_time,
            min_duration_ms=3000,
            cooldown_ms=2000,
        )
        if e3:
            created_events.append(e3)

        # 4. SHARP_TURNING: |accel_lat| >= 4.0 m/s^2 or |yaw_rate| >= 20.0 deg/s, min speed 10 km/h
        lat_val = abs(telemetry.lateral_acceleration_ms2 or 0.0)
        yaw_val = abs(telemetry.yaw_rate_deg_s or 0.0)
        st_condition = (
            telemetry.sensor_valid
            and telemetry.speed_kmh is not None
            and telemetry.speed_kmh >= 10.0
            and (lat_val >= 4.0 or yaw_val >= 20.0)
        )
        turn_meas = max(lat_val, yaw_val / 5.0)
        e4 = await self._evaluate_event_type(
            telemetry=telemetry,
            event_type=EventType.SHARP_TURNING,
            condition_met=st_condition,
            primary_measurement=turn_meas,
            threshold_val=4.0,
            packet_time=packet_time,
            min_duration_ms=500,
            cooldown_ms=1000,
        )
        if e4:
            created_events.append(e4)

        return created_events

    async def _evaluate_event_type(
        self,
        telemetry: TelemetryRecord,
        event_type: EventType,
        condition_met: bool,
        primary_measurement: float,
        threshold_val: float,
        packet_time: datetime,
        min_duration_ms: int,
        cooldown_ms: int,
    ) -> DrivingEvent | None:
        """State machine for a single event type."""
        stmt = select(EventDetectionState).where(
            EventDetectionState.trip_id == telemetry.trip_id,
            EventDetectionState.event_type == event_type,
        )
        res = await self.session.execute(stmt)
        det_state = res.scalar_one_or_none()

        if not det_state:
            det_state = EventDetectionState(
                trip_id=telemetry.trip_id,
                event_type=event_type,
                state=DetectorStateEnum.NORMAL,
            )
            self.session.add(det_state)
            await self.session.flush()

        current_event: DrivingEvent | None = None

        if det_state.state == DetectorStateEnum.COOLDOWN:
            if det_state.cooldown_until and packet_time >= det_state.cooldown_until:
                det_state.state = DetectorStateEnum.NORMAL
                det_state.cooldown_until = None

        if det_state.state == DetectorStateEnum.NORMAL:
            if condition_met:
                det_state.state = DetectorStateEnum.CANDIDATE
                det_state.candidate_started_at = packet_time

        elif det_state.state == DetectorStateEnum.CANDIDATE:
            if condition_met:
                start = det_state.candidate_started_at or packet_time
                duration_ms = int((packet_time - start).total_seconds() * 1000)
                if duration_ms >= min_duration_ms:
                    # Confirm event!
                    severity = calculate_event_severity(event_type, primary_measurement)
                    event = DrivingEvent(
                        organization_id=telemetry.organization_id,
                        trip_id=telemetry.trip_id,
                        event_type=event_type,
                        status=EventStatus.ACTIVE,
                        severity=severity,
                        source=EventSource.BACKEND_RULE,
                        started_at=start,
                        ended_at=packet_time,
                        duration_ms=duration_ms,
                        primary_measurement=primary_measurement,
                        threshold_value=threshold_val,
                        maximum_speed_kmh=telemetry.speed_kmh,
                        minimum_forward_acceleration_ms2=telemetry.forward_acceleration_ms2,
                        maximum_forward_acceleration_ms2=telemetry.forward_acceleration_ms2,
                        maximum_lateral_acceleration_ms2=telemetry.lateral_acceleration_ms2,
                        maximum_absolute_yaw_rate_deg_s=abs(telemetry.yaw_rate_deg_s or 0.0),
                    )
                    self.session.add(event)
                    await self.session.flush()

                    # Add evidence link
                    link = EventTelemetryLink(
                        event_id=event.id,
                        telemetry_id=telemetry.id,
                        evidence_role=EvidenceRole.TRIGGER,
                    )
                    self.session.add(link)

                    # Deduct score & log ledger
                    await self.apply_penalty_and_update_score(telemetry.trip_id, event)

                    det_state.state = DetectorStateEnum.ACTIVE
                    det_state.active_event_id = event.id
                    current_event = event
            else:
                det_state.state = DetectorStateEnum.NORMAL
                det_state.candidate_started_at = None

        elif det_state.state == DetectorStateEnum.ACTIVE:
            active_event = None
            if det_state.active_event_id:
                ev_stmt = select(DrivingEvent).where(DrivingEvent.id == det_state.active_event_id)
                ev_res = await self.session.execute(ev_stmt)
                active_event = ev_res.scalar_one_or_none()

            if condition_met:
                if active_event:
                    active_event.ended_at = packet_time
                    if active_event.started_at:
                        active_event.duration_ms = int(
                            (packet_time - active_event.started_at).total_seconds() * 1000
                        )
                    if primary_measurement > active_event.primary_measurement:
                        active_event.primary_measurement = primary_measurement
                        active_event.severity = calculate_event_severity(
                            event_type, primary_measurement
                        )

                    link = EventTelemetryLink(
                        event_id=active_event.id,
                        telemetry_id=telemetry.id,
                        evidence_role=EvidenceRole.DURING,
                    )
                    self.session.add(link)
            else:
                # Event ended -> move to COMPLETED & COOLDOWN
                if active_event:
                    active_event.status = EventStatus.COMPLETED
                    active_event.ended_at = packet_time
                    if active_event.started_at:
                        active_event.duration_ms = int(
                            (packet_time - active_event.started_at).total_seconds() * 1000
                        )
                    link = EventTelemetryLink(
                        event_id=active_event.id,
                        telemetry_id=telemetry.id,
                        evidence_role=EvidenceRole.RELEASE,
                    )
                    self.session.add(link)

                det_state.state = DetectorStateEnum.COOLDOWN
                det_state.active_event_id = None
                det_state.cooldown_until = packet_time + timedelta(milliseconds=cooldown_ms)

        det_state.latest_telemetry_id = telemetry.id
        det_state.last_triggered_at = packet_time
        await self.session.flush()

        return current_event
