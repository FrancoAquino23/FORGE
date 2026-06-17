# ==================================================================
# CATALOG MODELS
# ==================================================================

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

# Model Attribute (Attributes & Materials)
class Attribute(Base):
    __tablename__ = "attributes"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(1), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    material_name: Mapped[str] = mapped_column(String(50), nullable=False)
    icon_key: Mapped[str | None] = mapped_column(String(80))

# Model ForgeConfig (Mechanics)
class ForgeConfig(Base):
    __tablename__ = "forge_config"
    __table_args__ = (CheckConstraint("id = 1", name="single_row"),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    base_cost: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, default=Decimal("8")
    )
    poly_exponent: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False, default=Decimal("1.2")
    )
    growth_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False, default=Decimal("1.07")
    )
    prestige_threshold_level: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=10
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Model VisualTier (Cosmetic)
class VisualTier(Base):
    __tablename__ = "visual_tiers"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    unlock_level: Mapped[int] = mapped_column(SmallInteger, unique=True, nullable=False)
    asset_key: Mapped[str] = mapped_column(String(100), nullable=False)

# Model ForgeTierRecipe (Recipes)
class ForgeTierRecipe(Base):
    __tablename__ = "forge_tier_recipes"
    __table_args__ = (
        UniqueConstraint("tier_start", "attribute_id", name="uq_recipe_tier_attr"),
    )

    tier_start: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    tier_end: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    attribute_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("attributes.id"), primary_key=True
    )
    proportion: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    attribute: Mapped["Attribute"] = relationship()
