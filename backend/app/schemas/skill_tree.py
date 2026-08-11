# ==================================================================
# SKILL TREE SCHEMAS
# ==================================================================

from pydantic import BaseModel


# Model SkillNodeInfo (Single node in the prestige skill tree)
class SkillNodeInfo(BaseModel):
    node_id: str
    path: str
    display_name: str
    description: str
    current_level: int
    max_level: int
    cost_to_upgrade: int | None
    locked_by_choice: bool
    bonus_at_current: float
    bonus_at_next: float | None
    current_effect: str
    next_effect: str | None


# Model SkillTreeResponse (Full tree state for the Skill Tree view)
class SkillTreeResponse(BaseModel):
    nodes: list[SkillNodeInfo]
    pp_total: int
    pp_available: int


# Model UpgradeNodeRequest (Request body to upgrade a skill node)
class UpgradeNodeRequest(BaseModel):
    node_id: str


# Model UpgradeNodeResponse (Response after a successful node upgrade)
class UpgradeNodeResponse(BaseModel):
    node_id: str
    new_level: int
    pp_spent: int
    pp_available: int
    next_effect: str | None


# Model ResetTreeResponse (Response after resetting all skill nodes)
class ResetTreeResponse(BaseModel):
    pp_refunded: int
    pp_available: int
