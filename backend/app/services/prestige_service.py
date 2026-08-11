# ==================================================================
# PRESTIGE SERVICE
# ==================================================================

import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import InsufficientMaterialsError, PrestigeNotAvailableError
from app.models.catalog import Attribute
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile
from app.models.prestige import PrestigeHistory
from app.models.relic import Relic
from app.models.skill_tree import PlayerSkillNode
from app.schemas.prestige import PrestigeStatusResponse, PrestigeUpResponse
from app.constants import ORDINARY_CODES as _ORDINARY_CODES, MAX_ATTRIBUTE_LEVEL as _MAX_ATTRIBUTE_LEVEL
from app.services.achievement_service import AchievementService
from app.services.reward_service import RewardService, xp_scale_factor
from app.services.skill_tree_service import get_node_level, node_bonus, pp_node_bonus, total_pp_for_level


# Function to compute Stardust cost for next prestige level
def prestige_stardust_cost(current_prestige: int) -> int:
    target = current_prestige + 1
    if target <= 10: return 1_000 + (target - 1) * 500
    if target <= 25: return 10_000 + (target - 11) * 1_000
    if target <= 40: return 35_000 + (target - 26) * 2_000
    return 75_000 + (target - 41) * 2_500

# Function to compute points per prestige level
def prestige_points_for_prestige(prestige_number: int) -> int:
    if prestige_number <= 25: return 2
    if prestige_number <= 40: return 3
    return 4


# Model PrestigeService (Business Logic for Prestige Sacrifice)
class PrestigeService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Returns full prestige status for the Prestige view
    async def get_status(self, player: PlayerProfile) -> PrestigeStatusResponse:
        threshold = _MAX_ATTRIBUTE_LEVEL

        return PrestigeStatusResponse(
            prestige_count=player.prestige_count,
            threshold_level=threshold,
            stardust_cost=prestige_stardust_cost(player.prestige_count),
            prestige_points_total=player.prestige_points_total,
            prestige_points_available=player.prestige_points_available,
        )

    # Helper to perform a full prestige-up (Verify - Reset - Reward PP)
    async def prestige_up(self, player: PlayerProfile) -> PrestigeUpResponse:
        threshold = _MAX_ATTRIBUTE_LEVEL

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

        # Read skill node levels before any resets
        null_cycle_level = await get_node_level(self._db, player.id, "early_start_boost")
        material_compression_level = await get_node_level(self._db, player.id, "material_compression")
        relic_head_start_level = await get_node_level(self._db, player.id, "relic_head_start")
        pp_bonus_level = await get_node_level(self._db, player.id, "pp_bonus")

        # Compute Stardust cost (material_compression discount applies)
        raw_stardust_cost = prestige_stardust_cost(player.prestige_count)
        if material_compression_level > 0:
            discount = node_bonus(material_compression_level)
            stardust_cost = max(1, round(raw_stardust_cost * (1.0 - discount)))
        else:
            stardust_cost = raw_stardust_cost

        # Lock and verify Stardust inventory
        luck_attr = next((a for a in all_attrs if a.code == "L"), None)
        if not luck_attr:
            raise PrestigeNotAvailableError(threshold)
        stardust_inv = (
            await self._db.execute(
                select(PlayerInventory)
                .where(
                    PlayerInventory.player_id == player.id,
                    PlayerInventory.attribute_id == luck_attr.id,
                )
                .with_for_update()
            )
        ).scalar_one()
        if stardust_inv.quantity < stardust_cost:
            raise InsufficientMaterialsError(
                f"Need {stardust_cost} Stardust to prestige"
            )

        # Lock ordinary inventories for reset
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

        # Reset ALL attributes to level 1 (XP threshold scales with new prestige count)
        prestige_number = player.prestige_count + 1
        xp_discount = node_bonus(null_cycle_level) if null_cycle_level > 0 else 0.0
        xp_to_next_l1 = max(1, round(
            RewardService.xp_for_level(1) * xp_scale_factor(prestige_number) * (1.0 - xp_discount)
        ))
        reset_codes: list[str] = []
        for a in all_attrs:
            pa = pa_by_attr_id.get(a.id)
            if pa:
                pa.level = 1
                pa.xp_current = 0
                pa.xp_to_next = xp_to_next_l1
                reset_codes.append(a.code)

        # Deduct Stardust and reset all ordinary material inventories to 0
        stardust_inv.quantity -= stardust_cost
        for inv in ordinary_inventories:
            inv.quantity = 0

        # Delete ALL relics (Fresh Start Reset)
        all_relics = (
            await self._db.execute(
                select(Relic).where(Relic.player_id == player.id).with_for_update()
            )
        ).scalars().all()
        existing_codes = [r.attribute_code for r in all_relics]
        for relic in all_relics:
            await self._db.delete(relic)

        if relic_head_start_level > 0:
            num_saved = relic_head_start_level
            head_start_relic_level = 2 if relic_head_start_level == 3 else 1
            chosen_codes = random.sample(list(_ORDINARY_CODES), num_saved)
            for code in chosen_codes:
                self._db.add(Relic(
                    player_id=player.id,
                    attribute_code=code,
                    level=head_start_relic_level,
                ))

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

        # Award points per prestige for this prestige (+ Noble Legacy bonus if active)
        pp_earned = prestige_points_for_prestige(prestige_number)
        if pp_bonus_level > 0:
            pp_earned += pp_node_bonus(pp_bonus_level)
        locked_profile.prestige_points_total += pp_earned
        locked_profile.prestige_points_available += pp_refunded + pp_earned

        # Check and unlock achievements
        from app.schemas.mission import AchievementUnlocked
        unlocked_defs = await AchievementService(self._db).check_and_unlock(locked_profile)
        newly_unlocked = [
            AchievementUnlocked(code=a.code, title=a.title, description=a.description, flavor=a.flavor)
            for a in unlocked_defs
        ]

        await self._db.commit()

        return PrestigeUpResponse(
            prestige_number=prestige_number,
            attributes_reset=reset_codes,
            pp_earned=pp_earned,
            newly_unlocked=newly_unlocked,
        )
