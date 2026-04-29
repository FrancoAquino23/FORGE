# ==================================================================
# GAME MASTER SCHEMAS
# ==================================================================

from pydantic import BaseModel

# Model for AI-generated mission item (Data)
class AIMissionItem(BaseModel):
    title: str
    description: str
    attribute_code: str
    objective_type: str
    objective_target: int
    reward_xp: int
    reward_material_qty: int

# Model for a batch of AI-generated missions
class AIMissionBatch(BaseModel):
    missions: list[AIMissionItem]


# Model for diagnostic strengths
class DiagnosticStrength(BaseModel):
    attribute: str
    detail: str

# Model for diagnostic areas needing improvement
class DiagnosticArea(BaseModel):
    attribute: str
    detail: str

# Model for the complete diagnostic response
class DiagnosticResponse(BaseModel):
    narrative: str
    strengths: list[DiagnosticStrength]
    areas_to_improve: list[DiagnosticArea]
    recommendation: str
    tokens_used: int
    cache_hit: bool
