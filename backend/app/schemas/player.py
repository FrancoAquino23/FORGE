# ==================================================================
# PLAYER PROFILE SCHEMAS
# ==================================================================

from pydantic import BaseModel


class AttributeProfile(BaseModel):
    code: str
    name: str
    level: int
    xp_current: int
    xp_to_next: int
    material_name: str
    material_balance: int


class PlayerProfileResponse(BaseModel):
    username: str
    prestige_count: int
    streak_current: int
    streak_max: int
    attributes: list[AttributeProfile]
