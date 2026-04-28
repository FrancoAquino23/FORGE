# ==================================================================
# ACTIVITIES ROUTES
# ==================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.activity import ActivityLogRequest, ActivityLogResponse
from app.services.activity_service import ActivityService

# Router for activity-related endpoints (logging activities, fetching activity history)
router = APIRouter(prefix="/activities", tags=["activities"])

# Endpoint (POST /activities/log) for logging a real-world activity
@router.post("/log", response_model=ActivityLogResponse, status_code=201)
async def log_activity(
    body: ActivityLogRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> ActivityLogResponse:

    service = ActivityService(session)
    return await service.log_activity(player, body)
