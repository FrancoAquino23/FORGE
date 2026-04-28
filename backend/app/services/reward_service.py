import math
from decimal import Decimal


class RewardService:
    """
    Pure math layer — no I/O, no DB, fully testable.
    All bonuses are percentages (5.00 = +5%).
    """

    BASE_XP: int = 25
    XP_PER_MINUTE: float = 0.5
    MAX_XP_PER_ACTIVITY: int = 100

    BASE_MATERIALS: int = 20
    MATERIAL_PER_MINUTE: float = 0.2
    MAX_MATERIAL_DURATION_BONUS: int = 20

    @staticmethod
    def xp_for_level(level: int) -> int:
        """XP required to advance FROM `level` to the next level."""
        return math.floor(100 * (level**1.5))

    @staticmethod
    def calculate_xp(
        duration_minutes: int | None,
        xp_bonus_pct: Decimal,
        overcharge_multiplier: Decimal,
    ) -> int:
        """
        Returns XP earned for a single activity.
        overcharge_multiplier comes from an active Overcharge Chip (normally 1.0).
        """
        base = RewardService.BASE_XP
        if duration_minutes:
            duration_bonus = int(duration_minutes * RewardService.XP_PER_MINUTE)
            base = min(base + duration_bonus, RewardService.MAX_XP_PER_ACTIVITY)

        multiplier = (1 + float(xp_bonus_pct) / 100) * float(overcharge_multiplier)
        return max(1, int(base * multiplier))

    @staticmethod
    def calculate_materials(
        duration_minutes: int | None,
        global_bonus_pct: Decimal,
        attribute_bonus_pct: Decimal,
    ) -> int:
        """
        Returns materials earned for a single activity.
        Applies additive prestige buffs: global + attribute-specific.
        """
        base = RewardService.BASE_MATERIALS
        if duration_minutes:
            duration_bonus = min(
                int(duration_minutes * RewardService.MATERIAL_PER_MINUTE),
                RewardService.MAX_MATERIAL_DURATION_BONUS,
            )
            base += duration_bonus

        total_pct = float(global_bonus_pct) + float(attribute_bonus_pct)
        multiplier = 1 + total_pct / 100
        return max(1, int(base * multiplier))

    @staticmethod
    def apply_xp_to_attribute(
        current_xp: int,
        current_level: int,
        xp_earned: int,
    ) -> tuple[int, int, int, bool]:
        """
        Returns (new_xp, new_level, new_xp_to_next, did_level_up).
        Handles multi-level-ups from a single activity.
        """
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
