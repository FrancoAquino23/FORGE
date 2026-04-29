# ==================================================================
# GAME MASTER ROUTES
# ==================================================================

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.gm import DiagnosticResponse
from app.services.gm_service import GmService

# API Router for Game Master (GM) related endpoints
router = APIRouter(tags=["gm"])

# Endpoint (GET /player/diagnostics) - AI narrative analysis of player progress
@router.get("/player/diagnostics", response_model=DiagnosticResponse)
async def get_player_diagnostics(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> DiagnosticResponse:
    service = GmService(session)
    return await service.generate_diagnostic(player.id)
