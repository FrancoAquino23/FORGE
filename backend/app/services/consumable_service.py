# ==================================================================
# CONSUMABLE SERVICE
# ==================================================================

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import ConflictError, NotFoundError
from app.models.activity import PlayerActiveEffect, PlayerConsumable
from app.models.catalog import ConsumableType
from app.models.player import PlayerProfile
from app.schemas.consumable import ConsumableItem, InventoryResponse, UseConsumableResponse

# Service ConsumableService (Business Logic for Consumables)
class ConsumableService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def get_inventory(self, player_id: uuid.UUID) -> InventoryResponse:
        consumables = (
            await self._db.scalars(
                select(PlayerConsumable)
                .where(PlayerConsumable.player_id == player_id)
                .options(selectinload(PlayerConsumable.consumable_type))
            )
        ).all()

        now = datetime.now(timezone.utc)
        active_effects = {
            ae.consumable_type_id: ae
            for ae in (
                await self._db.scalars(
                    select(PlayerActiveEffect).where(
                        PlayerActiveEffect.player_id == player_id,
                        PlayerActiveEffect.expires_at > now,
                    )
                )
            ).all()
        }

        items = [
            ConsumableItem(
                consumable_code=pc.consumable_type.code,
                name=pc.consumable_type.name,
                description=pc.consumable_type.description,
                effect_type=pc.consumable_type.effect_type,
                quantity=pc.quantity,
                is_active=pc.consumable_type_id in active_effects,
                active_until=(
                    active_effects[pc.consumable_type_id].expires_at
                    if pc.consumable_type_id in active_effects
                    else None
                ),
            )
            for pc in consumables
        ]
        return InventoryResponse(items=items)

    # Helper method to use a consumable and apply its effect
    async def use_consumable(
        self, player_id: uuid.UUID, consumable_code: str
    ) -> UseConsumableResponse:
        ct = await self._db.scalar(
            select(ConsumableType).where(ConsumableType.code == consumable_code)
        )
        if not ct:
            raise NotFoundError(f"Consumable '{consumable_code}'")

        pc = (
            await self._db.execute(
                select(PlayerConsumable)
                .where(
                    PlayerConsumable.player_id == player_id,
                    PlayerConsumable.consumable_type_id == ct.id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

        if not pc or pc.quantity < 1:
            raise ConflictError(f"No tienes {ct.name} en tu inventario")

        now = datetime.now(timezone.utc)
        active_until = None

        if ct.effect_type == "overcharge":
            existing = await self._db.scalar(
                select(PlayerActiveEffect).where(
                    PlayerActiveEffect.player_id == player_id,
                    PlayerActiveEffect.consumable_type_id == ct.id,
                    PlayerActiveEffect.expires_at > now,
                )
            )
            if existing:
                raise ConflictError("El Overcharge ya está activo")

            duration = ct.effect_duration_hours or 2
            active_until = now + timedelta(hours=duration)
            multiplier = ct.effect_value or Decimal("2.0")
            self._db.add(
                PlayerActiveEffect(
                    player_id=player_id,
                    consumable_type_id=ct.id,
                    multiplier=multiplier,
                    expires_at=active_until,
                )
            )
            pc.quantity -= 1
            message = f"Overcharge activo por {duration}h — XP x{multiplier}"

        elif ct.effect_type == "streak_shield":
            # Manual use: recover stamina to max
            profile = (
                await self._db.execute(
                    select(PlayerProfile)
                    .where(PlayerProfile.id == player_id)
                    .with_for_update()
                )
            ).scalar_one()
            profile.stamina_current = 100
            profile.stamina_updated_at = now
            pc.quantity -= 1
            message = "Estamina recuperada al máximo."

        else:
            raise ConflictError(f"Tipo de efecto no soportado: {ct.effect_type}")

        await self._db.commit()

        return UseConsumableResponse(
            consumable_code=ct.code,
            name=ct.name,
            effect_type=ct.effect_type,
            quantity_remaining=pc.quantity,
            active_until=active_until,
            message=message,
        )
