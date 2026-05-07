# ==================================================================
# FORGE - ADD CHECKPOINTS TABLE FOR MISSION SUB-TASKS
# ==================================================================

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.create_table(
        "checkpoints",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mission_id",
            UUID(as_uuid=True),
            sa.ForeignKey("missions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column(
            "is_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("order_index", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.create_index("ix_checkpoints_mission_id", "checkpoints", ["mission_id"])

# Function to revert the migration
def downgrade() -> None:
    op.drop_index("ix_checkpoints_mission_id", table_name="checkpoints")
    op.drop_table("checkpoints")
