# ==================================================================
# MISSION ROUTES
# ==================================================================

import uuid
from datetime import date
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.mission import DeployMissionRequest, DeployMissionResponse, MissionClaimResponse, MissionListResponse
from app.services.gm_service import GmService
from app.services.mission_service import MissionService

# APIRouter for mission-related endpoints
router = APIRouter(prefix="/missions", tags=["missions"])

# Endpoint (GET /missions/active) — Returns PENDING + ACTIVE missions
@router.get("/active", response_model=MissionListResponse)
async def get_active_missions(
    background_tasks: BackgroundTasks,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> MissionListResponse:
    service = MissionService(session)
    result = await service.get_active_with_progress(player.id, date.today())
    background_tasks.add_task(GmService.run_background_mission_generation, player.id)
    return result

# Endpoint (POST /missions/deploy) — Dispatch a new player-created PENDING mission
@router.post("/deploy", response_model=DeployMissionResponse)
async def deploy_mission(
    body: DeployMissionRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> DeployMissionResponse:
    service = MissionService(session)
    return await service.deploy(player.id, body)

# Endpoint (POST /missions/{mission_id}/claim) — Claim/complete a mission and receive rewards
@router.post("/{mission_id}/claim", response_model=MissionClaimResponse)
async def claim_mission(
    mission_id: uuid.UUID,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> MissionClaimResponse:
    service = MissionService(session)
    return await service.claim(player.id, mission_id)
