# ==================================================================
# PRESTIGE SERVICE TESTS
# ==================================================================

from decimal import Decimal
import pytest
from app.services.prestige_service import PrestigeService
from app.services.reward_service import RewardService


# Service TestComputeNewBonus (Additive Buff Stacking)
class TestComputeNewBonus:
    def test_first_stack_from_zero(self):
        result = PrestigeService.compute_new_bonus(Decimal("0.00"), Decimal("5.00"))
        assert result == Decimal("5.00")

    def test_second_stack_additive(self):
        result = PrestigeService.compute_new_bonus(Decimal("5.00"), Decimal("5.00"))
        assert result == Decimal("10.00")

    def test_five_stacks_total_25(self):
        total = Decimal("0.00")
        for _ in range(5):
            total = PrestigeService.compute_new_bonus(total, Decimal("5.00"))
        assert total == Decimal("25.00")

    def test_different_bonus_amounts(self):
        result = PrestigeService.compute_new_bonus(Decimal("10.00"), Decimal("3.75"))
        assert result == Decimal("13.75")

    def test_stacking_is_commutative(self):
        # Order of stacking does not matter for additive bonuses
        a = PrestigeService.compute_new_bonus(Decimal("5.00"), Decimal("3.00"))
        b = PrestigeService.compute_new_bonus(Decimal("3.00"), Decimal("5.00"))
        assert a == b

    def test_bonus_always_positive(self):
        result = PrestigeService.compute_new_bonus(Decimal("0.00"), Decimal("5.00"))
        assert result > Decimal("0.00")


# Service TestAttributeResetContract (Attribute Reset After Prestige)
class TestAttributeResetContract:

    def test_reset_xp_to_next_at_level_1(self):
        # After prestige reset, level=1, xp_to_next must equal xp_for_level(1) = 500
        assert RewardService.xp_for_level(1) == 500

    def test_from_reset_level_up_requires_full_xp(self):
        # From xp=0 at level 1, earning exactly 500 XP triggers level-up
        _, level, _, leveled = RewardService.apply_xp_to_attribute(0, 1, 500)
        assert level == 2
        assert leveled is True

    def test_from_reset_partial_xp_no_level_up(self):
        # Earning 499 XP at level 1 should NOT trigger a level-up
        xp, level, _, leveled = RewardService.apply_xp_to_attribute(0, 1, 499)
        assert level == 1
        assert leveled is False
        assert xp == 499

