# ==================================================================
# PLAYER PROFILE SCHEMAS
# ==================================================================

from pydantic import BaseModel

# Model AttributeProfile (Data)
class AttributeProfile(BaseModel):
    code: str
    name: str
    level: int
    xp_current: int
    xp_to_next: int
    material_name: str
    material_balance: int

# Model PlayerProfileResponse (Endpoint Response)
class PlayerProfileResponse(BaseModel):
    username: str
    prestige_count: int
    streak_current: int
    streak_max: int
    attributes: list[AttributeProfile]
