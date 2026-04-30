# ==================================================================
# ACTIVITY MODELS
# ==================================================================

import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

# Model ActivityLog (Activity Tracking & Analytics)
class ActivityLog(Base):
    __tablename__ = "activity_logs"

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
    description: Mapped[str | None] = mapped_column(String(500))
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    material_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    overcharge_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    attribute: Mapped["Attribute"] = relationship()  # type: ignore[name-defined]

# Model PlayerConsumable (Consumables & Effects)
class PlayerConsumable(Base):
    __tablename__ = "player_consumables"
    __table_args__ = (
        UniqueConstraint("player_id", "consumable_type_id", name="uq_player_consumable"),
        CheckConstraint("quantity >= 0", name="non_negative_consumable"),
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    consumable_type_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("consumable_types.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consumable_type: Mapped["ConsumableType"] = relationship()  # type: ignore[name-defined]

# Model PlayerActiveEffect (Active Effects & Buffs)
class PlayerActiveEffect(Base):
    __tablename__ = "player_active_effects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    consumable_type_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("consumable_types.id"), nullable=False
    )
    multiplier: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumable_type: Mapped["ConsumableType"] = relationship()  # type: ignore[name-defined]
