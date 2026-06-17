/* ==================================================================
   DASHBOARD COMPONENT LOGIC
   ================================================================== */

import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { LucideAngularModule, LucideIconData } from 'lucide-angular';
import {
  ApiService,
  AttributeProfile,
  MissionProgress,
  PlayerProfile,
} from '../../core/api.service';
import { RelicWorkshopComponent } from '../relic-workshop/relic-workshop.component';
import { ATTR_COLORS, ATTR_HEX, ATTR_ICONS } from '../../shared/attr-constants';

// Glow effect mappings for attributes (used on hover)
const ATTR_GLOW: Record<string, string> = {
  S: 'hover:shadow-[0_0_18px_rgba(248,113,113,0.3)]',
  P: 'hover:shadow-[0_0_18px_rgba(96,165,250,0.3)]',
  E: 'hover:shadow-[0_0_18px_rgba(74,222,128,0.3)]',
  C: 'hover:shadow-[0_0_18px_rgba(253,224,71,0.3)]',
  I: 'hover:shadow-[0_0_18px_rgba(192,132,252,0.3)]',
  A: 'hover:shadow-[0_0_18px_rgba(34,211,238,0.3)]',
  L: 'hover:shadow-[0_0_18px_rgba(251,146,60,0.3)]',
};

// Threat bar colors
const THREAT_BAR: Record<string, string> = {
  MINOR: '#22d3ee',
  MAJOR: '#f59e0b',
  CRITICAL: '#ef4444',
};

// Visual Prestige tiers
const VISUAL_TIERS = [
  {
    min: 50,
    name: 'Singularity',
    color: '#e2e8f0',
    glow: 'drop-shadow(0 0 16px rgba(226,232,240,0.95))',
    animated: true,
  },
  {
    min: 35,
    name: 'Absolute Void',
    color: '#bf00ff',
    glow: 'drop-shadow(0 0 14px rgba(191,0,255,0.85))',
    animated: true,
  },
  {
    min: 20,
    name: 'Eternal Flame',
    color: '#ef4444',
    glow: 'drop-shadow(0 0 12px rgba(239,68,68,0.80))',
    animated: true,
  },
  {
    min: 10,
    name: 'Arcane Crystal',
    color: '#3b82f6',
    glow: 'drop-shadow(0 0 10px rgba(59,130,246,0.75))',
    animated: false,
  },
  {
    min: 6,
    name: 'Forged Obsidian',
    color: '#10b981',
    glow: 'drop-shadow(0 0 8px rgba(16,185,129,0.65))',
    animated: false,
  },
  {
    min: 3,
    name: 'Smelted Ore',
    color: '#f59e0b',
    glow: 'drop-shadow(0 0 6px rgba(245,158,11,0.55))',
    animated: false,
  },
  { min: 0, name: 'Scrap Metal', color: '#475569', glow: 'none', animated: false },
] as const;

// Number of segments in each attribute bar before reaching prestige
const PRESTIGE_THRESHOLD = 10;

// Main dashboard component
@Component({
  selector: 'app-dashboard',
  imports: [RelicWorkshopComponent, LucideAngularModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);

  profile = signal<PlayerProfile | null>(null);
  missions = signal<MissionProgress[]>([]);
  loadError = signal('');
  xpFlash = signal('');

  readonly SEGMENTS = Array.from({ length: PRESTIGE_THRESHOLD }, (_, i) => i + 1);

  // All active missions sorted by priority:
  urgentMissions = computed<MissionProgress[]>(() => {
    const all = this.missions();
    const threatOrder: Record<string, number> = { CRITICAL: 0, MAJOR: 1, MINOR: 2 };
    return [...all].sort((a, b) => {
      const aIsDaily = a.category === 'DAILY_GRIND';
      const bIsDaily = b.category === 'DAILY_GRIND';
      if (aIsDaily && !bIsDaily) return 1;
      if (!aIsDaily && bIsDaily) return -1;
      const aDay = a.due_date ? new Date(a.due_date).getTime() : Infinity;
      const bDay = b.due_date ? new Date(b.due_date).getTime() : Infinity;
      if (aDay !== bDay) return aDay - bDay;
      return (threatOrder[a.threat_level] ?? 1) - (threatOrder[b.threat_level] ?? 1);
    });
  });

  // Load component
  ngOnInit(): void {
    this.loadProfile();
    this.loadMissions();
  }

  // Load player profile from API
  private loadProfile(): void {
    this.api.getProfile().subscribe({
      next: (p) => this.profile.set(p),
      error: () => this.loadError.set('Could not load profile. Check your token.'),
    });
  }

  // Load active missions from API
  private loadMissions(): void {
    this.api.getActiveMissions().subscribe({
      next: (res) => this.missions.set(res.missions),
      error: () => {},
    });
  }

  // Prestige tier helper (Level)
  prestigeTier(count: number) {
    return VISUAL_TIERS.find((t) => count >= t.min)!;
  }

  // Prestige gem helper (Color)
  prestigeGemColor(count: number): string {
    return this.prestigeTier(count).color;
  }

  // Prestige gem glow helper (Hover effect)
  prestigeGemGlow(count: number): string {
    return this.prestigeTier(count).glow;
  }

  // Prestige gem animation helper (Pulse effect)
  prestigeGemAnimated(count: number): boolean {
    return this.prestigeTier(count).animated;
  }

  // Determine styles for attribute segments based on level and prestige status
  segmentClass(attr: AttributeProfile, seg: number): string {
    if (attr.level >= PRESTIGE_THRESHOLD) return 'seg-prestige';
    return attr.level >= seg ? 'seg-active' : 'seg-off';
  }

  // Function to calculate XP percentage for progress bars
  xpPct(attr: AttributeProfile): number {
    if (attr.level >= PRESTIGE_THRESHOLD) return 100;
    return attr.xp_to_next > 0 ? Math.min(100, (attr.xp_current / attr.xp_to_next) * 100) : 0;
  }

  // Function to get color class for an attribute based on its code
  xpBarColor(code: string): string {
    return ATTR_HEX[code] ?? '#f59e0b';
  }

  // Function to get text color class for an attribute based on its code
  attrColor(code: string): string {
    return ATTR_COLORS[code] ?? 'text-forge-primary';
  }

  // Function to get glow class for an attribute based on its code
  attrGlow(code: string): string {
    return ATTR_GLOW[code] ?? '';
  }

  // Function to get the appropriate icon for an attribute based on its code
  getIconName(code: string): LucideIconData {
    return ATTR_ICONS[code] ?? ATTR_ICONS['L'];
  }

  // Mission helper (Threat Level)
  threatBarColor(level: string): string {
    return THREAT_BAR[level] ?? '#f59e0b';
  }

  // Mission helper (Threat Text)
  threatTextClass(level: string): string {
    const map: Record<string, string> = {
      MINOR: 'text-cyan-400',
      MAJOR: 'text-amber-400',
      CRITICAL: 'text-red-400',
    };
    return map[level] ?? 'text-forge-muted';
  }

  // Mission helper (Due Date formatting)
  formatDueDate(due: string): string {
    return new Date(due).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  // Mission helper (Checkpoint completion count)
  completedCount(m: MissionProgress): number {
    return m.checkpoints.filter((c) => c.is_completed).length;
  }

  // Mission helper (Checkpoint completion percentage)
  checkpointPct(m: MissionProgress): number {
    if (!m.checkpoints.length) return 0;
    return Math.round((this.completedCount(m) / m.checkpoints.length) * 100);
  }
}
