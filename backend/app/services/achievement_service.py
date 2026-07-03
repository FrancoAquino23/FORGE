# ==================================================================
# FORGE - ACHIEVEMENT SERVICE
# ==================================================================

import uuid
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.player import PlayerAchievement, PlayerAttribute, PlayerProfile
from app.services.achievement_definitions import ACHIEVEMENT_MAP, ACHIEVEMENTS, AchievementDef

# Service for checking & unlocking achievements
class AchievementService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # Helper to check any achievements that can be unlocked
    async def check_and_unlock(self, player: PlayerProfile) -> list[AchievementDef]:
        result = await self._db.execute(
            select(PlayerAchievement.achievement_code).where(
                PlayerAchievement.player_id == player.id
            )
        )
        already_unlocked: set[str] = {row[0] for row in result.all()}
        attrs_result = await self._db.execute(
            select(PlayerAttribute.level).where(PlayerAttribute.player_id == player.id)
        )
        attr_levels = [row[0] for row in attrs_result.all()]

        # Evaluate conditions for each achievement
        total_missions: int = player.total_missions_completed
        total_xp: int = player.total_xp_earned
        total_mat: int = player.total_materials_earned
        prestige: int = player.prestige_count
        best_streak: int = player.best_streak
        all_maxed: bool = bool(attr_levels) and all(lv >= 10 for lv in attr_levels)

        conditions: dict[str, bool] = {
            "internship":      total_missions >= 100,
            "full_time":       total_missions >= 1_000,
            "senior":          total_missions >= 10_000,
            "pizza_party":     best_streak >= 30,
            "overqualified":   total_xp >= 1_000_000,
            "inventory":       total_mat >= 1_000_000,
            "first_steps":     prestige >= 1,
            "worn_path":       prestige >= 25,
            "no_turning_back": prestige >= 50,
            "special":         all_maxed,
        }

        newly_unlocked: list[AchievementDef] = []
        for code, met in conditions.items():
            if met and code not in already_unlocked:
                stmt = pg_insert(PlayerAchievement).values(
                    id=uuid.uuid4(),
                    player_id=player.id,
                    achievement_code=code,
                ).on_conflict_do_nothing(
                    index_elements=["player_id", "achievement_code"]
                )
                await self._db.execute(stmt)
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
