# ==================================================================
# FORGE - REMOVE STAMINA FROM PLAYER PROFILES
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None

# Function Upgrade (Drop stamina columns)
def upgrade() -> None:
    op.drop_column("player_profiles", "stamina_current")
    op.drop_column("player_profiles", "stamina_updated_at")

# Function Downgrade (Restore stamina columns)
def downgrade() -> None:
    op.add_column(
        "player_profiles",
        sa.Column(
            "stamina_updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "player_profiles",
        sa.Column(
            "stamina_current",
            sa.Integer(),
            server_default=sa.text("100"),
            nullable=False,
        ),
    )
