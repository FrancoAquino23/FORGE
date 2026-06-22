# ==================================================================
# FORGE - BACKFILL XP/MAT AWARDED FROM BASE REWARD VALUES
# ==================================================================

from alembic import op

revision = "q7r8s9t0u1v2"
down_revision = "p6q7r8s9t0u1"
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.execute("""
        UPDATE missions
        SET xp_awarded  = reward_xp,
            mat_awarded = reward_material_qty
        WHERE status = 'COMPLETED'
          AND xp_awarded = 0
          AND mat_awarded = 0
    """)

# Function to revert the migration
def downgrade() -> None:
    op.execute("""
        UPDATE missions
        SET xp_awarded = 0,
            mat_awarded = 0
        WHERE status = 'COMPLETED'
    """)
