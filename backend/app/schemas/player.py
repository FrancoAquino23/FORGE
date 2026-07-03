# ==================================================================
# PLAYER PROFILE SCHEMAS
# ==================================================================

from pydantic import BaseModel

# Model AttributeProfile (Data)
class AttributeProfile(BaseModel):
    code: str
    name: str
    level: int
    xp_current: int
    xp_to_next: int
    material_name: str
    material_balance: int

# Model PlayerProfileResponse (Endpoint Response)
class PlayerProfileResponse(BaseModel):
    username: str
    prestige_count: int
    prestige_points_total: int
    prestige_points_available: int
    attributes: list[AttributeProfile]

# Model PlayerStatsResponse (Endpoint Response)
class PlayerStatsResponse(BaseModel):
    total_missions_completed: int
    total_xp_earned: int
    total_materials_earned: int
    best_streak: int

# Model CategoryBreakdown (Data)
class CategoryBreakdown(BaseModel):
    main_quest: int
    side_quest: int
    daily_grind: int
    total: int

# Model ThreatBreakdown (Data)
class ThreatBreakdown(BaseModel):
    minor: int
    major: int
    critical: int

# Model AttributeMetric (Data)
class AttributeMetric(BaseModel):
    code: str
    name: str
    missions_completed: int
    xp_earned: int

# Model AvgResolutionTime (Data)
class AvgResolutionTime(BaseModel):
    main_quest_hours: float | None
    side_quest_hours: float | None
    daily_grind_hours: float | None

# Model PlayerMetricsResponse (Endpoint Response)
class PlayerMetricsResponse(BaseModel):
    week_label: str
    week_offset: int
    has_previous: bool
    has_next: bool
    category_breakdown: CategoryBreakdown
    threat_breakdown: ThreatBreakdown
    attribute_breakdown: list[AttributeMetric]
    avg_resolution_hours: AvgResolutionTime
