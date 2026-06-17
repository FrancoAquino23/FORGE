# ==================================================================
# FORGE SCHEMAS
# ==================================================================

from pydantic import BaseModel, Field

# Model TransmuteRequest (Request to transmute ordinary materials into Stardust)
class TransmuteRequest(BaseModel):
    batch_size: int = Field(1, ge=1)

# Model TransmuteResponse (Result of a transmutation operation)
class TransmuteResponse(BaseModel):
    batch_size: int
    materials_consumed_each: int
    stardust_gained: int
    new_stardust_balance: int
