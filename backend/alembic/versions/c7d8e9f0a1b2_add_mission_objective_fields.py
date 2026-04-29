# ==================================================================
# FORGE - MISSION OBJECTIVE FIELDS MIGRATION
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "c7d8e9f0a1b2"
down_revision = "618235e9966a"
branch_labels = None
depends_on = None

# Function Upgrade (Apply Migration)
def upgrade() -> None:
    op.add_column(
        "missions",
        sa.Column(
            "objective_type",
            sa.String(30),
            nullable=False,
            server_default=sa.text("'LOG_MINUTES'"),
        ),
    )
    op.add_column(
        "missions",
        sa.Column(
            "objective_target",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
    )

# Function Downgrade (Revert Migration)
def downgrade() -> None:
    op.drop_column("missions", "objective_target")
    op.drop_column("missions", "objective_type")
