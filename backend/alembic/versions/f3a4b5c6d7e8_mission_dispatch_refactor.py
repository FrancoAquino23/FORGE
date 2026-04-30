# ==================================================================
# FORGE - MISSION DISPATCH REFACTOR
# ==================================================================

from alembic import op
import sqlalchemy as sa

revision = "f3a4b5c6d7e8"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Remove duration_minutes from activity_logs
    op.drop_constraint("valid_duration", "activity_logs", type_="check")
    op.drop_column("activity_logs", "duration_minutes")

    # Migrate existing LOG_MINUTES missions to LOG_COUNT (column is going away)
    op.execute(
        "UPDATE missions SET objective_type = 'LOG_COUNT', objective_target = 1 "
        "WHERE objective_type = 'LOG_MINUTES'"
    )

    # Add category column to missions (nullable — AI missions won't have one)
    op.add_column("missions", sa.Column("category", sa.String(20), nullable=True))

    # Expand status constraint to include PENDING
    op.drop_constraint("valid_mission_status", "missions", type_="check")
    op.create_check_constraint(
        "valid_mission_status",
        "missions",
        "status IN ('ACTIVE', 'COMPLETED', 'EXPIRED', 'ABANDONED', 'PENDING')",
    )

# Restore previous state (revert mission status and remove category)
def downgrade() -> None:
    op.drop_constraint("valid_mission_status", "missions", type_="check")
    op.create_check_constraint(
        "valid_mission_status",
        "missions",
        "status IN ('ACTIVE', 'COMPLETED', 'EXPIRED', 'ABANDONED')",
    )
    op.drop_column("missions", "category")
    op.add_column(
        "activity_logs",
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "valid_duration",
        "activity_logs",
        "duration_minutes BETWEEN 1 AND 1440",
    )
