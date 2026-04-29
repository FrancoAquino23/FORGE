# ==================================================================
# MISSION SCHEMAS
# ==================================================================

import uuid
from datetime import datetime
from pydantic import BaseModel

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

# Model MissionListResponse (Data - Response for listing missions)
class MissionListResponse(BaseModel):
    missions: list[MissionProgress]

# Model MissionClaimResponse (Data - Response for claiming a mission)
class MissionClaimResponse(BaseModel):
    mission_id: uuid.UUID
    attribute_code: str
    material_name: str
    xp_earned: int
    material_earned: int
    new_attribute_level: int
    leveled_up: bool
