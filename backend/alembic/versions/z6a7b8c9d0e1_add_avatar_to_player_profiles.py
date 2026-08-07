# ==================================================================
# FORGE - ADD AVATAR AND ICON TO PLAYER PROFILE
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = 'z6a7b8c9d0e1'
down_revision = 'y5z6a7b8c9d0'
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.add_column('player_profiles', sa.Column('avatar_color', sa.String(16), nullable=True))
    op.add_column('player_profiles', sa.Column('avatar_icon', sa.String(64), nullable=True))

# Function to reverse the migration
def downgrade() -> None:
    op.drop_column('player_profiles', 'avatar_icon')
    op.drop_column('player_profiles', 'avatar_color')
