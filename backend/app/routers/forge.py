from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.forge import ForgeUpgradeRequest, ForgeUpgradeResponse
from app.services.forge_service import ForgeService

router = APIRouter(prefix="/forge", tags=["forge"])


@router.post("/upgrade", response_model=ForgeUpgradeResponse)
async def upgrade_attribute(
    body: ForgeUpgradeRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> ForgeUpgradeResponse:
    """
    Spend attribute materials to directly upgrade a S.P.E.C.I.A.L. level.
    Cost: 25 × current_level units of the attribute's own material.
    XP resets to 0 on forge upgrade. Transaction is atomic.
    """
    service = ForgeService(session)
    return await service.upgrade_attribute(player, body.attribute_code)
