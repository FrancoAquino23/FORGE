# ==================================================================
# FORGE - ADD STAMINA TO PLAYER PROFILES
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "d1e2f3a4b5c6"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None

# Function Upgrade (Apply Migration)
def upgrade() -> None:
    op.add_column(
        "player_profiles",
        sa.Column(
            "stamina_current",
            sa.Integer(),
            nullable=False,
            server_default="100",
        ),
    )
    op.add_column(
        "player_profiles",
        sa.Column(
            "stamina_updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

# Function Downgrade (Revert Migration)
def downgrade() -> None:
    op.drop_column("player_profiles", "stamina_updated_at")
    op.drop_column("player_profiles", "stamina_current")
