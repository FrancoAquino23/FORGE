# ==================================================================
# PRESTIGE SERVICE
# ==================================================================

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PrestigeNotAvailableError
from app.models.catalog import Attribute, BuffType, ForgeConfig
from app.models.player import PlayerAttribute, PlayerProfile
from app.models.prestige import PlayerBuff, PrestigeHistory
from app.schemas.prestige import PrestigeSacrificeResponse
from app.services.reward_service import RewardService

_DEFAULT_THRESHOLD = 10


class PrestigeService:
    @staticmethod
    def is_eligible(attribute_level: int, threshold: int) -> bool:
        """Returns True when the attribute level meets the prestige threshold."""
        return attribute_level >= threshold

    @staticmethod
    def compute_new_bonus(current_total: Decimal, bonus_per_stack: Decimal) -> Decimal:
        """Additive buff stacking: each prestige adds one bonus_per_stack to the total."""
        return current_total + bonus_per_stack

    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def sacrifice(
        self,
        player: PlayerProfile,
        attribute_code: str,
        buff_type_code: str,
    ) -> PrestigeSacrificeResponse:
        attr = await self._get_attribute(attribute_code)

        config = await self._db.scalar(select(ForgeConfig))
        threshold = config.prestige_threshold_level if config else _DEFAULT_THRESHOLD

        player_attr = (
            await self._db.execute(
                select(PlayerAttribute)
                .where(
                    PlayerAttribute.player_id == player.id,
                    PlayerAttribute.attribute_id == attr.id,
                )
                .with_for_update()
            )
        ).scalar_one()

        if not self.is_eligible(player_attr.level, threshold):
            raise PrestigeNotAvailableError(threshold)

        buff_type = await self._db.scalar(
            select(BuffType).where(BuffType.code == buff_type_code)
        )
        if not buff_type:
            raise NotFoundError(f"Buff type '{buff_type_code}'")

        # Upsert PlayerBuff — additive stacking
        existing_buff = (
            await self._db.execute(
                select(PlayerBuff)
                .where(
                    PlayerBuff.player_id == player.id,
                    PlayerBuff.buff_type_id == buff_type.id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

        if existing_buff:
            existing_buff.stack_count += 1
            new_total = self.compute_new_bonus(
                existing_buff.total_bonus, buff_type.bonus_percent
            )
            existing_buff.total_bonus = new_total
            new_stack = existing_buff.stack_count
        else:
            new_total = buff_type.bonus_percent
            new_stack = 1
            self._db.add(
                PlayerBuff(
                    player_id=player.id,
                    buff_type_id=buff_type.id,
                    stack_count=1,
                    total_bonus=new_total,
                )
            )

        # Sync PlayerAttribute.material_bonus for MATERIAL buffs
        if buff_type.target_type == "MATERIAL" and buff_type.attribute_id:
            mat_attr = (
                await self._db.execute(
                    select(PlayerAttribute)
                    .where(
                        PlayerAttribute.player_id == player.id,
                        PlayerAttribute.attribute_id == buff_type.attribute_id,
                    )
                    .with_for_update()
                )
            ).scalar_one()
            mat_attr.material_bonus = new_total

        # Capture level before reset for history record
        level_before = player_attr.level

        # Reset the sacrificed attribute to level 1
        player_attr.level = 1
        player_attr.xp_current = 0
        player_attr.xp_to_next = RewardService.xp_for_level(1)

        # Record history and update prestige count atomically
        prestige_number = player.prestige_count + 1
        self._db.add(
            PrestigeHistory(
                player_id=player.id,
                prestige_number=prestige_number,
                artifact_level_reached=level_before,
                buff_type_id=buff_type.id,
            )
        )

        locked_profile = (
            await self._db.execute(
                select(PlayerProfile)
                .where(PlayerProfile.id == player.id)
                .with_for_update()
            )
        ).scalar_one()
        locked_profile.prestige_count += 1

        await self._db.commit()

        return PrestigeSacrificeResponse(
            prestige_number=prestige_number,
            attribute_reset_code=attr.code,
            level_before=level_before,
            buff_type_code=buff_type.code,
            buff_display_name=buff_type.display_name,
            new_stack_count=new_stack,
            new_total_bonus=new_total,
        )

    async def _get_attribute(self, code: str) -> Attribute:
        attr = await self._db.scalar(select(Attribute).where(Attribute.code == code))
        if not attr:
            raise NotFoundError(f"Attribute '{code}'")
        return attr
