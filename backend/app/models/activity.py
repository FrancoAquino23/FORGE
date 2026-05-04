# ==================================================================
# ACTIVITY MODELS
# ==================================================================

import uuid
from datetime import date, datetime
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

# Model ActivityLog (Activity Tracking & Analytics)
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    # Primary key and foreign keys
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("player_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Attribute ID to link activity to a specific S.P.E.C.I.A.L. attribute
    attribute_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("attributes.id"), nullable=False
    )
    # Activity details
    description: Mapped[str | None] = mapped_column(String(500))
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    material_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    overcharge_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    attribute: Mapped["Attribute"] = relationship()  # type: ignore[name-defined]
