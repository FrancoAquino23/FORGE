# ==================================================================
# FORGE - REMOVE AI FEATURES
# ==================================================================

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Function to apply the migration
def upgrade() -> None:
    op.drop_table("gm_context_snapshots")
    op.drop_column("missions", "generated_by_model")
    op.drop_column("missions", "prompt_tokens_used")
    op.drop_column("player_profiles", "ai_calls_today")
    op.drop_column("player_profiles", "ai_calls_limit")
    op.drop_column("player_profiles", "ai_budget_reset_at")

# Function to revert the migration
def downgrade() -> None:
    op.add_column(
        "player_profiles",
        sa.Column("ai_budget_reset_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "player_profiles",
        sa.Column("ai_calls_limit", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "player_profiles",
        sa.Column("ai_calls_today", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "missions",
        sa.Column("prompt_tokens_used", sa.Integer(), nullable=True),
    )
    op.add_column(
        "missions",
        sa.Column("generated_by_model", sa.String(length=60), nullable=True),
    )
    op.create_table(
        "gm_context_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "snapshot_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["player_id"], ["player_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
