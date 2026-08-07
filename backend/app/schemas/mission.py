# ==================================================================
# MISSION SCHEMAS
# ==================================================================

import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

MissionCategory = Literal["MAIN_QUEST", "SIDE_QUEST", "DAILY_GRIND"]
ThreatLevel = Literal["MINOR", "MAJOR", "CRITICAL"]

# Model CheckpointSchema (Data - A single sub-task step within a mission)
class CheckpointSchema(BaseModel):
    id: uuid.UUID
    description: str
    is_completed: bool
    order_index: int

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
    status: str = "ACTIVE"
    category: str | None = None
    due_date: datetime | None = None
    description: str | None = None
    is_favorite: bool = False
    checkpoints: list[CheckpointSchema] = []
    threat_level: str = "MAJOR"
    current_streak: int = 0

# Model MissionListResponse (Data - Response for listing missions)
class MissionListResponse(BaseModel):
    missions: list[MissionProgress]

# Model AchievementUnlocked (Data - Response for an unlocked achievement)
class AchievementUnlocked(BaseModel):
    code: str
    title: str
    description: str

# Model MissionClaimResponse (Data - Response for claiming a mission)
class MissionClaimResponse(BaseModel):
    mission_id: uuid.UUID
    attribute_code: str
    material_name: str
    xp_earned: int
    material_earned: int
    new_attribute_level: int
    leveled_up: bool
    newly_unlocked: list[AchievementUnlocked] = []

# Model DeployMissionRequest (Request to dispatch a player-created mission)
class DeployMissionRequest(BaseModel):
    attribute_code: Literal["S", "P", "E", "C", "I", "A"]
    category: MissionCategory
    description: str = Field(default="", max_length=500)
    detail: str | None = Field(default=None, max_length=1000)
    due_date: datetime | None = None
    steps: list[str] = Field(default_factory=list)
    threat_level: ThreatLevel = "MAJOR"
    is_draft: bool = False

# Model ActivateMissionResponse (Response after activating a DRAFT mission)
class ActivateMissionResponse(BaseModel):
    mission_id: uuid.UUID
    title: str
    category: str

# Model DeployMissionResponse (Response after dispatching a mission)
class DeployMissionResponse(BaseModel):
    mission_id: uuid.UUID
    title: str
    category: str
    attribute_code: str
    reward_xp: int
    reward_material_qty: int
    threat_level: str = "MAJOR"

# Model CheckpointUpdateItem (Request a single checkpoint entry for update operations)
class CheckpointUpdateItem(BaseModel):
    id: uuid.UUID | None = None
    description: str = Field(..., max_length=500)
    order_index: int

# Model UpdateMissionRequest (Request to edit an existing mission)
class UpdateMissionRequest(BaseModel):
    objective_description: str | None = None
    detail: str | None = None
    due_date: datetime | None = None
    checkpoints: list[CheckpointUpdateItem] | None = None
    threat_level: ThreatLevel | None = None

# Model ToggleCheckpointResponse (Data - Response after toggling a checkpoint)
class ToggleCheckpointResponse(BaseModel):
    checkpoint_id: uuid.UUID
    is_completed: bool

# Model MissionHistoryItem (Data - Single completed mission in the history)
class MissionHistoryItem(BaseModel):
    mission_id: uuid.UUID
    title: str
    objective_description: str
    attribute_code: str
    attribute_name: str
    category: str | None = None
    threat_level: str = "MAJOR"
    reward_xp: int
    reward_material_qty: int
    completed_at: datetime

# Model MissionHistoryResponse (Data - Response for listing completed missions)
class MissionHistoryResponse(BaseModel):
    missions: list[MissionHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int
