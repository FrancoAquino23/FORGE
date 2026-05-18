# ==================================================================
# ACTIVITY SERVICE 
# ==================================================================

import uuid
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, RateLimitError
from app.models.activity import ActivityLog
from app.models.catalog import Attribute
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile
from app.models.relic import Relic
from app.schemas.activity import ActivityLogRequest, ActivityLogResponse, LevelUpInfo
from app.services.reward_service import RewardService

# Constants for rate limiting
_RATE_LIMIT_COUNT = 10
_RATE_LIMIT_WINDOW = timedelta(hours=1)

# Model ActivityService (Handles activity logging and related logic)
class ActivityService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Helper method to log an activity & handle all related updates (XP, materials)
    async def log_activity(
        self,
        player: PlayerProfile,
        request: ActivityLogRequest,
    ) -> ActivityLogResponse:
        await self._enforce_rate_limit(player.id)

        attr = await self._get_attribute(request.attribute_code)
        player_attr = await self._get_player_attribute(player.id, attr.id)
        relic_level = await self._get_relic_level(player.id, attr.code, player.prestige_count)

        xp_earned = RewardService.calculate_xp(relic_level, player.prestige_count)
        material_earned = RewardService.calculate_materials(relic_level, player.prestige_count)

        today = date.today()

        # Create the activity log entry before applying rewards
        log_entry = ActivityLog(
            player_id=player.id,
            attribute_id=attr.id,
            description=request.description,
            xp_earned=xp_earned,
            material_earned=material_earned,
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

        await self._db.commit()

        # Construct response with all relevant info for frontend display
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
            material_balance=new_balance,
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
        attr = await self._db.scalar(select(Attribute).where(Attribute.code == code))
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

    # Helper (Data Access - Relic Level)
    async def _get_relic_level(
        self, player_id: uuid.UUID, attr_code: str, prestige_count: int
    ) -> int:
        if attr_code == "L":
            return prestige_count
        result = await self._db.scalar(
            select(Relic.level).where(
                Relic.player_id == player_id,
                Relic.attribute_code == attr_code,
            )
        )
        return result or 0

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
