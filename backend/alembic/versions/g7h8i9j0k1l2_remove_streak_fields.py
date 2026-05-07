# ==================================================================
# FORGE - REMOVE STREAK & RECORDS FIELDS
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "g7h8i9j0k1l2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.drop_column("player_profiles", "streak_current")
    op.drop_column("player_profiles", "streak_max")
    op.drop_column("player_profiles", "streak_last_date")

# Function to revert the migration
def downgrade() -> None:
    op.add_column(
        "player_profiles",
        sa.Column("streak_last_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "player_profiles",
        sa.Column("streak_max", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "player_profiles",
        sa.Column("streak_current", sa.Integer(), nullable=False, server_default="0"),
    )
