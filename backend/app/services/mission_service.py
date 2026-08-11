# ==================================================================
# MISSION SERVICE
# ==================================================================

import math
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import nullslast, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.constants import (
    CATEGORY_LABELS as _CATEGORY_LABELS,
    CATEGORY_REWARDS as _CATEGORY_REWARDS,
    THREAT_LABEL as _THREAT_LABEL,
    THREAT_MULTIPLIER as _THREAT_MULTIPLIER,
    THREAT_ORDER as _TL_ORDER,
    THREAT_VALUE as _THREAT_VALUE,
)
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.catalog import Attribute
from app.models.mission import Checkpoint, DailyCompletion, Mission
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile
from app.models.relic import Relic
from app.schemas.mission import (
    AchievementUnlocked,
    ActivateMissionResponse,
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
)
from app.services.achievement_service import AchievementService
from app.services.luck_sync import sync_luck_level
from app.services.reward_service import RewardService, prestige_bonus, xp_scale_factor
from app.services.skill_tree_service import get_node_level, node_bonus
from app.utils import local_now as _local_now


# Reward multiplier based on streak
def _streak_multiplier(streak: int) -> float:
    if streak >= 30:
        return 3.0
    if streak >= 14:
        return 2.0
    if streak >= 7:
        return 1.6
    if streak >= 3:
        return 1.3
    if streak >= 3:
        return 1.25
    return 1.0

# Service for managing missions (fetching, generating, claiming)
class MissionService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Helper to delete missions that have passed their expiry date
    async def _delete_expired_missions(self, player_id: uuid.UUID) -> None:
        now = datetime.now(timezone.utc)
        expired = (
            await self._db.scalars(
                select(Mission).where(
                    Mission.player_id == player_id,
                    Mission.status.in_(["PENDING", "ACTIVE", "DRAFT"]),
                    Mission.expires_at <= now,
                )
            )
        ).all()
        if expired:
            for mission in expired:
                await self._db.delete(mission)
            await self._db.commit()

    # Helper to get active missions with progress for a player
    async def get_active_with_progress(
        self, player: PlayerProfile
    ) -> MissionListResponse:
        await self._delete_expired_missions(player.id)
        await self._reset_completed_favorite_dailies(player.id, player.timezone)

        pending = await self._load_pending_missions(player.id)
        active = await self._load_active_missions(player.id)
        drafts = await self._load_draft_missions(player.id)

        relic_rows = (
            await self._db.scalars(select(Relic).where(Relic.player_id == player.id))
        ).all()
        relic_levels: dict[str, int] = {r.attribute_code: r.level for r in relic_rows}

        progress_list = (
            [await self._build_progress(m, player.id, relic_levels) for m in pending]
            + [await self._build_progress(m, player.id, relic_levels) for m in active]
            + [await self._build_progress(m, player.id, relic_levels) for m in drafts]
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

        threat_mult = _THREAT_MULTIPLIER.get(request.threat_level, 1.0)
        now = datetime.now(timezone.utc)
        is_draft = request.is_draft and request.category != "DAILY_GRIND"
        mission = Mission(
            player_id=player_id,
            title=f"{label}: {attr.name}",
            objective_description=objective,
            description=request.detail.strip() if request.detail else None,
            target_attribute_id=attr.id,
            objective_type="MANUAL",
            objective_target=0,
            reward_xp=max(1, round(base["reward_xp"] * threat_mult)),
            reward_material_qty=max(1, round(base["reward_mat"] * threat_mult)),
            status="DRAFT" if is_draft else "PENDING",
            category=request.category,
            expires_at=now + timedelta(days=30),
            due_date=request.due_date,
            threat_level=_THREAT_VALUE.get(request.threat_level, 1),
            issued_at=None if is_draft else now,
            cycle_started_at=None if is_draft else now,
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

        relic_rows = (
            await self._db.execute(
                select(Relic.attribute_code, Relic.level).where(
                    Relic.player_id == player_id,
                    Relic.attribute_code.in_([attr.code, "L"]),
                )
            )
        ).all()
        relic_map = {r.attribute_code: r.level for r in relic_rows}
        display_xp, display_mat = RewardService.apply_mission_bonuses(
            base["reward_xp"], base["reward_mat"],
            relic_map.get(attr.code, 0), relic_map.get("L", 0),
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

    # Helper to activate a DRAFT mission
    async def activate(
        self, player_id: uuid.UUID, mission_id: uuid.UUID
    ) -> ActivateMissionResponse:
        mission = await self._db.scalar(
            select(Mission).where(Mission.id == mission_id)
        )
        if not mission:
            raise NotFoundError("Mission")
        if mission.player_id != player_id:
            raise ForbiddenError("Mission does not belong to this player")
        if mission.status != "DRAFT":
            raise ConflictError(f"Mission is not a draft (status: '{mission.status}')")

        now = datetime.now(timezone.utc)
        mission.status = "PENDING"
        mission.issued_at = now
        mission.cycle_started_at = now
        await self._db.commit()

        return ActivateMissionResponse(
            mission_id=mission.id,
            title=mission.title,
            category=mission.category or "",
        )

    # Helper to claim a completed mission and receive rewards
    async def claim(
        self, player: PlayerProfile, mission_id: uuid.UUID
    ) -> MissionClaimResponse:
        mission = await self._load_mission_for_claim(player.id, mission_id)
        if mission.checkpoints:
            incomplete = sum(1 for cp in mission.checkpoints if not cp.is_completed)
            if incomplete:
                raise ConflictError(f"Complete all checkpoints first ({incomplete} remaining)")

        now = datetime.now(timezone.utc)
        mission.status = "COMPLETED"
        mission.completed_at = now
        daily_completion: DailyCompletion | None = None
        if mission.is_favorite and mission.category == "DAILY_GRIND":
            mission.last_completed_at = now
            mission.times_completed += 1
            local_now = _local_now(player.timezone)
            today = local_now.date()
            yesterday = today - timedelta(days=1)
            if mission.last_streak_date in (today, yesterday):
                mission.current_streak += 1
            else:
                mission.current_streak = 1
            mission.last_streak_date = today
            daily_completion = DailyCompletion(
                mission_id=mission.id,
                player_id=player.id,
                target_attribute_id=mission.target_attribute_id,
                threat_level=mission.threat_level,
                completed_at=now,
                cycle_started_at=mission.cycle_started_at or now,
            )
            self._db.add(daily_completion)

        # Apply rewards at claim time using current relic & prestige state
        attr_code = mission.target_attribute.code
        relic_rows = (
            await self._db.execute(
                select(Relic.attribute_code, Relic.level).where(
                    Relic.player_id == player.id,
                    Relic.attribute_code.in_([attr_code, "L"]),
                )
            )
        ).all()
        relic_map = {r.attribute_code: r.level for r in relic_rows}
        relic_level = relic_map.get(attr_code, 0)
        luck_relic_level = relic_map.get("L", 0)

        # Apply streak multiplier to base rewards
        streak_mult = _streak_multiplier(mission.current_streak) if mission.is_favorite and mission.category == "DAILY_GRIND" else 1.0
        base_xp = max(1, round(mission.reward_xp * streak_mult))
        base_mat = max(1, round(mission.reward_material_qty * streak_mult))

        xp_earned, mat_earned = RewardService.apply_mission_bonuses(
            base_xp, base_mat, relic_level, luck_relic_level
        )

        # Apply global_xp_buff skill node
        xp_buff_level = await get_node_level(self._db, player.id, "global_xp_buff")
        if xp_buff_level > 0:
            xp_earned = max(1, round(xp_earned * (1.0 + node_bonus(xp_buff_level))))

        # Apply mission_material_multiplier skill node (Main Quests and Side Quests only)
        if mission.category in ("MAIN_QUEST", "SIDE_QUEST"):
            mat_buff_level = await get_node_level(self._db, player.id, "mission_material_multiplier")
            if mat_buff_level > 0:
                mat_earned = max(1, round(mat_earned * (1.0 + node_bonus(mat_buff_level))))

        # Apply critical_surge skill node (Main Quests — all threat levels)
        if mission.category == "MAIN_QUEST":
            critical_level = await get_node_level(self._db, player.id, "critical_surge")
            if critical_level > 0:
                bonus = node_bonus(critical_level)
                xp_earned = max(1, round(xp_earned * (1.0 + bonus)))
                mat_earned = max(1, round(mat_earned * (1.0 + bonus)))

        # Apply streak_amplifier skill node (Daily Grind with active streak)
        if mission.category == "DAILY_GRIND" and mission.current_streak > 0:
            streak_amp_level = await get_node_level(self._db, player.id, "streak_amplifier")
            if streak_amp_level > 0:
                bonus = node_bonus(streak_amp_level)
                xp_earned = max(1, round(xp_earned * (1.0 + bonus)))
                mat_earned = max(1, round(mat_earned * (1.0 + bonus)))

        # Apply permanent prestige bonus multiplier
        prestige_mult = prestige_bonus(player.prestige_count)
        xp_earned = max(1, round(xp_earned * prestige_mult))
        mat_earned = max(1, round(mat_earned * prestige_mult))

        player_attr = (
            await self._db.execute(
                select(PlayerAttribute)
                .where(
                    PlayerAttribute.player_id == player.id,
                    PlayerAttribute.attribute_id == mission.target_attribute_id,
                )
                .with_for_update()
            )
        ).scalar_one()

        null_cycle_level = await get_node_level(self._db, player.id, "early_start_boost")
        xp_discount = node_bonus(null_cycle_level) if null_cycle_level > 0 else 0.0
        new_xp, new_level, new_xp_to_next, leveled_up = RewardService.apply_xp_to_attribute(
            player_attr.xp_current, player_attr.level, xp_earned, xp_discount,
            prestige_factor=xp_scale_factor(player.prestige_count),
        )
        player_attr.xp_current = new_xp
        player_attr.level = new_level
        player_attr.xp_to_next = new_xp_to_next
        if leveled_up:
            await sync_luck_level(self._db, player.id)

        inventory = (
            await self._db.execute(
                select(PlayerInventory)
                .where(
                    PlayerInventory.player_id == player.id,
                    PlayerInventory.attribute_id == mission.target_attribute_id,
                )
                .with_for_update()
            )
        ).scalar_one()
        inventory.quantity += mat_earned

        # Persist actual awarded values for lifetime stats
        mission.xp_awarded = xp_earned
        mission.mat_awarded = mat_earned
        if daily_completion is not None:
            daily_completion.xp_awarded = xp_earned
            daily_completion.mat_awarded = mat_earned

        # Update lifetime stats and streak on player profile
        profile = await self._db.scalar(
            select(PlayerProfile).where(PlayerProfile.id == player.id).with_for_update()
        )
        if profile:
            profile.total_missions_completed += 1
            profile.total_xp_earned += xp_earned
            profile.total_materials_earned += mat_earned
            if mission.is_favorite and mission.category == "DAILY_GRIND" and mission.current_streak > 0:
                if mission.current_streak > profile.best_streak:
                    profile.best_streak = mission.current_streak

        # Check and unlock achievements
        newly_unlocked = []
        if profile:
            unlocked_defs = await AchievementService(self._db).check_and_unlock(profile)
            newly_unlocked = [
                AchievementUnlocked(code=a.code, title=a.title, description=a.description, flavor=a.flavor)
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

    # Helper to return the last 20 completed missions for the history tab
    async def get_history(
        self, player_id: uuid.UUID, page: int = 1, page_size: int = 5
    ) -> MissionHistoryResponse:
        HISTORY_LIMIT = 20

        std_missions = (
            await self._db.scalars(
                select(Mission)
                .where(
                    Mission.player_id == player_id,
                    Mission.status == "COMPLETED",
                )
                .options(selectinload(Mission.target_attribute))
                .order_by(Mission.completed_at.desc())
                .limit(HISTORY_LIMIT)
            )
        ).all()

        rec_missions = (
            await self._db.scalars(
                select(Mission)
                .where(
                    Mission.player_id == player_id,
                    Mission.is_favorite == True,  # noqa: E712
                    Mission.category == "DAILY_GRIND",
                    Mission.status != "COMPLETED",
                    Mission.last_completed_at.is_not(None),
                )
                .options(selectinload(Mission.target_attribute))
                .order_by(Mission.last_completed_at.desc())
                .limit(HISTORY_LIMIT)
            )
        ).all()

        def _sort_key(m: Mission) -> datetime:
            return m.completed_at or m.last_completed_at  # type: ignore[return-value]

        all_missions = sorted(
            list(std_missions) + list(rec_missions),
            key=_sort_key,
            reverse=True,
        )[:HISTORY_LIMIT]

        total = len(all_missions)
        page_missions = all_missions[(page - 1) * page_size : page * page_size]

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
                    completed_at=m.completed_at or m.last_completed_at,  # type: ignore[arg-type]
                )
                for m in page_missions
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
        if mission.status not in ("ACTIVE", "PENDING", "DRAFT"):
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
        if mission.status not in ("ACTIVE", "PENDING", "DRAFT"):
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
        return list(
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
        )

    # Helper to load draft missions for a player
    async def _load_draft_missions(self, player_id: uuid.UUID) -> list[Mission]:
        return list(
            await self._db.scalars(
                select(Mission)
                .where(
                    Mission.player_id == player_id,
                    Mission.status == "DRAFT",
                )
                .options(
                    selectinload(Mission.target_attribute),
                    selectinload(Mission.checkpoints),
                )
                .order_by(Mission.threat_level.desc(), nullslast(Mission.due_date.asc()))
            )
        )

    # Helper to load pending missions for a player
    async def _load_pending_missions(self, player_id: uuid.UUID) -> list[Mission]:
        now = datetime.now(timezone.utc)
        return list(
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
        )

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

        if mission.status == "DRAFT":
            has_steps = len(checkpoints) > 0
            return MissionProgress(
                mission_id=mission.id,
                title=mission.title,
                objective_description=mission.objective_description,
                objective_type="MANUAL",
                objective_target=len(checkpoints) if has_steps else 1,
                current_progress=0,
                attribute_code=mission.target_attribute.code,
                attribute_name=mission.target_attribute.name,
                reward_xp=reward_xp,
                reward_material_qty=reward_mat,
                expires_at=mission.expires_at,
                is_completable=False,
                status="DRAFT",
                category=mission.category,
                due_date=mission.due_date,
                description=mission.description,
                is_favorite=False,
                checkpoints=checkpoints,
                threat_level=threat,
                current_streak=0,
            )

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
    async def _reset_completed_favorite_dailies(self, player_id: uuid.UUID, tz_name: str) -> None:
        local_now = _local_now(tz_name)
        today_start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_utc = today_start_local.astimezone(timezone.utc)
        missions = (
            await self._db.scalars(
                select(Mission).where(
                    Mission.player_id == player_id,
                    Mission.is_favorite == True,  # noqa: E712
                    Mission.category == "DAILY_GRIND",
                    Mission.status == "COMPLETED",
                    Mission.completed_at < today_start_utc,
                ).with_for_update()
            )
        ).all()
        yesterday = (local_now - timedelta(days=1)).date()
        for m in missions:
            m.status = "PENDING" if m.objective_type == "MANUAL" else "ACTIVE"
            m.completed_at = None
            m.issued_at = today_start_utc
            m.cycle_started_at = today_start_utc
            m.expires_at = today_start_utc + timedelta(hours=24)
            if m.last_streak_date is not None and m.last_streak_date < yesterday:
                m.current_streak = 0
                m.last_streak_date = None
        if missions:
            await self._db.commit()

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
