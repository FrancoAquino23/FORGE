/* ==================================================================
   RELIC WORKSHOP COMPONENT LOGIC
   ================================================================== */

import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
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
  phosphorStarFourBold,
} from '@ng-icons/phosphor-icons/bold';
import { ApiService, RelicInfo } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { SoundService } from '../../core/sound.service';
import { ATTR_COLORS, ATTR_HEX, RELIC_NAMES, fmt, attrColor } from '../../shared/ui-constants';

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

// Constants for relic borders
const BORDER_COLORS: Record<string, string> = {
  S: 'border-red-400/30 hover:border-red-400/60',
  P: 'border-blue-400/30 hover:border-blue-400/60',
  E: 'border-green-400/30 hover:border-green-400/60',
  C: 'border-yellow-300/30 hover:border-yellow-300/60',
  I: 'border-purple-400/30 hover:border-purple-400/60',
  A: 'border-cyan-400/30 hover:border-cyan-400/60',
  L: 'border-orange-400/30 hover:border-orange-400/60',
};

@Component({
  selector: 'app-relic-workshop',
  imports: [NgIconComponent],
  providers: [
    provideIcons({
      phosphorCrownBold,
      phosphorStarFourBold,
      phosphorHandEyeBold,
      phosphorCastleTurretBold,
      phosphorHeartBold,
      phosphorAtomBold,
      phosphorInfinityBold,
      phosphorCloverBold,
    }),
  ],
  templateUrl: './relic-workshop.component.html',
})
export class RelicWorkshopComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private sound = inject(SoundService);
  private destroyRef = inject(DestroyRef);

  relics = signal<RelicInfo[]>([]);
  loading = signal(false);
  upgrading = signal('');

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
    if (this.upgrading() || !relic.can_upgrade) return;
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

  // Function to get the display name of a relic
  relicName(code: string): string {
    return RELIC_NAMES[code] ?? code;
  }

  // Constants & utility functions
  protected attrColor = attrColor;

  // Function to get the border class for a relic
  borderClass(code: string): string {
    return BORDER_COLORS[code] ?? 'border-forge-border';
  }

  // Function to get the icon name for a relic
  relicIcon(code: string): string {
    return RELIC_ICONS[code] ?? 'phosphorCloverBold';
  }

  // Constants & utility functions
  protected fmt = fmt;
  hoveredRelic = signal('');

  // Function to get the glow style for a relic
  glowStyle(code: string): Record<string, string> {
    if (this.hoveredRelic() !== code) return {};
    const hex = ATTR_HEX[code] ?? '';
    return { 'box-shadow': `0 0 14px ${hex}99` };
  }

  // Function to format a level number
  formatLevel(n: number): string {
    return String(n).padStart(2, '0');
  }
}
