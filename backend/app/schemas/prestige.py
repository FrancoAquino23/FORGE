# ==================================================================
# PRESTIGE SCHEMAS
# ==================================================================

from decimal import Decimal
from pydantic import BaseModel

# Model BuffTypeInfo (Catalog entry for a buff type)
class BuffTypeInfo(BaseModel):
    code: str
    display_name: str
    target_type: str
    bonus_percent: Decimal
    attribute_code: str | None = None

# Model PlayerBuffInfo (Active buff on the player)
class PlayerBuffInfo(BaseModel):
    buff_type_code: str
    display_name: str
    target_type: str
    stack_count: int
    total_bonus: Decimal

# Model PrestigeStatusResponse (Full status for the Prestige view)
class PrestigeStatusResponse(BaseModel):
    prestige_count: int
    threshold_level: int
    material_cost: int
    active_buffs: list[PlayerBuffInfo]
    available_buff_types: list[BuffTypeInfo]
    prestige_points_total: int = 0
    prestige_points_available: int = 0

# Model PrestigeUpRequest (Request body for the all-in prestige up action)
class PrestigeUpRequest(BaseModel):
    buff_type_code: str

# Model PrestigeUpResponse (Response after a full prestige up, all attributes reset)
class PrestigeUpResponse(BaseModel):
    prestige_number: int
    attributes_reset: list[str]
    buff_type_code: str
    buff_display_name: str
    new_stack_count: int
    new_total_bonus: Decimal
