# ==================================================================
# REWARD SERVICE TESTS
# ==================================================================

import pytest
from app.services.reward_service import RewardService


# Service TestXpForLevel (Static XP Table)
class TestXpForLevel:
    def test_level_1(self):
        assert RewardService.xp_for_level(1) == 500

    def test_level_2(self):
        assert RewardService.xp_for_level(2) == 1_500

    def test_level_5(self):
        assert RewardService.xp_for_level(5) == 4_500

    def test_level_9(self):
        assert RewardService.xp_for_level(9) == 10_000

    def test_level_10_is_zero(self):
        assert RewardService.xp_for_level(10) == 0

    def test_levels_1_to_9_increase_monotonically(self):
        levels = [RewardService.xp_for_level(i) for i in range(1, 10)]
        assert levels == sorted(levels)


# Service TestApplyXpToAttribute (Leveling Logic)
class TestApplyXpToAttribute:
    def test_no_level_up(self):
        xp, level, xp_next, leveled = RewardService.apply_xp_to_attribute(0, 1, 400)
        assert xp == 400
        assert level == 1
        assert xp_next == 500
        assert leveled is False

    def test_exact_level_up(self):
        xp, level, xp_next, leveled = RewardService.apply_xp_to_attribute(0, 1, 500)
        assert level == 2
        assert xp == 0
        assert xp_next == 1_500
        assert leveled is True

    def test_level_up_with_overflow(self):
        xp, level, xp_next, leveled = RewardService.apply_xp_to_attribute(400, 1, 200)
        assert level == 2
        assert xp == 100
        assert leveled is True

    def test_max_level_blocks_all_xp(self):
        xp, level, xp_next, leveled = RewardService.apply_xp_to_attribute(0, 10, 99_999)
        assert level == 10
        assert xp == 0
        assert xp_next == 0
        assert leveled is False

    def test_overflow_xp_discarded_at_max_level(self):
        xp, level, xp_next, leveled = RewardService.apply_xp_to_attribute(0, 9, 100_000)
        assert level == 10
        assert xp == 0
        assert xp_next == 0
        assert leveled is True


# Service TestRelicUpgradeCost (Static Relic Upgrade Cost Table)
class TestRelicUpgradeCost:
    def test_level_1_to_2_costs_500(self):
        assert RewardService.upgrade_cost(1) == 500

    def test_level_2_to_3_costs_1500(self):
        assert RewardService.upgrade_cost(2) == 1_500

    def test_level_5_to_6_costs_4500(self):
        assert RewardService.upgrade_cost(5) == 4_500

    def test_level_9_to_10_costs_10000(self):
        assert RewardService.upgrade_cost(9) == 10_000

    def test_level_10_blocked(self):
        assert RewardService.upgrade_cost(10) == 0

    def test_mirrors_xp_table_for_all_levels(self):
        for level in range(1, 11):
            assert RewardService.upgrade_cost(level) == RewardService.xp_for_level(level)
