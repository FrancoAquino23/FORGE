from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.player import PlayerProfileResponse
from app.services.player_service import PlayerService

router = APIRouter(prefix="/player", tags=["player"])


@router.get("/profile", response_model=PlayerProfileResponse)
async def get_profile(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> PlayerProfileResponse:
    """Returns the current player's full S.P.E.C.I.A.L. profile, streak, and inventory."""
    service = PlayerService(session)
    return await service.get_profile(player)
