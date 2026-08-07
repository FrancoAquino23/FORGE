# ==================================================================
# PRESTIGE SCHEMAS
# ==================================================================

from pydantic import BaseModel
from app.schemas.mission import AchievementUnlocked

# Model PrestigeStatusResponse (Full status for the Prestige view)
class PrestigeStatusResponse(BaseModel):
    prestige_count: int
    threshold_level: int
    stardust_cost: int
    prestige_points_total: int = 0
    prestige_points_available: int = 0

# Model PrestigeUpResponse (Response after a full prestige up, all attributes reset)
class PrestigeUpResponse(BaseModel):
    prestige_number: int
    attributes_reset: list[str]
    pp_earned: int
    newly_unlocked: list[AchievementUnlocked] = []
