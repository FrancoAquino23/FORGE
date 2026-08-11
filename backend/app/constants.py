# ==================================================================
# BACKEND - SHARED CONSTANTS
# ==================================================================

# Attribute codes
ORDINARY_CODES: frozenset[str] = frozenset({"S", "P", "E", "C", "I", "A"})
ORDINARY_CODES_ORDERED: tuple[str, ...] = ("S", "P", "E", "C", "I", "A")

# Maximum level for attributes and relics
MAX_ATTRIBUTE_LEVEL: int = 10

# Mission category rewards — base values for MINOR threat level
CATEGORY_REWARDS: dict[str, dict] = {
    "MAIN_QUEST":  {"reward_xp": 600, "reward_mat": 300},
    "SIDE_QUEST":  {"reward_xp": 300, "reward_mat": 150},
    "DAILY_GRIND": {"reward_xp": 200, "reward_mat": 100},
}

# Threat level reward multipliers (applied at mission creation)
THREAT_MULTIPLIER: dict[str, float] = {
    "MINOR":    1.0,
    "MAJOR":    1.5,
    "CRITICAL": 2.0,
}

# Mission category labels
CATEGORY_LABELS: dict[str, str] = {
    "MAIN_QUEST":  "Main Quest",
    "SIDE_QUEST":  "Side Quest",
    "DAILY_GRIND": "Daily Grind",
}

# Threat level mappings
THREAT_LABEL: dict[int, str] = {0: "MINOR", 1: "MAJOR", 2: "CRITICAL"}
THREAT_VALUE: dict[str, int] = {"MINOR": 0, "MAJOR": 1, "CRITICAL": 2}
