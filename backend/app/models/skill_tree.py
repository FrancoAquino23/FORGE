# ==================================================================
# SKILL TREE MODELS
# ==================================================================

import uuid
from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


# Model PlayerSkillNode (Prestige Skill Tree — per-player node investment)
class PlayerSkillNode(Base):
    __tablename__ = "player_skill_nodes"
    __table_args__ = (
        UniqueConstraint("player_id", "node_id", name="uq_player_skill_node"),
        CheckConstraint("current_level BETWEEN 0 AND 3", name="chk_skill_node_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_id: Mapped[str] = mapped_column(String(50), nullable=False)
    current_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
