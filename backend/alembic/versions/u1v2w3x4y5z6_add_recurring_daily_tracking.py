# ==================================================================
# FORGE - ADD RECURRING DAILY TRACKING
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = 'u1v2w3x4y5z6'
down_revision = 't0u1v2w3x4y5'
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.add_column('missions', sa.Column(
        'last_completed_at',
        sa.DateTime(timezone=True),
        nullable=True,
    ))
    op.add_column('missions', sa.Column(
        'times_completed',
        sa.Integer(),
        nullable=False,
        server_default='0',
    ))

# Function to reverse the migration
def downgrade() -> None:
    op.drop_column('missions', 'times_completed')
    op.drop_column('missions', 'last_completed_at')
