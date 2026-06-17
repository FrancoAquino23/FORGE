# ==================================================================
# PRESTIGE SERVICE
# ==================================================================

import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import InsufficientMaterialsError, PrestigeNotAvailableError
from app.models.catalog import Attribute, ForgeConfig
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile
from app.models.prestige import PrestigeHistory
from app.models.relic import Relic
from app.models.skill_tree import PlayerSkillNode
from app.schemas.prestige import PrestigeStatusResponse, PrestigeUpResponse
from app.services.reward_service import RewardService
from app.services.skill_tree_service import total_pp_for_level

# Default prestige threshold
_DEFAULT_THRESHOLD = 10

# Ordinary attribute codes
_ORDINARY_CODES = frozenset({"S", "P", "E", "C", "I", "A"})

# Function to compute material cost for next prestige level
def prestige_material_cost(current_prestige: int) -> int:
    """Return the per-material cost to advance from current_prestige to current_prestige+1."""
    target = current_prestige + 1
    if target == 50:
        return 500_000
    if target <= 2:
        return target * 100
    if target <= 5:
        return 500 + (target - 3) * 200
    if target <= 9:
        return 1_500 + (target - 6) * 500
    if target <= 19:
        return 4_000 + (target - 10) * 1_000
    if target <= 34:
        return 16_000 + (target - 20) * 2_500
    if target <= 49:
        return 60_000 + (target - 35) * 10_000
    return 200_000 + (target - 49) * 10_000

# Function to compute points per prestige level
def prestige_points_for_prestige(prestige_number: int) -> int:
    """PP awarded for completing the given prestige number (1-indexed)."""
    if prestige_number <= 9:
        return 2
    if prestige_number <= 19:
        return 3
    if prestige_number <= 34:
        return 4
    return 5


# Model PrestigeService (Business Logic for Prestige Sacrifice)
class PrestigeService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Returns full prestige status for the Prestige view
    async def get_status(self, player: PlayerProfile) -> PrestigeStatusResponse:
        config = await self._db.scalar(select(ForgeConfig))
        threshold = config.prestige_threshold_level if config else _DEFAULT_THRESHOLD

        return PrestigeStatusResponse(
            prestige_count=player.prestige_count,
            threshold_level=threshold,
            material_cost=prestige_material_cost(player.prestige_count),
            prestige_points_total=player.prestige_points_total,
            prestige_points_available=player.prestige_points_available,
        )

    # Helper to perform a full prestige-up (Verify - Reset - Reward PP)
    async def prestige_up(self, player: PlayerProfile) -> PrestigeUpResponse:
        config = await self._db.scalar(select(ForgeConfig))
        threshold = config.prestige_threshold_level if config else _DEFAULT_THRESHOLD

        # Load all catalog attributes and all player attributes (locked)
        all_attrs = (await self._db.scalars(select(Attribute))).all()
        all_player_attrs = (
            await self._db.execute(
                select(PlayerAttribute)
                .where(PlayerAttribute.player_id == player.id)
                .with_for_update()
            )
        ).scalars().all()
        pa_by_attr_id = {pa.attribute_id: pa for pa in all_player_attrs}

        # Verify every attribute is at the threshold
        for a in all_attrs:
            pa = pa_by_attr_id.get(a.id)
            if not pa or pa.level < threshold:
                raise PrestigeNotAvailableError(threshold)

        # Read early_start_boost level before any resets
        early_boost_level = (
            await self._db.scalar(
                select(PlayerSkillNode.current_level).where(
                    PlayerSkillNode.player_id == player.id,
                    PlayerSkillNode.node_id == "early_start_boost",
                )
            )
        ) or 0

        # Verify and lock ordinary-material inventories for the material gate
        material_cost = prestige_material_cost(player.prestige_count)
        ordinary_attr_ids = [a.id for a in all_attrs if a.code in _ORDINARY_CODES]
        ordinary_inventories = (
            await self._db.execute(
                select(PlayerInventory)
                .where(
                    PlayerInventory.player_id == player.id,
                    PlayerInventory.attribute_id.in_(ordinary_attr_ids),
                )
                .with_for_update()
            )
        ).scalars().all()

        for inv in ordinary_inventories:
            if inv.quantity < material_cost:
                raise InsufficientMaterialsError(
                    f"Need {material_cost} of each ordinary material to prestige"
                )

        # Reset ALL attributes to level 1
        reset_codes: list[str] = []
        for a in all_attrs:
            pa = pa_by_attr_id.get(a.id)
            if pa:
                pa.level = 1
                pa.xp_current = 0
                pa.xp_to_next = RewardService.xp_for_level(1)
                reset_codes.append(a.code)

        # Apply early_start_boost to randomly selected ordinary attributes
        if early_boost_level > 0:
            ordinary_attrs = [a for a in all_attrs if a.code in _ORDINARY_CODES]
            num_boosted = early_boost_level
            start_level = 3 if early_boost_level == 3 else 2
            chosen = random.sample(ordinary_attrs, min(num_boosted, len(ordinary_attrs)))
            for a in chosen:
                pa = pa_by_attr_id.get(a.id)
                if pa:
                    pa.level = start_level
                    pa.xp_current = 0
                    pa.xp_to_next = RewardService.xp_for_level(start_level)

        # Consume ordinary materials
        for inv in ordinary_inventories:
            inv.quantity -= material_cost

        # Delete ALL relics (Fresh Start Reset)
        all_relics = (
            await self._db.execute(
                select(Relic).where(Relic.player_id == player.id).with_for_update()
            )
        ).scalars().all()
        for relic in all_relics:
            await self._db.delete(relic)

        # Reset skill tree nodes and compute full points per prestige refund
        all_nodes = (
            await self._db.execute(
                select(PlayerSkillNode)
                .where(PlayerSkillNode.player_id == player.id)
                .with_for_update()
            )
        ).scalars().all()
        pp_refunded = sum(total_pp_for_level(n.current_level) for n in all_nodes)
        for n in all_nodes:
            n.current_level = 0

        prestige_number = player.prestige_count + 1
        self._db.add(
            PrestigeHistory(
                player_id=player.id,
                prestige_number=prestige_number,
                artifact_level_reached=threshold,
            )
        )

        locked_profile = (
            await self._db.execute(
                select(PlayerProfile).where(PlayerProfile.id == player.id).with_for_update()
            )
        ).scalar_one()
        locked_profile.prestige_count += 1

        # Award points per prestige for this prestige
        pp_earned = prestige_points_for_prestige(prestige_number)
        locked_profile.prestige_points_total += pp_earned
        locked_profile.prestige_points_available += pp_refunded + pp_earned

        await self._db.commit()

        return PrestigeUpResponse(
            prestige_number=prestige_number,
            attributes_reset=reset_codes,
            pp_earned=pp_earned,
        )
