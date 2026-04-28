# ==================================================================
# FORGE SCHEMAS
# ==================================================================

from pydantic import BaseModel
from app.schemas.activity import AttributeCode

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
