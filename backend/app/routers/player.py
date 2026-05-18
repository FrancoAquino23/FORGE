# ==================================================================
# PLAYER ROUTES
# ==================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.player import PlayerProfileResponse
from app.services.player_service import PlayerService

# Create the router for player-related endpoints
router = APIRouter(prefix="/player", tags=["player"])

# Endpoint (GET /player/profile) to retrieve the player's profile & inventory
@router.get("/profile", response_model=PlayerProfileResponse)
async def get_profile(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> PlayerProfileResponse:

    service = PlayerService(session)
    return await service.get_profile(player)
