# ==================================================================
# PRESTIGE ROUTES
# ==================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.prestige import (
    PrestigeStatusResponse,
    PrestigeUpRequest, PrestigeUpResponse,
)
from app.schemas.skill_tree import (
    ResetTreeResponse,
    SkillTreeResponse,
    UpgradeNodeRequest,
    UpgradeNodeResponse,
)
from app.services.prestige_service import PrestigeService
from app.services.skill_tree_service import SkillTreeService

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

# Endpoint (GET /prestige/tree) - Returns full skill tree
@router.get("/tree", response_model=SkillTreeResponse)
async def get_skill_tree(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> SkillTreeResponse:
    service = SkillTreeService(session)
    return await service.get_tree(player)

# Endpoint (POST /prestige/tree/upgrade) - Spend points per prestige to upgrade a skill node
@router.post("/tree/upgrade", response_model=UpgradeNodeResponse)
async def upgrade_node(
    body: UpgradeNodeRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> UpgradeNodeResponse:
    service = SkillTreeService(session)
    return await service.upgrade_node(player, body.node_id)

# Endpoint (POST /prestige/tree/reset) - Refund all points per prestige invested in the skill tree
@router.post("/tree/reset", response_model=ResetTreeResponse)
async def reset_skill_tree(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> ResetTreeResponse:
    service = SkillTreeService(session)
    return await service.reset_tree(player)
