/* ==================================================================
   PRESTIGE COMPONENT LOGIC
   ================================================================== */

import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  ApiService,
  PlayerProfile,
  PrestigeStatusResponse,
  PrestigeUpResponse,
} from '../../core/api.service';
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

  profile = signal<PlayerProfile | null>(null);
  status = signal<PrestigeStatusResponse | null>(null);
  prestiging = signal(false);
  prestigeFlash = signal(false);

  selectedBuff = '';

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

  // Helper (True only when all 7 attributes are at threshold)
  readonly canPrestigeUp = computed(
    () => this.ringSegments().every((s) => s.ready) && !!this.selectedBuff,
  );

  // Helper (Segments whose level is still below the threshold)
  readonly missingSegments = computed(() => this.ringSegments().filter((s) => !s.ready));

  // Helper (Counts attributes already at threshold)
  readonly readyCount = computed(() => this.ringSegments().filter((s) => s.ready).length);

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
            title: `¡PRESTIGE #${res.prestige_number}!`,
            message: `${res.buff_display_name} +${res.new_total_bonus}% · Todos los atributos reiniciados`,
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
          title: 'Prestige Fallido',
          message: err.error?.detail ?? 'No se pudo completar el prestige',
        });
      },
    });
  }

  // Function to get the bonus percentage of the currently selected buff
  buffPreviewBonus(): string {
    const bt = this.status()?.available_buff_types.find((b) => b.code === this.selectedBuff);
    return bt ? String(bt.bonus_percent) : '?';
  }

  // Function to return the display name of the currently selected buff type
  buffPreviewName(): string {
    return (
      this.status()?.available_buff_types.find((b) => b.code === this.selectedBuff)?.display_name ??
      ''
    );
  }

  // Function to glow dynamicly based on prestige count
  ringGlowClass(): string {
    const n = this.status()?.prestige_count ?? 0;
    if (n === 0) return '';
    if (n < 3) return 'ring-glow-low';
    if (n < 7) return 'ring-glow-mid';
    return 'ring-glow-high';
  }

  // Function to get the color class for a buff type based on its code
  attrColor(code: string): string {
    return ATTR_COLORS[code] ?? 'text-forge-primary';
  }

  // Function to get the hex color for an attribute
  attrHex(code: string): string {
    return ATTR_HEX[code] ?? '#f59e0b';
  }
}
