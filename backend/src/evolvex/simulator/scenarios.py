"""
Deterministic Simulation Scenario Definitions and Packet Generator.

Provides 6 pitch-ready driving scenarios:
1. NORMAL_CITY_DRIVING
2. HARSH_BRAKING_EVENT
3. SUDDEN_ACCELERATION_EVENT
4. OVERSPEEDING_SUSTAINED
5. SHARP_TURNING_EVENT
6. PITCH_DEMO_REPLAY
"""

import math
import random
from typing import Any


class ScenarioGenerator:
    """Generates telemetry packets for deterministic scenarios."""

    SCENARIOS: dict[str, dict[str, Any]] = {
        "NORMAL_CITY_DRIVING": {
            "code": "NORMAL_CITY_DRIVING",
            "name": "Normal City Driving",
            "description": "Smooth driving within speed limits without aggressive events.",
            "duration_seconds": 15,
        },
        "HARSH_BRAKING_EVENT": {
            "code": "HARSH_BRAKING_EVENT",
            "name": "Harsh Braking Event",
            "description": "Vehicle decelerates sharply from 55 to 20 km/h exceeding 3.5 m/s².",
            "duration_seconds": 12,
        },
        "SUDDEN_ACCELERATION_EVENT": {
            "code": "SUDDEN_ACCELERATION_EVENT",
            "name": "Sudden Acceleration Event",
            "description": "Vehicle accelerates rapidly from low speed (accel > 3.5 m/s²).",
            "duration_seconds": 12,
        },
        "OVERSPEEDING_SUSTAINED": {
            "code": "OVERSPEEDING_SUSTAINED",
            "name": "Sustained Overspeeding Event",
            "description": "Vehicle exceeds speed limit reaching 75 km/h for > 4 seconds.",
            "duration_seconds": 15,
        },
        "SHARP_TURNING_EVENT": {
            "code": "SHARP_TURNING_EVENT",
            "name": "Sharp Turning Event",
            "description": "Vehicle turns aggressively at 35 km/h (lat accel > 4.5 m/s²).",
            "duration_seconds": 12,
        },
        "PITCH_DEMO_REPLAY": {
            "code": "PITCH_DEMO_REPLAY",
            "name": "Complete Pitch Demo Replay",
            "description": (
                "Full pitch demo sequence combining normal driving, overspeeding, "
                "harsh braking, sharp turning, and sudden acceleration."
            ),
            "duration_seconds": 35,
        },
    }

    @classmethod
    def list_scenarios(cls) -> list[dict[str, Any]]:
        """Return available scenario metadata."""
        return list(cls.SCENARIOS.values())

    @classmethod
    def generate_packets(
        cls,
        scenario_code: str,
        boot_id: str,
        seed: int = 2026,
        start_seq: int = 1,
        start_time_ms: int = 0,
        base_lat: float = 6.9271,
        base_lng: float = 79.8612,
    ) -> list[dict[str, Any]]:
        """
        Generate deterministic telemetry packets for the given scenario code using fixed seed.
        """
        rng = random.Random(seed)
        packets: list[dict[str, Any]] = []

        # Sequence of phases per scenario
        if scenario_code == "NORMAL_CITY_DRIVING":
            phases = [("NORMAL", 15)]
        elif scenario_code == "HARSH_BRAKING_EVENT":
            phases = [("NORMAL", 3), ("HARSH_BRAKE", 4), ("RECOVERY", 5)]
        elif scenario_code == "SUDDEN_ACCELERATION_EVENT":
            phases = [("NORMAL", 2), ("SUDDEN_ACCEL", 4), ("RECOVERY", 6)]
        elif scenario_code == "OVERSPEEDING_SUSTAINED":
            phases = [("NORMAL", 3), ("OVERSPEED", 6), ("RECOVERY", 6)]
        elif scenario_code == "SHARP_TURNING_EVENT":
            phases = [("NORMAL", 3), ("SHARP_TURN", 4), ("RECOVERY", 5)]
        elif scenario_code == "PITCH_DEMO_REPLAY":
            phases = [
                ("NORMAL", 5),
                ("OVERSPEED", 6),
                ("HARSH_BRAKE", 5),
                ("SHARP_TURN", 5),
                ("SUDDEN_ACCEL", 5),
                ("NORMAL", 9),
            ]
        else:
            phases = [("NORMAL", 10)]

        curr_seq = start_seq
        curr_time_ms = start_time_ms
        curr_lat = base_lat
        curr_lng = base_lng
        curr_speed = 40.0

        for phase_type, duration_sec in phases:
            for _ in range(duration_sec):
                # Calculate physics per phase
                if phase_type == "NORMAL":
                    target_speed = 45.0 + rng.uniform(-3.0, 3.0)
                    accel_fwd = (target_speed - curr_speed) / 3.6 + rng.uniform(-0.3, 0.3)
                    accel_lat = rng.uniform(-0.5, 0.5)
                    yaw_rate = rng.uniform(-3.0, 3.0)
                    curr_speed += (target_speed - curr_speed) * 0.3
                elif phase_type == "HARSH_BRAKE":
                    accel_fwd = -4.2 + rng.uniform(-0.5, 0.2)
                    curr_speed = max(15.0, curr_speed + accel_fwd * 3.6)
                    accel_lat = rng.uniform(-0.8, 0.8)
                    yaw_rate = rng.uniform(-5.0, 5.0)
                elif phase_type == "SUDDEN_ACCEL":
                    accel_fwd = 4.5 + rng.uniform(-0.2, 0.5)
                    curr_speed = min(70.0, curr_speed + accel_fwd * 3.6)
                    accel_lat = rng.uniform(-0.5, 0.5)
                    yaw_rate = rng.uniform(-3.0, 3.0)
                elif phase_type == "OVERSPEED":
                    target_speed = 78.0 + rng.uniform(-2.0, 3.0)
                    accel_fwd = (target_speed - curr_speed) / 3.6 + rng.uniform(-0.2, 0.3)
                    curr_speed += (target_speed - curr_speed) * 0.4
                    accel_lat = rng.uniform(-0.6, 0.6)
                    yaw_rate = rng.uniform(-4.0, 4.0)
                elif phase_type == "SHARP_TURN":
                    target_speed = 38.0
                    accel_fwd = rng.uniform(-0.5, 0.5)
                    accel_lat = 4.8 + rng.uniform(-0.3, 0.6)
                    yaw_rate = 25.0 + rng.uniform(-2.0, 5.0)
                    curr_speed += (target_speed - curr_speed) * 0.2
                else:  # RECOVERY
                    target_speed = 42.0
                    accel_fwd = (target_speed - curr_speed) / 3.6
                    accel_lat = rng.uniform(-0.4, 0.4)
                    yaw_rate = rng.uniform(-2.0, 2.0)
                    curr_speed += (target_speed - curr_speed) * 0.3

                # GPS linear movement forward
                dist_m = (curr_speed / 3.6) * 1.0
                curr_lat += (dist_m / 111111.0) * math.cos(math.radians(curr_lng))
                curr_lng += dist_m / 111111.0

                packet = {
                    "boot_id": boot_id,
                    "sequence_number": curr_seq,
                    "timestamp": curr_time_ms,
                    "lat": round(curr_lat, 6),
                    "lng": round(curr_lng, 6),
                    "speed_kmh": round(max(0.0, curr_speed), 1),
                    "accel_fwd": round(accel_fwd, 2),
                    "accel_lat": round(accel_lat, 2),
                    "yaw_rate": round(yaw_rate, 2),
                    "gps_valid": True,
                    "harsh_brake": accel_fwd < -3.0,
                    "harsh_accel": accel_fwd > 3.0,
                    "harsh_corner": abs(accel_lat) > 4.0 or abs(yaw_rate) > 20.0,
                    "overspeed": curr_speed > 65.0,
                }
                packets.append(packet)

                curr_seq += 1
                curr_time_ms += 1000

        return packets
