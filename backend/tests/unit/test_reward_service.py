"""
Unit tests for RewardService and StreakService — zero I/O, pure math.
Run: venv/Scripts/pytest.exe tests/unit/test_reward_service.py -v
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.services.reward_service import RewardService
from app.services.streak_service import StreakService


# ── RewardService.xp_for_level ────────────────────────────────────────────────

class TestXpForLevel:
    def test_level_1(self):
        assert RewardService.xp_for_level(1) == 100

    def test_level_2(self):
        # floor(100 * 2^1.5) = floor(282.84) = 282
        assert RewardService.xp_for_level(2) == 282

    def test_level_5(self):
        # floor(100 * 5^1.5) = floor(1118.03) = 1118
        assert RewardService.xp_for_level(5) == 1118

    def test_level_10(self):
        # floor(100 * 10^1.5) = floor(3162.27) = 3162
        assert RewardService.xp_for_level(10) == 3162

    def test_increases_monotonically(self):
        levels = [RewardService.xp_for_level(i) for i in range(1, 20)]
        assert levels == sorted(levels)


# ── RewardService.calculate_xp ───────────────────────────────────────────────

class TestCalculateXp:
    NO_BONUS = Decimal("0.00")
    NO_OVERCHARGE = Decimal("1.0")

    def test_base_no_duration(self):
        xp = RewardService.calculate_xp(None, self.NO_BONUS, self.NO_OVERCHARGE)
        assert xp == 25

    def test_30_minute_session(self):
        # 25 + floor(30 * 0.5) = 25 + 15 = 40
        xp = RewardService.calculate_xp(30, self.NO_BONUS, self.NO_OVERCHARGE)
        assert xp == 40

    def test_90_minute_session(self):
        # 25 + floor(90 * 0.5) = 25 + 45 = 70
        xp = RewardService.calculate_xp(90, self.NO_BONUS, self.NO_OVERCHARGE)
        assert xp == 70

    def test_caps_at_max(self):
        # 25 + floor(300 * 0.5) = 25 + 150 → capped at 100
        xp = RewardService.calculate_xp(300, self.NO_BONUS, self.NO_OVERCHARGE)
        assert xp == 100

    def test_overcharge_chip_doubles(self):
        xp = RewardService.calculate_xp(None, self.NO_BONUS, Decimal("2.0"))
        assert xp == 50  # 25 * 2

    def test_xp_bonus_pct_applied(self):
        # 25 * 1.10 = 27.5 → int = 27
        xp = RewardService.calculate_xp(None, Decimal("10.00"), self.NO_OVERCHARGE)
        assert xp == 27

    def test_minimum_is_1(self):
        xp = RewardService.calculate_xp(None, Decimal("0"), Decimal("0.01"))
        assert xp >= 1

    def test_overcharge_and_bonus_stack(self):
        # 25 * (1 + 0.10) * 2.0 = 25 * 1.1 * 2 = 55
        xp = RewardService.calculate_xp(None, Decimal("10.00"), Decimal("2.0"))
        assert xp == 55


# ── RewardService.calculate_materials ────────────────────────────────────────

class TestCalculateMaterials:
    NO_BONUS = Decimal("0.00")

    def test_base_no_duration(self):
        mats = RewardService.calculate_materials(None, self.NO_BONUS, self.NO_BONUS)
        assert mats == 20

    def test_60_minute_session(self):
        # 20 + min(floor(60 * 0.2), 20) = 20 + min(12, 20) = 32
        mats = RewardService.calculate_materials(60, self.NO_BONUS, self.NO_BONUS)
        assert mats == 32

    def test_duration_bonus_capped_at_20(self):
        # floor(300 * 0.2) = 60 → capped at 20 → 20 + 20 = 40
        mats = RewardService.calculate_materials(300, self.NO_BONUS, self.NO_BONUS)
        assert mats == 40

    def test_global_bonus_applied(self):
        # 20 * 1.05 = 21
        mats = RewardService.calculate_materials(None, Decimal("5.00"), self.NO_BONUS)
        assert mats == 21

    def test_attribute_bonus_applied(self):
        mats = RewardService.calculate_materials(None, self.NO_BONUS, Decimal("5.00"))
        assert mats == 21

    def test_bonuses_are_additive(self):
        # 20 * (1 + 0.05 + 0.05) = 20 * 1.10 = 22
        mats = RewardService.calculate_materials(
            None, Decimal("5.00"), Decimal("5.00")
        )
        assert mats == 22


# ── RewardService.apply_xp_to_attribute ──────────────────────────────────────

class TestApplyXpToAttribute:
    def test_no_level_up(self):
        xp, level, xp_next, leveled = RewardService.apply_xp_to_attribute(0, 1, 50)
        assert xp == 50
        assert level == 1
        assert leveled is False

    def test_exact_level_up(self):
        # Level 1 needs 100 XP. Give exactly 100.
        xp, level, xp_next, leveled = RewardService.apply_xp_to_attribute(0, 1, 100)
        assert level == 2
        assert xp == 0
        assert leveled is True

    def test_level_up_with_overflow(self):
        # Currently at level 1 with 90 XP. Give 50 XP → overflow of 40 into level 2.
        xp, level, _, leveled = RewardService.apply_xp_to_attribute(90, 1, 50)
        assert level == 2
        assert xp == 40
        assert leveled is True

    def test_multi_level_up(self):
        # Level 1 needs 100, level 2 needs 282. Start at 0, give 400.
        # After level 1: xp = 300, level = 2
        # After level 2: xp = 300 - 282 = 18, level = 3
        xp, level, _, leveled = RewardService.apply_xp_to_attribute(0, 1, 400)
        assert level == 3
        assert xp == 18
        assert leveled is True


# ── StreakService.compute ─────────────────────────────────────────────────────

class TestStreakService:
    TODAY = date(2026, 4, 28)
    YESTERDAY = TODAY - timedelta(days=1)
    TWO_DAYS_AGO = TODAY - timedelta(days=2)

    def test_first_activity_ever(self):
        result = StreakService.compute(None, 0, 0, self.TODAY)
        assert result.new_streak == 1
        assert result.was_broken is False
        assert result.already_logged_today is False

    def test_consecutive_day(self):
        result = StreakService.compute(self.YESTERDAY, 5, 5, self.TODAY)
        assert result.new_streak == 6
        assert result.was_broken is False
        assert result.new_max == 6

    def test_already_logged_today(self):
        result = StreakService.compute(self.TODAY, 3, 3, self.TODAY)
        assert result.already_logged_today is True
        assert result.new_streak == 3  # unchanged

    def test_streak_broken_one_day_gap(self):
        result = StreakService.compute(self.TWO_DAYS_AGO, 10, 10, self.TODAY)
        assert result.was_broken is True
        assert result.missed_days == 1
        assert result.new_streak == 1
        assert result.new_max == 10  # max preserved

    def test_streak_broken_many_days_gap(self):
        old_date = self.TODAY - timedelta(days=5)
        result = StreakService.compute(old_date, 20, 20, self.TODAY)
        assert result.was_broken is True
        assert result.missed_days == 4

    def test_can_shield_protect_one_day(self):
        assert StreakService.can_shield_protect(1) is True

    def test_shield_cannot_protect_two_days(self):
        assert StreakService.can_shield_protect(2) is False

    def test_apply_shield_increments_streak(self):
        shielded = StreakService.apply_shield(current_streak=7, current_max=7)
        assert shielded.new_streak == 8
        assert shielded.was_broken is False

    def test_max_streak_never_decreases(self):
        result = StreakService.compute(self.TWO_DAYS_AGO, 5, 30, self.TODAY)
        assert result.new_max == 30  # old max preserved even after break
