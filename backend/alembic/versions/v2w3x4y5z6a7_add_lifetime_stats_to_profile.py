# ==================================================================
# FORGE - ADD LIFETIME STATS TO PLAYERS PROFILE
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = 'v2w3x4y5z6a7'
down_revision = 'u1v2w3x4y5z6'
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.add_column('player_profiles', sa.Column(
        'total_missions_completed',
        sa.Integer(),
        nullable=False,
        server_default='0',
    ))
    op.add_column('player_profiles', sa.Column(
        'total_xp_earned',
        sa.Integer(),
        nullable=False,
        server_default='0',
    ))
    op.add_column('player_profiles', sa.Column(
        'total_materials_earned',
        sa.Integer(),
        nullable=False,
        server_default='0',
    ))

# Function to reverse the migration
def downgrade() -> None:
    op.drop_column('player_profiles', 'total_materials_earned')
    op.drop_column('player_profiles', 'total_xp_earned')
    op.drop_column('player_profiles', 'total_missions_completed')
