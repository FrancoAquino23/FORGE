# ==================================================================
# FORGE SCHEMAS
# ==================================================================

from typing import Literal
from pydantic import BaseModel, Field

AttributeCode = Literal["S", "P", "E", "C", "I", "A"]

# Model ForgeUpgradeRequest (Endpoint Request)
class ForgeUpgradeRequest(BaseModel):
    attribute_code: AttributeCode

# Model ForgeUpgradeResponse (Data)
class ForgeUpgradeResponse(BaseModel):
    attribute_code: str
    from_level: int
    to_level: int
    materials_spent: int
    material_name: str
    new_material_balance: int

# Model TransmuteRequest (Request to transmute ordinary materials into Stardust)
class TransmuteRequest(BaseModel):
    batch_size: int = Field(1, ge=1)

# Model TransmuteResponse (Result of a transmutation operation)
class TransmuteResponse(BaseModel):
    batch_size: int
    materials_consumed_each: int
    stardust_gained: int
    new_stardust_balance: int
