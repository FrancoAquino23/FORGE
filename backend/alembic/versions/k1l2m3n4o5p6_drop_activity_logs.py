# ==================================================================
# FORGE - DROP ACTIVITY LOGS TABLE
# ==================================================================

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "k1l2m3n4o5p6"
down_revision: str | None = "j0k1l2m3n4o5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Function to apply the migration
def upgrade() -> None:
    op.drop_index("ix_activity_logs_player_date", table_name="activity_logs")
    op.drop_index("ix_activity_logs_player_logged", table_name="activity_logs")
    op.drop_table("activity_logs")

# Function to revert the migration
def downgrade() -> None:
    op.create_table(
        "activity_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("player_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "attribute_id",
            sa.SmallInteger(),
            sa.ForeignKey("attributes.id"),
            nullable=False,
        ),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("xp_earned", sa.Integer(), nullable=False),
        sa.Column("material_earned", sa.Integer(), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column(
            "logged_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_activity_logs_player_date", "activity_logs", ["player_id", "activity_date"]
    )
    op.create_index(
        "ix_activity_logs_player_logged", "activity_logs", ["player_id", "logged_at"]
    )
