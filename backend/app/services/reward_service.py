# ==================================================================
# REWARD SERVICE
# ==================================================================

from app.constants import MAX_ATTRIBUTE_LEVEL as _MAX_LEVEL

# Table of XP required to level up each attribute level
_XP_TABLE: dict[int, int] = {
    1:  2_000,
    2:  4_000,
    3:  6_000,
    4:  9_000,
    5:  12_000,
    6:  15_000,
    7:  20_000,
    8:  25_000,
    9:  30_000,
    10: 0,
}

# Table of materials required to upgrade a relic level
_RELIC_UPGRADE_TABLE: dict[int, int] = {
    1:  1_000,
    2:  1_500,
    3:  2_000,
    4:  2_500,
    5:  3_500,
    6:  4_500,
    7:  6_000,
    8:  7_500,
    9:  9_000,
    10: 12_000,
}


# XP scale factor based on prestige_count
def xp_scale_factor(prestige_count: int) -> float:
    p = prestige_count
    if p <= 10: return 1.0 + p * 0.10
    if p <= 25: return 2.0 + (p - 10) * 0.15
    if p <= 40: return 4.25 + (p - 25) * 0.20
    return 7.25 + (p - 40) * 0.25

# Permanent prestige bonus multiplier (never resets)
def prestige_bonus(prestige_count: int) -> float:
    p = prestige_count
    if p <= 10: return 1.0 + p * 0.01
    if p <= 25: return 1.10 + (p - 10) * 0.02
    if p <= 40: return 1.40 + (p - 25) * 0.03
    return min(2.15, 1.85 + (p - 40) * 0.03)


# Model RewardService (Data)
class RewardService:
    RELIC_BONUS_PER_LEVEL: float = 0.05 

    # Helper method to get XP required
    @staticmethod
    def xp_for_level(level: int) -> int:
        return _XP_TABLE.get(level, 0)

    # Helper method to get material required
    @staticmethod
    def upgrade_cost(current_level: int) -> int:
        return _RELIC_UPGRADE_TABLE.get(current_level, 0)

    # Helper method to calculate bonus multiplier (relics)
    @staticmethod
    def _bonus_multiplier(relic_attr_level: int, luck_relic_level: int = 0) -> float:
        bonus = (relic_attr_level + luck_relic_level) * RewardService.RELIC_BONUS_PER_LEVEL
        return 1.0 + bonus

    # Helper method to apply bonuses to mission rewards
    @staticmethod
    def apply_mission_bonuses(
        base_xp: int, base_mat: int, relic_attr_level: int, luck_relic_level: int = 0
    ) -> tuple[int, int]:
        mult = RewardService._bonus_multiplier(relic_attr_level, luck_relic_level)
        return max(1, round(base_xp * mult)), max(1, round(base_mat * mult))

    # Helper method to apply XP to an attribute
    @staticmethod
    def apply_xp_to_attribute(
        current_xp: int,
        current_level: int,
        xp_earned: int,
        xp_discount: float = 0.0,
        prestige_factor: float = 1.0,
    ) -> tuple[int, int, int, bool]:
        if current_level >= _MAX_LEVEL:
            return 0, _MAX_LEVEL, 0, False

        xp = current_xp + xp_earned
        level = current_level
        leveled_up = False

        while level < _MAX_LEVEL:
            needed = max(1, round(_XP_TABLE.get(level, 0) * prestige_factor * (1.0 - xp_discount)))
            if xp < needed:
                break
            xp -= needed
            level += 1
            leveled_up = True

        if level >= _MAX_LEVEL:
            return 0, _MAX_LEVEL, 0, leveled_up

        xp_to_next = max(1, round(_XP_TABLE.get(level, 0) * prestige_factor * (1.0 - xp_discount)))
        return xp, level, xp_to_next, leveled_up
