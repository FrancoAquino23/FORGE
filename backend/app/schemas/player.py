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
    prestige_points_total: int
    prestige_points_available: int
    attributes: list[AttributeProfile]

# Model PlayerStatsResponse (Endpoint Response)
class PlayerStatsResponse(BaseModel):
    main_quest_completed: int
    side_quest_completed: int
    daily_grind_completed: int
    total_missions_completed: int
    total_xp_earned: int
    total_materials_earned: int
    best_streak: int
