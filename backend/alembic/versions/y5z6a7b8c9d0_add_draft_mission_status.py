# ==================================================================
# MIGRATION: add_draft_mission_status
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


def upgrade() -> None:
    # Drop old constraint and recreate with DRAFT included
    op.drop_constraint('valid_mission_status', 'missions', type_='check')
    op.create_check_constraint(
        'valid_mission_status',
        'missions',
        "status IN ('ACTIVE', 'COMPLETED', 'PENDING', 'DRAFT')",
    )
    # Allow issued_at to be NULL for DRAFT missions (timer not started yet)
    op.alter_column('missions', 'issued_at', nullable=True)


def downgrade() -> None:
    op.alter_column('missions', 'issued_at', nullable=False)
    op.drop_constraint('valid_mission_status', 'missions', type_='check')
    op.create_check_constraint(
        'valid_mission_status',
        'missions',
        "status IN ('ACTIVE', 'COMPLETED', 'PENDING')",
    )
