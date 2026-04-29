# ==================================================================
# ACTIVITY SERVICE 
# ==================================================================

import random
import uuid
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, RateLimitError
from app.models.activity import ActivityLog, PlayerConsumable
from app.models.catalog import Attribute, BuffType, ConsumableType
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile
from app.models.prestige import PlayerBuff
from app.schemas.activity import ActivityLogRequest, ActivityLogResponse, LevelUpInfo
from app.services.reward_service import RewardService
from app.services.streak_service import StreakService

# Constants for rate limiting and overcharge logic
_RATE_LIMIT_COUNT = 10
_RATE_LIMIT_WINDOW = timedelta(hours=1)
_OVERCHARGE_CODE = "OVERCHARGE_CHIP"
_STABILITY_CODE = "STABILITY_POTION"
_DROP_RATE_OVERCHARGE = 0.05   
_DROP_RATE_STABILITY = 0.10    

# Service ActivityService (Business Logic)
class ActivityService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def log_activity(
        self,
        player: PlayerProfile,
        request: ActivityLogRequest,
    ) -> ActivityLogResponse:
        await self._enforce_rate_limit(player.id)

        attr = await self._get_attribute(request.attribute_code)
        player_attr = await self._get_player_attribute(player.id, attr.id)
        overcharge_mult, overcharge_active = await self._get_overcharge(player.id)
        xp_bonus_pct = await self._get_xp_bonus(player.id, attr.id)

        xp_earned = RewardService.calculate_xp(
            request.duration_minutes, xp_bonus_pct, overcharge_mult
        )
        material_earned = RewardService.calculate_materials(
            request.duration_minutes,
            player.global_material_bonus,
            player_attr.material_bonus,
        )

        today = date.today()

        # Create the activity log entry before applying rewards
        log_entry = ActivityLog(
            player_id=player.id,
            attribute_id=attr.id,
            description=request.description,
            duration_minutes=request.duration_minutes,
            xp_earned=xp_earned,
            material_earned=material_earned,
            overcharge_active=overcharge_active,
            activity_date=today,
        )
        self._db.add(log_entry)
        await self._db.flush() 

        # Apply rewards and update player state
        new_xp, new_level, new_xp_to_next, leveled_up = await self._update_attribute_xp(
            player_attr, xp_earned
        )

        # Update inventory with materials earned
        new_balance = await self._update_inventory(player.id, attr.id, material_earned)

        # Update streak and check for breaks/shields
        streak_broken, shield_used, new_streak = await self._update_streak(player, today)

        # Attempt consumable drop
        dropped = await self._try_drop_consumable(player.id)

        await self._db.commit()

        #  # Construct response with all relevant info for frontend display
        return ActivityLogResponse(
            activity_id=log_entry.id,
            attribute_code=attr.code,
            material_name=attr.material_name,
            xp_earned=xp_earned,
            material_earned=material_earned,
            new_attribute_level=new_level,
            new_attribute_xp=new_xp,
            xp_to_next_level=new_xp_to_next,
            level_up=LevelUpInfo(occurred=leveled_up, new_level=new_level),
            streak_current=new_streak,
            streak_broken=streak_broken,
            streak_shield_used=shield_used,
            material_balance=new_balance,
            overcharge_was_active=overcharge_active,
            dropped_consumable=dropped,
        )

    # Helper (Rate Limiting)
    async def _enforce_rate_limit(self, player_id: uuid.UUID) -> None:
        window_start = datetime.now(timezone.utc) - _RATE_LIMIT_WINDOW
        count = await self._db.scalar(
            select(func.count(ActivityLog.id)).where(
                ActivityLog.player_id == player_id,
                ActivityLog.logged_at >= window_start,
            )
        )
        if count and count >= _RATE_LIMIT_COUNT:
            raise RateLimitError()

    # Helper (Data Access - Attribute)
    async def _get_attribute(self, code: str) -> Attribute:
        attr = await self._db.scalar(
            select(Attribute).where(Attribute.code == code)
        )
        if not attr:
            raise NotFoundError(f"Attribute '{code}'")
        return attr

    # Helper (Data Access - Player Attribute)
    async def _get_player_attribute(
        self, player_id: uuid.UUID, attribute_id: int
    ) -> PlayerAttribute:
        result = await self._db.execute(
            select(PlayerAttribute).where(
                PlayerAttribute.player_id == player_id,
                PlayerAttribute.attribute_id == attribute_id,
            )
        )
        return result.scalar_one()

    # Helper (Overcharge Logic)
    async def _get_overcharge(self, player_id: uuid.UUID) -> tuple:
        from decimal import Decimal

        now = datetime.now(timezone.utc)
        consumable = await self._db.scalar(
            select(ConsumableType).where(ConsumableType.code == _OVERCHARGE_CODE)
        )
        if not consumable:
            return Decimal("1.0"), False

        from app.models.activity import PlayerActiveEffect

        active = await self._db.scalar(
            select(PlayerActiveEffect).where(
                PlayerActiveEffect.player_id == player_id,
                PlayerActiveEffect.consumable_type_id == consumable.id,
                PlayerActiveEffect.expires_at > now,
            )
        )
        if active:
            return active.multiplier, True
        return Decimal("1.0"), False

    # Helper (XP Bonus Calculation)
    async def _get_xp_bonus(self, player_id: uuid.UUID, attribute_id: int):
        from decimal import Decimal

        result = await self._db.scalar(
            select(PlayerBuff.total_bonus)
            .join(BuffType, BuffType.id == PlayerBuff.buff_type_id)
            .where(
                PlayerBuff.player_id == player_id,
                BuffType.target_type == "XP",
                BuffType.attribute_id == attribute_id,
            )
        )
        return result or Decimal("0.00")

    # Helper (Apply XP & Handle Level-Ups)
    async def _update_attribute_xp(
        self, player_attr: PlayerAttribute, xp_earned: int
    ) -> tuple[int, int, int, bool]:

        new_xp, new_level, new_xp_to_next, leveled_up = RewardService.apply_xp_to_attribute(
            player_attr.xp_current, player_attr.level, xp_earned
        )
        player_attr.xp_current = new_xp
        player_attr.level = new_level
        player_attr.xp_to_next = new_xp_to_next
        return new_xp, new_level, new_xp_to_next, leveled_up

    # Helper (Update Inventory with Materials Earned)
    async def _update_inventory(
        self, player_id: uuid.UUID, attribute_id: int, amount: int
    ) -> int:

        result = await self._db.execute(
            select(PlayerInventory)
            .where(
                PlayerInventory.player_id == player_id,
                PlayerInventory.attribute_id == attribute_id,
            )
            .with_for_update()
        )
        inventory = result.scalar_one()
        inventory.quantity += amount
        return inventory.quantity

    # Helper (Update Streak & Handle Breaks/Shields)
    async def _update_streak(
        self, player: PlayerProfile, today: date
    ) -> tuple[bool, bool, int]:
        
        locked = await self._db.execute(
            select(PlayerProfile)
            .where(PlayerProfile.id == player.id)
            .with_for_update()
        )
        profile = locked.scalar_one()

        update = StreakService.compute(
            profile.streak_last_date, profile.streak_current, profile.streak_max, today
        )

        if update.already_logged_today:
            return False, False, profile.streak_current

        shield_used = False

        if update.was_broken and StreakService.can_shield_protect(update.missed_days):
            shield_used = await self._try_consume_shield(player.id)

        if shield_used:
            final = StreakService.apply_shield(profile.streak_current, profile.streak_max)
        else:
            final = update

        profile.streak_current = final.new_streak
        profile.streak_max = final.new_max
        profile.streak_last_date = today

        return update.was_broken and not shield_used, shield_used, final.new_streak

    # Helper (Consume Shield if Available)
    async def _try_consume_shield(self, player_id: uuid.UUID) -> bool:

        consumable_type = await self._db.scalar(
            select(ConsumableType).where(ConsumableType.code == "STABILITY_POTION")
        )
        if not consumable_type:
            return False

        result = await self._db.execute(
            select(PlayerConsumable)
            .where(
                PlayerConsumable.player_id == player_id,
                PlayerConsumable.consumable_type_id == consumable_type.id,
            )
            .with_for_update()
        )
        potion_slot = result.scalar_one_or_none()
        if not potion_slot or potion_slot.quantity < 1:
            return False

        potion_slot.quantity -= 1
        return True

    # Helper Attempt Consumable Drop After Activity
    async def _try_drop_consumable(self, player_id: uuid.UUID) -> str | None:

        roll = random.random()
        if roll < _DROP_RATE_OVERCHARGE:
            code = _OVERCHARGE_CODE
        elif roll < _DROP_RATE_OVERCHARGE + _DROP_RATE_STABILITY:
            code = _STABILITY_CODE
        else:
            return None

        ct = await self._db.scalar(
            select(ConsumableType).where(ConsumableType.code == code)
        )
        if not ct:
            return None

        result = await self._db.execute(
            select(PlayerConsumable)
            .where(
                PlayerConsumable.player_id == player_id,
                PlayerConsumable.consumable_type_id == ct.id,
            )
            .with_for_update()
        )
        slot = result.scalar_one_or_none()
        if not slot:
            return None

        slot.quantity += 1
        return ct.name
