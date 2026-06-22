# ==================================================================
# FORGE - ADD XP/MAT AWARDED TO MISSIONS & BEST STREAK TO PROFILE
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "p6q7r8s9t0u1"
down_revision = "o5p6q7r8s9t0"
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.add_column(
        "missions",
        sa.Column("xp_awarded", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "missions",
        sa.Column("mat_awarded", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "player_profiles",
        sa.Column("best_streak", sa.Integer(), nullable=False, server_default="0"),
    )

# Function to revert the migration
def downgrade() -> None:
    op.drop_column("player_profiles", "best_streak")
    op.drop_column("missions", "mat_awarded")
    op.drop_column("missions", "xp_awarded")
