# ==================================================================
# PRESTIGE SERVICE
# ==================================================================

import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import NotFoundError, PrestigeNotAvailableError
from app.models.catalog import Attribute, BuffType, ForgeConfig
from app.models.player import PlayerAttribute, PlayerProfile
from app.models.prestige import PlayerBuff, PrestigeHistory
from app.schemas.prestige import (
    BuffTypeInfo, PlayerBuffInfo,
    PrestigeSacrificeResponse, PrestigeStatusResponse,
    PrestigeUpResponse,
)
from app.services.reward_service import RewardService

# Default prestige threshold if not set in ForgeConfig
_DEFAULT_THRESHOLD = 10

# Model PrestigeService (Business Logic for Prestige Sacrifice)
class PrestigeService:
    # Function to check if an attribute level meets the prestige threshold
    @staticmethod
    def is_eligible(attribute_level: int, threshold: int) -> bool:
        return attribute_level >= threshold

    # Function to compute new total bonus for a buff after adding a stack
    @staticmethod
    def compute_new_bonus(current_total: Decimal, bonus_per_stack: Decimal) -> Decimal:
        return current_total + bonus_per_stack

    # Constructor to initialize the service with a database session
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    # Helper to sacrifice an attribute for a prestige buff, reset the attribute, and record history
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

    # Returns full prestige status for the "Altar de Prestigio" view
    async def get_status(self, player: PlayerProfile) -> PrestigeStatusResponse:
        config = await self._db.scalar(select(ForgeConfig))
        threshold = config.prestige_threshold_level if config else _DEFAULT_THRESHOLD

        buffs_result = await self._db.execute(
            select(PlayerBuff)
            .options(selectinload(PlayerBuff.buff_type))
            .where(PlayerBuff.player_id == player.id)
        )
        buffs = buffs_result.scalars().all()

        buff_types_result = await self._db.execute(
            select(BuffType).options(selectinload(BuffType.attribute))
        )
        buff_types = buff_types_result.scalars().all()

        return PrestigeStatusResponse(
            prestige_count=player.prestige_count,
            threshold_level=threshold,
            active_buffs=[
                PlayerBuffInfo(
                    buff_type_code=b.buff_type.code,
                    display_name=b.buff_type.display_name,
                    target_type=b.buff_type.target_type,
                    stack_count=b.stack_count,
                    total_bonus=b.total_bonus,
                )
                for b in buffs
            ],
            available_buff_types=[
                BuffTypeInfo(
                    code=bt.code,
                    display_name=bt.display_name,
                    target_type=bt.target_type,
                    bonus_percent=bt.bonus_percent,
                    attribute_code=bt.attribute.code if bt.attribute else None,
                )
                for bt in buff_types
            ],
        )

    # Helper to perform a full prestige-up
    async def prestige_up(self, player: PlayerProfile, buff_type_code: str) -> PrestigeUpResponse:
        config = await self._db.scalar(select(ForgeConfig))
        threshold = config.prestige_threshold_level if config else _DEFAULT_THRESHOLD

        # Load all catalog attributes and all player attributes (locked)
        all_attrs = (await self._db.scalars(select(Attribute))).all()
        all_player_attrs = (
            await self._db.execute(
                select(PlayerAttribute)
                .where(PlayerAttribute.player_id == player.id)
                .with_for_update()
            )
        ).scalars().all()
        pa_by_attr_id = {pa.attribute_id: pa for pa in all_player_attrs}

        # Verify every attribute is at the threshold
        for a in all_attrs:
            pa = pa_by_attr_id.get(a.id)
            if not pa or pa.level < threshold:
                raise PrestigeNotAvailableError(threshold)

        buff_type = await self._db.scalar(select(BuffType).where(BuffType.code == buff_type_code))
        if not buff_type:
            raise NotFoundError(f"Buff type '{buff_type_code}'")

        # Upsert buff (same additive stacking logic as sacrifice)
        existing_buff = (
            await self._db.execute(
                select(PlayerBuff)
                .where(PlayerBuff.player_id == player.id, PlayerBuff.buff_type_id == buff_type.id)
                .with_for_update()
            )
        ).scalar_one_or_none()

        if existing_buff:
            existing_buff.stack_count += 1
            new_total = self.compute_new_bonus(existing_buff.total_bonus, buff_type.bonus_percent)
            existing_buff.total_bonus = new_total
            new_stack = existing_buff.stack_count
        else:
            new_total = buff_type.bonus_percent
            new_stack = 1
            self._db.add(
                PlayerBuff(player_id=player.id, buff_type_id=buff_type.id, stack_count=1, total_bonus=new_total)
            )

        # Sync material bonus for MATERIAL buff types
        if buff_type.target_type == "MATERIAL" and buff_type.attribute_id:
            mat_attr = pa_by_attr_id.get(buff_type.attribute_id)
            if mat_attr:
                mat_attr.material_bonus = new_total

        # Reset ALL attributes to level 1
        reset_codes: list[str] = []
        for a in all_attrs:
            pa = pa_by_attr_id.get(a.id)
            if pa:
                pa.level = 1
                pa.xp_current = 0
                pa.xp_to_next = RewardService.xp_for_level(1)
                reset_codes.append(a.code)

        prestige_number = player.prestige_count + 1
        self._db.add(
            PrestigeHistory(
                player_id=player.id,
                prestige_number=prestige_number,
                artifact_level_reached=threshold,
                buff_type_id=buff_type.id,
            )
        )

        locked_profile = (
            await self._db.execute(
                select(PlayerProfile).where(PlayerProfile.id == player.id).with_for_update()
            )
        ).scalar_one()
        locked_profile.prestige_count += 1

        await self._db.commit()

        return PrestigeUpResponse(
            prestige_number=prestige_number,
            attributes_reset=reset_codes,
            buff_type_code=buff_type.code,
            buff_display_name=buff_type.display_name,
            new_stack_count=new_stack,
            new_total_bonus=new_total,
        )

    # Helper to load an attribute by code, ensuring it exists
    async def _get_attribute(self, code: str) -> Attribute:
        attr = await self._db.scalar(select(Attribute).where(Attribute.code == code))
        if not attr:
            raise NotFoundError(f"Attribute '{code}'")
        return attr
