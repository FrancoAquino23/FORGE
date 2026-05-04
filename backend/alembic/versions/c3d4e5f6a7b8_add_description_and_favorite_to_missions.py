# ==================================================================
# FORGE - Add description and is_favorite to missions table
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None

# Functions to apply the migration
def upgrade() -> None:
    op.add_column("missions", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "missions",
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

# Function to revert the migration
def downgrade() -> None:
    op.drop_column("missions", "is_favorite")
    op.drop_column("missions", "description")
