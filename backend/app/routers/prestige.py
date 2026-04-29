# ==================================================================
# PRESTIGE ROUTES
# ==================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.prestige import PrestigeSacrificeRequest, PrestigeSacrificeResponse
from app.services.prestige_service import PrestigeService

router = APIRouter(prefix="/prestige", tags=["prestige"])


@router.post("/sacrifice", response_model=PrestigeSacrificeResponse)
async def sacrifice(
    body: PrestigeSacrificeRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> PrestigeSacrificeResponse:
    """
    Sacrifices an attribute at the prestige threshold to earn a permanent passive buff.
    The chosen attribute resets to level 1; accumulated XP is lost. Transaction is atomic.
    """
    service = PrestigeService(session)
    return await service.sacrifice(player, body.attribute_code, body.buff_type_code)
