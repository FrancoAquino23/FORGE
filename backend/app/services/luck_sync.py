# ==================================================================
# LUCK SYNC — Passive Luck level helper
# ==================================================================

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.catalog import Attribute
from app.models.player import PlayerAttribute

# Helper function to sync Luck's level after any change to ordinary attributes
async def sync_luck_level(db: AsyncSession, player_id: uuid.UUID) -> None:
    rows = (
        await db.scalars(
            select(PlayerAttribute)
            .join(Attribute, Attribute.id == PlayerAttribute.attribute_id)
            .where(PlayerAttribute.player_id == player_id)
            .options(selectinload(PlayerAttribute.attribute))
        )
    ).all()

    ordinary_levels = [pa.level for pa in rows if pa.attribute.code != "L"]
    luck_pa = next((pa for pa in rows if pa.attribute.code == "L"), None)

    if luck_pa and ordinary_levels:
        new_level = min(ordinary_levels)
        if luck_pa.level != new_level:
            luck_pa.level = new_level
            luck_pa.xp_current = 0
            luck_pa.xp_to_next = 0
