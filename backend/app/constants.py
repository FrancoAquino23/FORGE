# ==================================================================
# BACKEND - SHARED CONSTANTS
# ==================================================================

# Attribute codes
ORDINARY_CODES: frozenset[str] = frozenset({"S", "P", "E", "C", "I", "A"})
ORDINARY_CODES_ORDERED: tuple[str, ...] = ("S", "P", "E", "C", "I", "A")

# Maximum level for attributes and relics
MAX_ATTRIBUTE_LEVEL: int = 10

# Mission category rewards (Base XP & materials)
CATEGORY_REWARDS: dict[str, dict] = {
    "MAIN_QUEST":  {"reward_xp": 100, "reward_mat": 50},
    "SIDE_QUEST":  {"reward_xp": 50,  "reward_mat": 25},
    "DAILY_GRIND": {"reward_xp": 30,  "reward_mat": 15},
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
THREAT_ORDER: dict[str, int] = {"CRITICAL": 2, "MAJOR": 1, "MINOR": 0}
