/* ==================================================================
   ATTRIBUTE CONSTANTS
  ================================================================== */

import { LucideIconData, Hammer, Eye, Shield, Gem, Cpu, Zap, Sparkles } from 'lucide-angular';

// Tailwind text color class per attribute code
export const ATTR_COLORS: Record<string, string> = {
  S: 'text-red-400',
  P: 'text-blue-400',
  E: 'text-green-400',
  C: 'text-yellow-300',
  I: 'text-purple-400',
  A: 'text-cyan-400',
  L: 'text-orange-400',
};

// Hex color value per attribute code
export const ATTR_HEX: Record<string, string> = {
  S: '#f87171',
  P: '#60a5fa',
  E: '#4ade80',
  C: '#fde047',
  I: '#c084fc',
  A: '#22d3ee',
  L: '#fb923c',
};

// Lucide icon per attribute code
export const ATTR_ICONS: Record<string, LucideIconData> = {
  S: Hammer,
  P: Eye,
  E: Shield,
  C: Gem,
  I: Cpu,
  A: Zap,
  L: Sparkles,
};

// Relic artifact name per attribute code
export const RELIC_NAMES: Record<string, string> = {
  S: 'Anvil of Power',
  P: 'Beacon of Clarity',
  E: 'Shield of Eternity',
  C: 'Chalice of Harmony',
  I: 'Orb of Logic',
  A: 'Elixir of Speed',
  L: 'Totem of Grace',
};

// Raw material name per attribute code
export const MATERIAL_NAMES: Record<string, string> = {
  S: 'Damascus Steel',
  P: 'Quartz Lens',
  E: 'Carbon Fiber',
  C: 'Resonance Crystal',
  I: 'Binary Essence',
  A: 'Inertial Catalyst',
  L: 'Stardust',
};
