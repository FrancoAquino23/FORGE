# ==================================================================
# FORGE - BACKFILL XP FOR EXISTING PLAYER ATTRIBUTES
# ==================================================================

revision = "t0u1v2w3x4y5"
down_revision = "s9t0u1v2w3x4"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

# Function to apply the migration
def upgrade() -> None:
    xp_table = {
        1: 500,
        2: 1_500,
        3: 2_500,
        4: 3_500,
        5: 4_500,
        6: 5_500,
        7: 6_500,
        8: 7_500,
        9: 10_000,
        10: 0,
    }
    conn = op.get_bind()
    for level, xp_to_next in xp_table.items():
        conn.execute(
            sa.text(
                "UPDATE player_attributes SET xp_to_next = :xp WHERE level = :level"
            ),
            {"xp": xp_to_next, "level": level},
        )

# Function to reverse the migration
def downgrade() -> None:
    pass
