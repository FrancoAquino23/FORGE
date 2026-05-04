# ==================================================================
# FORGE - RELIC WORKSHOP (replaces consumable system)
# ==================================================================

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None

# Functions to apply and revert the migration
def upgrade() -> None:
    # Drop consumable tables (data loss intentional — replacing system)
    op.drop_table("player_active_effects")
    op.drop_table("player_consumables")

    # Create relics table
    op.create_table(
        "relics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attribute_code", sa.String(1), nullable=False),
        sa.Column("level", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("total_invested", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("player_id", "attribute_code", name="uq_player_relic"),
        sa.CheckConstraint("level BETWEEN 1 AND 10", name="relic_level_range"),
        sa.CheckConstraint(
            "attribute_code IN ('S','P','E','C','I','A')", name="valid_relic_attr"
        ),
    )

# Function to revert the migration (recreate consumable tables, drop relics)
def downgrade() -> None:
    op.drop_table("relics")

    op.create_table(
        "player_consumables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("consumable_type_id", sa.SmallInteger(), sa.ForeignKey("consumable_types.id"), nullable=False),
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
        sa.Column("consumable_type_id", sa.SmallInteger(), sa.ForeignKey("consumable_types.id"), nullable=False),
        sa.Column("multiplier", sa.Numeric(5, 2), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
