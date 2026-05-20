/* ==================================================================
   PRESTIGE COMPONENT LOGIC
   ================================================================== */

import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService, PrestigeStatusResponse, PrestigeUpResponse } from '../../core/api.service';
import { PlayerStateService } from '../../core/player-state.service';
import { ToastService } from '../../core/toast.service';

// Color mappings for attributes
const ATTR_COLORS: Record<string, string> = {
  S: 'text-red-400',
  P: 'text-blue-400',
  E: 'text-green-400',
  C: 'text-yellow-300',
  I: 'text-purple-400',
  A: 'text-cyan-400',
  L: 'text-orange-400',
};

// Hex fill colors per attribute (for SVG strokes and inline styles)
const ATTR_HEX: Record<string, string> = {
  S: '#f87171',
  P: '#60a5fa',
  E: '#4ade80',
  C: '#fde047',
  I: '#c084fc',
  A: '#22d3ee',
  L: '#fb923c',
};

// English material names keyed by attribute code
const MATERIAL_NAMES: Record<string, string> = {
  S: 'Damascus Steel',
  P: 'Quartz Lens',
  E: 'Carbon Fiber',
  C: 'Resonance Crystal',
  I: 'Binary Essence',
  A: 'Inertial Catalyst',
  L: 'Stardust',
};

// Data shape for a single SVG ring segment
interface RingSegment {
  code: string;
  color: string;
  bgPath: string;
  fillPath: string | null;
  fillPct: number;
  level: number;
  threshold: number;
  ready: boolean;
  labelX: string;
  labelY: string;
}

// Canonical S.P.E.C.I.A.L. order for ring layout
const SPECIAL_ORDER = ['S', 'P', 'E', 'C', 'I', 'A', 'L'] as const;

// Ordinary material codes
const ORDINARY_CODES = new Set(['S', 'P', 'E', 'C', 'I', 'A']);

// Ring geometry constants
const RING_R = 38;
const CX = 50;
const CY = 50;
const GAP_DEG = 4;
const LABEL_R = 47;
const SEG_ARC = (360 - SPECIAL_ORDER.length * GAP_DEG) / SPECIAL_ORDER.length;

function toRad(d: number): number {
  return (d * Math.PI) / 180;
}

function buildArcPath(fromDeg: number, toDeg: number): string {
  const x1 = CX + RING_R * Math.cos(toRad(fromDeg));
  const y1 = CY + RING_R * Math.sin(toRad(fromDeg));
  const x2 = CX + RING_R * Math.cos(toRad(toDeg));
  const y2 = CY + RING_R * Math.sin(toRad(toDeg));
  const large = toDeg - fromDeg > 180 ? 1 : 0;
  return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${RING_R} ${RING_R} 0 ${large} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
}

@Component({
  selector: 'app-prestige',
  imports: [FormsModule],
  templateUrl: './prestige.component.html',
  styleUrl: './prestige.component.scss',
})
export class PrestigeComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private playerState = inject(PlayerStateService);

  readonly profile = this.playerState.profile;
  status = signal<PrestigeStatusResponse | null>(null);
  prestiging = signal(false);
  prestigeFlash = signal(false);

  selectedBuff = '';
  hoverPanel = signal(false);

  // XP-only buff types
  readonly xpBuffTypes = computed(() =>
    (this.status()?.available_buff_types ?? []).filter((bt) => bt.target_type === 'XP'),
  );

  // Load component
  ngOnInit(): void {
    this.load();
  }

  // Load player profile and prestige status from API
  private load(): void {
    this.api.getProfile().subscribe({ next: (p) => this.profile.set(p) });
    this.api.getPrestigeStatus().subscribe({
      next: (s) => {
        this.status.set(s);
        this.playerState.prestigeCount.set(s.prestige_count);
      },
    });
  }

  // Computes the 7 ring segments from current attribute levels
  readonly ringSegments = computed<RingSegment[]>(() => {
    const attrs = this.profile()?.attributes ?? [];
    const threshold = this.status()?.threshold_level ?? 10;

    return SPECIAL_ORDER.map((code, i) => {
      const attr = attrs.find((a) => a.code === code);
      const level = attr?.level ?? 0;
      const fillPct = Math.min(1, level / threshold);
      const startDeg = -90 + i * (SEG_ARC + GAP_DEG);
      const midDeg = startDeg + SEG_ARC / 2;

      return {
        code,
        color: ATTR_HEX[code] ?? '#f59e0b',
        bgPath: buildArcPath(startDeg, startDeg + SEG_ARC),
        fillPath: fillPct >= 0.01 ? buildArcPath(startDeg, startDeg + SEG_ARC * fillPct) : null,
        fillPct,
        level,
        threshold,
        ready: level >= threshold,
        labelX: (CX + LABEL_R * Math.cos(toRad(midDeg))).toFixed(2),
        labelY: (CY + LABEL_R * Math.sin(toRad(midDeg))).toFixed(2),
      };
    });
  });

  // Material shortfalls against the required prestige cost
  readonly materialShortfalls = computed(() => {
    const cost = this.status()?.material_cost ?? 0;
    if (cost === 0) return [];
    return (this.profile()?.attributes ?? [])
      .filter((a) => ORDINARY_CODES.has(a.code))
      .map((a) => ({
        code: a.code,
        name: MATERIAL_NAMES[a.code] ?? a.code,
        balance: a.material_balance,
        shortfall: Math.max(0, cost - a.material_balance),
      }))
      .filter((a) => a.shortfall > 0);
  });

  // Helper (True only when all 7 attributes are at threshold, materials are sufficient, and a buff is selected)
  readonly canPrestigeUp = computed(
    () =>
      this.ringSegments().every((s) => s.ready) &&
      this.materialShortfalls().length === 0 &&
      !!this.selectedBuff,
  );

  // Helper (Segments whose level is still below the threshold)
  readonly missingSegments = computed(() => this.ringSegments().filter((s) => !s.ready));

  // Helper (Counts attributes already at threshold)
  readonly readyCount = computed(() => this.ringSegments().filter((s) => s.ready).length);

  // Helper (Missing materials with English names and levels needed)
  readonly missingMaterials = computed(() =>
    this.missingSegments().map((s) => ({
      code: s.code,
      name: MATERIAL_NAMES[s.code] ?? s.code,
      needed: s.threshold - s.level,
    })),
  );

  // Helper (Profile attributes sorted in strict SPECIAL order)
  readonly sortedAttributes = computed(() => {
    const attrs = this.profile()?.attributes ?? [];
    return SPECIAL_ORDER.map((code) => attrs.find((a) => a.code === code)).filter(
      Boolean,
    ) as typeof attrs;
  });

  // Helper (Next prestige number)
  readonly nextPrestigeNumber = computed(() => (this.status()?.prestige_count ?? 0) + 1);

  // Function to perform the Prestige Up action
  prestigeUp(): void {
    if (!this.canPrestigeUp() || this.prestiging()) return;
    this.prestiging.set(true);

    this.api.prestigeUp({ buff_type_code: this.selectedBuff }).subscribe({
      next: (res: PrestigeUpResponse) => {
        this.prestiging.set(false);
        this.selectedBuff = '';
        this.playerState.prestigeCount.set(res.prestige_number);
        this.toast.show(
          {
            type: 'levelup',
            icon: '🔥',
            title: `PRESTIGE #${res.prestige_number}!`,
            message: `${res.buff_display_name} +${res.new_total_bonus}% · All attributes reset`,
          },
          6000,
        );
        this.prestigeFlash.set(true);
        setTimeout(() => this.prestigeFlash.set(false), 1500);
        this.load();
      },
      error: (err) => {
        this.prestiging.set(false);
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Prestige Failed',
          message: err.error?.detail ?? 'Could not complete prestige',
        });
      },
    });
  }

  // Function to get the current total bonus for the selected buff type
  currentBuffBonus(): number {
    const active = this.status()?.active_buffs.find((b) => b.buff_type_code === this.selectedBuff);
    return active?.total_bonus ?? 0;
  }

  // Function to get the projected total bonus after performing prestige
  nextBuffBonus(): number {
    const bt = this.status()?.available_buff_types.find((b) => b.code === this.selectedBuff);
    return this.currentBuffBonus() + (bt?.bonus_percent ?? 0);
  }

  // Function to return the display name of the currently selected buff type
  buffPreviewName(): string {
    return (
      this.status()?.available_buff_types.find((b) => b.code === this.selectedBuff)?.display_name ??
      ''
    );
  }

  // Function to return material name for an attribute code
  materialName(code: string): string {
    return MATERIAL_NAMES[code] ?? code;
  }

  // Function to glow dynamically based on prestige count
  ringGlowClass(): string {
    const n = this.status()?.prestige_count ?? 0;
    if (n === 0) return '';
    if (n < 3) return 'ring-glow-low';
    if (n < 7) return 'ring-glow-mid';
    return 'ring-glow-high';
  }

  // Function to get the color class for an attribute code
  attrColor(code: string): string {
    return ATTR_COLORS[code] ?? 'text-forge-primary';
  }

  // Function to get the hex color for an attribute
  attrHex(code: string): string {
    return ATTR_HEX[code] ?? '#f59e0b';
  }
}
