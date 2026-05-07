# ==================================================================
# ACTIVITY LOGGING SCHEMAS
# ==================================================================

import uuid
from typing import Literal
from pydantic import BaseModel, Field, field_validator

# Attribute codes for validation
AttributeCode = Literal["S", "P", "E", "C", "I", "A", "L"]

# Model ActivityLogRequest (Request to log an activity)
class ActivityLogRequest(BaseModel):
    attribute_code: AttributeCode
    description: str | None = Field(default=None, max_length=500)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) else v

# Model LevelUpInfo (Information about level-up events)
class LevelUpInfo(BaseModel):
    occurred: bool
    new_level: int

# Model ActivityLogResponse (Response after logging an activity)
class ActivityLogResponse(BaseModel):
    activity_id: uuid.UUID
    attribute_code: str
    material_name: str
    xp_earned: int
    material_earned: int
    new_attribute_level: int
    new_attribute_xp: int
    xp_to_next_level: int
    level_up: LevelUpInfo
    material_balance: int
