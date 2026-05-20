# ==================================================================
# FORGE - LUCK RELIC STARDUST
# ==================================================================

import sqlalchemy as sa
from alembic import op

revision = "j0k1l2m3n4o5"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE relics DROP CONSTRAINT valid_relic_attr"))
    op.execute(sa.text(
        "ALTER TABLE relics ADD CONSTRAINT valid_relic_attr "
        "CHECK (attribute_code IN ('S','P','E','C','I','A','L'))"
    ))

# Function to revert the migration
def downgrade() -> None:
    op.execute(sa.text("DELETE FROM relics WHERE attribute_code = 'L'"))
    op.execute(sa.text("ALTER TABLE relics DROP CONSTRAINT valid_relic_attr"))
    op.execute(sa.text(
        "ALTER TABLE relics ADD CONSTRAINT valid_relic_attr "
        "CHECK (attribute_code IN ('S','P','E','C','I','A'))"
    ))
