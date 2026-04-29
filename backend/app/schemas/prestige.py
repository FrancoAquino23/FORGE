# ==================================================================
# PRESTIGE SCHEMAS
# ==================================================================

from decimal import Decimal
from pydantic import BaseModel
from app.schemas.activity import AttributeCode

# Model PrestigeSacrificeRequest (Data - Request body for sacrificing an attribute at prestige)
class PrestigeSacrificeRequest(BaseModel):
    attribute_code: AttributeCode
    buff_type_code: str

# Model PrestigeSacrificeResponse (Data - Response for sacrificing an attribute at prestige)
class PrestigeSacrificeResponse(BaseModel):
    prestige_number: int
    attribute_reset_code: str
    level_before: int
    buff_type_code: str
    buff_display_name: str
    new_stack_count: int
    new_total_bonus: Decimal
