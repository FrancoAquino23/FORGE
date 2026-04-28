# ==================================================================
# FORGE SERVICE
# ==================================================================

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientMaterialsError, NotFoundError
from app.models.catalog import Attribute
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile
from app.schemas.forge import ForgeUpgradeResponse
from app.services.reward_service import RewardService


class ForgeService:
    # Base cost for level 1 → 2; scales linearly: cost = BASE × current_level
    BASE_UPGRADE_COST = 25

    @staticmethod
    def attribute_upgrade_cost(current_level: int) -> int:
        """Materials needed to upgrade from current_level to current_level + 1."""
        return ForgeService.BASE_UPGRADE_COST * current_level

    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def upgrade_attribute(
        self,
        player: PlayerProfile,
        attribute_code: str,
    ) -> ForgeUpgradeResponse:
        attr = await self._get_attribute(attribute_code)
        player_attr, inventory = await self._lock_rows(player.id, attr.id)

        cost = ForgeService.attribute_upgrade_cost(player_attr.level)
        if inventory.quantity < cost:
            raise InsufficientMaterialsError(
                f"Need {cost} {attr.material_name}, have {inventory.quantity}"
            )

        from_level = player_attr.level
        inventory.quantity -= cost
        player_attr.level += 1
        player_attr.xp_current = 0
        player_attr.xp_to_next = RewardService.xp_for_level(player_attr.level)

        await self._db.commit()

        return ForgeUpgradeResponse(
            attribute_code=attr.code,
            from_level=from_level,
            to_level=player_attr.level,
            materials_spent=cost,
            material_name=attr.material_name,
            new_material_balance=inventory.quantity,
        )

    async def _get_attribute(self, code: str) -> Attribute:
        attr = await self._db.scalar(select(Attribute).where(Attribute.code == code))
        if not attr:
            raise NotFoundError(f"Attribute '{code}'")
        return attr

    async def _lock_rows(
        self,
        player_id: uuid.UUID,
        attribute_id: int,
    ) -> tuple[PlayerAttribute, PlayerInventory]:
        player_attr = (
            await self._db.execute(
                select(PlayerAttribute)
                .where(
                    PlayerAttribute.player_id == player_id,
                    PlayerAttribute.attribute_id == attribute_id,
                )
                .with_for_update()
            )
        ).scalar_one()

        inventory = (
            await self._db.execute(
                select(PlayerInventory)
                .where(
                    PlayerInventory.player_id == player_id,
                    PlayerInventory.attribute_id == attribute_id,
                )
                .with_for_update()
            )
        ).scalar_one()

        return player_attr, inventory
