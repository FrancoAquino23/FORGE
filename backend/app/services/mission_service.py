# ==================================================================
# MISSION SERVICE
# ==================================================================

import uuid
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import func, nullslast, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.catalog import Attribute
from app.models.mission import Checkpoint, Mission
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile
from app.models.relic import Relic
from app.schemas.mission import (
    AchievementUnlocked,
    CheckpointSchema,
    DeployMissionRequest,
    DeployMissionResponse,
    MissionClaimResponse,
    MissionHistoryItem,
    MissionHistoryResponse,
    MissionListResponse,
    MissionProgress,
    ToggleCheckpointResponse,
    UpdateMissionRequest,
    CheckpointUpdateItem,
)
from app.services.achievement_service import AchievementService
from app.services.luck_sync import sync_luck_level
from app.services.reward_service import RewardService
from app.services.skill_tree_service import get_node_level, node_bonus

# Reward amounts per category for player-dispatched missions
_CATEGORY_REWARDS: dict[str, dict] = {
    "MAIN_QUEST":  {"reward_xp": 100, "reward_mat": 50},
    "SIDE_QUEST":  {"reward_xp": 50,  "reward_mat": 25},
    "DAILY_GRIND": {"reward_xp": 30,  "reward_mat": 15},
}

# User-friendly labels for mission categories
_CATEGORY_LABELS: dict[str, str] = {
    "MAIN_QUEST":  "Main Quest",
    "SIDE_QUEST":  "Side Quest",
    "DAILY_GRIND": "Daily Grind",
}

# Threat level mappings between integer storage and string labels
_THREAT_LABEL: dict[int, str] = {0: "MINOR", 1: "MAJOR", 2: "CRITICAL"}
_THREAT_VALUE: dict[str, int] = {"MINOR": 0, "MAJOR": 1, "CRITICAL": 2}
_TL_ORDER: dict[str, int] = {"CRITICAL": 2, "MAJOR": 1, "MINOR": 0}

# Reward multiplier based on streak 
def _streak_multiplier(streak: int) -> float:
    if streak >= 14:
        return 2.0
    if streak >= 7:
        return 1.6
    if streak >= 3:
        return 1.3
    return 1.0

# Service for managing missions (fetching, generating, claiming)
class MissionService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Helper to get active missions with progress for a player
    async def get_active_with_progress(
        self, player_id: uuid.UUID
    ) -> MissionListResponse:
        await self._reset_completed_favorite_dailies(player_id)

        pending = await self._load_pending_missions(player_id)
        active = await self._load_active_missions(player_id)

        relic_rows = (
            await self._db.scalars(select(Relic).where(Relic.player_id == player_id))
        ).all()
        relic_levels: dict[str, int] = {r.attribute_code: r.level for r in relic_rows}

        progress_list = (
            [await self._build_progress(m, player_id, relic_levels) for m in pending]
            + [await self._build_progress(m, player_id, relic_levels) for m in active]
        )

        far_future = datetime(9999, 12, 31, tzinfo=timezone.utc)
        progress_list.sort(
            key=lambda p: (
                -_TL_ORDER.get(p.threat_level, 1),
                p.due_date or far_future,
            )
        )

        return MissionListResponse(missions=progress_list)

    # Helper to claim a completed mission and receive rewards
    async def deploy(
        self, player_id: uuid.UUID, request: DeployMissionRequest
    ) -> DeployMissionResponse:
        attr = await self._db.scalar(
            select(Attribute).where(Attribute.code == request.attribute_code)
        )
        if not attr:
            raise NotFoundError(f"Attribute '{request.attribute_code}'")
        if attr.code == "L":
            raise ConflictError("Luck cannot be assigned as a mission attribute")

        base = _CATEGORY_REWARDS.get(request.category, _CATEGORY_REWARDS["DAILY_GRIND"])
        label = _CATEGORY_LABELS.get(request.category, request.category)

        objective = request.description.strip() or f"{label}: {attr.name}"

        mission = Mission(
            player_id=player_id,
            title=f"{label}: {attr.name}",
            objective_description=objective,
            description=request.detail.strip() if request.detail else None,
            target_attribute_id=attr.id,
            objective_type="MANUAL",
            objective_target=0,
            reward_xp=base["reward_xp"],
            reward_material_qty=base["reward_mat"],
            status="PENDING",
            category=request.category,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            due_date=request.due_date,
            threat_level=_THREAT_VALUE.get(request.threat_level, 1),
        )
        self._db.add(mission)
        await self._db.flush()

        # Create checkpoints for MAIN_QUEST / SIDE_QUEST when steps are provided
        if request.category != "DAILY_GRIND" and request.steps:
            for idx, step_text in enumerate(
                s.strip() for s in request.steps if s.strip()
            ):
                self._db.add(
                    Checkpoint(
                        mission_id=mission.id,
                        description=step_text[:500],
                        order_index=idx,
                    )
                )

        await self._db.commit()

        relic_level = await self._get_relic_level(player_id, attr.code)
        luck_relic_level = await self._get_relic_level(player_id, "L")
        display_xp, display_mat = RewardService.apply_mission_bonuses(
            base["reward_xp"], base["reward_mat"], relic_level, luck_relic_level
        )

        return DeployMissionResponse(
            mission_id=mission.id,
            title=mission.title,
            category=request.category,
            attribute_code=attr.code,
            reward_xp=display_xp,
            reward_material_qty=display_mat,
            threat_level=_THREAT_LABEL.get(mission.threat_level, "MAJOR"),
        )

    # Helper to claim a completed mission and receive rewards
    async def claim(
        self, player_id: uuid.UUID, mission_id: uuid.UUID
    ) -> MissionClaimResponse:
        mission = await self._load_mission_for_claim(player_id, mission_id)
        if mission.checkpoints:
            incomplete = sum(1 for cp in mission.checkpoints if not cp.is_completed)
            if incomplete:
                raise ConflictError(f"Complete all checkpoints first ({incomplete} remaining)")

        now = datetime.now(timezone.utc)
        mission.status = "COMPLETED"
        mission.completed_at = now

        if mission.is_favorite and mission.category == "DAILY_GRIND":
            today = now.date()
            yesterday = today - timedelta(days=1)
            if mission.last_streak_date in (today, yesterday):
                mission.current_streak += 1
            else:
                mission.current_streak = 1
            mission.last_streak_date = today

        # Apply rewards at claim time using current relic & prestige state
        attr_code = mission.target_attribute.code
        relic_level = await self._get_relic_level(player_id, attr_code)
        luck_relic_level = await self._get_relic_level(player_id, "L")

        # Apply streak multiplier to base rewards
        streak_mult = _streak_multiplier(mission.current_streak) if mission.is_favorite and mission.category == "DAILY_GRIND" else 1.0
        base_xp = max(1, round(mission.reward_xp * streak_mult))
        base_mat = max(1, round(mission.reward_material_qty * streak_mult))

        xp_earned, mat_earned = RewardService.apply_mission_bonuses(
            base_xp, base_mat, relic_level, luck_relic_level
        )

        # Apply global_xp_buff skill node
        xp_buff_level = await get_node_level(self._db, player_id, "global_xp_buff")
        if xp_buff_level > 0:
            xp_earned = max(1, round(xp_earned * (1.0 + node_bonus(xp_buff_level))))

        # Apply mission_material_multiplier skill node (Side Quests and Daily Grinds only)
        if mission.category in ("SIDE_QUEST", "DAILY_GRIND"):
            mat_buff_level = await get_node_level(self._db, player_id, "mission_material_multiplier")
            if mat_buff_level > 0:
                mat_earned = max(1, round(mat_earned * (1.0 + node_bonus(mat_buff_level))))

        player_attr = (
            await self._db.execute(
                select(PlayerAttribute)
                .where(
                    PlayerAttribute.player_id == player_id,
                    PlayerAttribute.attribute_id == mission.target_attribute_id,
                )
                .with_for_update()
            )
        ).scalar_one()

        new_xp, new_level, new_xp_to_next, leveled_up = RewardService.apply_xp_to_attribute(
            player_attr.xp_current, player_attr.level, xp_earned
        )
        player_attr.xp_current = new_xp
        player_attr.level = new_level
        player_attr.xp_to_next = new_xp_to_next
        if leveled_up:
            await sync_luck_level(self._db, player_id)

        inventory = (
            await self._db.execute(
                select(PlayerInventory)
                .where(
                    PlayerInventory.player_id == player_id,
                    PlayerInventory.attribute_id == mission.target_attribute_id,
                )
                .with_for_update()
            )
        ).scalar_one()
        inventory.quantity += mat_earned

        # Persist actual awarded values for lifetime stats
        mission.xp_awarded = xp_earned
        mission.mat_awarded = mat_earned

        # Update streak on player profile
        profile = await self._db.scalar(
            select(PlayerProfile).where(PlayerProfile.id == player_id).with_for_update()
        )
        if profile and mission.is_favorite and mission.category == "DAILY_GRIND" and mission.current_streak > 0:
            if mission.current_streak > profile.best_streak:
                profile.best_streak = mission.current_streak

        # Check and unlock achievements
        newly_unlocked = []
        if profile:
            unlocked_defs = await AchievementService(self._db).check_and_unlock(profile)
            newly_unlocked = [
                AchievementUnlocked(code=a.code, title=a.title, description=a.description)
                for a in unlocked_defs
            ]

        await self._db.commit()

        return MissionClaimResponse(
            mission_id=mission.id,
            attribute_code=mission.target_attribute.code,
            material_name=mission.target_attribute.material_name,
            xp_earned=xp_earned,
            material_earned=mat_earned,
            new_attribute_level=new_level,
            leveled_up=leveled_up,
            newly_unlocked=newly_unlocked,
        )

    # Helper to return paginated completed missions for the history tab
    async def get_history(
        self, player_id: uuid.UUID, page: int = 1, page_size: int = 10
    ) -> MissionHistoryResponse:
        base_query = select(Mission).where(
            Mission.player_id == player_id,
            Mission.status == "COMPLETED",
        )

        total = (await self._db.scalar(
            select(func.count()).select_from(base_query.subquery())
        )) or 0

        missions = (
            await self._db.scalars(
                base_query
                .options(selectinload(Mission.target_attribute))
                .order_by(Mission.completed_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()

        import math
        return MissionHistoryResponse(
            missions=[
                MissionHistoryItem(
                    mission_id=m.id,
                    title=m.title,
                    objective_description=m.objective_description,
                    attribute_code=m.target_attribute.code,
                    attribute_name=m.target_attribute.name,
                    category=m.category,
                    threat_level=_THREAT_LABEL.get(m.threat_level, "MAJOR"),
                    reward_xp=m.reward_xp,
                    reward_material_qty=m.reward_material_qty,
                    completed_at=m.completed_at,
                )
                for m in missions
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 1,
        )

    # Helper to delete a PENDING or ACTIVE mission belonging to the player
    async def delete(self, player_id: uuid.UUID, mission_id: uuid.UUID) -> None:
        mission = await self._db.scalar(
            select(Mission).where(Mission.id == mission_id)
        )
        if not mission:
            raise NotFoundError("Mission")
        if mission.player_id != player_id:
            raise ForbiddenError("Mission does not belong to this player")
        if mission.status not in ("ACTIVE", "PENDING"):
            raise ConflictError(f"Cannot delete a mission with status '{mission.status}'")
        await self._db.delete(mission)
        await self._db.commit()

    # Helper to update editable fields (objective, detail, due_date, checkpoints) of a mission
    async def update(
        self, player_id: uuid.UUID, mission_id: uuid.UUID, request: UpdateMissionRequest
    ) -> None:
        mission = await self._db.scalar(
            select(Mission)
            .where(Mission.id == mission_id)
            .options(selectinload(Mission.checkpoints))
        )
        if not mission:
            raise NotFoundError("Mission")
        if mission.player_id != player_id:
            raise ForbiddenError("Mission does not belong to this player")
        if mission.status not in ("ACTIVE", "PENDING"):
            raise ConflictError(f"Cannot edit a mission with status '{mission.status}'")
        if request.objective_description:
            mission.objective_description = request.objective_description.strip()
        if request.detail is not None:
            mission.description = request.detail.strip() or None
        mission.due_date = request.due_date
        if request.threat_level is not None:
            mission.threat_level = _THREAT_VALUE.get(request.threat_level, 1)

        if request.checkpoints is not None:
            existing_by_id = {cp.id: cp for cp in mission.checkpoints}
            incoming_ids = {item.id for item in request.checkpoints if item.id is not None}
            for cp_id, cp in existing_by_id.items():
                if cp_id not in incoming_ids:
                    await self._db.delete(cp)
            for item in request.checkpoints:
                desc = item.description.strip()[:500]
                if not desc:
                    continue
                if item.id and item.id in existing_by_id:
                    existing_by_id[item.id].description = desc
                    existing_by_id[item.id].order_index = item.order_index
                else:
                    self._db.add(Checkpoint(
                        mission_id=mission.id,
                        description=desc,
                        order_index=item.order_index,
                    ))

        await self._db.commit()

    # Helper to toggle is_completed on a checkpoint
    async def toggle_checkpoint(
        self, player_id: uuid.UUID, checkpoint_id: uuid.UUID
    ) -> ToggleCheckpointResponse:
        checkpoint = (
            await self._db.execute(
                select(Checkpoint)
                .join(Mission, Mission.id == Checkpoint.mission_id)
                .where(Checkpoint.id == checkpoint_id, Mission.player_id == player_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if not checkpoint:
            raise NotFoundError("Checkpoint")
        checkpoint.is_completed = not checkpoint.is_completed
        await self._db.commit()
        return ToggleCheckpointResponse(
            checkpoint_id=checkpoint.id,
            is_completed=checkpoint.is_completed,
        )

    # Helper for toggling the is_favorite flag on a DAILY_GRIND mission; returns the new state
    async def toggle_favorite(self, player_id: uuid.UUID, mission_id: uuid.UUID) -> bool:
        mission = await self._db.scalar(
            select(Mission).where(Mission.id == mission_id)
        )
        if not mission:
            raise NotFoundError("Mission")
        if mission.player_id != player_id:
            raise ForbiddenError("Mission does not belong to this player")
        mission.is_favorite = not mission.is_favorite
        await self._db.commit()
        return mission.is_favorite

    # Helper to load active missions for a player
    async def _load_active_missions(self, player_id: uuid.UUID) -> list[Mission]:
        now = datetime.now(timezone.utc)
        return (
            await self._db.scalars(
                select(Mission)
                .where(
                    Mission.player_id == player_id,
                    Mission.status == "ACTIVE",
                    Mission.expires_at > now,
                )
                .options(
                    selectinload(Mission.target_attribute),
                    selectinload(Mission.checkpoints),
                )
                .order_by(Mission.threat_level.desc(), nullslast(Mission.due_date.asc()))
            )
        ).all()

    # Helper to load pending missions for a player
    async def _load_pending_missions(self, player_id: uuid.UUID) -> list[Mission]:
        now = datetime.now(timezone.utc)
        return (
            await self._db.scalars(
                select(Mission)
                .where(
                    Mission.player_id == player_id,
                    Mission.status == "PENDING",
                    Mission.expires_at > now,
                )
                .options(
                    selectinload(Mission.target_attribute),
                    selectinload(Mission.checkpoints),
                )
                .order_by(Mission.threat_level.desc(), nullslast(Mission.due_date.asc()))
            )
        ).all()

    # Helper to build mission progress details for a mission and player
    async def _build_progress(
        self, mission: Mission, player_id: uuid.UUID,
        relic_levels: dict[str, int],
    ) -> MissionProgress:
        attr_code = mission.target_attribute.code
        relic_level = relic_levels.get(attr_code, 0)
        luck_relic_level = relic_levels.get("L", 0)
        reward_xp, reward_mat = RewardService.apply_mission_bonuses(
            mission.reward_xp, mission.reward_material_qty, relic_level, luck_relic_level
        )

        checkpoints = [
            CheckpointSchema(
                id=cp.id,
                description=cp.description,
                is_completed=cp.is_completed,
                order_index=cp.order_index,
            )
            for cp in mission.checkpoints
        ]

        threat = _THREAT_LABEL.get(mission.threat_level, "MAJOR")

        if mission.status == "PENDING":
            has_steps = len(checkpoints) > 0
            all_done = all(cp.is_completed for cp in checkpoints) if has_steps else True
            return MissionProgress(
                mission_id=mission.id,
                title=mission.title,
                objective_description=mission.objective_description,
                objective_type="MANUAL",
                objective_target=len(checkpoints) if has_steps else 1,
                current_progress=sum(1 for cp in checkpoints if cp.is_completed) if has_steps else 1,
                attribute_code=mission.target_attribute.code,
                attribute_name=mission.target_attribute.name,
                reward_xp=reward_xp,
                reward_material_qty=reward_mat,
                expires_at=mission.expires_at,
                is_completable=all_done,
                status="PENDING",
                category=mission.category,
                due_date=mission.due_date,
                description=mission.description,
                is_favorite=mission.is_favorite,
                checkpoints=checkpoints,
                threat_level=threat,
                current_streak=mission.current_streak,
            )

        return MissionProgress(
            mission_id=mission.id,
            title=mission.title,
            objective_description=mission.objective_description,
            objective_type=mission.objective_type,
            objective_target=mission.objective_target,
            current_progress=mission.objective_target,
            attribute_code=mission.target_attribute.code,
            attribute_name=mission.target_attribute.name,
            reward_xp=reward_xp,
            reward_material_qty=reward_mat,
            expires_at=mission.expires_at,
            is_completable=True,
            status=mission.status,
            category=mission.category,
            due_date=mission.due_date,
            description=mission.description,
            is_favorite=mission.is_favorite,
            checkpoints=checkpoints,
            threat_level=threat,
            current_streak=mission.current_streak,
        )

    # Helper to reset completed favorite DAILY_GRIND missions from previous days back to active
    async def _reset_completed_favorite_dailies(self, player_id: uuid.UUID) -> None:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        missions = (
            await self._db.scalars(
                select(Mission).where(
                    Mission.player_id == player_id,
                    Mission.is_favorite == True,  # noqa: E712
                    Mission.category == "DAILY_GRIND",
                    Mission.status == "COMPLETED",
                    Mission.completed_at < today_start,
                )
            )
        ).all()
        yesterday = (now - timedelta(days=1)).date()
        for m in missions:
            m.status = "PENDING" if m.objective_type == "MANUAL" else "ACTIVE"
            m.completed_at = None
            m.expires_at = today_start + timedelta(hours=24)
            if m.last_streak_date is not None and m.last_streak_date < yesterday:
                m.current_streak = 0
                m.last_streak_date = None
        if missions:
            await self._db.commit()

    # Helper to get the level of a relic for a given attribute and player
    async def _get_relic_level(self, player_id: uuid.UUID, attr_code: str) -> int:
        result = await self._db.scalar(
            select(Relic.level).where(
                Relic.player_id == player_id,
                Relic.attribute_code == attr_code,
            )
        )
        return result or 0

    # Helper to load a mission for claiming, ensuring it belongs to the player and is claimable
    async def _load_mission_for_claim(
        self, player_id: uuid.UUID, mission_id: uuid.UUID
    ) -> Mission:
        mission = await self._db.scalar(
            select(Mission)
            .where(Mission.id == mission_id)
            .options(
                selectinload(Mission.target_attribute),
                selectinload(Mission.checkpoints),
            )
        )
        if not mission:
            raise NotFoundError("Mission")
        if mission.player_id != player_id:
            raise ForbiddenError("Mission does not belong to this player")
        if mission.status not in ("ACTIVE", "PENDING"):
            raise ConflictError(f"Mission is already {mission.status}")
        if mission.expires_at < datetime.now(timezone.utc):
            raise ConflictError("Mission has expired")
        return mission
