# ==================================================================
# FORGE ROUTES
# ==================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.forge import TransmuteRequest, TransmuteResponse
from app.services.forge_service import ForgeService

# Create the router for forge-related endpoints
router = APIRouter(prefix="/forge", tags=["forge"])

# Endpoint (POST /forge/transmute) to burn equal amounts of ordinary materials for Stardust
@router.post("/transmute", response_model=TransmuteResponse)
async def transmute(
    body: TransmuteRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> TransmuteResponse:

    service = ForgeService(session)
    return await service.transmute(player.id, body)
