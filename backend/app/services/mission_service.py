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
from app.models.mission import Mission
from app.models.player import PlayerAttribute, PlayerInventory
from app.schemas.mission import MissionClaimResponse, MissionListResponse, MissionProgress
from app.services.reward_service import RewardService

# Temporary hardcoded mission configs
_MISSION_CONFIGS = [
    {"obj_type": "LOG_COUNT",   "target": 1,  "reward_xp": 50,  "reward_mat": 20},
    {"obj_type": "LOG_MINUTES", "target": 60, "reward_xp": 100, "reward_mat": 40},
    {"obj_type": "LOG_MINUTES", "target": 90, "reward_xp": 200, "reward_mat": 80},
]

# Model MissionService (Business Logic for Missions)
class MissionService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Function to build mission title based on objective type and target
    @staticmethod
    def build_title(obj_type: str, target: int, attr_name: str) -> str:
        if obj_type == "LOG_MINUTES":
            return f"Dedicar {target} minutos a {attr_name}"
        return f"Registrar {target} actividad(es) de {attr_name}"

    # Function to build mission description based on objective type and target
    @staticmethod
    def build_description(obj_type: str, target: int, attr_name: str) -> str:
        if obj_type == "LOG_MINUTES":
            return f"Acumula al menos {target} minutos de actividad de {attr_name} hoy."
        return f"Completa {target} registro(s) de actividad de {attr_name} hoy."

    # Helper to get active missions with progress for a player
    async def get_active_with_progress(
        self, player_id: uuid.UUID, today: date
    ) -> MissionListResponse:
        missions = await self._load_active_missions(player_id)
        if not missions:
            await self._generate_missions(player_id)
            missions = await self._load_active_missions(player_id)

        ai_ready = any(m.generated_by_model is not None for m in missions)
        progress_list = [
            await self._build_progress(m, player_id, today) for m in missions
        ]
        return MissionListResponse(missions=progress_list, ai_ready=ai_ready)

    # Helper to claim a completed mission and receive rewards
    async def claim(
        self, player_id: uuid.UUID, mission_id: uuid.UUID
    ) -> MissionClaimResponse:
        mission = await self._load_mission_for_claim(player_id, mission_id)
        today = date.today()

        progress = await self._get_progress_value(mission, player_id, today)
        if progress < mission.objective_target:
            raise ConflictError(
                f"Mission not yet complete: {progress}/{mission.objective_target}"
            )

        now = datetime.now(timezone.utc)
        mission.status = "COMPLETED"
        mission.completed_at = now

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
            player_attr.xp_current, player_attr.level, mission.reward_xp
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
        inventory.quantity += mission.reward_material_qty

        await self._db.commit()

        return MissionClaimResponse(
            mission_id=mission.id,
            attribute_code=mission.target_attribute.code,
            material_name=mission.target_attribute.material_name,
            xp_earned=mission.reward_xp,
            material_earned=mission.reward_material_qty,
            new_attribute_level=new_level,
            leveled_up=leveled_up,
        )

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
                .options(selectinload(Mission.target_attribute))
            )
        ).all()

    # Helper to generate new missions for a player randomly
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
        )

    # Helper to calculate current progress value for a mission based on its objective type
    async def _get_progress_value(
        self, mission: Mission, player_id: uuid.UUID, today: date
    ) -> int:
        if mission.objective_type == "LOG_MINUTES":
            result = await self._db.scalar(
                select(func.sum(ActivityLog.duration_minutes)).where(
                    ActivityLog.player_id == player_id,
                    ActivityLog.attribute_id == mission.target_attribute_id,
                    ActivityLog.activity_date == today,
                )
            )
        else:  # LOG_COUNT
            result = await self._db.scalar(
                select(func.count(ActivityLog.id)).where(
                    ActivityLog.player_id == player_id,
                    ActivityLog.attribute_id == mission.target_attribute_id,
                    ActivityLog.activity_date == today,
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
            .options(selectinload(Mission.target_attribute))
        )
        if not mission:
            raise NotFoundError("Mission")
        if mission.player_id != player_id:
            raise ForbiddenError("Mission does not belong to this player")
        if mission.status != "ACTIVE":
            raise ConflictError(f"Mission is already {mission.status}")
        if mission.expires_at < datetime.now(timezone.utc):
            raise ConflictError("Mission has expired")
        return mission
