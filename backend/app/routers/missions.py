# ==================================================================
# MISSION ROUTES
# ==================================================================

import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.mission import (
    DeployMissionRequest,
    DeployMissionResponse,
    MissionClaimResponse,
    MissionHistoryResponse,
    MissionListResponse,
    ToggleCheckpointResponse,
    UpdateMissionRequest,
)
from app.services.mission_service import MissionService

# APIRouter for mission-related endpoints
router = APIRouter(prefix="/missions", tags=["missions"])

# Endpoint (GET /missions/active) — Returns PENDING + ACTIVE missions
@router.get("/active", response_model=MissionListResponse)
async def get_active_missions(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> MissionListResponse:
    service = MissionService(session)
    return await service.get_active_with_progress(player)

# Endpoint (GET /missions/history) — Returns completed missions paginated
@router.get("/history", response_model=MissionHistoryResponse)
async def get_mission_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> MissionHistoryResponse:
    service = MissionService(session)
    return await service.get_history(player.id, page=page, page_size=page_size)

# Endpoint (POST /missions/deploy) — Dispatch a new player-created PENDING mission
@router.post("/deploy", response_model=DeployMissionResponse)
async def deploy_mission(
    body: DeployMissionRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> DeployMissionResponse:
    service = MissionService(session)
    return await service.deploy(player.id, body)

# Endpoint (PATCH /missions/checkpoints/{checkpoint_id}/toggle) — Toggle a checkpoint's completion state
@router.patch("/checkpoints/{checkpoint_id}/toggle", response_model=ToggleCheckpointResponse)
async def toggle_checkpoint(
    checkpoint_id: uuid.UUID,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> ToggleCheckpointResponse:
    service = MissionService(session)
    return await service.toggle_checkpoint(player.id, checkpoint_id)

# Endpoint (POST /missions/{mission_id}/claim) — Claim/complete a mission and receive rewards
@router.post("/{mission_id}/claim", response_model=MissionClaimResponse)
async def claim_mission(
    mission_id: uuid.UUID,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> MissionClaimResponse:
    service = MissionService(session)
    return await service.claim(player, mission_id)

# Endpoint (POST /missions/{mission_id}/favorite) — Toggle the is_favorite flag
@router.post("/{mission_id}/favorite")
async def toggle_favorite(
    mission_id: uuid.UUID,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> dict:
    service = MissionService(session)
    new_state = await service.toggle_favorite(player.id, mission_id)
    return {"is_favorite": new_state}

# Endpoint (PATCH /missions/{mission_id}) — Edit objective, description, or due_date
@router.patch("/{mission_id}")
async def update_mission(
    mission_id: uuid.UUID,
    body: UpdateMissionRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> dict:
    service = MissionService(session)
    await service.update(player.id, mission_id, body)
    return {"ok": True}

# Endpoint (DELETE /missions/{mission_id}) — Delete an ACTIVE or PENDING mission
@router.delete("/{mission_id}", status_code=204)
async def delete_mission(
    mission_id: uuid.UUID,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = MissionService(session)
    await service.delete(player.id, mission_id)
    