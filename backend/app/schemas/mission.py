# ==================================================================
# MISSION SCHEMAS
# ==================================================================

import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

MissionCategory = Literal["MAIN_QUEST", "SIDE_QUEST", "DAILY_GRIND"]

# Model MissionProgress (Data - Represents a mission with progress details)
class MissionProgress(BaseModel):
    mission_id: uuid.UUID
    title: str
    objective_description: str
    objective_type: str
    objective_target: int
    current_progress: int
    attribute_code: str
    attribute_name: str
    reward_xp: int
    reward_material_qty: int
    expires_at: datetime
    is_completable: bool
    ai_generated: bool = False
    status: str = "ACTIVE"
    category: str | None = None

# Model MissionListResponse (Data - Response for listing missions)
class MissionListResponse(BaseModel):
    missions: list[MissionProgress]
    ai_ready: bool = False

# Model MissionClaimResponse (Data - Response for claiming a mission)
class MissionClaimResponse(BaseModel):
    mission_id: uuid.UUID
    attribute_code: str
    material_name: str
    xp_earned: int
    material_earned: int
    new_attribute_level: int
    leveled_up: bool

# Model DeployMissionRequest (Request to dispatch a player-created mission)
class DeployMissionRequest(BaseModel):
    attribute_code: str = Field(..., pattern="^[SPECIAL]$")
    category: MissionCategory
    description: str = Field(default="", max_length=500)

# Model DeployMissionResponse (Response after dispatching a mission)
class DeployMissionResponse(BaseModel):
    mission_id: uuid.UUID
    title: str
    category: str
    attribute_code: str
    reward_xp: int
    reward_material_qty: int
