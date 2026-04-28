# ==================================================================
# PRESTIGE MODELS
# ==================================================================

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, SmallInteger, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

# Model PrestigeHistory (Buffs & Milestones)
class PrestigeHistory(Base):
    __tablename__ = "prestige_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("player_profiles.id"), nullable=False
    )
    prestige_number: Mapped[int] = mapped_column(Integer, nullable=False)
    artifact_level_reached: Mapped[int] = mapped_column(Integer, nullable=False)
    buff_type_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("buff_types.id"), nullable=False
    )
    sacrificed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    buff_type: Mapped["BuffType"] = relationship()  # type: ignore[name-defined]

# Model PlayerBuff (Active Buffs)
class PlayerBuff(Base):
    __tablename__ = "player_buffs"
    __table_args__ = (
        UniqueConstraint("player_id", "buff_type_id", name="uq_player_buff"),
        CheckConstraint("stack_count > 0", name="positive_stack"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    buff_type_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("buff_types.id"), nullable=False
    )
    stack_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_bonus: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    player: Mapped["PlayerProfile"] = relationship(back_populates="buffs")  # type: ignore[name-defined]
    buff_type: Mapped["BuffType"] = relationship()  # type: ignore[name-defined]
