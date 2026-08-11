# ==================================================================
# SKILL TREE SERVICE
# ==================================================================

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, InsufficientMaterialsError
from app.models.player import PlayerProfile
from app.models.skill_tree import PlayerSkillNode
from app.schemas.skill_tree import (
    ResetTreeResponse,
    SkillNodeInfo,
    SkillTreeResponse,
    UpgradeNodeRequest,
    UpgradeNodeResponse,
)

# Points per prestige cost to advance a level
_NODE_COSTS: tuple[int, ...] = (0, 1, 4, 10)

# Additive bonus fraction at each level (5% / 10% / 20%)
_NODE_BONUSES: tuple[float, ...] = (0.0, 0.05, 0.10, 0.20)

# Extra PP granted per prestige by the pp_bonus node (0 / +1 / +2 / +3)
_PP_BONUS_VALUES: tuple[int, ...] = (0, 1, 2, 3)

_MAX_NODE_LEVEL = 3

# Static display labels for the "relic_head_start" node
_RELIC_HEAD_START_LABELS = ("Off", "1 relic → Lv 1", "2 relics → Lv 1", "3 relics → Lv 2")


# Buffs (Data - node_id → (path_name, display_name, description))
_NODES: dict[str, tuple[str, str, str]] = {
    "reduc_transmute_cost": (
        "Stellar Mastery",
        "Void Pact",
        "Discount on materials consumed per Forge operation.",
    ),
    "double_transmute_chance": (
        "Stellar Mastery",
        "Nova Burst",
        "Chance to double Stardust output on every Forge.",
    ),
    "mission_material_multiplier": (
        "Industrial Mastery",
        "Bounty Rush",
        "Bonus materials from Main Quests and Side Quests.",
    ),
    "relic_cost_discount": (
        "Industrial Mastery",
        "Forge Oath",
        "Discount on materials required to upgrade relics.",
    ),
    "global_xp_buff": (
        "Cycle Mastery",
        "XP Overdrive",
        "Bonus XP earned from all attribute missions.",
    ),
    "early_start_boost": (
        "Cycle Mastery",
        "Null Cycle",
        "Reduces XP required to level up all attributes.",
    ),
    "critical_surge": (
        "Operative Mastery",
        "Crimson Protocol",
        "Bonus XP and materials on all Main Quests.",
    ),
    "streak_amplifier": (
        "Operative Mastery",
        "Chain Reaction",
        "Bonus rewards on Daily Grind missions with an active streak.",
    ),
    "material_compression": (
        "Prestige Mastery",
        "Prestige Rift",
        "Discount on material cost required to ascend.",
    ),
    "relic_head_start": (
        "Prestige Mastery",
        "Relic Echo",
        "Carries random relics into a higher level after prestige.",
    ),
    "luck_cost_reduction": (
        "Royal Mastery",
        "Fortune's Grace",
        "Reduces the cost to upgrade the Luck relic.",
    ),
    "pp_bonus": (
        "Royal Mastery",
        "Noble Legacy",
        "Grants bonus Prestige Points for each prestige completed.",
    ),
}

# Function to calculate the additive bonus
def node_bonus(level: int) -> float:
    return _NODE_BONUSES[min(level, _MAX_NODE_LEVEL)]

# Function to calculate extra PP granted by the pp_bonus node
def pp_node_bonus(level: int) -> int:
    return _PP_BONUS_VALUES[min(level, _MAX_NODE_LEVEL)]

# Function to calculate total points per prestige invested
def total_pp_for_level(level: int) -> int:
    return sum(_NODE_COSTS[1 : level + 1])

# Function to get display label for current/next effect
def _effect_label(node_id: str, level: int) -> str:
    if node_id == "early_start_boost":
        pct = round(_NODE_BONUSES[level] * 100)
        return f"-{pct}% XP req." if pct > 0 else "0%"
    if node_id == "relic_head_start":
        return _RELIC_HEAD_START_LABELS[level]
    if node_id == "material_compression":
        pct = round(_NODE_BONUSES[level] * 100)
        return f"-{pct}% cost" if pct > 0 else "0%"
    if node_id == "luck_cost_reduction":
        pct = round(_NODE_BONUSES[level] * 100)
        return f"-{pct}% cost" if pct > 0 else "0%"
    if node_id == "pp_bonus":
        b = _PP_BONUS_VALUES[min(level, _MAX_NODE_LEVEL)]
        return f"+{b} PP" if b > 0 else "0 PP"
    pct = round(_NODE_BONUSES[level] * 100)
    return f"+{pct}%" if pct > 0 else "0%"

# Helper method for fast lookup of a node's current level
async def get_node_level(db: AsyncSession, player_id: uuid.UUID, node_id: str) -> int:
    val = await db.scalar(
        select(PlayerSkillNode.current_level).where(
            PlayerSkillNode.player_id == player_id,
            PlayerSkillNode.node_id == node_id,
        )
    )
    return val or 0


# Service SkillTreeService (Manages node upgrades, resets, and tree reads)
class SkillTreeService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def get_tree(self, player: PlayerProfile) -> SkillTreeResponse:
        rows = (
            await self._db.execute(
                select(PlayerSkillNode).where(PlayerSkillNode.player_id == player.id)
            )
        ).scalars().all()
        level_map = {r.node_id: r.current_level for r in rows}

        path_siblings: dict[str, list[str]] = {}
        for nid, (p, _, _) in _NODES.items():
            path_siblings.setdefault(p, []).append(nid)

        nodes: list[SkillNodeInfo] = []
        for node_id, (path, display_name, description) in _NODES.items():
            lvl = level_map.get(node_id, 0)
            cost = _NODE_COSTS[lvl + 1] if lvl < _MAX_NODE_LEVEL else None
            locked_by_choice = lvl == 0 and any(
                level_map.get(s, 0) > 0
                for s in path_siblings[path]
                if s != node_id
            )
            nodes.append(
                SkillNodeInfo(
                    node_id=node_id,
                    path=path,
                    display_name=display_name,
                    description=description,
                    current_level=lvl,
                    max_level=_MAX_NODE_LEVEL,
                    cost_to_upgrade=cost,
                    locked_by_choice=locked_by_choice,
                    bonus_at_current=_NODE_BONUSES[lvl],
                    bonus_at_next=_NODE_BONUSES[lvl + 1] if lvl < _MAX_NODE_LEVEL else None,
                    current_effect=_effect_label(node_id, lvl),
                    next_effect=_effect_label(node_id, lvl + 1) if lvl < _MAX_NODE_LEVEL else None,
                )
            )

        return SkillTreeResponse(
            nodes=nodes,
            pp_total=player.prestige_points_total,
            pp_available=player.prestige_points_available,
        )

    # Helper method to perform node upgrade
    async def upgrade_node(self, player: PlayerProfile, node_id: str) -> UpgradeNodeResponse:
        if node_id not in _NODES:
            raise ConflictError(f"Unknown skill node '{node_id}'")

        row = (
            await self._db.execute(
                select(PlayerSkillNode)
                .where(
                    PlayerSkillNode.player_id == player.id,
                    PlayerSkillNode.node_id == node_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

        current_level = row.current_level if row else 0
        if current_level >= _MAX_NODE_LEVEL:
            raise ConflictError(f"Node '{node_id}' is already at maximum level")

        # Block upgrade if a sibling node in the same path is already active
        path = _NODES[node_id][0]
        siblings = [s for s, (p, _, _) in _NODES.items() if p == path and s != node_id]
        if siblings:
            active_sibling = await self._db.scalar(
                select(PlayerSkillNode.node_id).where(
                    PlayerSkillNode.player_id == player.id,
                    PlayerSkillNode.node_id.in_(siblings),
                    PlayerSkillNode.current_level > 0,
                )
            )
            if active_sibling:
                raise ConflictError(f"Another node in '{path}' is already active. Reset the tree to change your choice.")

        cost = _NODE_COSTS[current_level + 1]

        locked_profile = (
            await self._db.execute(
                select(PlayerProfile)
                .where(PlayerProfile.id == player.id)
                .with_for_update()
            )
        ).scalar_one()

        if locked_profile.prestige_points_available < cost:
            raise InsufficientMaterialsError(
                f"Need {cost} PP, have {locked_profile.prestige_points_available}"
            )

        locked_profile.prestige_points_available -= cost
        new_level = current_level + 1

        if row:
            row.current_level = new_level
        else:
            self._db.add(
                PlayerSkillNode(
                    player_id=player.id,
                    node_id=node_id,
                    current_level=new_level,
                )
            )

        await self._db.commit()

        return UpgradeNodeResponse(
            node_id=node_id,
            new_level=new_level,
            pp_spent=cost,
            pp_available=locked_profile.prestige_points_available,
            next_effect=_effect_label(node_id, new_level + 1) if new_level < _MAX_NODE_LEVEL else None,
        )

    # Helper method to reset the entire skill tree
    async def reset_tree(self, player: PlayerProfile) -> ResetTreeResponse:
        rows = (
            await self._db.execute(
                select(PlayerSkillNode)
                .where(PlayerSkillNode.player_id == player.id)
                .with_for_update()
            )
        ).scalars().all()

        pp_refunded = sum(total_pp_for_level(r.current_level) for r in rows)

        for r in rows:
            r.current_level = 0

        locked_profile = (
            await self._db.execute(
                select(PlayerProfile)
                .where(PlayerProfile.id == player.id)
                .with_for_update()
            )
        ).scalar_one()
        locked_profile.prestige_points_available += pp_refunded

        await self._db.commit()

        return ResetTreeResponse(
            pp_refunded=pp_refunded,
            pp_available=locked_profile.prestige_points_available,
        )
