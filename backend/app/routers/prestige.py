# ==================================================================
# PRESTIGE ROUTES
# ==================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.prestige import (
    PrestigeSacrificeRequest, PrestigeSacrificeResponse, PrestigeStatusResponse,
    PrestigeUpRequest, PrestigeUpResponse,
)
from app.services.prestige_service import PrestigeService

# APIRouter for prestige-related endpoints
router = APIRouter(prefix="/prestige", tags=["prestige"])

# Endpoint (GET /prestige/status) - Returns prestige status for the Altar view
@router.get("/status", response_model=PrestigeStatusResponse)
async def get_prestige_status(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> PrestigeStatusResponse:
    service = PrestigeService(session)
    return await service.get_status(player)

# Endpoint (POST /prestige/prestige-up) - Sacrifice all attributes at threshold and apply one buff
@router.post("/prestige-up", response_model=PrestigeUpResponse)
async def prestige_up(
    body: PrestigeUpRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> PrestigeUpResponse:
    service = PrestigeService(session)
    return await service.prestige_up(player, body.buff_type_code)

# Endpoint (POST /prestige/sacrifice) - Sacrifice an attribute for a prestige buff (legacy)
@router.post("/sacrifice", response_model=PrestigeSacrificeResponse)
async def sacrifice(
    body: PrestigeSacrificeRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> PrestigeSacrificeResponse:
    service = PrestigeService(session)
    return await service.sacrifice(player, body.attribute_code, body.buff_type_code)
