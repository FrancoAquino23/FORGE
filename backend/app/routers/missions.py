# ==================================================================
# MISSION ROUTES
# ==================================================================

import uuid
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.mission import MissionClaimResponse, MissionListResponse
from app.services.mission_service import MissionService

# APIRouter for mission-related endpoints
router = APIRouter(prefix="/missions", tags=["missions"])

# Endpoint (GET /missions/active) - Get active missions with progress
@router.get("/active", response_model=MissionListResponse)
async def get_active_missions(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> MissionListResponse:

    service = MissionService(session)
    return await service.get_active_with_progress(player.id, date.today())

# Endpoint (POST /missions/{mission_id}/claim) - Claim a completed mission
@router.post("/{mission_id}/claim", response_model=MissionClaimResponse)
async def claim_mission(
    mission_id: uuid.UUID,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> MissionClaimResponse:
   
    service = MissionService(session)
    return await service.claim(player.id, mission_id)
