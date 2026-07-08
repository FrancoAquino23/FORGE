# ==================================================================
# PLAYER ROUTES
# ==================================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.core.exceptions import UnauthorizedError
from app.core.security import verify_password
from app.database import get_db
from app.models.player import PlayerProfile
from app.models.player import User
from app.schemas.player import DeleteAccountRequest, PlayerMetricsResponse, PlayerProfileResponse, PlayerStatsResponse
from app.services.achievement_service import AchievementService
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

# Endpoint (GET /player/stats) to retrieve lifetime mission statistics
@router.get("/stats", response_model=PlayerStatsResponse)
async def get_stats(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> PlayerStatsResponse:

    service = PlayerService(session)
    return await service.get_stats(player)

# Endpoint (GET /player/achievements) to retrieve all achievements
@router.get("/achievements")
async def get_achievements(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> list[dict]:

    return await AchievementService(session).get_all(player)

# Endpoint (GET /player/metrics) to retrieve weekly metrics
@router.get("/metrics", response_model=PlayerMetricsResponse)
async def get_metrics(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
    week_offset: int = Query(default=0, le=0),
) -> PlayerMetricsResponse:

    service = PlayerService(session)
    return await service.get_metrics(player, week_offset)

# Endpoint (DELETE /player/account) permanently delete account
@router.delete("/account", status_code=204)
async def delete_account(
    body: DeleteAccountRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> None:
    user = await session.scalar(select(User).where(User.id == player.user_id))
    if not user or not verify_password(body.password, user.password_hash):
        raise UnauthorizedError("Invalid password")
    await session.delete(user)
    await session.commit()
