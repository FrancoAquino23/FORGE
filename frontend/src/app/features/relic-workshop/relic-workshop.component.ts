/* ==================================================================
   RELIC WORKSHOP COMPONENT LOGIC
   ================================================================== */

import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import {
  phosphorCrownBold,
  phosphorHandEyeBold,
  phosphorCastleTurretBold,
  phosphorHeartBold,
  phosphorAtomBold,
  phosphorInfinityBold,
  phosphorCloverBold,
} from '@ng-icons/phosphor-icons/bold';
import { ApiService, RelicInfo } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { SoundService } from '../../core/sound.service';
import { ATTR_HEX, RELIC_NAMES, fmt, attrColor } from '../../shared/ui-constants';

// Preview levels to cycle through
const PREVIEW_LEVELS = [1, 5, 10];

// Constants for relic icons
const RELIC_ICONS: Record<string, string> = {
  S: 'phosphorCrownBold',
  P: 'phosphorHandEyeBold',
  E: 'phosphorCastleTurretBold',
  C: 'phosphorHeartBold',
  I: 'phosphorAtomBold',
  A: 'phosphorInfinityBold',
  L: 'phosphorCloverBold',
};

// Level 1–4: dim border
const BORDER_DIM: Record<string, string> = {
  S: 'border-red-400/30',
  P: 'border-blue-400/30',
  E: 'border-green-400/30',
  C: 'border-yellow-300/30',
  I: 'border-purple-400/30',
  A: 'border-cyan-400/30',
  L: 'border-orange-400/30',
};

// Level 5–9: medium border
const BORDER_MED: Record<string, string> = {
  S: 'border-red-400/60',
  P: 'border-blue-400/60',
  E: 'border-green-400/60',
  C: 'border-yellow-300/60',
  I: 'border-purple-400/60',
  A: 'border-cyan-400/60',
  L: 'border-orange-400/60',
};

// Level 10 (MAX): full border
const BORDER_MAX: Record<string, string> = {
  S: 'border-red-400',
  P: 'border-blue-400',
  E: 'border-green-400',
  C: 'border-yellow-300',
  I: 'border-purple-400',
  A: 'border-cyan-400',
  L: 'border-orange-400',
};

@Component({
  selector: 'app-relic-workshop',
  imports: [NgIconComponent],
  providers: [
    provideIcons({
      phosphorCrownBold,
      phosphorHandEyeBold,
      phosphorCastleTurretBold,
      phosphorHeartBold,
      phosphorAtomBold,
      phosphorInfinityBold,
      phosphorCloverBold,
    }),
  ],
  templateUrl: './relic-workshop.component.html',
  styleUrl: './relic-workshop.component.scss',
})
export class RelicWorkshopComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private sound = inject(SoundService);
  private destroyRef = inject(DestroyRef);

  relics = signal<RelicInfo[]>([]);
  loading = signal(false);
  upgrading = signal('');

  readonly previewLevelIdx = signal(-1);

  readonly previewLabel = computed(() => {
    const idx = this.previewLevelIdx();
    return idx >= 0 ? `LV ${PREVIEW_LEVELS[idx]}` : null;
  });

  readonly displayRelics = computed<RelicInfo[]>(() => {
    const idx = this.previewLevelIdx();
    if (idx < 0) return this.relics();
    const level = PREVIEW_LEVELS[idx];
    return this.relics().map((r) => ({
      ...r,
      level,
      bonus_pct: level * 5,
      can_upgrade: level < 10,
      upgrade_cost: level < 10 ? level * 150 : null,
    }));
  });

  // Load component
  ngOnInit(): void {
    this.load();
  }

  // Function to load component data
  load(): void {
    if (this.loading()) return;
    this.loading.set(true);
    this.api
      .getRelics()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.relics.set(res.relics);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  // Function to handle relic upgrade
  upgrade(relic: RelicInfo): void {
    if (this.previewLabel() || this.upgrading() || !relic.can_upgrade) return;
    this.upgrading.set(relic.attribute_code);

    this.api
      .upgradeRelic(relic.attribute_code)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.sound.playUpgrade();
          this.upgrading.set('');
          this.toast.fromRelicUpgrade(res);
          this.load();
        },
        error: (err) => {
          this.upgrading.set('');
          this.toast.showError(
            'Relic Upgrade Failed',
            err,
            'Could not upgrade relic. Please try again.',
          );
        },
      });
  }

  // PREVIEW — cycle through LV 1 → LV 5 → LV 10 → off
  cyclePreviewLevel(): void {
    this.previewLevelIdx.update((i) =>
      i >= PREVIEW_LEVELS.length - 1 ? -1 : i + 1,
    );
  }

  // Function to get the display name of a relic
  relicName(code: string): string {
    return RELIC_NAMES[code] ?? code;
  }

  // Function to get the icon name for a relic
  relicIcon(code: string): string {
    return RELIC_ICONS[code] ?? 'phosphorCloverBold';
  }

  // Function to get level-based border + level class for a relic card
  relicBorderClass(r: RelicInfo): string {
    if (r.level >= 10) return `${BORDER_MAX[r.attribute_code] ?? 'border-forge-border'} relic-card--max`;
    if (r.level >= 5) return `${BORDER_MED[r.attribute_code] ?? 'border-forge-border'} relic-card--mid`;
    return BORDER_DIM[r.attribute_code] ?? 'border-forge-border';
  }

  // Function to pass the attribute hex color as a CSS custom property for glow
  relicCardStyle(r: RelicInfo): Record<string, string> {
    return { '--relic-hex': ATTR_HEX[r.attribute_code] ?? '' };
  }

  // Function to format a level number
  formatLevel(n: number): string {
    return String(n).padStart(2, '0');
  }

  // Constants & utility functions
  protected attrColor = attrColor;
  protected fmt = fmt;
}
