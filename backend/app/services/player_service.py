# ==================================================================
# PLAYER SERVICE
# ==================================================================

from datetime import datetime, timedelta, timezone
from sqlalchemy import case, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import UnauthorizedError
from app.models.catalog import Attribute
from app.models.mission import DailyCompletion, Mission
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile, User
from app.schemas.player import (
    AttributeMetric,
    AttributeProfile,
    AvgResolutionTime,
    CategoryBreakdown,
    PlayerMetricsResponse,
    PlayerProfileResponse,
    PlayerStatsResponse,
    ThreatBreakdown,
)
from app.services.reward_service import RewardService
from app.utils import local_now as _local_now

# Service PlayerService (Business Logic for Player Profile Retrieval)
class PlayerService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Function (get_profile) to retrieve the player's profile & inventory
    async def get_profile(self, player: PlayerProfile) -> PlayerProfileResponse:
        user = await self._db.scalar(select(User).where(User.id == player.user_id))
        if not user:
            raise UnauthorizedError("Account no longer exists")

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
        return PlayerStatsResponse(
            total_missions_completed=player.total_missions_completed,
            total_xp_earned=player.total_xp_earned,
            total_materials_earned=player.total_materials_earned,
            best_streak=player.best_streak,
        )

    # Helper to retrieve weekly metrics for the Metrics view
    async def get_metrics(self, player: PlayerProfile, week_offset: int) -> PlayerMetricsResponse:
        local_now = _local_now(player.timezone)
        days_since_monday = local_now.weekday()
        monday_local = (local_now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        monday_local = monday_local + timedelta(weeks=week_offset)
        sunday_local = monday_local + timedelta(days=7)

        week_start_utc = monday_local.astimezone(timezone.utc)
        week_end_utc = sunday_local.astimezone(timezone.utc)

        end_day = sunday_local - timedelta(days=1)
        week_label = (
            f"{monday_local.strftime('%b')} {monday_local.day}"
            f" – {end_day.strftime('%b')} {end_day.day}"
        )

        # Completed missions this week (Excludes Favorite Dailies)
        base_filter = [
            Mission.player_id == player.id,
            Mission.status == "COMPLETED",
            Mission.completed_at >= week_start_utc,
            Mission.completed_at < week_end_utc,
            ~((Mission.category == "DAILY_GRIND") & (Mission.is_favorite == True)),
        ]
        recurring_filter = [
            DailyCompletion.player_id == player.id,
            DailyCompletion.completed_at >= week_start_utc,
            DailyCompletion.completed_at < week_end_utc,
        ]

        _elapsed_hours = extract("epoch", Mission.completed_at - Mission.issued_at) / 3600.0
        _elapsed_hours_rec = extract("epoch", DailyCompletion.completed_at - DailyCompletion.cycle_started_at) / 3600.0

        # Query 1: All aggregates for COMPLETED missions this week (category + threat + avg resolution)
        std_row = (
            await self._db.execute(
                select(
                    func.count(case((Mission.category == "MAIN_QUEST", 1))).label("main"),
                    func.count(case((Mission.category == "SIDE_QUEST", 1))).label("side"),
                    func.count(case((Mission.category == "DAILY_GRIND", 1))).label("daily"),
                    func.count().label("total"),
                    func.count(case((Mission.threat_level == 0, 1))).label("minor"),
                    func.count(case((Mission.threat_level == 1, 1))).label("major"),
                    func.count(case((Mission.threat_level == 2, 1))).label("critical"),
                    func.avg(case((Mission.category == "MAIN_QUEST", _elapsed_hours))).label("main_avg"),
                    func.avg(case((Mission.category == "SIDE_QUEST", _elapsed_hours))).label("side_avg"),
                    func.avg(case((Mission.category == "DAILY_GRIND", _elapsed_hours))).label("daily_avg"),
                ).where(*base_filter)
            )
        ).one()

        # Query 2: All aggregates for RECURRING dailies completed this week
        rec_row = (
            await self._db.execute(
                select(
                    func.count().label("total"),
                    func.count(case((DailyCompletion.threat_level == 0, 1))).label("minor"),
                    func.count(case((DailyCompletion.threat_level == 1, 1))).label("major"),
                    func.count(case((DailyCompletion.threat_level == 2, 1))).label("critical"),
                    func.avg(_elapsed_hours_rec).label("daily_avg"),
                ).where(*recurring_filter)
            )
        ).one()

        # Query 3: Attribute breakdown (COMPLETED + RECURRING)
        std_attr_q = (
            select(
                Mission.target_attribute_id,
                func.count().label("missions"),
                func.coalesce(func.sum(Mission.xp_awarded), 0).label("xp"),
            )
            .where(*base_filter)
            .group_by(Mission.target_attribute_id)
        )
        rec_attr_q = (
            select(
                DailyCompletion.target_attribute_id,
                func.count().label("missions"),
                func.coalesce(func.sum(DailyCompletion.xp_awarded), 0).label("xp"),
            )
            .where(*recurring_filter)
            .group_by(DailyCompletion.target_attribute_id)
        )
        all_attr_rows = (await self._db.execute(std_attr_q.union_all(rec_attr_q))).all()

        all_attrs = (await self._db.scalars(select(Attribute))).all()
        attr_map = {a.id: a for a in all_attrs}

        attr_totals: dict[int, dict] = {}
        for row in all_attr_rows:
            if row.target_attribute_id not in attr_map:
                continue
            if row.target_attribute_id not in attr_totals:
                attr_totals[row.target_attribute_id] = {"missions": 0, "xp": 0}
            attr_totals[row.target_attribute_id]["missions"] += row.missions
            attr_totals[row.target_attribute_id]["xp"] += row.xp

        attribute_breakdown = sorted(
            [
                AttributeMetric(
                    code=attr_map[attr_id].code,
                    name=attr_map[attr_id].name,
                    missions_completed=totals["missions"],
                    xp_earned=totals["xp"],
                )
                for attr_id, totals in attr_totals.items()
            ],
            key=lambda x: x.missions_completed,
            reverse=True,
        )

        # Query 4: Check if any completed missions exist before this week
        has_previous = (
            await self._db.scalar(
                select(func.count()).where(
                    Mission.player_id == player.id,
                    Mission.status == "COMPLETED",
                    Mission.completed_at < week_start_utc,
                )
            ) or 0
        ) > 0

        # Round hours (1 Decimal) 
        def _round_hours(val: float | None) -> float | None:
            return round(val, 1) if val is not None else None

        # Weighted average for dailies (standard + RECURRING)
        def _weighted_daily_avg(
            std_avg: float | None, std_count: int,
            rec_avg: float | None, rec_count: int,
        ) -> float | None:
            total = std_count + rec_count
            if total == 0:
                return None
            return round(((std_avg or 0.0) * std_count + (rec_avg or 0.0) * rec_count) / total, 1)

        return PlayerMetricsResponse(
            week_label=week_label,
            week_offset=week_offset,
            has_previous=has_previous,
            has_next=week_offset < 0,
            category_breakdown=CategoryBreakdown(
                main_quest=std_row.main,
                side_quest=std_row.side,
                daily_grind=std_row.daily + rec_row.total,
                total=std_row.total + rec_row.total,
            ),
            threat_breakdown=ThreatBreakdown(
                minor=std_row.minor + rec_row.minor,
                major=std_row.major + rec_row.major,
                critical=std_row.critical + rec_row.critical,
            ),
            attribute_breakdown=attribute_breakdown,
            avg_resolution_hours=AvgResolutionTime(
                main_quest_hours=_round_hours(std_row.main_avg),
                side_quest_hours=_round_hours(std_row.side_avg),
                daily_grind_hours=_weighted_daily_avg(
                    std_row.daily_avg, std_row.daily,
                    rec_row.daily_avg, rec_row.total,
                ),
            ),
        )
