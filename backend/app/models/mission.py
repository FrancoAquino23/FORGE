# ==================================================================
# MISSION MODELS
# ==================================================================

import uuid
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

# Model Mission (Daily & Weekly Tasks)
class Mission(Base):
    __tablename__ = "missions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'COMPLETED', 'EXPIRED', 'ABANDONED', 'PENDING')",
            name="valid_mission_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    objective_description: Mapped[str] = mapped_column(Text, nullable=False)
    target_attribute_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("attributes.id"), nullable=False
    )
    reward_material_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'ACTIVE'"),
        default="ACTIVE",
    )
    # Player-assigned category
    category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    generated_by_model: Mapped[str | None] = mapped_column(String(60))
    prompt_tokens_used: Mapped[int | None] = mapped_column(Integer)
    objective_type: Mapped[str] = mapped_column(String(30), nullable=False, default="LOG_COUNT")
    objective_target: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    target_attribute: Mapped["Attribute"] = relationship()  # type: ignore[name-defined]

# Model GmContextSnapshot (Game Master Context Snapshots)
class GmContextSnapshot(Base):
    __tablename__ = "gm_context_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
