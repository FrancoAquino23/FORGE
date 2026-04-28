from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.activity import ActivityLogRequest, ActivityLogResponse
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/activities", tags=["activities"])


@router.post("/log", response_model=ActivityLogResponse, status_code=201)
async def log_activity(
    body: ActivityLogRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> ActivityLogResponse:
    """
    Register a real-world activity.
    Rewards XP to the corresponding S.P.E.C.I.A.L. attribute and materials to inventory.
    Updates the daily streak. All writes are atomic.
    """
    service = ActivityService(session)
    return await service.log_activity(player, body)
