"""
EvolveX Idempotent Development & Pitch Demo Seed Script.

Creates demo organization, users, driver, vehicle, simulator device,
active assignment, and default active rule set version
per Milestone 5 specifications.
"""

import asyncio
import hashlib
import os
from datetime import UTC, datetime

from sqlalchemy import select, update

from evolvex.core.database import close_engine, get_session_factory
from evolvex.core.logging import logger
from evolvex.db.models.trip import Trip, TripStatus
from evolvex.db.models import (
    AccelerationRule,
    AssignmentStatus,
    Device,
    DeviceAdminStatus,
    DeviceAssignment,
    DeviceType,
    Driver,
    DriverStatus,
    EventPenalty,
    EventSeverity,
    EventType,
    Organization,
    OrganizationStatus,
    OverspeedRule,
    RiskBand,
    RiskLevel,
    RuleSet,
    RuleSetVersion,
    RuleSetVersionStatus,
    TurningRule,
    User,
    UserRole,
    UserStatus,
    Vehicle,
    VehicleStatus,
)


def hash_password(password: str) -> str:
    """Create SHA-256 hash for user passwords in seed environment."""
    return hashlib.sha256(password.encode()).hexdigest()


def hash_api_key(api_key: str) -> str:
    """Create SHA-256 hash for device API keys."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def run_seed() -> dict:
    """Execute idempotent seed process for development & pitch demo."""
    logger.info("Executing EvolveX pitch demo seed process...")
    session_factory = get_session_factory()

    admin_email = os.getenv("DEMO_ADMIN_EMAIL", "admin@evolvex.demo")
    admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "EvolveXPass123!")
    manager_email = os.getenv("DEMO_MANAGER_EMAIL", "manager@evolvex.demo")
    manager_password = os.getenv("DEMO_MANAGER_PASSWORD", "EvolveXPass123!")
    sim_key = os.getenv("SIMULATOR_DEVICE_KEY", "demo-simulator-secret-key-2026")

    async with session_factory() as session:
        # 0. Clean up any leftover active trips from previous runs/tests
        await session.execute(
            update(Trip)
            .where(Trip.status == TripStatus.ACTIVE)
            .values(status=TripStatus.COMPLETED, end_time=datetime.now(UTC))
        )
        await session.flush()

        # 1. Organization
        org_code = "ORG-PITCH-001"
        org_stmt = select(Organization).where(Organization.organization_code == org_code)
        org = (await session.execute(org_stmt)).scalar_one_or_none()

        if not org:
            org = Organization(
                name="EvolveX Pitch Logistics",
                organization_code=org_code,
                status=OrganizationStatus.ACTIVE,
                timezone="UTC",
            )
            session.add(org)
            await session.flush()
            logger.info("Created Demo Organization: %s", org.name)

        # 2. Users
        # Admin User
        admin_stmt = select(User).where(User.email == admin_email)
        admin_user = (await session.execute(admin_stmt)).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                organization_id=org.id,
                email=admin_email,
                password_hash=hash_password(admin_password),
                full_name="Pitch Administrator",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
            session.add(admin_user)
            logger.info("Created Demo Administrator: %s", admin_email)

        # Fleet Manager User
        mgr_stmt = select(User).where(User.email == manager_email)
        mgr_user = (await session.execute(mgr_stmt)).scalar_one_or_none()
        if not mgr_user:
            mgr_user = User(
                organization_id=org.id,
                email=manager_email,
                password_hash=hash_password(manager_password),
                full_name="Pitch Manager",
                role=UserRole.FLEET_MANAGER,
                status=UserStatus.ACTIVE,
            )
            session.add(mgr_user)
            logger.info("Created Demo Fleet Manager: %s", manager_email)

        await session.flush()

        # 3. Drivers
        demo_drivers = [
            {
                "employee_code": "DRV-DEMO-001",
                "first_name": "John",
                "last_name": "Doe",
                "license_number": "LIC-PITCH-999",
                "email": "john.doe@evolvex.demo",
                "phone": "+94771234567"
            },
            {
                "employee_code": "DRV-DEMO-002",
                "first_name": "Sarah",
                "last_name": "Jenkins",
                "license_number": "LIC-PITCH-888",
                "email": "sarah.j@evolvex.demo",
                "phone": "+94778888888"
            },
            {
                "employee_code": "DRV-DEMO-003",
                "first_name": "Michael",
                "last_name": "Chen",
                "license_number": "LIC-PITCH-777",
                "email": "m.chen@evolvex.demo",
                "phone": "+94777777777"
            }
        ]
        
        driver_ids = []
        for d_info in demo_drivers:
            dr_stmt = select(Driver).where(Driver.employee_code == d_info["employee_code"])
            driver = (await session.execute(dr_stmt)).scalar_one_or_none()
            if not driver:
                driver = Driver(
                    organization_id=org.id,
                    employee_code=d_info["employee_code"],
                    first_name=d_info["first_name"],
                    last_name=d_info["last_name"],
                    license_number=d_info["license_number"],
                    status=DriverStatus.ACTIVE,
                    phone=d_info["phone"],
                    email=d_info["email"],
                )
                session.add(driver)
                await session.flush()
                logger.info("Created Demo Driver: %s %s", driver.first_name, driver.last_name)
            driver_ids.append(driver.id)

        # 4. Vehicles, Simulator Devices & Assignments
        demo_assets = [
            {
                "vehicle_code": "VEH-DEMO-001",
                "registration_number": "EV-2026-SL",
                "make": "Toyota",
                "model": "Hilux",
                "device_code": "SIM-DEVICE-001",
                "display_name": "Virtual Telemetry Simulator 1"
            },
            {
                "vehicle_code": "VEH-DEMO-002",
                "registration_number": "EV-2026-NY",
                "make": "Ford",
                "model": "F-150 Lightning",
                "device_code": "SIM-DEVICE-002",
                "display_name": "Virtual Telemetry Simulator 2"
            },
            {
                "vehicle_code": "VEH-DEMO-003",
                "registration_number": "EV-2026-TX",
                "make": "Tesla",
                "model": "Cybertruck",
                "device_code": "SIM-DEVICE-003",
                "display_name": "Virtual Telemetry Simulator 3"
            }
        ]

        for asset in demo_assets:
            # Vehicle
            vh_stmt = select(Vehicle).where(Vehicle.vehicle_code == asset["vehicle_code"])
            vehicle = (await session.execute(vh_stmt)).scalar_one_or_none()
            if not vehicle:
                vehicle = Vehicle(
                    organization_id=org.id,
                    registration_number=asset["registration_number"],
                    vehicle_code=asset["vehicle_code"],
                    make=asset["make"],
                    model=asset["model"],
                    manufacture_year=2024,
                    default_speed_limit_kmh=60.0,
                    status=VehicleStatus.ACTIVE,
                )
                session.add(vehicle)
                await session.flush()
                logger.info("Created Demo Vehicle: %s", vehicle.registration_number)

            # Device
            dev_stmt = select(Device).where(Device.device_code == asset["device_code"])
            device = (await session.execute(dev_stmt)).scalar_one_or_none()
            if not device:
                device = Device(
                    organization_id=org.id,
                    device_code=asset["device_code"],
                    display_name=asset["display_name"],
                    device_type=DeviceType.SIMULATOR,
                    administrative_status=DeviceAdminStatus.TESTING,
                    api_key_hash=hash_api_key(sim_key),
                    firmware_version="sim-1.0.0",
                    telemetry_schema_version="1.0",
                )
                session.add(device)
                await session.flush()
                logger.info("Created Simulator Device: %s", device.device_code)

            # Assignment
            asgn_stmt = select(DeviceAssignment).where(
                DeviceAssignment.device_id == device.id,
                DeviceAssignment.vehicle_id == vehicle.id,
                DeviceAssignment.status == AssignmentStatus.ACTIVE,
            )
            assignment = (await session.execute(asgn_stmt)).scalar_one_or_none()
            if not assignment:
                assignment = DeviceAssignment(
                    organization_id=org.id,
                    device_id=device.id,
                    vehicle_id=vehicle.id,
                    status=AssignmentStatus.ACTIVE,
                    assigned_at=datetime.now(UTC),
                    notes=f"Pitch demo assignment for {device.device_code}",
                )
                session.add(assignment)
                await session.flush()
                logger.info(
                    "Created Active Assignment: %s -> %s",
                    device.device_code,
                    vehicle.registration_number,
                )

        # 7. Rule Set & Active Rule Version
        rs_stmt = select(RuleSet).where(
            RuleSet.organization_id == org.id,
            RuleSet.name == "Standard Safety Rule Set",
        )
        rule_set = (await session.execute(rs_stmt)).scalar_one_or_none()
        if not rule_set:
            rule_set = RuleSet(
                organization_id=org.id,
                name="Standard Safety Rule Set",
                description="Default driving behaviour rule thresholds",
                status="ACTIVE",
            )
            session.add(rule_set)
            await session.flush()

        rv_stmt = select(RuleSetVersion).where(
            RuleSetVersion.rule_set_id == rule_set.id,
            RuleSetVersion.version_number == 1,
        )
        rule_version = (await session.execute(rv_stmt)).scalar_one_or_none()
        if not rule_version:
            rule_version = RuleSetVersion(
                rule_set_id=rule_set.id,
                version_number=1,
                status=RuleSetVersionStatus.ACTIVE,
                activated_at=datetime.now(UTC),
            )
            session.add(rule_version)
            await session.flush()

            # Add Acceleration Rules
            hb_rule = AccelerationRule(
                rule_set_version_id=rule_version.id,
                behaviour_type=EventType.HARSH_BRAKING,
                trigger_threshold_ms2=3.0,
                release_threshold_ms2=1.5,
                minimum_duration_ms=500,
                minimum_speed_kmh=5.0,
                cooldown_ms=1000,
            )
            sa_rule = AccelerationRule(
                rule_set_version_id=rule_version.id,
                behaviour_type=EventType.SUDDEN_ACCELERATION,
                trigger_threshold_ms2=3.0,
                release_threshold_ms2=1.5,
                minimum_duration_ms=500,
                minimum_speed_kmh=5.0,
                cooldown_ms=1000,
            )
            os_rule = OverspeedRule(
                rule_set_version_id=rule_version.id,
                tolerance_kmh=5.0,
                minimum_duration_ms=3000,
                release_margin_kmh=2.0,
                cooldown_ms=2000,
            )
            st_rule = TurningRule(
                rule_set_version_id=rule_version.id,
                lateral_acceleration_threshold_ms2=4.0,
                yaw_rate_threshold_deg_s=20.0,
                minimum_speed_kmh=10.0,
                minimum_duration_ms=500,
                release_lateral_threshold_ms2=2.0,
                release_yaw_threshold_deg_s=10.0,
                cooldown_ms=1000,
            )
            session.add_all([hb_rule, sa_rule, os_rule, st_rule])

            # Event Penalties
            p1 = EventPenalty(
                rule_set_version_id=rule_version.id,
                event_type=EventType.HARSH_BRAKING,
                severity=EventSeverity.MODERATE,
                points_delta=-4.0,
            )
            p2 = EventPenalty(
                rule_set_version_id=rule_version.id,
                event_type=EventType.SUDDEN_ACCELERATION,
                severity=EventSeverity.MODERATE,
                points_delta=-3.0,
            )
            p3 = EventPenalty(
                rule_set_version_id=rule_version.id,
                event_type=EventType.OVERSPEEDING,
                severity=EventSeverity.MODERATE,
                points_delta=-5.0,
            )
            p4 = EventPenalty(
                rule_set_version_id=rule_version.id,
                event_type=EventType.SHARP_TURNING,
                severity=EventSeverity.MODERATE,
                points_delta=-3.0,
            )
            session.add_all([p1, p2, p3, p4])

            # Risk Bands
            rb1 = RiskBand(
                rule_set_version_id=rule_version.id,
                risk_level=RiskLevel.LOW,
                minimum_score=80.0,
                maximum_score=100.0,
                priority_order=1,
            )
            rb2 = RiskBand(
                rule_set_version_id=rule_version.id,
                risk_level=RiskLevel.MEDIUM,
                minimum_score=60.0,
                maximum_score=79.9,
                priority_order=2,
            )
            rb3 = RiskBand(
                rule_set_version_id=rule_version.id,
                risk_level=RiskLevel.HIGH,
                minimum_score=0.0,
                maximum_score=59.9,
                priority_order=3,
            )
            session.add_all([rb1, rb2, rb3])

            await session.flush()
            logger.info("Created Active Rule Version #1 with default safety rules & penalties")

        await session.commit()
        logger.info("Seed process completed successfully!")

        return {
            "organization_id": str(org.id),
            "admin_email": admin_email,
            "manager_email": manager_email,
            "driver_id": str(driver.id),
            "vehicle_id": str(vehicle.id),
            "device_code": "SIM-DEVICE-001",
            "assignment_id": str(assignment.id),
            "rule_version_id": str(rule_version.id),
        }


async def main() -> None:
    try:
        await run_seed()
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(main())
