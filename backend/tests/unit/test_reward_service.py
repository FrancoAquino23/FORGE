# ==================================================================
# REWARD SERVICE TESTS
# ==================================================================

from decimal import Decimal
import pytest
from app.services.reward_service import RewardService

# Service TestXpForLevel (XP Calculation) 
class TestXpForLevel:
    def test_level_1(self):
        assert RewardService.xp_for_level(1) == 100

    def test_level_2(self):
        assert RewardService.xp_for_level(2) == 282

    def test_level_5(self):
        assert RewardService.xp_for_level(5) == 1118

    def test_level_10(self):
        assert RewardService.xp_for_level(10) == 3162

    def test_increases_monotonically(self):
        levels = [RewardService.xp_for_level(i) for i in range(1, 20)]
        assert levels == sorted(levels)

# Service TestCalculateXp (XP Rewards)
class TestCalculateXp:
    def test_base_no_bonus(self):
        assert RewardService.calculate_xp(0, 0) == 25

    def test_relic_bonus_applied(self):
        assert RewardService.calculate_xp(1, 0) == 26

    def test_prestige_bonus_applied(self):
        assert RewardService.calculate_xp(0, 1) == 26

    def test_relic_and_prestige_stack(self):
        # relic=5, prestige=3 → multiplier = 1 + 8*0.05 = 1.4 → int(25*1.4) = 35
        assert RewardService.calculate_xp(5, 3) == 35

    def test_minimum_is_1(self):
        assert RewardService.calculate_xp(0, 0) >= 1

# Service TestCalculateMaterials (Material Rewards)
class TestCalculateMaterials:
    def test_base_no_bonus(self):
        assert RewardService.calculate_materials(0, 0) == 20

    def test_relic_bonus_applied(self):
        assert RewardService.calculate_materials(1, 0) == 21

    def test_prestige_bonus_applied(self):
        assert RewardService.calculate_materials(0, 1) == 21

    def test_relic_and_prestige_stack(self):
        # relic=5, prestige=3 → multiplier = 1.4 → int(20*1.4) = 28
        assert RewardService.calculate_materials(5, 3) == 28

    def test_minimum_is_1(self):
        assert RewardService.calculate_materials(0, 0) >= 1

# Service TestApplyXpToAttribute (Leveling Logic)
class TestApplyXpToAttribute:
    def test_no_level_up(self):
        xp, level, xp_next, leveled = RewardService.apply_xp_to_attribute(0, 1, 50)
        assert xp == 50
        assert level == 1
        assert leveled is False

    def test_exact_level_up(self):
        xp, level, xp_next, leveled = RewardService.apply_xp_to_attribute(0, 1, 100)
        assert level == 2
        assert xp == 0
        assert leveled is True

    def test_level_up_with_overflow(self):
        xp, level, _, leveled = RewardService.apply_xp_to_attribute(90, 1, 50)
        assert level == 2
        assert xp == 40
        assert leveled is True

    def test_multi_level_up(self):
        xp, level, _, leveled = RewardService.apply_xp_to_attribute(0, 1, 400)
        assert level == 3
        assert xp == 18
        assert leveled is True
