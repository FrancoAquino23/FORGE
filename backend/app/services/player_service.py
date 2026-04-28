# ==================================================================
# PLAYER SERVICE
# ==================================================================

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile, User
from app.schemas.player import AttributeProfile, PlayerProfileResponse


class PlayerService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def get_profile(self, player: PlayerProfile) -> PlayerProfileResponse:
        user = await self._db.scalar(select(User).where(User.id == player.user_id))

        attr_rows = (
            await self._db.scalars(
                select(PlayerAttribute)
                .where(PlayerAttribute.player_id == player.id)
                .options(selectinload(PlayerAttribute.attribute))
            )
        ).all()

        inv_rows = (
            await self._db.scalars(
                select(PlayerInventory)
                .where(PlayerInventory.player_id == player.id)
                .options(selectinload(PlayerInventory.attribute))
            )
        ).all()

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

        return PlayerProfileResponse(
            username=user.username,
            prestige_count=player.prestige_count,
            streak_current=player.streak_current,
            streak_max=player.streak_max,
            attributes=attributes,
        )
