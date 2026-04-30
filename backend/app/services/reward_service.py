# ==================================================================
# REWARD SERVICE 
# ==================================================================

import math
from decimal import Decimal

# Model RewardService (Data)
class RewardService:
    BASE_XP: int = 25
    BASE_MATERIALS: int = 20

    # XP required to advance from a given level to the next (Following a 1.5 power curve)
    @staticmethod
    def xp_for_level(level: int) -> int:
        return math.floor(100 * (level**1.5))

    # Calculates XP earned for an activity
    @staticmethod
    def calculate_xp(xp_bonus_pct: Decimal, overcharge_multiplier: Decimal) -> int:
        multiplier = (1 + float(xp_bonus_pct) / 100) * float(overcharge_multiplier)
        return max(1, int(RewardService.BASE_XP * multiplier))

    # Calculates materials earned for an activity
    @staticmethod
    def calculate_materials(global_bonus_pct: Decimal, attribute_bonus_pct: Decimal) -> int:
        total_pct = float(global_bonus_pct) + float(attribute_bonus_pct)
        multiplier = 1 + total_pct / 100
        return max(1, int(RewardService.BASE_MATERIALS * multiplier))

    # Applies earned XP to an attribute
    @staticmethod
    def apply_xp_to_attribute(
        current_xp: int,
        current_level: int,
        xp_earned: int,
    ) -> tuple[int, int, int, bool]:
        xp = current_xp + xp_earned
        level = current_level
        leveled_up = False

        xp_to_next = RewardService.xp_for_level(level)
        while xp >= xp_to_next:
            xp -= xp_to_next
            level += 1
            xp_to_next = RewardService.xp_for_level(level)
            leveled_up = True

        return xp, level, xp_to_next, leveled_up
