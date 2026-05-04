# ==================================================================
# RELIC SCHEMAS
# ==================================================================

from pydantic import BaseModel

# Model RelicInfo (Detailed info for each relic in the list)
class RelicInfo(BaseModel):
    attribute_code: str
    attribute_name: str
    level: int
    total_invested: int
    bonus_pct: int         
    upgrade_cost: int | None 
    can_upgrade: bool
    material_balance: int
    is_luck: bool

# Model RelicListResponse (Response schema for GET /relics)
class RelicListResponse(BaseModel):
    relics: list[RelicInfo]

# Model RelicUpgradeResponse (Response schema for POST /relics/upgrade)
class RelicUpgradeResponse(BaseModel):
    attribute_code: str
    new_level: int
    material_spent: int
    new_balance: int
    new_bonus_pct: int
