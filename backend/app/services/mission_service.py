# ==================================================================
# MISSION SERVICE
# ==================================================================

import random
import uuid
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.activity import ActivityLog
from app.models.catalog import Attribute
from app.models.mission import Checkpoint, Mission
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile
from app.models.relic import Relic
from app.schemas.mission import (
    CheckpointSchema,
    DeployMissionRequest,
    DeployMissionResponse,
    MissionClaimResponse,
    MissionListResponse,
    MissionProgress,
    ToggleCheckpointResponse,
    UpdateMissionRequest,
    CheckpointUpdateItem,
)
from app.services.reward_service import RewardService

# Configuration for auto-generated missions (type, target count, rewards)
_MISSION_CONFIGS = [
    {"obj_type": "LOG_COUNT", "target": 1, "reward_xp": 50,  "reward_mat": 20},
    {"obj_type": "LOG_COUNT", "target": 3, "reward_xp": 100, "reward_mat": 40},
    {"obj_type": "LOG_COUNT", "target": 5, "reward_xp": 200, "reward_mat": 80},
]

# Reward amounts per category for player-dispatched missions
_CATEGORY_REWARDS: dict[str, dict] = {
    "MAIN_QUEST":  {"reward_xp": 80,  "reward_mat": 35},
    "SIDE_QUEST":  {"reward_xp": 50,  "reward_mat": 20},
    "DAILY_GRIND": {"reward_xp": 30,  "reward_mat": 12},
}

# User-friendly labels for mission categories
_CATEGORY_LABELS: dict[str, str] = {
    "MAIN_QUEST":  "Main Quest",
    "SIDE_QUEST":  "Side Quest",
    "DAILY_GRIND": "Daily Grind",
}

# Service for managing missions (fetching, generating, claiming)
class MissionService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Function to build mission title based on objective type and target
    @staticmethod
    def build_title(obj_type: str, target: int, attr_name: str) -> str:
        return f"Registrar {target} actividad(es) de {attr_name}"

    # Function to build mission description based on objective type and target
    @staticmethod
    def build_description(obj_type: str, target: int, attr_name: str) -> str:
        return f"Completa {target} registro(s) de actividad de {attr_name} hoy."

    # Helper to get active missions with progress for a player
    async def get_active_with_progress(
        self, player_id: uuid.UUID, today: date
    ) -> MissionListResponse:
        await self._reset_completed_favorite_dailies(player_id)

        pending = await self._load_pending_missions(player_id)
        active = await self._load_active_missions(player_id)

        if not active:
            await self._generate_missions(player_id)
            active = await self._load_active_missions(player_id)

        ai_ready = any(m.generated_by_model is not None for m in active)
        progress_list = (
            [await self._build_progress(m, player_id, today) for m in pending]
            + [await self._build_progress(m, player_id, today) for m in active]
        )
        return MissionListResponse(missions=progress_list, ai_ready=ai_ready)
    
    # Helper to claim a completed mission and receive rewards
    async def deploy(
        self, player_id: uuid.UUID, request: DeployMissionRequest
    ) -> DeployMissionResponse:
        attr = await self._db.scalar(
            select(Attribute).where(Attribute.code == request.attribute_code)
        )
        if not attr:
            raise NotFoundError(f"Attribute '{request.attribute_code}'")

        rewards = _CATEGORY_REWARDS.get(request.category, _CATEGORY_REWARDS["DAILY_GRIND"])
        label = _CATEGORY_LABELS.get(request.category, request.category)

        objective = request.description.strip() or f"Misión despachada por el jugador — {label} de {attr.name}."

        mission = Mission(
            player_id=player_id,
            title=f"{label}: {attr.name}",
            objective_description=objective,
            description=request.detail.strip() if request.detail else None,
            target_attribute_id=attr.id,
            objective_type="MANUAL",
            objective_target=0,
            reward_xp=rewards["reward_xp"],
            reward_material_qty=rewards["reward_mat"],
            status="PENDING",
            category=request.category,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            due_date=request.due_date,
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

        return DeployMissionResponse(
            mission_id=mission.id,
            title=mission.title,
            category=request.category,
            attribute_code=attr.code,
            reward_xp=mission.reward_xp,
            reward_material_qty=mission.reward_material_qty,
        )

    # Helper to claim a completed mission and receive rewards
    async def claim(
        self, player_id: uuid.UUID, mission_id: uuid.UUID
    ) -> MissionClaimResponse:
        mission = await self._load_mission_for_claim(player_id, mission_id)
        if mission.status != "PENDING":
            today = date.today()
            progress = await self._get_progress_value(mission, player_id, today)
            if progress < mission.objective_target:
                raise ConflictError(
                    f"Mission not yet complete: {progress}/{mission.objective_target}"
                )
        elif mission.checkpoints:
            incomplete = sum(1 for cp in mission.checkpoints if not cp.is_completed)
            if incomplete:
                raise ConflictError(f"Complete all checkpoints first ({incomplete} remaining)")

        now = datetime.now(timezone.utc)
        mission.status = "COMPLETED"
        mission.completed_at = now

        # Apply relic bonuses to base rewards at claim time
        attr_code = mission.target_attribute.code
        relic_level = await self._get_relic_level(player_id, attr_code)
        player_profile = await self._db.scalar(
            select(PlayerProfile).where(PlayerProfile.id == player_id)
        )
        prestige_count = player_profile.prestige_count if player_profile else 0
        xp_earned, mat_earned = RewardService.apply_mission_bonuses(
            mission.reward_xp, mission.reward_material_qty, relic_level, prestige_count
        )

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

        await self._db.commit()

        return MissionClaimResponse(
            mission_id=mission.id,
            attribute_code=mission.target_attribute.code,
            material_name=mission.target_attribute.material_name,
            xp_earned=xp_earned,
            material_earned=mat_earned,
            new_attribute_level=new_level,
            leveled_up=leveled_up,
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
                .order_by(Mission.issued_at.desc())
            )
        ).all()

    # Helper to generate new missions for a player based on configuration
    async def _generate_missions(self, player_id: uuid.UUID) -> None:
        all_attrs = (await self._db.scalars(select(Attribute))).all()
        selected = random.sample(all_attrs, k=min(len(_MISSION_CONFIGS), len(all_attrs)))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        for cfg, attr in zip(_MISSION_CONFIGS, selected):
            self._db.add(
                Mission(
                    player_id=player_id,
                    title=self.build_title(cfg["obj_type"], cfg["target"], attr.name),
                    objective_description=self.build_description(
                        cfg["obj_type"], cfg["target"], attr.name
                    ),
                    target_attribute_id=attr.id,
                    objective_type=cfg["obj_type"],
                    objective_target=cfg["target"],
                    reward_xp=cfg["reward_xp"],
                    reward_material_qty=cfg["reward_mat"],
                    expires_at=expires_at,
                )
            )
        await self._db.commit()

    # Helper to build mission progress details for a mission and player
    async def _build_progress(
        self, mission: Mission, player_id: uuid.UUID, today: date
    ) -> MissionProgress:
        checkpoints = [
            CheckpointSchema(
                id=cp.id,
                description=cp.description,
                is_completed=cp.is_completed,
                order_index=cp.order_index,
            )
            for cp in mission.checkpoints
        ]

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
                reward_xp=mission.reward_xp,
                reward_material_qty=mission.reward_material_qty,
                expires_at=mission.expires_at,
                is_completable=all_done,
                ai_generated=False,
                status="PENDING",
                category=mission.category,
                due_date=mission.due_date,
                description=mission.description,
                is_favorite=mission.is_favorite,
                checkpoints=checkpoints,
            )

        progress = await self._get_progress_value(mission, player_id, today)
        return MissionProgress(
            mission_id=mission.id,
            title=mission.title,
            objective_description=mission.objective_description,
            objective_type=mission.objective_type,
            objective_target=mission.objective_target,
            current_progress=progress,
            attribute_code=mission.target_attribute.code,
            attribute_name=mission.target_attribute.name,
            reward_xp=mission.reward_xp,
            reward_material_qty=mission.reward_material_qty,
            expires_at=mission.expires_at,
            is_completable=(progress >= mission.objective_target),
            ai_generated=(mission.generated_by_model is not None),
            status=mission.status,
            category=mission.category,
            due_date=mission.due_date,
            description=mission.description,
            is_favorite=mission.is_favorite,
            checkpoints=checkpoints,
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
        for m in missions:
            m.status = "PENDING" if m.objective_type == "MANUAL" else "ACTIVE"
            m.completed_at = None
            m.expires_at = today_start + timedelta(hours=24)
        if missions:
            await self._db.commit()

    # Helper to calculate current progress value for a mission based on its objective type
    async def _get_progress_value(
        self, mission: Mission, player_id: uuid.UUID, today: date
    ) -> int:
        result = await self._db.scalar(
            select(func.count(ActivityLog.id)).where(
                ActivityLog.player_id == player_id,
                ActivityLog.attribute_id == mission.target_attribute_id,
                ActivityLog.activity_date == today,
            )
        )
        return result or 0

    # Helper to get the level of a relic for a given attribute and player
    async def _get_relic_level(self, player_id: uuid.UUID, attr_code: str) -> int:
        if attr_code == "L":
            p = await self._db.scalar(
                select(PlayerProfile).where(PlayerProfile.id == player_id)
            )
            return p.prestige_count if p else 0
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
