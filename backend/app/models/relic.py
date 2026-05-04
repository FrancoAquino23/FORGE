# ==================================================================
# RELIC MODELS
# ==================================================================

import uuid
from sqlalchemy import CheckConstraint, ForeignKey, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

# Model for an enhancement item that boosts specific attributes. 
class Relic(Base):
    __tablename__ = "relics"
    __table_args__ = (
        UniqueConstraint("player_id", "attribute_code", name="uq_player_relic"),
        CheckConstraint("level BETWEEN 1 AND 10", name="relic_level_range"),
        CheckConstraint("attribute_code IN ('S','P','E','C','I','A')", name="valid_relic_attr"),
    )

    # Primary key and foreign key to the player profile
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Attribute code indicating which attribute the relic boosts
    attribute_code: Mapped[str] = mapped_column(String(1), nullable=False)
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    total_invested: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
