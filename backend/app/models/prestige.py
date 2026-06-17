# ==================================================================
# PRESTIGE MODELS
# ==================================================================

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

# Model PrestigeHistory (Milestones)
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
    sacrificed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
