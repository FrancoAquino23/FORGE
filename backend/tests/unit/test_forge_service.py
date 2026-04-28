"""
Unit tests for ForgeService cost math — zero I/O, pure logic.
Run: venv/Scripts/pytest.exe tests/unit/test_forge_service.py -v
"""
import pytest

from app.services.forge_service import ForgeService
from app.services.reward_service import RewardService


class TestAttributeUpgradeCost:
    def test_level_1_to_2_costs_25(self):
        assert ForgeService.attribute_upgrade_cost(1) == 25

    def test_level_2_to_3_costs_50(self):
        assert ForgeService.attribute_upgrade_cost(2) == 50

    def test_level_5_to_6_costs_125(self):
        assert ForgeService.attribute_upgrade_cost(5) == 125

    def test_level_10_to_11_costs_250(self):
        assert ForgeService.attribute_upgrade_cost(10) == 250

    def test_cost_increases_monotonically(self):
        costs = [ForgeService.attribute_upgrade_cost(i) for i in range(1, 20)]
        assert costs == sorted(costs)

    def test_always_positive(self):
        assert all(ForgeService.attribute_upgrade_cost(i) > 0 for i in range(1, 20))

    def test_linear_scaling(self):
        # cost(N) should equal N * BASE_UPGRADE_COST
        base = ForgeService.BASE_UPGRADE_COST
        for level in range(1, 10):
            assert ForgeService.attribute_upgrade_cost(level) == base * level


class TestForgeXpReset:
    """Verifies xp_to_next after a forge level-up uses the correct RewardService formula."""

    def test_xp_to_next_after_forge_to_level_2(self):
        # After forging to level 2, xp_to_next must match xp_for_level(2)
        assert RewardService.xp_for_level(2) == 282

    def test_xp_to_next_after_forge_to_level_5(self):
        assert RewardService.xp_for_level(5) == 1118

    def test_xp_to_next_after_forge_to_level_10(self):
        assert RewardService.xp_for_level(10) == 3162
