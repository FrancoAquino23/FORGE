# ==================================================================
# FORGE - ADD STREAK FIELDS TO DAILY MISSIONS
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "o5p6q7r8s9t0"
down_revision = "n4o5p6q7r8s9"
branch_labels = None
depends_on = None


# Function to apply the migration
def upgrade() -> None:
    op.add_column(
        "missions",
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "missions",
        sa.Column("last_streak_date", sa.Date(), nullable=True),
    )


# Function to revert the migration
def downgrade() -> None:
    op.drop_column("missions", "last_streak_date")
    op.drop_column("missions", "current_streak")
