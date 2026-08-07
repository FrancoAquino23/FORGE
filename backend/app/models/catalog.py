# ==================================================================
# CATALOG MODELS
# ==================================================================

from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

# Model Attribute (Attributes & Materials)
class Attribute(Base):
    __tablename__ = "attributes"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(1), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    material_name: Mapped[str] = mapped_column(String(50), nullable=False)
    icon_key: Mapped[str | None] = mapped_column(String(80))

# Model VisualTier (Cosmetic)
class VisualTier(Base):
    __tablename__ = "visual_tiers"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    unlock_level: Mapped[int] = mapped_column(SmallInteger, unique=True, nullable=False)
    asset_key: Mapped[str] = mapped_column(String(100), nullable=False)
