# ==================================================================
# REWARD SERVICE 
# ==================================================================

import math


# Model RewardService (Data)
class RewardService:
    BASE_XP: int = 25
    BASE_MATERIALS: int = 20
    RELIC_BONUS_PER_LEVEL: float = 0.05  # 5% per level
    RELIC_BASE_COST: int = 25

    # XP required to advance from a given level to the next (Following a 1.5 power curve)
    @staticmethod
    def xp_for_level(level: int) -> int:
        return math.floor(100 * (level ** 1.5))

    # Cost to upgrade a relic from its current level to the next
    @staticmethod
    def upgrade_cost(current_level: int) -> int:
        return max(1, int(RewardService.RELIC_BASE_COST * (current_level ** 1.5)))

    # Bonus multiplier based on relic attribute level and prestige count (Luck)
    @staticmethod
    def _bonus_multiplier(relic_attr_level: int, prestige_count: int) -> float:
        bonus = (relic_attr_level + prestige_count) * RewardService.RELIC_BONUS_PER_LEVEL
        return 1.0 + bonus

    # Calculate final XP reward for an activity, applying relic and luck bonuses
    @staticmethod
    def calculate_xp(relic_attr_level: int, prestige_count: int) -> int:
        mult = RewardService._bonus_multiplier(relic_attr_level, prestige_count)
        return max(1, int(RewardService.BASE_XP * mult))

    # Calculate final material reward for an activity, applying relic and luck bonuses
    @staticmethod
    def calculate_materials(relic_attr_level: int, prestige_count: int) -> int:
        mult = RewardService._bonus_multiplier(relic_attr_level, prestige_count)
        return max(1, int(RewardService.BASE_MATERIALS * mult))

    # Apply relic and luck bonuses to stored mission rewards at claim time
    @staticmethod
    def apply_mission_bonuses(
        base_xp: int, base_mat: int, relic_attr_level: int, prestige_count: int
    ) -> tuple[int, int]:
        mult = RewardService._bonus_multiplier(relic_attr_level, prestige_count)
        return max(1, int(base_xp * mult)), max(1, int(base_mat * mult))

    # Apply earned XP to an attribute, calculating new XP, level, XP to next level, and whether a level-up occurred
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
