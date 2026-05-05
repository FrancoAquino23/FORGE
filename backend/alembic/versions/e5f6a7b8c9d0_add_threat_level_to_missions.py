# ==================================================================
# FORGE - Add threat_level priority field to missions table
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.add_column(
        "missions",
        sa.Column(
            "threat_level",
            sa.SmallInteger(),
            nullable=False,
            server_default="1",
        ),
    )
    op.create_check_constraint(
        "valid_threat_level",
        "missions",
        "threat_level IN (0, 1, 2)",
    )

# Function to revert the migration
def downgrade() -> None:
    op.drop_constraint("valid_threat_level", "missions", type_="check")
    op.drop_column("missions", "threat_level")
