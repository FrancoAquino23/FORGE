# ==================================================================
# FORGE ROUTES
# ==================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.forge import ForgeUpgradeRequest, ForgeUpgradeResponse
from app.services.forge_service import ForgeService

# Create the router for forge-related endpoints
router = APIRouter(prefix="/forge", tags=["forge"])

# Endpoint (POST /forge/upgrade) to upgrade a S.P.E.C.I.A.L. attribute using attribute materials
@router.post("/upgrade", response_model=ForgeUpgradeResponse)
async def upgrade_attribute(
    body: ForgeUpgradeRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> ForgeUpgradeResponse:

    service = ForgeService(session)
    return await service.upgrade_attribute(player, body.attribute_code)
