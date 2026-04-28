import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator

AttributeCode = Literal["S", "P", "E", "C", "I", "A", "L"]


class ActivityLogRequest(BaseModel):
    attribute_code: AttributeCode
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) else v


class LevelUpInfo(BaseModel):
    occurred: bool
    new_level: int


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

    streak_current: int
    streak_broken: bool
    streak_shield_used: bool

    material_balance: int
    overcharge_was_active: bool
