# ==================================================================
# FORGE - PRESTIGE SKILL TREE
# ==================================================================

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "l2m3n4o5p6q7"
down_revision: str | None = "k1l2m3n4o5p6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Function to apply the migration
def upgrade() -> None:
    op.add_column(
        "player_profiles",
        sa.Column("prestige_points_total", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "player_profiles",
        sa.Column("prestige_points_available", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "player_skill_nodes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("node_id", sa.String(50), nullable=False),
        sa.Column(
            "current_level",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["player_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("player_id", "node_id", name="uq_player_skill_node"),
        sa.CheckConstraint(
            "current_level BETWEEN 0 AND 3",
            name="chk_skill_node_level",
        ),
    )

# Function to revert the migration
def downgrade() -> None:
    op.drop_table("player_skill_nodes")
    op.drop_column("player_profiles", "prestige_points_available")
    op.drop_column("player_profiles", "prestige_points_total")
