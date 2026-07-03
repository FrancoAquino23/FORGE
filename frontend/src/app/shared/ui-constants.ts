/* ==================================================================
   FRONT - ATTRIBUTE CONSTANTS
  ================================================================== */

// Color class per attribute
export const ATTR_COLORS: Record<string, string> = {
  S: 'text-red-400',
  P: 'text-blue-400',
  E: 'text-green-400',
  C: 'text-yellow-300',
  I: 'text-purple-400',
  A: 'text-cyan-400',
  L: 'text-orange-400',
};

// Hex color value per attribute
export const ATTR_HEX: Record<string, string> = {
  S: '#f87171',
  P: '#60a5fa',
  E: '#4ade80',
  C: '#fde047',
  I: '#c084fc',
  A: '#22d3ee',
  L: '#fb923c',
};

// Icon name per attribute
export const ATTR_ICONS: Record<string, string> = {
  S: 'phosphorSwordBold',
  P: 'phosphorEyeBold',
  E: 'phosphorShieldBold',
  C: 'phosphorSketchLogoBold',
  I: 'phosphorDnaBold',
  A: 'phosphorLightningBold',
  L: 'phosphorSparkleBold',
};

// Color class per threat level
export const THREAT_COLORS: Record<string, string> = {
  MINOR: 'text-sky-400',
  MAJOR: 'text-amber-400',
  CRITICAL: 'text-rose-500',
};

// Color class per threat level (Fills)
export const THREAT_BAR_COLORS: Record<string, string> = {
  MINOR: 'bg-sky-400',
  MAJOR: 'bg-amber-400',
  CRITICAL: 'bg-rose-500',
};

// Hex color per threat level (Inlines)
export const THREAT_HEX: Record<string, string> = {
  MINOR: '#38bdf8',
  MAJOR: '#fbbf24',
  CRITICAL: '#f43f5e',
};

// Color class per mission category
export const CATEGORY_COLORS: Record<string, string> = {
  MAIN_QUEST: 'text-violet-400',
  SIDE_QUEST: 'text-blue-400',
  DAILY_GRIND: 'text-amber-400',
};

// Color class per mission category (Fills)
export const CATEGORY_BAR_COLORS: Record<string, string> = {
  MAIN_QUEST: 'bg-violet-400',
  SIDE_QUEST: 'bg-blue-400',
  DAILY_GRIND: 'bg-amber-400',
};

// Glow class per threat level (Cards)
export const THREAT_GLOW: Record<string, string> = {
  MINOR: 'hover:shadow-[0_0_18px_rgba(56,189,248,0.22)]',
  MAJOR: 'hover:shadow-[0_0_18px_rgba(251,191,36,0.22)]',
  CRITICAL: 'shadow-[0_0_22px_rgba(244,63,94,0.32)]',
};

// Border color class per threat level
export const THREAT_BORDER: Record<string, string> = {
  MINOR: 'border-sky-500/35',
  MAJOR: 'border-amber-500/40',
  CRITICAL: 'border-rose-500/50',
};

// Color class per threat level (Backgrounds)
export const THREAT_FAV_BG: Record<string, string> = {
  MINOR: 'bg-sky-950/30',
  MAJOR: 'bg-amber-950/30',
  CRITICAL: 'bg-rose-950/30',
};

// Color class per attribute (Fills)
export const ATTR_BAR_COLORS: Record<string, string> = {
  S: 'bg-red-400',
  P: 'bg-blue-400',
  E: 'bg-green-400',
  C: 'bg-yellow-300',
  I: 'bg-purple-400',
  A: 'bg-cyan-400',
  L: 'bg-orange-400',
};

// Relic artifact name per attribute
export const RELIC_NAMES: Record<string, string> = {
  S: 'Anvil of Power',
  P: 'Beacon of Clarity',
  E: 'Shield of Eternity',
  C: 'Chalice of Harmony',
  I: 'Orb of Logic',
  A: 'Elixir of Speed',
  L: 'Totem of Grace',
};

// Full attribute name
export const ATTR_NAMES: Record<string, string> = {
  S: 'Strength',
  P: 'Perception',
  E: 'Endurance',
  C: 'Charisma',
  I: 'Intelligence',
  A: 'Agility',
  L: 'Luck',
};

// Raw material name per attribute
export const MATERIAL_NAMES: Record<string, string> = {
  S: 'Damascus Steel',
  P: 'Quartz Lens',
  E: 'Carbon Fiber',
  C: 'Resonance Crystal',
  I: 'Binary Essence',
  A: 'Inertial Catalyst',
  L: 'Stardust',
};

// Export number formatting
export function fmt(n: number): string {
  return n.toLocaleString('en-US');
}

// Export attribute color
export function attrColor(code: string): string {
  return ATTR_COLORS[code] ?? 'text-forge-primary';
}

// Export attribute icon
export function attrIcon(code: string): string {
  return ATTR_ICONS[code] ?? ATTR_ICONS['L'];
}

// Export threat bar color
export function threatBarColor(level: string): string {
  return THREAT_HEX[level] ?? '#fbbf24';
}

// Export threat color
export function threatTextClass(level: string): string {
  return THREAT_COLORS[level] ?? 'text-forge-muted';
}

// Export due date formatting
export function formatDueDate(due: string | null): string {
  if (!due) return '';
  return new Date(due).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
