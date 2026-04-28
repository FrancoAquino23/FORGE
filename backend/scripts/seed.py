# ==================================================================
# FORGE - DATABASE SEED SCRIPT
# ==================================================================

import asyncio
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal


# S.P.E.C.I.A.L. Attributes
ATTRIBUTES = [
    {"id": 1, "code": "S", "name": "Strength",     "material_name": "Acero de Damasco",      "icon_key": "attr_strength"},
    {"id": 2, "code": "P", "name": "Perception",   "material_name": "Lente de Cuarzo",        "icon_key": "attr_perception"},
    {"id": 3, "code": "E", "name": "Endurance",    "material_name": "Fibra de Carbono",       "icon_key": "attr_endurance"},
    {"id": 4, "code": "C", "name": "Charisma",     "material_name": "Cristal de Resonancia",  "icon_key": "attr_charisma"},
    {"id": 5, "code": "I", "name": "Intelligence", "material_name": "Esencia Binaria",        "icon_key": "attr_intelligence"},
    {"id": 6, "code": "A", "name": "Agility",      "material_name": "Catalizador Inercial",   "icon_key": "attr_agility"},
    {"id": 7, "code": "L", "name": "Luck",         "material_name": "Polvo de Estrellas",     "icon_key": "attr_luck"},
]

# Prestige Buff Catalog 
BUFF_TYPES = [
    # Material gain buffs
    {"id": 1,  "code": "MATERIAL_BONUS_S", "display_name": "+5% Acero de Damasco",     "target_type": "MATERIAL", "attribute_id": 1, "bonus_percent": Decimal("5.00")},
    {"id": 2,  "code": "MATERIAL_BONUS_P", "display_name": "+5% Lente de Cuarzo",      "target_type": "MATERIAL", "attribute_id": 2, "bonus_percent": Decimal("5.00")},
    {"id": 3,  "code": "MATERIAL_BONUS_E", "display_name": "+5% Fibra de Carbono",     "target_type": "MATERIAL", "attribute_id": 3, "bonus_percent": Decimal("5.00")},
    {"id": 4,  "code": "MATERIAL_BONUS_C", "display_name": "+5% Cristal de Resonancia","target_type": "MATERIAL", "attribute_id": 4, "bonus_percent": Decimal("5.00")},
    {"id": 5,  "code": "MATERIAL_BONUS_I", "display_name": "+5% Esencia Binaria",      "target_type": "MATERIAL", "attribute_id": 5, "bonus_percent": Decimal("5.00")},
    {"id": 6,  "code": "MATERIAL_BONUS_A", "display_name": "+5% Catalizador Inercial", "target_type": "MATERIAL", "attribute_id": 6, "bonus_percent": Decimal("5.00")},
    {"id": 7,  "code": "MATERIAL_BONUS_L", "display_name": "+5% Polvo de Estrellas",   "target_type": "MATERIAL", "attribute_id": 7, "bonus_percent": Decimal("5.00")},
    # XP gain buffs
    {"id": 8,  "code": "XP_BONUS_S", "display_name": "+5% XP en Strength",     "target_type": "XP", "attribute_id": 1, "bonus_percent": Decimal("5.00")},
    {"id": 9,  "code": "XP_BONUS_P", "display_name": "+5% XP en Perception",   "target_type": "XP", "attribute_id": 2, "bonus_percent": Decimal("5.00")},
    {"id": 10, "code": "XP_BONUS_E", "display_name": "+5% XP en Endurance",    "target_type": "XP", "attribute_id": 3, "bonus_percent": Decimal("5.00")},
    {"id": 11, "code": "XP_BONUS_C", "display_name": "+5% XP en Charisma",     "target_type": "XP", "attribute_id": 4, "bonus_percent": Decimal("5.00")},
    {"id": 12, "code": "XP_BONUS_I", "display_name": "+5% XP en Intelligence", "target_type": "XP", "attribute_id": 5, "bonus_percent": Decimal("5.00")},
    {"id": 13, "code": "XP_BONUS_A", "display_name": "+5% XP en Agility",      "target_type": "XP", "attribute_id": 6, "bonus_percent": Decimal("5.00")},
    {"id": 14, "code": "XP_BONUS_L", "display_name": "+5% XP en Luck",         "target_type": "XP", "attribute_id": 7, "bonus_percent": Decimal("5.00")},
]

# ── Forge Config
FORGE_CONFIG = {
    "id": 1,
    "base_cost": Decimal("8"),
    "poly_exponent": Decimal("1.2"),
    "growth_rate": Decimal("1.07"),
    "prestige_threshold_level": 10,
}

# Visual Tiers 
VISUAL_TIERS = [
    {"id": 1, "name": "Hierro Oxidado",    "unlock_level": 0,  "asset_key": "tier_iron"},
    {"id": 2, "name": "Acero Vivo",        "unlock_level": 3,  "asset_key": "tier_steel"},
    {"id": 3, "name": "Obsidiana Forjada", "unlock_level": 6,  "asset_key": "tier_obsidian"},
    {"id": 4, "name": "Cristal Arcano",    "unlock_level": 10, "asset_key": "tier_arcane"},
    {"id": 5, "name": "Llama Eterna",      "unlock_level": 20, "asset_key": "tier_eternal"},
    {"id": 6, "name": "Vacío Absoluto",    "unlock_level": 35, "asset_key": "tier_void"},
    {"id": 7, "name": "Singularidad",      "unlock_level": 50, "asset_key": "tier_singularity"},
]

# Forge Tier Recipes
FORGE_TIER_RECIPES = [
    # Early tier (levels 1–5): Strength 40%, Endurance 35%, Intelligence 25%
    {"tier_start": 1, "tier_end": 5,    "attribute_id": 1, "proportion": Decimal("0.4000")},
    {"tier_start": 1, "tier_end": 5,    "attribute_id": 3, "proportion": Decimal("0.3500")},
    {"tier_start": 1, "tier_end": 5,    "attribute_id": 5, "proportion": Decimal("0.2500")},
    # Mid tier (levels 6–10): S 25%, P 20%, E 25%, I 20%, A 10%
    {"tier_start": 6, "tier_end": 10,   "attribute_id": 1, "proportion": Decimal("0.2500")},
    {"tier_start": 6, "tier_end": 10,   "attribute_id": 2, "proportion": Decimal("0.2000")},
    {"tier_start": 6, "tier_end": 10,   "attribute_id": 3, "proportion": Decimal("0.2500")},
    {"tier_start": 6, "tier_end": 10,   "attribute_id": 5, "proportion": Decimal("0.2000")},
    {"tier_start": 6, "tier_end": 10,   "attribute_id": 6, "proportion": Decimal("0.1000")},
    # Late tier (levels 11+): all 7, Luck appears as rare catalyst
    {"tier_start": 11, "tier_end": None, "attribute_id": 1, "proportion": Decimal("0.2000")},
    {"tier_start": 11, "tier_end": None, "attribute_id": 2, "proportion": Decimal("0.1500")},
    {"tier_start": 11, "tier_end": None, "attribute_id": 3, "proportion": Decimal("0.2000")},
    {"tier_start": 11, "tier_end": None, "attribute_id": 4, "proportion": Decimal("0.1000")},
    {"tier_start": 11, "tier_end": None, "attribute_id": 5, "proportion": Decimal("0.1500")},
    {"tier_start": 11, "tier_end": None, "attribute_id": 6, "proportion": Decimal("0.1500")},
    {"tier_start": 11, "tier_end": None, "attribute_id": 7, "proportion": Decimal("0.0500")},
]

# Consumable Types
CONSUMABLE_TYPES = [
    {
        "id": 1,
        "code": "STABILITY_POTION",
        "name": "Pocion de Estabilidad",
        "description": "Protege tu racha diaria si fallas una mision. Uso instantaneo.",
        "effect_type": "STREAK_SHIELD",
        "effect_value": None,
        "effect_duration_hours": None,
    },
    {
        "id": 2,
        "code": "OVERCHARGE_CHIP",
        "name": "Chip de Sobrecarga",
        "description": "Duplica la ganancia de XP durante 2 horas.",
        "effect_type": "XP_MULTIPLIER",
        "effect_value": Decimal("2.00"),
        "effect_duration_hours": 2,
    },
]


# Seed runner
async def seed(session: AsyncSession) -> None:
    print("Seeding attributes...")
    for row in ATTRIBUTES:
        await session.execute(
            text(
                "INSERT INTO attributes (id, code, name, material_name, icon_key) "
                "VALUES (:id, :code, :name, :material_name, :icon_key) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            row,
        )
    # Prestige Buff Types
    print("Seeding buff_types...")
    for row in BUFF_TYPES:
        await session.execute(
            text(
                "INSERT INTO buff_types (id, code, display_name, target_type, attribute_id, bonus_percent) "
                "VALUES (:id, :code, :display_name, :target_type, :attribute_id, :bonus_percent) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            row,
        )
    # Forge Config (singleton)
    print("Seeding forge_config...")
    await session.execute(
        text(
            "INSERT INTO forge_config (id, base_cost, poly_exponent, growth_rate, prestige_threshold_level) "
            "VALUES (:id, :base_cost, :poly_exponent, :growth_rate, :prestige_threshold_level) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        FORGE_CONFIG,
    )
    # Visual Tiers
    print("Seeding visual_tiers...")
    for row in VISUAL_TIERS:
        await session.execute(
            text(
                "INSERT INTO visual_tiers (id, name, unlock_level, asset_key) "
                "VALUES (:id, :name, :unlock_level, :asset_key) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            row,
        )
    # Forge Tier Recipes
    print("Seeding forge_tier_recipes...")
    for row in FORGE_TIER_RECIPES:
        await session.execute(
            text(
                "INSERT INTO forge_tier_recipes (tier_start, tier_end, attribute_id, proportion) "
                "VALUES (:tier_start, :tier_end, :attribute_id, :proportion) "
                "ON CONFLICT ON CONSTRAINT uq_recipe_tier_attr DO NOTHING"
            ),
            row,
        )
    # Consumable Types
    print("Seeding consumable_types...")
    for row in CONSUMABLE_TYPES:
        await session.execute(
            text(
                "INSERT INTO consumable_types (id, code, name, description, effect_type, effect_value, effect_duration_hours) "
                "VALUES (:id, :code, :name, :description, :effect_type, :effect_value, :effect_duration_hours) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            row,
        )
    # Stage all changes
    await session.commit()
    print("Seed complete.")

# Entry point
async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed(session)

# Run the seed script
if __name__ == "__main__":
    asyncio.run(main())
