# EvolveX Driver Behaviour Intelligence Platform

## Database Design Document

**Document version:** 1.0  
**Project stage:** Pitching MVP  
**Database:** PostgreSQL  
**Database approach:** Normalized relational design  
**Migration system:** Alembic  
**Application access:** FastAPI backend only  

---

## 1. Purpose

This document defines the logical database structure for the EvolveX MVP.

The database must support:

- Organizations and users
- Drivers
- Vehicles
- Devices
- Device-to-vehicle assignment history
- Rule configuration and versioning
- Trips
- Raw telemetry
- Driving events
- Behaviour patterns
- Trip scoring
- Alerts
- Trip summaries
- Driver performance
- Data quality
- Simulation separation
- Auditability

PostgreSQL is the persistent source of truth.

The React frontend must never connect directly to PostgreSQL.

```text
React
    ↓
FastAPI
    ↓
PostgreSQL
```

---

## 2. Database Design Principles

### 2.1 Normalization

The schema should satisfy:

- First Normal Form
- Second Normal Form
- Third Normal Form
- BCNF where practically appropriate

Repeated business facts should be stored once and referenced by foreign keys.

Example:

The trip does not separately store an unrelated device ID and vehicle ID when the approved device assignment already identifies that relationship.

The trip references:

```text
device_assignment_id
```

That assignment identifies:

```text
Device
    ↔
Vehicle
```

### 2.2 Historical integrity

Historical records must preserve the configuration and context that existed when they were created.

Examples:

- Trip keeps the selected rule-set version.
- Event stores the applied threshold.
- Score entry stores the applied penalty.
- Trip references the device assignment used at trip start.
- Completed summaries are not recalculated silently using new rules.

### 2.3 Explainability

Every derived result must be traceable.

```text
Raw telemetry
    ↓
Driving event
    ↓
Event severity
    ↓
Score-ledger entry
    ↓
Trip score
    ↓
Risk level
```

### 2.4 Simulation separation

Simulated data must be identifiable through:

- Testing device
- Test trip
- Telemetry source
- Simulation run
- Dashboard labels

Test trips must not affect official driver or fleet analytics.

### 2.5 Raw data preservation

Raw telemetry should remain immutable after storage, except for controlled processing metadata.

Derived records can be voided, reversed or superseded without deleting the original evidence.

### 2.6 Database-enforced integrity

Important rules should be protected by PostgreSQL constraints where possible.

Examples:

- Unique email inside the required scope
- Unique device code
- One active device assignment per vehicle
- One active trip per driver
- One active trip per device assignment
- Valid score range
- Valid latitude and longitude
- End time cannot precede start time
- Official and test mode values must come from permitted enums

---

## 3. Main Entity Groups

The schema is divided into these logical groups:

1. Organization and users
2. Drivers
3. Vehicles
4. Devices and assignments
5. Rule configuration
6. Trips
7. Telemetry
8. Events
9. Behaviour patterns
10. Scores and risk
11. Alerts
12. Data quality
13. Trip summaries
14. Driver analytics
15. Simulation
16. Audit and operational records

---

## 4. Organization

### 4.1 `organizations`

Represents a fleet organization.

Important fields:

- `id`
- `organization_code`
- `name`
- `status`
- `timezone`
- `created_at`
- `updated_at`

Purpose:

```text
Organization
    ↓
Owns users, drivers, vehicles, devices, trips and rules
```

The pitch environment may contain one organization, but organization ownership remains part of the schema.

---

## 5. Users and Authentication

### 5.1 `users`

Represents administrators and fleet managers.

Important fields:

- `id`
- `organization_id`
- `email`
- `password_hash`
- `full_name`
- `role`
- `status`
- `last_login_at`
- `created_at`
- `updated_at`

Roles:

- `ADMIN`
- `FLEET_MANAGER`

Statuses may include:

- `ACTIVE`
- `DISABLED`

Passwords must never be stored as plain text.

### 5.2 `user_sessions`

Stores server-recognized login sessions or refresh-session records.

Important fields:

- `id`
- `user_id`
- `token_hash`
- `expires_at`
- `revoked_at`
- `created_at`
- `last_seen_at`
- `ip_address`
- `user_agent`

The browser stores only an HTTP-only cookie or token identifier.

The database stores a hash where applicable.

---

## 6. Drivers

### 6.1 `drivers`

Represents drivers managed by an organization.

Important fields:

- `id`
- `organization_id`
- `employee_code`
- `first_name`
- `last_name`
- `phone`
- `email`
- `license_number`
- `status`
- `created_at`
- `updated_at`

Statuses:

- `ACTIVE`
- `INACTIVE`
- `SUSPENDED`

A driver may have many trips.

```text
Driver
    1
    ↓
    many Trips
```

Driver records should not store the current vehicle as a permanent attribute because vehicles are selected per trip.

---

## 7. Vehicles

### 7.1 `vehicles`

Represents fleet vehicles.

Important fields:

- `id`
- `organization_id`
- `registration_number`
- `vehicle_code`
- `make`
- `model`
- `manufacture_year`
- `vehicle_type`
- `status`
- `default_speed_limit_kmh`
- `created_at`
- `updated_at`

Statuses:

- `ACTIVE`
- `INACTIVE`
- `MAINTENANCE`
- `RETIRED`

The vehicle must remain logically separate from the IoT device.

This allows the device to be replaced without losing vehicle history.

---

## 8. Devices

### 8.1 `devices`

Represents physical and simulated telemetry devices.

Important fields:

- `id`
- `organization_id`
- `device_code`
- `display_name`
- `device_type`
- `administrative_status`
- `firmware_version`
- `telemetry_schema_version`
- `api_key_hash`
- `last_credential_rotation_at`
- `created_at`
- `updated_at`

Device types:

- `HARDWARE`
- `SIMULATOR`

Administrative statuses may include:

- `ACTIVE`
- `TESTING`
- `DISABLED`
- `RETIRED`

The device API key must be stored as a hash where possible.

### 8.2 Device identity rule

A hardware packet identifies the device.

It must not be trusted to assign the official driver.

The backend resolves:

```text
Device
    ↓
Device assignment
    ↓
Vehicle
    ↓
Active trip
    ↓
Driver
```

---

## 9. Device Assignment History

### 9.1 `device_assignments`

Represents the period during which a device is attached to a vehicle.

Important fields:

- `id`
- `organization_id`
- `device_id`
- `vehicle_id`
- `assigned_at`
- `unassigned_at`
- `status`
- `assigned_by_user_id`
- `notes`
- `created_at`

Statuses:

- `ACTIVE`
- `ENDED`

Rules:

- One device may have multiple historical assignments.
- One vehicle may have multiple historical assignments.
- Only one active primary device assignment is permitted for a vehicle.
- A device must not be actively assigned to multiple vehicles unless the architecture is deliberately extended.

```text
Device
    1
    ↓
    many historical assignments

Vehicle
    1
    ↓
    many historical assignments
```

Historical assignments must not be overwritten.

---

## 10. Rule Configuration

Rule configuration must be versioned.

### 10.1 `rule_sets`

Represents a named collection of rules.

Important fields:

- `id`
- `organization_id`
- `name`
- `description`
- `status`
- `created_at`
- `updated_at`

### 10.2 `rule_set_versions`

Represents an immutable version of a rule set.

Important fields:

- `id`
- `rule_set_id`
- `version_number`
- `status`
- `effective_from`
- `activated_at`
- `activated_by_user_id`
- `created_at`

Statuses:

- `DRAFT`
- `ACTIVE`
- `RETIRED`

A trip references one `rule_set_version_id`.

After activation, the version should be treated as immutable.

To change a threshold:

```text
Create new draft version
    ↓
Validate
    ↓
Activate new version
    ↓
Future trips use the new version
```

Existing trips keep the old version.

---

## 11. Behaviour-Specific Rules

### 11.1 `acceleration_rules`

Stores harsh-braking and sudden-acceleration configuration.

Important fields:

- `id`
- `rule_set_version_id`
- `behaviour_type`
- `trigger_threshold_ms2`
- `release_threshold_ms2`
- `minimum_duration_ms`
- `minimum_speed_kmh`
- `cooldown_ms`
- `enabled`

Behaviour types:

- `HARSH_BRAKING`
- `SUDDEN_ACCELERATION`

### 11.2 `overspeed_rules`

Important fields:

- `id`
- `rule_set_version_id`
- `tolerance_kmh`
- `minimum_duration_ms`
- `release_margin_kmh`
- `cooldown_ms`
- `enabled`

The applied trip speed limit is combined with this rule.

Example:

```text
Trip speed limit = 60 km/h
Tolerance = 5 km/h
Detection threshold = 65 km/h
```

### 11.3 `turning_rules`

Important fields:

- `id`
- `rule_set_version_id`
- `lateral_acceleration_threshold_ms2`
- `yaw_rate_threshold_deg_s`
- `minimum_speed_kmh`
- `minimum_duration_ms`
- `release_lateral_threshold_ms2`
- `release_yaw_threshold_deg_s`
- `cooldown_ms`
- `enabled`

### 11.4 `pattern_rules`

Defines rolling-window behaviour-pattern rules.

Important fields:

- `id`
- `rule_set_version_id`
- `pattern_type`
- `window_seconds`
- `minimum_event_count`
- `minimum_weighted_points`
- `cooldown_seconds`
- `enabled`

Pattern types:

- `REPEATED_SAME_BEHAVIOUR`
- `MIXED_AGGRESSIVE`

### 11.5 `pattern_event_weights`

Defines the contribution of each event type to a pattern.

Important fields:

- `id`
- `pattern_rule_id`
- `event_type`
- `weight`

---

## 12. Severity Configuration

### 12.1 `event_severity_bands`

Stores severity ranges for event types.

Important fields:

- `id`
- `rule_set_version_id`
- `event_type`
- `severity`
- `minimum_measure`
- `maximum_measure`
- `minimum_duration_ms`
- `priority_order`

Severities:

- `LOW`
- `MODERATE`
- `HIGH`
- `CRITICAL`

### 12.2 `pattern_severity_bands`

Important fields:

- `id`
- `rule_set_version_id`
- `pattern_type`
- `severity`
- `minimum_event_count`
- `minimum_pattern_points`
- `priority_order`

The event record still stores the final applied severity and evidence.

---

## 13. Penalty and Risk Configuration

### 13.1 `event_penalties`

Important fields:

- `id`
- `rule_set_version_id`
- `event_type`
- `severity`
- `points_delta`

Example:

```text
HIGH HARSH_BRAKING
→ -4 points
```

### 13.2 `pattern_penalties`

Important fields:

- `id`
- `rule_set_version_id`
- `pattern_type`
- `severity`
- `points_delta`

### 13.3 `risk_bands`

Important fields:

- `id`
- `rule_set_version_id`
- `risk_level`
- `minimum_score`
- `maximum_score`
- `priority_order`

Initial proposed values:

| Risk | Score |
|---|---:|
| LOW | 80–100 |
| MEDIUM | 60–79 |
| HIGH | 0–59 |

### 13.4 `trip_assessment_rules`

Stores trip-quality and assessment eligibility settings.

Possible fields:

- `id`
- `rule_set_version_id`
- `minimum_trip_duration_seconds`
- `minimum_distance_km`
- `minimum_valid_packet_count`
- `maximum_gap_ratio`
- `official_analytics_minimum_quality`
- `created_at`

---

## 14. Trips

### 14.1 `trips`

Represents a driving session.

Important fields:

- `id`
- `organization_id`
- `trip_code`
- `driver_id`
- `device_assignment_id`
- `rule_set_version_id`
- `started_by_user_id`
- `ended_by_user_id`
- `trip_mode`
- `status`
- `start_time`
- `end_time`
- `applied_speed_limit_kmh`
- `start_reason`
- `end_reason`
- `created_at`
- `updated_at`

Trip modes:

- `OFFICIAL`
- `TEST`

Statuses:

- `ACTIVE`
- `COMPLETED`
- `CANCELLED`
- `FINALIZATION_FAILED`

Why the trip references `device_assignment_id`:

```text
Trip
    ↓
Device assignment
    ├── Device
    └── Vehicle
```

This preserves the exact device-to-vehicle relationship used for the trip.

### 14.2 Active-trip constraints

The database should prevent multiple active trips for the same:

- Driver
- Device assignment
- Vehicle derived from the assignment

Partial unique indexes or exclusion constraints may be used.

Business-service validation must also run before insertion.

---

## 15. Trip Live State

### 15.1 `trip_live_states`

Stores the most recent active-trip status.

Important fields:

- `trip_id`
- `latest_telemetry_id`
- `latest_telemetry_time`
- `current_speed_kmh`
- `current_latitude`
- `current_longitude`
- `gps_valid`
- `current_score`
- `current_risk_level`
- `device_connection_status`
- `current_data_quality`
- `updated_at`
- `version_number`

This table is a current-state optimization.

It does not replace historical telemetry or score history.

---

## 16. Raw Telemetry

### 16.1 `telemetry_records`

Stores one row for each accepted or preserved telemetry packet.

Important fields:

- `id`
- `organization_id`
- `device_id`
- `device_assignment_id`
- `trip_id`
- `source_type`
- `schema_version`
- `boot_id`
- `sequence_number`
- `device_timestamp`
- `server_received_at`
- `latitude`
- `longitude`
- `gps_valid`
- `speed_kmh`
- `forward_acceleration_ms2`
- `lateral_acceleration_ms2`
- `yaw_rate_deg_s`
- `processing_status`
- `validation_status`
- `processing_attempts`
- `last_processing_error`
- `processed_at`
- `raw_payload`
- `created_at`

Source types:

- `HARDWARE`
- `SIMULATOR`
- `REPLAY`

Processing statuses:

- `RECEIVED`
- `PROCESSED`
- `PARTIAL`
- `FAILED`
- `DUPLICATE`
- `REJECTED`

### 16.2 Raw payload

`raw_payload` may use PostgreSQL `JSONB`.

It preserves the original accepted device packet.

Standardized numeric values should also be stored in typed columns for querying and rule processing.

### 16.3 Duplicate protection

Recommended unique identity:

```text
device_id
+
boot_id
+
sequence_number
```

When sequence information is unavailable, another controlled idempotency method is required.

A retransmitted packet must not create duplicate events or score penalties.

---

## 17. Hardware Observation Flags

### 17.1 `telemetry_hardware_observations`

Stores device-generated flags separately from official backend events.

Important fields:

- `id`
- `telemetry_id`
- `observation_type`
- `observed_value`
- `created_at`

Possible observations:

- Hardware harsh-brake flag
- Hardware harsh-acceleration flag
- Hardware turn flag
- Hardware overspeed flag
- Device comfort estimate

These observations are supporting evidence only.

They must not independently become official events.

---

## 18. Latest Device and Vehicle State

### 18.1 `device_latest_states`

Important fields:

- `device_id`
- `latest_telemetry_id`
- `last_received_at`
- `connection_status`
- `latest_schema_version`
- `latest_firmware_version`
- `updated_at`

Connection statuses:

- `ONLINE`
- `DELAYED`
- `OFFLINE`
- `UNKNOWN`

### 18.2 `vehicle_latest_states`

Important fields:

- `vehicle_id`
- `latest_telemetry_id`
- `latest_trip_id`
- `last_location_time`
- `latitude`
- `longitude`
- `speed_kmh`
- `connection_status`
- `updated_at`

These tables support fast dashboard queries.

---

## 19. Telemetry Gaps and Data Quality

### 19.1 `telemetry_gaps`

Stores detected communication gaps.

Important fields:

- `id`
- `trip_id`
- `device_id`
- `gap_started_at`
- `gap_ended_at`
- `duration_seconds`
- `gap_type`
- `created_at`

Gap types may include:

- `DELAYED`
- `OFFLINE`
- `MISSING_SEQUENCE`

### 19.2 `trip_data_quality`

Stores data-quality assessment for a trip.

Important fields:

- `trip_id`
- `total_packets`
- `valid_packets`
- `partial_packets`
- `invalid_packets`
- `duplicate_packets`
- `gps_valid_packets`
- `gap_count`
- `maximum_gap_seconds`
- `valid_packet_ratio`
- `gps_valid_ratio`
- `quality_level`
- `confidence_level`
- `official_analytics_eligible`
- `calculated_at`

Quality levels:

- `GOOD`
- `ACCEPTABLE`
- `LIMITED`
- `INSUFFICIENT`

Poor data quality must not automatically generate unsafe-driving penalties.

---

## 20. Event Detection State

### 20.1 `event_detection_states`

Stores the current detector state for each active trip and event type.

Important fields:

- `id`
- `trip_id`
- `event_type`
- `state`
- `candidate_started_at`
- `active_event_id`
- `last_triggered_at`
- `cooldown_until`
- `latest_telemetry_id`
- `updated_at`
- `version_number`

States:

- `NORMAL`
- `CANDIDATE`
- `ACTIVE`
- `COOLDOWN`

This allows processing to recover from a backend restart.

A purely in-memory candidate cache may be used as an optimization, but persistent state is safer for correctness.

---

## 21. Driving Events

### 21.1 `driving_events`

Stores confirmed backend events.

Important fields:

- `id`
- `organization_id`
- `trip_id`
- `event_type`
- `status`
- `severity`
- `source`
- `started_at`
- `ended_at`
- `duration_ms`
- `rule_set_version_id`
- `detection_rule_id`
- `primary_measurement`
- `threshold_value`
- `release_threshold_value`
- `maximum_speed_kmh`
- `minimum_forward_acceleration_ms2`
- `maximum_forward_acceleration_ms2`
- `maximum_lateral_acceleration_ms2`
- `maximum_absolute_yaw_rate_deg_s`
- `voided_at`
- `voided_by_user_id`
- `void_reason`
- `created_at`
- `updated_at`

Event types:

- `HARSH_BRAKING`
- `SUDDEN_ACCELERATION`
- `OVERSPEEDING`
- `SHARP_TURNING`
- Optional `HIGH_IMPACT_REQUIRES_VERIFICATION`

Statuses:

- `ACTIVE`
- `COMPLETED`
- `VOIDED`

Sources:

- `BACKEND_RULE`
- `MANUAL_REVIEW`

Hardware flags must not be stored as `BACKEND_RULE` events.

---

## 22. Event-Type Detail Tables

A common event table stores shared fields.

Subtype tables store behaviour-specific details.

### 22.1 `harsh_braking_event_details`

Possible fields:

- `event_id`
- `minimum_acceleration_ms2`
- `speed_at_start_kmh`
- `speed_at_peak_kmh`
- `speed_reduction_kmh`

### 22.2 `sudden_acceleration_event_details`

Possible fields:

- `event_id`
- `maximum_acceleration_ms2`
- `speed_at_start_kmh`
- `speed_at_peak_kmh`
- `speed_increase_kmh`

### 22.3 `overspeed_event_details`

Possible fields:

- `event_id`
- `applied_speed_limit_kmh`
- `detection_threshold_kmh`
- `maximum_speed_kmh`
- `overspeed_duration_ms`
- `maximum_excess_speed_kmh`

### 22.4 `sharp_turn_event_details`

Possible fields:

- `event_id`
- `maximum_lateral_acceleration_ms2`
- `maximum_absolute_yaw_rate_deg_s`
- `speed_at_peak_kmh`
- `turn_direction`

This prevents a single event table from accumulating many unrelated nullable fields.

---

## 23. Event Evidence

### 23.1 `event_telemetry_links`

Creates a many-to-many relationship between events and telemetry evidence.

Important fields:

- `event_id`
- `telemetry_id`
- `evidence_role`
- `sequence_order`

Evidence roles:

- `BEFORE`
- `TRIGGER`
- `PEAK`
- `DURING`
- `RELEASE`
- `AFTER`

This allows graphs to show the telemetry that justified the event.

---

## 24. Behaviour Patterns

### 24.1 `behaviour_patterns`

Important fields:

- `id`
- `organization_id`
- `trip_id`
- `pattern_type`
- `status`
- `severity`
- `started_at`
- `ended_at`
- `window_seconds`
- `event_count`
- `pattern_points`
- `rule_set_version_id`
- `pattern_rule_id`
- `created_at`
- `updated_at`

Pattern types:

- `REPEATED_SAME_BEHAVIOUR`
- `MIXED_AGGRESSIVE`

Statuses:

- `ACTIVE`
- `COMPLETED`
- `VOIDED`

### 24.2 `behaviour_pattern_events`

Links patterns to the events that caused them.

Important fields:

- `pattern_id`
- `event_id`
- `event_weight`
- `sequence_order`

The database must prevent the same event from being linked twice to the same pattern.

---

## 25. Trip Score State

### 25.1 `trip_score_states`

Stores the current score state.

Important fields:

- `trip_id`
- `initial_score`
- `current_score`
- `current_risk_level`
- `last_ledger_entry_id`
- `updated_at`
- `version_number`

Constraints:

```text
0 ≤ current_score ≤ 100
```

This table supports fast live reads.

The score ledger remains the authoritative explanation.

---

## 26. Score Ledger

### 26.1 `trip_score_ledger`

Stores every score change.

Important fields:

- `id`
- `trip_id`
- `entry_type`
- `source_event_id`
- `source_pattern_id`
- `reverses_entry_id`
- `rule_set_version_id`
- `penalty_rule_id`
- `previous_score`
- `points_delta`
- `new_score`
- `reason`
- `created_at`
- `created_by_user_id`

Entry types:

- `INITIAL`
- `EVENT_PENALTY`
- `PATTERN_PENALTY`
- `MANUAL_ADJUSTMENT`
- `REVERSAL`

Rules:

- `INITIAL` creates the score of 100.
- Event penalty references one event.
- Pattern penalty references one pattern.
- Reversal references the entry being reversed.
- An event or pattern should not create duplicate active penalty entries.
- The ledger should not be edited destructively.

Example:

| Entry | Previous | Change | New |
|---|---:|---:|---:|
| Initial | 100 | 0 | 100 |
| Harsh braking | 100 | -4 | 96 |
| Overspeeding | 96 | -2 | 94 |
| Pattern | 94 | -8 | 86 |

---

## 27. Risk History

### 27.1 `trip_risk_history`

Stores risk transitions.

Important fields:

- `id`
- `trip_id`
- `previous_risk_level`
- `new_risk_level`
- `score_at_transition`
- `risk_band_id`
- `triggering_ledger_entry_id`
- `changed_at`

This supports:

- Risk timeline
- Alert deduplication
- Explainability
- Live dashboard recovery

---

## 28. Alerts

### 28.1 `alerts`

Important fields:

- `id`
- `organization_id`
- `trip_id`
- `driver_id`
- `vehicle_id`
- `device_id`
- `alert_type`
- `priority`
- `status`
- `deduplication_key`
- `title`
- `message`
- `source_event_id`
- `source_pattern_id`
- `source_risk_history_id`
- `created_at`
- `read_at`
- `read_by_user_id`
- `acknowledged_at`
- `acknowledged_by_user_id`
- `resolved_at`
- `resolved_by_user_id`
- `resolution_note`

Alert types may include:

- `SEVERE_EVENT`
- `AGGRESSIVE_PATTERN`
- `HIGH_RISK_TRANSITION`
- `DEVICE_OFFLINE`
- `DEVICE_RESTORED`
- `HIGH_IMPACT_REQUIRES_VERIFICATION`

Priorities:

- `INFO`
- `WARNING`
- `CRITICAL`

Statuses:

- `UNREAD`
- `READ`
- `ACKNOWLEDGED`
- `RESOLVED`

The `deduplication_key` prevents repeated alerts for one continuing condition.

---

## 29. Device Connection History

### 29.1 `device_connection_history`

Stores device status changes.

Important fields:

- `id`
- `device_id`
- `trip_id`
- `previous_status`
- `new_status`
- `changed_at`
- `last_telemetry_at`
- `reason`

This supports the timeline:

```text
ONLINE
    ↓
DELAYED
    ↓
OFFLINE
    ↓
ONLINE
```

Offline status must not be labelled as an accident.

---

## 30. Trip Summary

### 30.1 `trip_summaries`

Stores finalized trip results.

Important fields:

- `trip_id`
- `duration_seconds`
- `estimated_distance_km`
- `average_speed_kmh`
- `maximum_speed_kmh`
- `overspeed_duration_seconds`
- `total_event_count`
- `harsh_braking_count`
- `sudden_acceleration_count`
- `overspeed_count`
- `sharp_turn_count`
- `pattern_count`
- `final_score`
- `final_risk_level`
- `data_quality_level`
- `assessment_confidence`
- `primary_concern_code`
- `primary_concern_text`
- `recommendation_code`
- `recommendation_text`
- `eco_indicator`
- `finalized_at`
- `finalization_version`

The summary is created when the trip is finalized.

Recommendations must be rule-based in the MVP.

The system must not store a fabricated exact fuel-waste value.

---

## 31. Trip Behaviour Metrics

### 31.1 `trip_behaviour_metrics`

Stores normalized trip metrics.

Important fields:

- `trip_id`
- `event_type`
- `event_count`
- `events_per_100_km`
- `events_per_hour`
- `total_duration_seconds`
- `maximum_severity`
- `calculated_at`

Normalized metrics are more useful than raw counts when comparing trips of different lengths.

Example:

```text
2 harsh-braking events in 5 km
```

is not equivalent to:

```text
2 harsh-braking events in 200 km
```

---

## 32. Driver Performance Snapshots

### 32.1 `driver_performance_snapshots`

Stores calculated driver performance at a point in time.

Important fields:

- `id`
- `driver_id`
- `organization_id`
- `calculated_at`
- `overall_score`
- `risk_level`
- `trend`
- `valid_trip_count`
- `latest_trip_id`
- `primary_concern_code`
- `primary_concern_text`
- `confidence_level`
- `calculation_version`

The initial driver score uses the latest five eligible official trips.

Suggested weights:

| Position | Weight |
|---|---:|
| Most recent | 5 |
| Second | 4 |
| Third | 3 |
| Fourth | 2 |
| Fifth | 1 |

Eligibility requirements may include:

- Trip mode is `OFFICIAL`
- Status is `COMPLETED`
- Data quality meets the minimum
- Trip duration and distance satisfy the assessment rule
- Trip has not been excluded by review

Test trips must never affect this snapshot.

---

## 33. Driver Behaviour Metrics

### 33.1 `driver_behaviour_metrics`

Stores aggregated behaviour rates.

Important fields:

- `driver_performance_snapshot_id`
- `event_type`
- `total_event_count`
- `events_per_100_km`
- `events_per_hour`
- `weighted_severity_points`

This table supports driver-profile behaviour summaries.

---

## 34. Driver Notes and Reviews

### 34.1 `driver_notes`

Important fields:

- `id`
- `driver_id`
- `created_by_user_id`
- `note_text`
- `created_at`
- `updated_at`

### 34.2 `trip_reviews`

Important fields:

- `id`
- `trip_id`
- `reviewed_by_user_id`
- `review_status`
- `review_note`
- `exclude_from_driver_analytics`
- `created_at`
- `updated_at`

Review statuses may include:

- `PENDING`
- `REVIEWED`
- `DISPUTED`
- `RESOLVED`

A reviewed event should normally be voided through controlled event logic rather than deleting telemetry evidence.

---

## 35. Simulation

### 35.1 `simulation_scenarios`

Stores available scenarios.

Important fields:

- `id`
- `scenario_code`
- `name`
- `description`
- `estimated_duration_seconds`
- `scenario_version`
- `scenario_definition`
- `enabled`
- `created_at`

`scenario_definition` may use `JSONB`.

Required scenarios include:

- `NORMAL_DRIVING`
- `HARSH_BRAKING`
- `SUDDEN_ACCELERATION`
- `OVERSPEEDING`
- `SHARP_TURNING`
- `REPEATED_AGGRESSIVE_PATTERN`
- `CONNECTION_LOSS`
- `FULL_PITCH_DEMO`

### 35.2 `simulation_runs`

Important fields:

- `id`
- `organization_id`
- `scenario_id`
- `trip_id`
- `device_id`
- `status`
- `random_seed`
- `packet_interval_ms`
- `started_by_user_id`
- `started_at`
- `paused_at`
- `completed_at`
- `failed_at`
- `failure_reason`
- `current_step`
- `created_at`

Statuses:

- `STOPPED`
- `RUNNING`
- `PAUSED`
- `COMPLETED`
- `FAILED`

The simulation run controls packet generation.

Generated packets still pass through the normal telemetry API.

---

## 36. Monitoring Settings

### 36.1 `monitoring_settings`

Stores organization-level operational settings.

Important fields:

- `organization_id`
- `device_delayed_after_seconds`
- `device_offline_after_seconds`
- `live_telemetry_window_seconds`
- `websocket_heartbeat_seconds`
- `telemetry_retention_days`
- `created_at`
- `updated_at`

These settings are not event thresholds.

Behaviour thresholds belong to rule-set versions.

---

## 37. Audit Logs

### 37.1 `audit_logs`

Important fields:

- `id`
- `organization_id`
- `user_id`
- `action`
- `target_type`
- `target_id`
- `request_id`
- `ip_address`
- `metadata`
- `created_at`

Audited actions may include:

- Login
- Driver creation
- Vehicle creation
- Device registration
- Device credential rotation
- Device assignment
- Trip start
- Trip end
- Rule activation
- Event voiding
- Score adjustment
- Alert acknowledgement

Audit records should not contain plaintext passwords or API keys.

---

## 38. Idempotency

### 38.1 `idempotency_keys`

Used for retry-safe manager actions.

Important fields:

- `id`
- `organization_id`
- `idempotency_key`
- `request_method`
- `request_path`
- `request_hash`
- `response_status`
- `response_body`
- `created_at`
- `expires_at`

Useful for:

- Starting a trip
- Ending a trip
- Starting simulation
- Other important repeatable POST actions

Device packet idempotency primarily uses device packet identity.

---

## 39. Processing Attempts

### 39.1 `telemetry_processing_attempts`

Stores telemetry retry history.

Important fields:

- `id`
- `telemetry_id`
- `attempt_number`
- `started_at`
- `completed_at`
- `status`
- `error_code`
- `error_message`

This allows failed processing to be diagnosed without overwriting the original raw packet.

---

## 40. Recommended Views

Views may simplify read-only application queries.

### 40.1 `active_trip_overview`

Combines:

- Trip
- Driver
- Vehicle
- Device
- Latest telemetry
- Current score
- Current risk
- Device status

### 40.2 `completed_trip_overview`

Combines:

- Trip
- Driver
- Vehicle
- Final summary
- Data quality

### 40.3 `driver_current_performance`

Returns the latest valid performance snapshot per driver.

### 40.4 `unresolved_alert_overview`

Returns unread, acknowledged or unresolved alerts with trip context.

Views must not contain hidden business logic that differs from backend rules.

---

## 41. Recommended Indexes

Important indexes include:

### Identity and ownership

- `users(organization_id, email)`
- `drivers(organization_id, employee_code)`
- `vehicles(organization_id, registration_number)`
- `devices(organization_id, device_code)`

### Active relationships

- Active device assignment by vehicle
- Active device assignment by device
- Active trip by driver
- Active trip by device assignment

### Telemetry

- `telemetry_records(device_id, server_received_at DESC)`
- `telemetry_records(trip_id, server_received_at)`
- Unique packet identity
- `telemetry_records(processing_status, server_received_at)`

### Events

- `driving_events(trip_id, started_at)`
- `driving_events(trip_id, event_type)`
- `driving_events(status, started_at)`

### Patterns

- `behaviour_patterns(trip_id, started_at)`

### Scores

- `trip_score_ledger(trip_id, created_at)`
- Unique active event penalty
- Unique active pattern penalty

### Alerts

- `alerts(organization_id, status, created_at DESC)`
- `alerts(trip_id, created_at)`
- Deduplication key for unresolved continuing alerts

### Driver analytics

- `driver_performance_snapshots(driver_id, calculated_at DESC)`

---

## 42. Check Constraints

Examples include:

### Scores

```text
initial_score between 0 and 100
current_score between 0 and 100
new_score between 0 and 100
```

### Coordinates

```text
latitude between -90 and 90
longitude between -180 and 180
```

### Speed and durations

```text
speed_kmh >= 0
duration >= 0
end_time >= start_time
```

### Assignments

```text
unassigned_at is null
or
unassigned_at >= assigned_at
```

### Trips

```text
end_time is null
or
end_time >= start_time
```

### Risk bands

```text
minimum_score <= maximum_score
```

### Rule versions

Only validated versions may be activated.

---

## 43. Foreign-Key Deletion Behaviour

Deletion rules must preserve historical evidence.

Recommended behaviour:

### Organization-owned operational records

Normally use restricted deletion or soft status changes.

### Drivers, vehicles and devices

Do not delete when historical trips exist.

Use statuses such as:

- `INACTIVE`
- `RETIRED`
- `DISABLED`

### Trips

Do not cascade-delete telemetry, events, score history or summaries through normal application actions.

### Event evidence

Deleting raw telemetry should not be a normal operation.

### User references

When legally and operationally acceptable, preserve the user reference.

Otherwise, anonymization should be deliberate rather than accidental cascade deletion.

---

## 44. Soft Deletion and Status Changes

Not every table requires a generic `deleted_at`.

For core reference entities, status fields are preferred.

Examples:

```text
Driver → INACTIVE
Vehicle → RETIRED
Device → DISABLED
Rule version → RETIRED
```

Derived records should use domain-specific states:

```text
Event → VOIDED
Alert → RESOLVED
Trip → CANCELLED
```

This is more meaningful than hiding every record with generic soft deletion.

---

## 45. Transaction Requirements

### 45.1 Start trip

One transaction should:

- Validate active relationships
- Lock conflicting active resources where necessary
- Create trip
- Create trip live state
- Create initial score state
- Create initial score-ledger entry
- Create initial risk state
- Create audit record

### 45.2 Process telemetry

One controlled transaction may:

- Insert raw telemetry
- Update latest state
- Update detector state
- Create or update event
- Create pattern
- Add ledger entry
- Update trip score
- Add risk transition
- Create alert

WebSocket publication occurs only after commit.

### 45.3 End trip

One controlled workflow should:

- Mark trip as finalizing
- Close active events
- Finalize patterns
- Validate score ledger
- Calculate summary
- Calculate data quality
- Mark completed
- Create audit record

Long calculations may be divided carefully, but partial finalization must remain detectable.

---

## 46. Concurrency Control

Possible concurrency risks include:

- Two requests start trips for the same driver.
- Two telemetry packets process simultaneously.
- The same packet is retried.
- Two workers create the same offline alert.
- Two event updates apply the same score penalty.

Controls may include:

- Partial unique indexes
- Row-level locks
- Transaction isolation
- Optimistic version columns
- Idempotency keys
- Unique score-source constraints
- Alert deduplication keys

Application checks alone are not sufficient for critical uniqueness rules.

---

## 47. Test and Official Data Queries

Official analytics queries must include explicit eligibility rules.

Conceptually:

```text
trip_mode = OFFICIAL
AND status = COMPLETED
AND data quality is eligible
AND trip review does not exclude analytics
```

They must not rely only on:

```text
source_type != SIMULATOR
```

because a test trip could contain replay or hardware data.

The trip mode is the main official-versus-test decision.

Telemetry source provides additional evidence and traceability.

---

## 48. Data Retention

For the pitching MVP, raw telemetry may be retained completely.

Future retention may include:

- Full-resolution recent telemetry
- Downsampled long-term telemetry
- Preserved event evidence
- Preserved summaries
- Preserved audit history

Retention jobs must not delete telemetry still required by:

- Event evidence
- Trip disputes
- Demonstration records
- Required audits

---

## 49. Database Migration Strategy

All schema changes must use Alembic migrations.

Migration groups may include:

1. Foundation tables
2. Rule configuration
3. Trips and telemetry
4. Events, patterns and scoring
5. Alerts, summaries and analytics
6. Simulation and operational tables

The deployment process is:

```text
Create empty PostgreSQL database
    ↓
Set DATABASE_URL
    ↓
Run Alembic upgrade
    ↓
Run seed script
    ↓
Start backend
```

Do not manually create production tables through a graphical interface.

---

## 50. Seed Data

Development seed data should include:

- Demo organization
- Admin user
- Fleet manager
- Demo driver
- Demo vehicle
- Simulator device
- Active device assignment
- Active rule set and version
- Rule thresholds
- Severity bands
- Penalties
- Risk bands
- Monitoring settings
- Simulation scenarios

The seed script must not contain real production passwords.

Development credentials should be replaceable through environment variables.

---

## 51. Database Backup

The pitch database must support:

- Backup
- Restore
- Clean demo reset

A pitch reset process may:

1. Stop simulation.
2. End or remove previous test-run data in a controlled environment.
3. Restore a clean demo backup or reseed.
4. Start services.
5. Run health checks.
6. Run the full scenario.

Backup files must not be committed to Git.

---

## 52. Entity Relationship Summary

```text
Organization
├── Users
├── Drivers
├── Vehicles
├── Devices
├── Rule Sets
├── Trips
└── Alerts

Device
    ↓
Device Assignment
    ↓
Vehicle

Driver
    ↓
Trip
    ↓
Device Assignment
    ├── Vehicle
    └── Device

Trip
├── Telemetry
├── Detection States
├── Driving Events
│   └── Event Evidence
├── Behaviour Patterns
│   └── Pattern Events
├── Score Ledger
├── Risk History
├── Alerts
├── Data Quality
└── Trip Summary

Eligible Official Trips
    ↓
Driver Performance Snapshot
    ↓
Driver Behaviour Metrics
```

---

## 53. Database Restrictions

The implementation must not:

- Allow React to connect directly to PostgreSQL
- Store plaintext passwords
- Store plaintext device API keys when hashing is possible
- Delete historical trips through routine entity deletion
- Mix test trips into official analytics
- Create score changes without ledger entries
- Create official events from hardware flags alone
- Overwrite activated rule versions
- Recalculate completed trips silently with newer rules
- Publish WebSocket updates before transaction commit
- Depend only on application code for critical active-trip uniqueness
- Store exact fuel-waste claims without reliable measurements
- Treat device offline state as an accident
- Insert simulation events directly

---

## 54. Database Acceptance Criteria

The database design is accepted when:

- All organization-owned entities are scoped correctly.
- Drivers, vehicles and devices are separate entities.
- Device assignment history is preserved.
- Trips reference the applicable device assignment and rule version.
- Only one active trip is allowed per driver and assigned vehicle/device context.
- Raw telemetry stores source and processing status.
- Duplicate packet identity is supported.
- Hardware flags are separated from official events.
- Rule thresholds and penalties are versioned.
- Continuous occurrences create one event.
- Events link to supporting telemetry.
- Patterns link to confirmed events.
- Every score change exists in an append-only ledger.
- Risk transitions are preserved.
- Alerts have deduplication and lifecycle states.
- Test trips are excluded from official analytics.
- Trip data quality is stored.
- Trip summaries are finalized and explainable.
- Driver performance uses eligible official trips only.
- Simulation runs are linked to test trips and simulator devices.
- Audit records preserve important administrative actions.
- Constraints and indexes protect critical integrity.
- Alembic can create the complete schema from an empty PostgreSQL database.