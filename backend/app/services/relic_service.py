# ==================================================================
# RELIC SERVICE
# ==================================================================

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError
from app.models.catalog import Attribute
from app.models.player import PlayerInventory
from app.models.relic import Relic
from app.schemas.relic import RelicInfo, RelicListResponse, RelicUpgradeResponse
from app.constants import MAX_ATTRIBUTE_LEVEL as _MAX_LEVEL, ORDINARY_CODES_ORDERED
from app.services.reward_service import RewardService
from app.services.skill_tree_service import get_node_level, node_bonus

# Attribute codes
_UPGRADEABLE_CODES = (*ORDINARY_CODES_ORDERED, "L")

# Model RelicService (Handles relic-related operations)
class RelicService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def get_all(self, player_id: uuid.UUID) -> RelicListResponse:
        relics = await self._ensure_relics(player_id)

        all_attrs = (await self._db.scalars(select(Attribute))).all()
        attr_by_id = {a.id: a for a in all_attrs}
        attr_by_code = {a.code: a for a in all_attrs}

        inv_rows = (
            await self._db.scalars(
                select(PlayerInventory).where(PlayerInventory.player_id == player_id)
            )
        ).all()
        inventory_by_code = {
            attr_by_id[inv.attribute_id].code: inv.quantity for inv in inv_rows
        }

        discount_level = await get_node_level(self._db, player_id, "relic_cost_discount")

        result: list[RelicInfo] = []

        for relic in relics:
            code = relic.attribute_code
            balance = inventory_by_code.get(code, 0)
            cost = RewardService.upgrade_cost(relic.level) if relic.level < _MAX_LEVEL else None
            if cost is not None and discount_level > 0:
                cost = max(1, round(cost * (1.0 - node_bonus(discount_level))))
            can_upgrade = cost is not None and balance >= cost

            result.append(
                RelicInfo(
                    attribute_code=code,
                    attribute_name=attr_by_code[code].name,
                    level=relic.level,
                    total_invested=relic.total_invested,
                    bonus_pct=round(relic.level * RewardService.RELIC_BONUS_PER_LEVEL * 100),
                    upgrade_cost=cost,
                    can_upgrade=can_upgrade,
                    material_balance=balance,
                    is_luck=(code == "L"),
                )
            )

        return RelicListResponse(relics=result)

    # Helper method to handle relic upgrades
    async def upgrade(
        self, player_id: uuid.UUID, attribute_code: str
    ) -> RelicUpgradeResponse:
        relic = (
            await self._db.execute(
                select(Relic)
                .where(
                    Relic.player_id == player_id,
                    Relic.attribute_code == attribute_code,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

        if not relic:
            raise NotFoundError(f"Relic '{attribute_code}'")
        if relic.level >= _MAX_LEVEL:
            raise ConflictError("Relic is already at maximum level")

        base_cost = RewardService.upgrade_cost(relic.level)
        discount_level = await get_node_level(self._db, player_id, "relic_cost_discount")
        cost = max(1, round(base_cost * (1.0 - node_bonus(discount_level)))) if discount_level > 0 else base_cost

        attr = await self._db.scalar(
            select(Attribute).where(Attribute.code == attribute_code)
        )
        if not attr:
            raise NotFoundError(f"Attribute '{attribute_code}'")

        inventory = (
            await self._db.execute(
                select(PlayerInventory)
                .where(
                    PlayerInventory.player_id == player_id,
                    PlayerInventory.attribute_id == attr.id,
                )
                .with_for_update()
            )
        ).scalar_one()

        if inventory.quantity < cost:
            raise ConflictError(
                f"Insufficient materials: {inventory.quantity}/{cost} needed"
            )

        inventory.quantity -= cost
        relic.level += 1
        relic.total_invested += cost

        await self._db.commit()

        return RelicUpgradeResponse(
            attribute_code=attribute_code,
            new_level=relic.level,
            material_spent=cost,
            new_balance=inventory.quantity,
            new_bonus_pct=round(relic.level * RewardService.RELIC_BONUS_PER_LEVEL * 100),
        )

    # Helper method to ensure all relics exist for the player, creating any missing ones
    async def _ensure_relics(self, player_id: uuid.UUID) -> list[Relic]:
        existing = {
            r.attribute_code: r
            for r in (
                await self._db.scalars(
                    select(Relic).where(Relic.player_id == player_id)
                )
            ).all()
        }
        created = False
        for code in _UPGRADEABLE_CODES:
            if code not in existing:
                r = Relic(player_id=player_id, attribute_code=code, level=0, total_invested=0)
                self._db.add(r)
                existing[code] = r
                created = True
        if created:
            await self._db.commit()
        return [existing[code] for code in _UPGRADEABLE_CODES]
