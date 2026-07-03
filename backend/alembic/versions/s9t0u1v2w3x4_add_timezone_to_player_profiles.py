# ==================================================================
# FORGE - ADD TIMEZONE TO PLAYERS PROFILE
# ==================================================================

revision = "s9t0u1v2w3x4"
down_revision = "r8s9t0u1v2w3"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

# Function to apply the migration
def upgrade() -> None:
    op.add_column(
        "player_profiles",
        sa.Column(
            "timezone",
            sa.String(64),
            nullable=False,
            server_default="UTC",
        ),
    )

# Function to reverse the migration
def downgrade() -> None:
    op.drop_column("player_profiles", "timezone")
