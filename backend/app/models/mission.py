# ==================================================================
# MISSION MODELS
# ==================================================================

import uuid
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

# Model Checkpoint (Sub-task step for Main Quest / Side Quest missions)
class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), default=False
    )
    order_index: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

# Model Mission (Daily & Weekly Tasks)
class Mission(Base):
    __tablename__ = "missions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'COMPLETED', 'PENDING')",
            name="valid_mission_status",
        ),
        CheckConstraint(
            "threat_level IN (0, 1, 2)",
            name="valid_threat_level",
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
    objective_type: Mapped[str] = mapped_column(String(30), nullable=False, default="MANUAL")
    objective_target: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)
    threat_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("1"), default=1)
    target_attribute: Mapped["Attribute"] = relationship()  # type: ignore[name-defined]
    checkpoints: Mapped[list["Checkpoint"]] = relationship(
        "Checkpoint",
        order_by="Checkpoint.order_index",
        cascade="all, delete-orphan",
        lazy="raise",
    )

