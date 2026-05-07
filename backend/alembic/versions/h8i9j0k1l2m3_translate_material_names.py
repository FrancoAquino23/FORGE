# ==================================================================
# FORGE - TRANSLATE MATERIAL & BUFF NAMES TO ENGLISH
# ==================================================================

from alembic import op

revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None

# Function to apply the migration
def upgrade() -> None:
    op.execute("UPDATE attributes SET material_name = 'Damascus Steel'    WHERE code = 'S'")
    op.execute("UPDATE attributes SET material_name = 'Quartz Lens'       WHERE code = 'P'")
    op.execute("UPDATE attributes SET material_name = 'Carbon Fiber'      WHERE code = 'E'")
    op.execute("UPDATE attributes SET material_name = 'Resonance Crystal' WHERE code = 'C'")
    op.execute("UPDATE attributes SET material_name = 'Binary Essence'    WHERE code = 'I'")
    op.execute("UPDATE attributes SET material_name = 'Inertial Catalyst' WHERE code = 'A'")
    op.execute("UPDATE attributes SET material_name = 'Stardust'          WHERE code = 'L'")

    op.execute("UPDATE buff_types SET display_name = '+5% XP on Strength'     WHERE code = 'XP_BONUS_S'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP on Perception'   WHERE code = 'XP_BONUS_P'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP on Endurance'    WHERE code = 'XP_BONUS_E'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP on Charisma'     WHERE code = 'XP_BONUS_C'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP on Intelligence' WHERE code = 'XP_BONUS_I'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP on Agility'      WHERE code = 'XP_BONUS_A'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP on Luck'         WHERE code = 'XP_BONUS_L'")

# Function to revert the migration
def downgrade() -> None:
    op.execute("UPDATE attributes SET material_name = 'Acero de Damasco'      WHERE code = 'S'")
    op.execute("UPDATE attributes SET material_name = 'Lente de Cuarzo'       WHERE code = 'P'")
    op.execute("UPDATE attributes SET material_name = 'Fibra de Carbono'      WHERE code = 'E'")
    op.execute("UPDATE attributes SET material_name = 'Cristal de Resonancia' WHERE code = 'C'")
    op.execute("UPDATE attributes SET material_name = 'Esencia Binaria'       WHERE code = 'I'")
    op.execute("UPDATE attributes SET material_name = 'Catalizador Inercial'  WHERE code = 'A'")
    op.execute("UPDATE attributes SET material_name = 'Polvo de Estrellas'    WHERE code = 'L'")

    op.execute("UPDATE buff_types SET display_name = '+5% XP en Strength'     WHERE code = 'XP_BONUS_S'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP en Perception'   WHERE code = 'XP_BONUS_P'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP en Endurance'    WHERE code = 'XP_BONUS_E'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP en Charisma'     WHERE code = 'XP_BONUS_C'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP en Intelligence' WHERE code = 'XP_BONUS_I'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP en Agility'      WHERE code = 'XP_BONUS_A'")
    op.execute("UPDATE buff_types SET display_name = '+5% XP en Luck'         WHERE code = 'XP_BONUS_L'")
