# ==================================================================
# CONSUMABLE ROUTES
# ==================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.database import get_db
from app.models.player import PlayerProfile
from app.schemas.consumable import InventoryResponse, UseConsumableRequest, UseConsumableResponse
from app.services.consumable_service import ConsumableService

# Router (consumables) for managing player consumable items and their effects
router = APIRouter(prefix="/consumables", tags=["consumables"])


# Endpoint (GET /consumables/inventory) - List player consumables with active-effect status
@router.get("/inventory", response_model=InventoryResponse)
async def get_inventory(
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> InventoryResponse:
    service = ConsumableService(session)
    return await service.get_inventory(player.id)


# Endpoint (POST /consumables/use) - Activate a consumable item
@router.post("/use", response_model=UseConsumableResponse)
async def use_consumable(
    body: UseConsumableRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> UseConsumableResponse:
    service = ConsumableService(session)
    return await service.use_consumable(player.id, body.consumable_code)
