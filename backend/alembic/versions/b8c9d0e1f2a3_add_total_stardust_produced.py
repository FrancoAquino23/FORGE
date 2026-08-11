# ==================================================================
# FORGE - ADD TOTAL STARDUST PRODUCED
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = 'b8c9d0e1f2a3'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.add_column(
        'player_profiles',
        sa.Column('total_stardust_produced', sa.Integer(), nullable=False, server_default='0'),
    )

# Function to revert the migration
def downgrade() -> None:
    op.drop_column('player_profiles', 'total_stardust_produced')
