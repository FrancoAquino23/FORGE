# ==================================================================
# FORGE - DATABASE CONFIGURATION
# ==================================================================
"""initial_schema

Revision ID: 618235e9966a
Revises:
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "618235e9966a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── CATALOG TABLES ────────────────────────────────────────────────────────

    op.create_table(
        "attributes",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("code", sa.String(1), unique=True, nullable=False),
        sa.Column("name", sa.String(30), nullable=False),
        sa.Column("material_name", sa.String(50), nullable=False),
        sa.Column("icon_key", sa.String(80), nullable=True),
    )

    op.create_table(
        "buff_types",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("code", sa.String(40), unique=True, nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("attribute_id", sa.SmallInteger(), sa.ForeignKey("attributes.id"), nullable=True),
        sa.Column("bonus_percent", sa.Numeric(5, 2), nullable=False),
    )

    op.create_table(
        "forge_config",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("base_cost", sa.Numeric(8, 4), nullable=False, server_default="8"),
        sa.Column("poly_exponent", sa.Numeric(6, 4), nullable=False, server_default="1.2"),
        sa.Column("growth_rate", sa.Numeric(6, 4), nullable=False, server_default="1.07"),
        sa.Column("prestige_threshold_level", sa.SmallInteger(), nullable=False, server_default="10"),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("id = 1", name="single_row"),
    )

    op.create_table(
        "visual_tiers",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("unlock_level", sa.SmallInteger(), unique=True, nullable=False),
        sa.Column("asset_key", sa.String(100), nullable=False),
    )

    op.create_table(
        "forge_tier_recipes",
        sa.Column("tier_start", sa.SmallInteger(), primary_key=True),
        sa.Column("tier_end", sa.SmallInteger(), nullable=True),
        sa.Column("attribute_id", sa.SmallInteger(), sa.ForeignKey("attributes.id"), primary_key=True),
        sa.Column("proportion", sa.Numeric(5, 4), nullable=False),
        sa.UniqueConstraint("tier_start", "attribute_id", name="uq_recipe_tier_attr"),
    )

    op.create_table(
        "consumable_types",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("code", sa.String(30), unique=True, nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("effect_type", sa.String(30), nullable=False),
        sa.Column("effect_value", sa.Numeric(5, 2), nullable=True),
        sa.Column("effect_duration_hours", sa.SmallInteger(), nullable=True),
    )

    # ── USER & PLAYER TABLES ─────────────────────────────────────────────────

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "player_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("prestige_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("global_material_bonus", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("global_xp_bonus", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("streak_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("streak_max", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("streak_last_date", sa.Date(), nullable=True),
        sa.Column("ai_calls_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_calls_limit", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("ai_budget_reset_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "player_attributes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attribute_id", sa.SmallInteger(), sa.ForeignKey("attributes.id"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("xp_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xp_to_next", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("material_bonus", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.UniqueConstraint("player_id", "attribute_id", name="uq_player_attribute"),
    )

    op.create_table(
        "player_inventory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attribute_id", sa.SmallInteger(), sa.ForeignKey("attributes.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("player_id", "attribute_id", name="uq_player_inventory"),
        sa.CheckConstraint("quantity >= 0", name="non_negative_quantity"),
    )

    # ── ARTIFACT TABLES ───────────────────────────────────────────────────────

    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prestige_cycle", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_levels_forged", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_visual_tier_id", sa.SmallInteger(), sa.ForeignKey("visual_tiers.id"), nullable=True),
        sa.Column("next_forge_cost", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}' :: jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "forge_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifacts.id"), nullable=False),
        sa.Column("from_level", sa.Integer(), nullable=False),
        sa.Column("to_level", sa.Integer(), nullable=False),
        sa.Column("prestige_cycle", sa.Integer(), nullable=False),
        sa.Column("materials_spent", postgresql.JSONB(), nullable=False),
        sa.Column("forged_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_forge_history_artifact_forged", "forge_history", ["artifact_id", "forged_at"])

    # ── PRESTIGE TABLES ───────────────────────────────────────────────────────

    op.create_table(
        "prestige_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("player_profiles.id"), nullable=False),
        sa.Column("prestige_number", sa.Integer(), nullable=False),
        sa.Column("artifact_level_reached", sa.Integer(), nullable=False),
        sa.Column("buff_type_id", sa.SmallInteger(), sa.ForeignKey("buff_types.id"), nullable=False),
        sa.Column("sacrificed_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "player_buffs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("buff_type_id", sa.SmallInteger(), sa.ForeignKey("buff_types.id"), nullable=False),
        sa.Column("stack_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_bonus", sa.Numeric(7, 2), nullable=False),
        sa.UniqueConstraint("player_id", "buff_type_id", name="uq_player_buff"),
        sa.CheckConstraint("stack_count > 0", name="positive_stack"),
    )

    # ── ACTIVITY & CONSUMABLE TABLES ──────────────────────────────────────────

    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attribute_id", sa.SmallInteger(), sa.ForeignKey("attributes.id"), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("xp_earned", sa.Integer(), nullable=False),
        sa.Column("material_earned", sa.Integer(), nullable=False),
        sa.Column("overcharge_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("logged_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("duration_minutes BETWEEN 1 AND 1440", name="valid_duration"),
    )
    op.create_index("ix_activity_logs_player_date", "activity_logs", ["player_id", "activity_date"])
    op.create_index("ix_activity_logs_player_logged", "activity_logs", ["player_id", "logged_at"])

    op.create_table(
        "player_consumables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consumable_type_id", sa.SmallInteger(), sa.ForeignKey("consumable_types.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("player_id", "consumable_type_id", name="uq_player_consumable"),
        sa.CheckConstraint("quantity >= 0", name="non_negative_consumable"),
    )

    op.create_table(
        "player_active_effects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consumable_type_id", sa.SmallInteger(), sa.ForeignKey("consumable_types.id"), nullable=False),
        sa.Column("multiplier", sa.Numeric(5, 2), nullable=False),
        sa.Column("activated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_active_effects_player_expires", "player_active_effects", ["player_id", "expires_at"])

    # ── MISSION & AI TABLES ───────────────────────────────────────────────────

    op.create_table(
        "missions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("objective_description", sa.Text(), nullable=False),
        sa.Column("target_attribute_id", sa.SmallInteger(), sa.ForeignKey("attributes.id"), nullable=False),
        sa.Column("reward_material_qty", sa.Integer(), nullable=False),
        sa.Column("reward_xp", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("generated_by_model", sa.String(60), nullable=True),
        sa.Column("prompt_tokens_used", sa.Integer(), nullable=True),
        sa.Column("issued_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'COMPLETED', 'EXPIRED', 'ABANDONED')",
            name="valid_mission_status",
        ),
    )
    op.create_index("ix_missions_player_status_expires", "missions", ["player_id", "status", "expires_at"])

    op.create_table(
        "gm_context_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("player_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_data", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_gm_snapshots_player_created", "gm_context_snapshots", ["player_id", "created_at"])


def downgrade() -> None:
    op.drop_table("gm_context_snapshots")
    op.drop_table("missions")
    op.drop_table("player_active_effects")
    op.drop_table("player_consumables")
    op.drop_table("activity_logs")
    op.drop_table("player_buffs")
    op.drop_table("prestige_history")
    op.drop_table("forge_history")
    op.drop_table("artifacts")
    op.drop_table("player_inventory")
    op.drop_table("player_attributes")
    op.drop_table("player_profiles")
    op.drop_table("users")
    op.drop_table("consumable_types")
    op.drop_table("forge_tier_recipes")
    op.drop_table("visual_tiers")
    op.drop_table("forge_config")
    op.drop_table("buff_types")
    op.drop_table("attributes")
