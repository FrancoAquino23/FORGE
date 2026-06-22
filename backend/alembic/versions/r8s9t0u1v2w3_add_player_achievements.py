# ==================================================================
# FORGE - PLAYER ACHIEVEMENTS TABLE
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "r8s9t0u1v2w3"
down_revision = "q7r8s9t0u1v2"
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.create_table(
        "player_achievements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("achievement_code", sa.String(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["player_id"], ["player_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_id", "achievement_code", name="uq_player_achievement"),
    )
    op.create_index("ix_player_achievements_player_id", "player_achievements", ["player_id"])

# Function to revert the migration
def downgrade() -> None:
    op.drop_index("ix_player_achievements_player_id", table_name="player_achievements")
    op.drop_table("player_achievements")
