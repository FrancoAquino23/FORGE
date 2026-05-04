# ==================================================================
# RELIC ROUTES
# ==================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.relic import RelicListResponse, RelicUpgradeResponse
from app.services.relic_service import RelicService

# Create a router for relic-related endpoints
router = APIRouter(prefix="/relics", tags=["relics"])

# Endpoint (GET /relics) to retrieve all relics for the current player
@router.get("", response_model=RelicListResponse)
async def get_relics(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> RelicListResponse:
    service = RelicService(session)
    return await service.get_all(player.id, player.prestige_count)

# Endpoint (POST /relics/{attribute_code}/upgrade) to upgrade a specific relic for the current player
@router.post("/{attribute_code}/upgrade", response_model=RelicUpgradeResponse)
async def upgrade_relic(
    attribute_code: str,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> RelicUpgradeResponse:
    service = RelicService(session)
    return await service.upgrade(player.id, attribute_code.upper())
