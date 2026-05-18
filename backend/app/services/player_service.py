# ==================================================================
# PLAYER SERVICE
# ==================================================================

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile, User
from app.schemas.player import AttributeProfile, PlayerProfileResponse

# Service PlayerService (Business Logic for Player Profile Retrieval)
class PlayerService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Function (get_profile) to retrieve the player's profile & inventory
    async def get_profile(self, player: PlayerProfile) -> PlayerProfileResponse:
        user = await self._db.scalar(select(User).where(User.id == player.user_id))

        # Retrieve (Player Attributes & Inventory)
        attr_rows = (
            await self._db.scalars(
                select(PlayerAttribute)
                .where(PlayerAttribute.player_id == player.id)
                .options(selectinload(PlayerAttribute.attribute))
            )
        ).all()

        # Retrieve (Inventory for Material Balances)
        inv_rows = (
            await self._db.scalars(
                select(PlayerInventory)
                .where(PlayerInventory.player_id == player.id)
                .options(selectinload(PlayerInventory.attribute))
            )
        ).all()

        # Create a mapping of attribute_id to quantity for quick lookup
        inv_by_attr: dict[int, int] = {row.attribute_id: row.quantity for row in inv_rows}

        attributes = [
            AttributeProfile(
                code=pa.attribute.code,
                name=pa.attribute.name,
                level=pa.level,
                xp_current=pa.xp_current,
                xp_to_next=pa.xp_to_next,
                material_name=pa.attribute.material_name,
                material_balance=inv_by_attr.get(pa.attribute_id, 0),
            )
            for pa in sorted(attr_rows, key=lambda x: x.attribute_id)
        ]
        
        # Return the full player profile response
        return PlayerProfileResponse(
            username=user.username,
            prestige_count=player.prestige_count,
            attributes=attributes,
        )
