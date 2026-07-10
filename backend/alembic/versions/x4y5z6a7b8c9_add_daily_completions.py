# ==================================================================
# FORGE - ADD DAILY COMPLETIONS TABLE
# ==================================================================

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'x4y5z6a7b8c9'
down_revision = 'w3x4y5z6a7b8'
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.create_table(
        'daily_completions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('mission_id', UUID(as_uuid=True), sa.ForeignKey('missions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('player_id', UUID(as_uuid=True), sa.ForeignKey('player_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_attribute_id', sa.SmallInteger(), sa.ForeignKey('attributes.id'), nullable=False),
        sa.Column('threat_level', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cycle_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('xp_awarded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mat_awarded', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_daily_completions_player_completed', 'daily_completions', ['player_id', 'completed_at'])

# Function to reverse the migration
def downgrade() -> None:
    op.drop_index('ix_daily_completions_player_completed', table_name='daily_completions')
    op.drop_table('daily_completions')
