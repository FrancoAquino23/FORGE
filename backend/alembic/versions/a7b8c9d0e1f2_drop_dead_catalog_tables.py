# ==================================================================
# MIGRATION: Drop unused catalog tables (forge_config, forge_tier_recipes)
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = 'a7b8c9d0e1f2'
down_revision = 'z6a7b8c9d0e1'
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.drop_table('forge_tier_recipes')
    op.drop_table('forge_config')

# Function to reverse the migration
def downgrade() -> None:
    op.create_table(
        'forge_config',
        sa.Column('id', sa.SmallInteger(), primary_key=True),
        sa.Column('base_cost', sa.Numeric(8, 4), nullable=False, server_default='8'),
        sa.Column('poly_exponent', sa.Numeric(6, 4), nullable=False, server_default='1.2'),
        sa.Column('growth_rate', sa.Numeric(6, 4), nullable=False, server_default='1.07'),
        sa.Column('prestige_threshold_level', sa.SmallInteger(), nullable=False, server_default='10'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.CheckConstraint('id = 1', name='single_row'),
    )
    op.create_table(
        'forge_tier_recipes',
        sa.Column('tier_start', sa.SmallInteger(), primary_key=True),
        sa.Column('tier_end', sa.SmallInteger(), nullable=True),
        sa.Column('attribute_id', sa.SmallInteger(), sa.ForeignKey('attributes.id'), primary_key=True),
        sa.Column('proportion', sa.Numeric(5, 4), nullable=False),
        sa.UniqueConstraint('tier_start', 'attribute_id', name='uq_recipe_tier_attr'),
    )
