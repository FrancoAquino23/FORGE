# ==================================================================
# CONSUMABLE SCHEMAS
# ==================================================================

from datetime import datetime
from pydantic import BaseModel

# Model for consumable item in inventory (Data)
class ConsumableItem(BaseModel):
    consumable_code: str
    name: str
    description: str | None
    effect_type: str
    quantity: int
    is_active: bool = False
    active_until: datetime | None = None

# Model for inventory response (List of consumable items)
class InventoryResponse(BaseModel):
    items: list[ConsumableItem]

# Model for using a consumable (Request & Response)
class UseConsumableRequest(BaseModel):
    consumable_code: str

# Model for response after using a consumable (Data)
class UseConsumableResponse(BaseModel):
    consumable_code: str
    name: str
    effect_type: str
    quantity_remaining: int
    active_until: datetime | None = None
    message: str
