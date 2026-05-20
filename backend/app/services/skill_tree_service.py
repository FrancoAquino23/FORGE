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
_NODE_COSTS: tuple[int, ...] = (0, 1, 2, 3)

# Additive bonus fraction at each level (3% / 5% / 10%)
_NODE_BONUSES: tuple[float, ...] = (0.0, 0.03, 0.05, 0.10)

_MAX_NODE_LEVEL = 3

# Static display labels for the early_start_boost node
_EARLY_START_LABELS = ("Off", "1 attr → Lv 2", "2 attrs → Lv 2", "3 attrs → Lv 3")


# Buffs (Data - node_id → (path_name, display_name, description))
_NODES: dict[str, tuple[str, str, str]] = {
    "reduc_transmute_cost": (
        "Stellar Alchemy",
        "Reduced Transmutation Cost",
        "Discount on ordinary materials consumed per transmutation batch.",
    ),
    "double_transmute_chance": (
        "Stellar Alchemy",
        "Double Transmutation Chance",
        "Chance of doubling Stardust output after each transmutation.",
    ),
    "mission_material_multiplier": (
        "Industrial Supply",
        "Mission Material Multiplier",
        "Bonus materials from Side Quests and Daily Grinds.",
    ),
    "relic_cost_discount": (
        "Industrial Supply",
        "Relic Cost Discount",
        "Discount on materials required to upgrade relics.",
    ),
    "global_xp_buff": (
        "Chronological Mastery",
        "Global XP Buff",
        "Bonus XP earned from all attribute missions.",
    ),
    "early_start_boost": (
        "Chronological Mastery",
        "Early Start Boost",
        "Ordinary attributes begin at a higher level after prestige.",
    ),
}

# Function to calculate the additive bonus
def node_bonus(level: int) -> float:
    return _NODE_BONUSES[min(level, _MAX_NODE_LEVEL)]

# Function to calculate total points per prestige invested
def total_pp_for_level(level: int) -> int:
    return sum(_NODE_COSTS[1 : level + 1])

# Function to get display label for current/next effect
def _effect_label(node_id: str, level: int) -> str:
    if node_id == "early_start_boost":
        return _EARLY_START_LABELS[level]
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

        nodes: list[SkillNodeInfo] = []
        for node_id, (path, display_name, description) in _NODES.items():
            lvl = level_map.get(node_id, 0)
            cost = _NODE_COSTS[lvl + 1] if lvl < _MAX_NODE_LEVEL else None
            nodes.append(
                SkillNodeInfo(
                    node_id=node_id,
                    path=path,
                    display_name=display_name,
                    description=description,
                    current_level=lvl,
                    max_level=_MAX_NODE_LEVEL,
                    cost_to_upgrade=cost,
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
