# ==================================================================
# FORGE - REMOVE CONSUMABLE ECOSYSTEM
# ==================================================================

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "i9j0k1l2m3n4"
down_revision = "h8i9j0k1l2m3"
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_active_effects_player_expires"))
    op.execute(sa.text("DROP TABLE IF EXISTS player_active_effects"))
    op.execute(sa.text("DROP TABLE IF EXISTS player_consumables"))
    op.execute(sa.text("DROP TABLE IF EXISTS consumable_types"))
    op.execute(sa.text(
        "ALTER TABLE activity_logs DROP COLUMN IF EXISTS overcharge_active"
    ))

# Function to revert the migration
def downgrade() -> None:
    op.add_column(
        "activity_logs",
        sa.Column("overcharge_active", sa.Boolean(), nullable=False, server_default="false"),
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
    op.create_table(
        "player_consumables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "consumable_type_id",
            sa.SmallInteger(),
            sa.ForeignKey("consumable_types.id"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("player_id", "consumable_type_id", name="uq_player_consumable"),
        sa.CheckConstraint("quantity >= 0", name="non_negative_consumable"),
    )
    op.create_table(
        "player_active_effects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "consumable_type_id",
            sa.SmallInteger(),
            sa.ForeignKey("consumable_types.id"),
            nullable=False,
        ),
        sa.Column("multiplier", sa.Numeric(5, 2), nullable=False),
        sa.Column("activated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_active_effects_player_expires",
        "player_active_effects",
        ["player_id", "expires_at"],
    )
