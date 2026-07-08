# ==================================================================
# FORGE - ADD CYCLE_STARTED_AT TO MISSIONS
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = 'w3x4y5z6a7b8'
down_revision = 'v2w3x4y5z6a7'
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.add_column('missions', sa.Column(
        'cycle_started_at',
        sa.DateTime(timezone=True),
        nullable=True,
    ))
    op.execute("UPDATE missions SET cycle_started_at = issued_at WHERE cycle_started_at IS NULL")

# Function to reverse the migration
def downgrade() -> None:
    op.drop_column('missions', 'cycle_started_at')
