# ==================================================================
# PLAYER SERVICE
# ==================================================================

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.mission import Mission
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile, User
from app.schemas.player import AttributeProfile, PlayerProfileResponse, PlayerStatsResponse
from app.services.reward_service import RewardService

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
                xp_to_next=(
                    RewardService.xp_for_level(pa.level)
                    if pa.attribute.code != "L"
                    else 0
                ),
                material_name=pa.attribute.material_name,
                material_balance=inv_by_attr.get(pa.attribute_id, 0),
            )
            for pa in sorted(attr_rows, key=lambda x: x.attribute_id)
        ]
        
        # Return the full player profile response
        return PlayerProfileResponse(
            username=user.username,
            prestige_count=player.prestige_count,
            prestige_points_total=player.prestige_points_total,
            prestige_points_available=player.prestige_points_available,
            attributes=attributes,
        )

    # Helper to retrieve lifetime mission statistics
    async def get_stats(self, player: PlayerProfile) -> PlayerStatsResponse:
        row = (
            await self._db.execute(
                select(
                    func.count().filter(Mission.category == "MAIN_QUEST").label("main_quest"),
                    func.count().filter(Mission.category == "SIDE_QUEST").label("side_quest"),
                    func.count().filter(Mission.category == "DAILY_GRIND").label("daily_grind"),
                    func.coalesce(func.sum(Mission.xp_awarded), 0).label("total_xp"),
                    func.coalesce(func.sum(Mission.mat_awarded), 0).label("total_materials"),
                ).where(
                    Mission.player_id == player.id,
                    Mission.status == "COMPLETED",
                )
            )
        ).one()

        return PlayerStatsResponse(
            main_quest_completed=row.main_quest,
            side_quest_completed=row.side_quest,
            daily_grind_completed=row.daily_grind,
            total_missions_completed=row.main_quest + row.side_quest + row.daily_grind,
            total_xp_earned=row.total_xp,
            total_materials_earned=row.total_materials,
            best_streak=player.best_streak,
        )
