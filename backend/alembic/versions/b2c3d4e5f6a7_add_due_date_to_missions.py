# ==================================================================
# FORGE - ADD DUE_DATE TO MISSIONS TABLE
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

# Functions to apply the migration
def upgrade() -> None:
    op.add_column(
        "missions",
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
    )

# Function to revert the migration
def downgrade() -> None:
    op.drop_column("missions", "due_date")
