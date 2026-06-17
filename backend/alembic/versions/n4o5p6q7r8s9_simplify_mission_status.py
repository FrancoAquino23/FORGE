# ==================================================================
# FORGE - SIMPLIFY MISSION STATUS
# ==================================================================

from alembic import op

revision = 'n4o5p6q7r8s9'
down_revision = 'm3n4o5p6q7r8'
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.execute("DELETE FROM missions WHERE status IN ('EXPIRED', 'ABANDONED')")

    op.drop_constraint('valid_mission_status', 'missions', type_='check')
    op.create_check_constraint(
        'valid_mission_status',
        'missions',
        "status IN ('ACTIVE', 'COMPLETED', 'PENDING')",
    )

# Function to revert the migration
def downgrade() -> None:
    op.drop_constraint('valid_mission_status', 'missions', type_='check')
    op.create_check_constraint(
        'valid_mission_status',
        'missions',
        "status IN ('ACTIVE', 'COMPLETED', 'EXPIRED', 'ABANDONED', 'PENDING')",
    )
