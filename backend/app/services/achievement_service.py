# ==================================================================
# FORGE - ACHIEVEMENT SERVICE
# ==================================================================

import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.mission import Mission
from app.models.player import PlayerAchievement, PlayerAttribute, PlayerProfile
from app.services.achievement_definitions import ACHIEVEMENT_MAP, ACHIEVEMENTS, AchievementDef

# Service for checking & unlocking achievements
class AchievementService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def check_and_unlock(self, player: PlayerProfile) -> list[AchievementDef]:
        # Get already unlocked achievements
        result = await self._db.execute(
            select(PlayerAchievement.achievement_code).where(
                PlayerAchievement.player_id == player.id
            )
        )
        already_unlocked: set[str] = {row[0] for row in result.all()}

        # Gather data needed for validation checks
        stats_row = (await self._db.execute(
            select(
                func.count().filter(Mission.status == "COMPLETED").label("total"),
                func.coalesce(func.sum(Mission.xp_awarded), 0).label("total_xp"),
                func.coalesce(func.sum(Mission.mat_awarded), 0).label("total_mat"),
            ).where(Mission.player_id == player.id)
        )).one()

        attrs_result = await self._db.execute(
            select(PlayerAttribute.level).where(PlayerAttribute.player_id == player.id)
        )
        attr_levels = [row[0] for row in attrs_result.all()]

        # Evaluate conditions for each achievement
        total_missions: int = stats_row.total
        total_xp: int = stats_row.total_xp
        total_mat: int = stats_row.total_mat
        prestige: int = player.prestige_count
        best_streak: int = player.best_streak
        all_maxed: bool = bool(attr_levels) and all(lv >= 10 for lv in attr_levels)

        conditions: dict[str, bool] = {
            "internship":     total_missions >= 100,
            "full_time":      total_missions >= 1_000,
            "senior":         total_missions >= 10_000,
            "pizza_party":    best_streak >= 30,
            "overqualified":  total_xp >= 1_000_000,
            "inventory":      total_mat >= 1_000_000,
            "first_steps":    prestige >= 1,
            "worn_path":      prestige >= 25,
            "no_turning_back": prestige >= 50,
            "special":        all_maxed,
        }

        newly_unlocked: list[AchievementDef] = []
        for code, met in conditions.items():
            if met and code not in already_unlocked:
                self._db.add(PlayerAchievement(
                    id=uuid.uuid4(),
                    player_id=player.id,
                    achievement_code=code,
                ))
                newly_unlocked.append(ACHIEVEMENT_MAP[code])

        return newly_unlocked

    # Helper to get all achievements with "Unlocked" status
    async def get_all(self, player: PlayerProfile) -> list[dict]:
        result = await self._db.execute(
            select(PlayerAchievement).where(PlayerAchievement.player_id == player.id)
        )
        unlocked_rows = {row.achievement_code: row.unlocked_at for row in result.scalars().all()}

        return [
            {
                "code": a.code,
                "title": a.title,
                "description": a.description,
                "flavor": a.flavor,
                "unlocked": a.code in unlocked_rows,
                "unlocked_at": unlocked_rows[a.code].isoformat() if a.code in unlocked_rows else None,
            }
            for a in ACHIEVEMENTS
        ]
