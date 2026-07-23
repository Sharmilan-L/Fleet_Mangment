"""
User SQLAlchemy model.

Represents administrators and fleet managers as defined in docs/database-design.md Section 5.1.
A User belongs to an Organization via an organization_id foreign key.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from evolvex.db.base import Base, CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin


class UserRole(enum.StrEnum):
    """Permitted roles for a user."""

    ADMIN = "ADMIN"
    FLEET_MANAGER = "FLEET_MANAGER"


class UserStatus(enum.StrEnum):
    """Permitted statuses for a user."""

    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """
    User entity (Administrator or Fleet Manager).

    Database design reference: docs/database-design.md Section 5.1

    Fields
    ------
    id             : UUID primary key (from mixin)
    organization_id: Foreign key referencing organizations.id
    email          : Unique login email address
    password_hash  : Hashed password (never stored plain-text)
    full_name      : Full display name of the user
    role           : UserRole enum (ADMIN, FLEET_MANAGER)
    status         : UserStatus enum (ACTIVE, DISABLED)
    last_login_at  : Optional timestamp of most recent login (TIMESTAMPTZ)
    created_at     : Insertion timestamp (from mixin, TIMESTAMPTZ)
    updated_at     : Last update timestamp (from mixin, TIMESTAMPTZ)
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('ADMIN', 'FLEET_MANAGER')",
            name="role",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'DISABLED')",
            name="status",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization ownership foreign key",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique login email address",
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hashed user password",
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Full display name of the user",
    )

    role: Mapped[UserRole] = mapped_column(
        String(30),
        nullable=False,
        default=UserRole.FLEET_MANAGER,
        server_default=UserRole.FLEET_MANAGER.value,
        comment="User role (ADMIN or FLEET_MANAGER)",
    )

    status: Mapped[UserStatus] = mapped_column(
        String(20),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
        comment="Current user status (ACTIVE or DISABLED)",
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful login",
    )

    # Optional ORM relationship for navigation
    organization = relationship("Organization", backref="users", lazy="selectin")
