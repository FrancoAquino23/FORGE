# ==================================================================
# ARTIFACT MODELS
# ==================================================================

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, SmallInteger, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

# Model Artifact (Player Progression & Customization)
class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prestige_cycle: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_levels_forged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_visual_tier_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("visual_tiers.id"), nullable=True
    )
    next_forge_cost: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}' :: jsonb"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    player: Mapped["PlayerProfile"] = relationship(back_populates="artifact")  # type: ignore[name-defined]
    current_visual_tier: Mapped["VisualTier | None"] = relationship()  # type: ignore[name-defined]
    forge_history: Mapped[list["ForgeHistory"]] = relationship(back_populates="artifact")

# Model ForgeHistory (History & Analytics)
class ForgeHistory(Base):
    __tablename__ = "forge_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False
    )
    from_level: Mapped[int] = mapped_column(Integer, nullable=False)
    to_level: Mapped[int] = mapped_column(Integer, nullable=False)
    prestige_cycle: Mapped[int] = mapped_column(Integer, nullable=False)
    materials_spent: Mapped[dict] = mapped_column(JSONB, nullable=False)
    forged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    artifact: Mapped["Artifact"] = relationship(back_populates="forge_history")
