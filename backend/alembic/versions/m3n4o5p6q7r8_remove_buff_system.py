# ==================================================================
# FORGE - REMOVE BUFF SYSTEM
# ==================================================================

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'm3n4o5p6q7r8'
down_revision = 'l2m3n4o5p6q7'
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.drop_table('player_buffs')

    op.drop_constraint('prestige_history_buff_type_id_fkey', 'prestige_history', type_='foreignkey')
    op.drop_column('prestige_history', 'buff_type_id')

    op.drop_table('buff_types')

    op.drop_column('player_profiles', 'global_material_bonus')
    op.drop_column('player_profiles', 'global_xp_bonus')

    op.drop_column('player_attributes', 'material_bonus')

# Function to revert the migration
def downgrade() -> None:
    op.add_column('player_attributes', sa.Column('material_bonus', sa.Numeric(6, 2), nullable=False, server_default='0.00'))
    op.add_column('player_profiles', sa.Column('global_xp_bonus', sa.Numeric(6, 2), nullable=False, server_default='0.00'))
    op.add_column('player_profiles', sa.Column('global_material_bonus', sa.Numeric(6, 2), nullable=False, server_default='0.00'))

    op.create_table(
        'buff_types',
        sa.Column('id', sa.SmallInteger(), primary_key=True),
        sa.Column('code', sa.String(40), unique=True, nullable=False),
        sa.Column('display_name', sa.String(80), nullable=False),
        sa.Column('target_type', sa.String(20), nullable=False),
        sa.Column('attribute_id', sa.SmallInteger(), sa.ForeignKey('attributes.id'), nullable=True),
        sa.Column('bonus_percent', sa.Numeric(5, 2), nullable=False),
    )

    op.add_column('prestige_history', sa.Column('buff_type_id', sa.SmallInteger(), nullable=False))
    op.create_foreign_key('prestige_history_buff_type_id_fkey', 'prestige_history', 'buff_types', ['buff_type_id'], ['id'])

    op.create_table(
        'player_buffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('player_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('buff_type_id', sa.SmallInteger(), sa.ForeignKey('buff_types.id'), nullable=False),
        sa.Column('stack_count', sa.Integer(), nullable=False),
        sa.Column('total_bonus', sa.Numeric(7, 2), nullable=False),
    )
