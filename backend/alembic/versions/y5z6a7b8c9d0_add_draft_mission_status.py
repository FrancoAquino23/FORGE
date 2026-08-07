# ==================================================================
# FORGE - ADD DRAFTED MISSION STATUS
# ==================================================================

"""add_draft_mission_status

Revision ID: y5z6a7b8c9d0
Revises: x4y5z6a7b8c9
Create Date: 2026-07-15

"""
from alembic import op

revision = 'y5z6a7b8c9d0'
down_revision = 'x4y5z6a7b8c9'
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.drop_constraint('valid_mission_status', 'missions', type_='check')
    op.create_check_constraint(
        'valid_mission_status',
        'missions',
        "status IN ('ACTIVE', 'COMPLETED', 'PENDING', 'DRAFT')",
    )
    op.alter_column('missions', 'issued_at', nullable=True)

# Function to reverse the migration
def downgrade() -> None:
    op.alter_column('missions', 'issued_at', nullable=False)
    op.drop_constraint('valid_mission_status', 'missions', type_='check')
    op.create_check_constraint(
        'valid_mission_status',
        'missions',
        "status IN ('ACTIVE', 'COMPLETED', 'PENDING')",
    )
