# ==================================================================
# FORGE SERVICE
# ==================================================================

import random
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError
from app.models.catalog import Attribute
from app.models.player import PlayerAttribute, PlayerInventory
from app.schemas.forge import TransmuteRequest, TransmuteResponse
from app.services.skill_tree_service import get_node_level, node_bonus

# Ordinary attribute codes 
_ORDINARY_CODES = ["S", "P", "E", "C", "I", "A"]

# Materials consumed per attribute 
_TRANSMUTE_COST_PER_UNIT = 10

# Service ForgeService (Business Logic for "The Forge")
class ForgeService:

    # Function primary Constructor
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Function to transmute ordinary materials into Stardust
    async def transmute(
        self,
        player_id: uuid.UUID,
        request: TransmuteRequest,
    ) -> TransmuteResponse:
        batch_size = request.batch_size

        # Apply reduc_transmute_cost skill node discount
        reduc_level = await get_node_level(self._db, player_id, "reduc_transmute_cost")
        raw_per_mat = batch_size * _TRANSMUTE_COST_PER_UNIT
        per_mat = max(1, round(raw_per_mat * (1.0 - node_bonus(reduc_level)))) if reduc_level > 0 else raw_per_mat

        all_attrs = (await self._db.scalars(select(Attribute))).all()
        attr_id_by_code = {a.code: a.id for a in all_attrs}
        attr_code_by_id = {v: k for k, v in attr_id_by_code.items()}

        # Lock all ordinary inventory rows at once
        ordinary_inventories = (
            await self._db.execute(
                select(PlayerInventory)
                .where(
                    PlayerInventory.player_id == player_id,
                    PlayerInventory.attribute_id.in_(
                        [attr_id_by_code[c] for c in _ORDINARY_CODES]
                    ),
                )
                .with_for_update()
            )
        ).scalars().all()

        inv_by_code = {attr_code_by_id[inv.attribute_id]: inv for inv in ordinary_inventories}

        for code in _ORDINARY_CODES:
            inv = inv_by_code.get(code)
            have = inv.quantity if inv else 0
            if have < per_mat:
                raise ConflictError(
                    f"Insufficient {code} materials: {have}/{per_mat} needed"
                )

        for code in _ORDINARY_CODES:
            inv_by_code[code].quantity -= per_mat

        stardust_gained = random.randint(batch_size, 3 * batch_size)

        # Apply double_transmute_chance skill node after generating the base value
        double_level = await get_node_level(self._db, player_id, "double_transmute_chance")
        if double_level > 0 and random.random() < node_bonus(double_level):
            stardust_gained *= 2

        stardust_inv = (
            await self._db.execute(
                select(PlayerInventory)
                .where(
                    PlayerInventory.player_id == player_id,
                    PlayerInventory.attribute_id == attr_id_by_code["L"],
                )
                .with_for_update()
            )
        ).scalar_one()
        stardust_inv.quantity += stardust_gained

        await self._db.commit()

        return TransmuteResponse(
            batch_size=batch_size,
            materials_consumed_each=per_mat,
            stardust_gained=stardust_gained,
            new_stardust_balance=stardust_inv.quantity,
        )

    # Function (Get Attribute by Code)
    async def _get_attribute(self, code: str) -> Attribute:
        attr = await self._db.scalar(select(Attribute).where(Attribute.code == code))
        if not attr:
            raise NotFoundError(f"Attribute '{code}'")
        return attr

    # Function (Lock Rows for Update)
    async def _lock_rows(
        self,
        player_id: uuid.UUID,
        attribute_id: int,
    ) -> tuple[PlayerAttribute, PlayerInventory]:
        player_attr = (
            await self._db.execute(
                select(PlayerAttribute)
                .where(
                    PlayerAttribute.player_id == player_id,
                    PlayerAttribute.attribute_id == attribute_id,
                )
                .with_for_update()
            )
        ).scalar_one()

        inventory = (
            await self._db.execute(
                select(PlayerInventory)
                .where(
                    PlayerInventory.player_id == player_id,
                    PlayerInventory.attribute_id == attribute_id,
                )
                .with_for_update()
            )
        ).scalar_one()

        return player_attr, inventory
