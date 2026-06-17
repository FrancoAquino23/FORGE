# ==================================================================
# PLAYER MODELS
# ==================================================================

import uuid
from datetime import datetime
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    Boolean,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

# Model User (Authentication & Account Management)
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profile: Mapped["PlayerProfile"] = relationship(back_populates="user", uselist=False)

# Model PlayerProfile (Data)
class PlayerProfile(Base):
    __tablename__ = "player_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    prestige_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prestige_points_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prestige_points_available: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user: Mapped["User"] = relationship(back_populates="profile")
    attributes: Mapped[list["PlayerAttribute"]] = relationship(back_populates="player")
    inventory: Mapped[list["PlayerInventory"]] = relationship(back_populates="player")
    artifact: Mapped["Artifact"] = relationship(back_populates="player", uselist=False)  # type: ignore[name-defined]
# Model PlayerAttribute (Attributes & Progression)
class PlayerAttribute(Base):
    __tablename__ = "player_attributes"
    __table_args__ = (
        UniqueConstraint("player_id", "attribute_id", name="uq_player_attribute"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    attribute_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("attributes.id"), nullable=False
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    xp_current: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp_to_next: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    player: Mapped["PlayerProfile"] = relationship(back_populates="attributes")
    attribute: Mapped["Attribute"] = relationship()  # type: ignore[name-defined]

# Model PlayerInventory (Items & Resources)
class PlayerInventory(Base):
    __tablename__ = "player_inventory"
    __table_args__ = (
        UniqueConstraint("player_id", "attribute_id", name="uq_player_inventory"),
        CheckConstraint("quantity >= 0", name="non_negative_quantity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    attribute_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("attributes.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    player: Mapped["PlayerProfile"] = relationship(back_populates="inventory")
    attribute: Mapped["Attribute"] = relationship()  # type: ignore[name-defined]
