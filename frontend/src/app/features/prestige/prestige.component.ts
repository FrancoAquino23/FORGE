/* ==================================================================
   PRESTIGE COMPONENT LOGIC
   ================================================================== */

import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import {
  phosphorSwordBold,
  phosphorEyeBold,
  phosphorShieldBold,
  phosphorSketchLogoBold,
  phosphorDnaBold,
  phosphorLightningBold,
  phosphorSparkleBold,
  phosphorSpinnerBold,
  phosphorPlugsBold,
} from '@ng-icons/phosphor-icons/bold';
import { ApiService, PrestigeStatusResponse, PrestigeUpResponse } from '../../core/api.service';
import { PlayerStateService } from '../../core/player-state.service';
import { ToastService } from '../../core/toast.service';
import { SoundService } from '../../core/sound.service';
import {
  ATTR_HEX,
  ATTR_ICONS,
  ATTR_NAMES,
  fmt,
  attrColor,
  attrIcon,
} from '../../shared/ui-constants';

// Canonical S.P.E.C.I.A.L. order
const SPECIAL_ORDER = ['S', 'P', 'E', 'C', 'I', 'A', 'L'] as const;

@Component({
  selector: 'app-prestige',
  imports: [NgIconComponent],
  providers: [
    provideIcons({
      phosphorSwordBold,
      phosphorEyeBold,
      phosphorShieldBold,
      phosphorSketchLogoBold,
      phosphorDnaBold,
      phosphorLightningBold,
      phosphorSparkleBold,
      phosphorSpinnerBold,
      phosphorPlugsBold,
    }),
  ],
  templateUrl: './prestige.component.html',
  styleUrl: './prestige.component.scss',
})
export class PrestigeComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private sound = inject(SoundService);
  private playerState = inject(PlayerStateService);
  private destroyRef = inject(DestroyRef);

  readonly profile = this.playerState.profile;
  status = signal<PrestigeStatusResponse | null>(null);
  loadError = signal(false);
  prestiging = signal(false);
  prestigeFlash = signal(false);

  // Lifecycle
  ngOnInit(): void {
    this.load();
  }

  // Load profile & prestige status
  private load(): void {
    this.api
      .getProfile()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (p) => this.profile.set(p),
        error: () => this.loadError.set(true),
      });
    this.api
      .getPrestigeStatus()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (s) => {
          this.status.set(s);
          this.playerState.prestigeCount.set(s.prestige_count);
        },
        error: () => this.loadError.set(true),
      });
  }

  // Attribute data for hexagon grid
  readonly hexAttrs = computed(() => {
    const attrs = this.profile()?.attributes ?? [];
    const threshold = this.status()?.threshold_level ?? 10;
    return SPECIAL_ORDER.map((code) => {
      const attr = attrs.find((a) => a.code === code);
      const level = attr?.level ?? 0;
      return {
        code,
        name: ATTR_NAMES[code] ?? code,
        icon: ATTR_ICONS[code],
        hex: ATTR_HEX[code] ?? '#f59e0b',
        level,
        threshold,
        ready: level >= threshold,
      };
    });
  });

  // Stardust shortfall for prestige upgrade
  readonly materialShortfalls = computed(() => {
    const cost = this.status()?.stardust_cost ?? 0;
    if (cost === 0) return [];
    const stardust = (this.profile()?.attributes ?? []).find((a) => a.code === 'L');
    const balance = stardust?.material_balance ?? 0;
    if (balance >= cost) return [];
    return [{ code: 'L', name: 'Stardust', balance, shortfall: cost - balance }];
  });

  // Prestige upgrade eligibility
  readonly canPrestigeUp = computed(
    () => this.hexAttrs().every((s) => s.ready) && this.materialShortfalls().length === 0,
  );

  // Count of attributes at threshold (Ready for PrestigeUp)
  readonly readyCount = computed(() => this.hexAttrs().filter((s) => s.ready).length);

  // Stardust info for prestige panel
  readonly stardustInfo = computed(() => {
    const cost = this.status()?.stardust_cost ?? 0;
    const stardust = (this.profile()?.attributes ?? []).find((a) => a.code === 'L');
    const balance = stardust?.material_balance ?? 0;
    const sufficient = balance >= cost;
    const fillPct = cost > 0 ? Math.min(100, Math.round((balance / cost) * 100)) : 100;
    return { balance, cost, sufficient, fillPct };
  });

  // Next prestige number
  readonly nextPrestigeNumber = computed(() => (this.status()?.prestige_count ?? 0) + 1);

  // Rows for honeycomb layout: 3 top + 4 bottom
  readonly hexRow1 = computed(() => this.hexAttrs().slice(0, 3));
  readonly hexRow2 = computed(() => this.hexAttrs().slice(3, 7));

  // Prestige upgrade action
  prestigeUp(): void {
    if (!this.canPrestigeUp() || this.prestiging()) return;
    this.prestiging.set(true);

    this.api
      .prestigeUp()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res: PrestigeUpResponse) => {
          this.sound.playPrestige();
          this.prestiging.set(false);
          this.playerState.prestigeCount.set(res.prestige_number);
          this.toast.show(
            {
              type: 'prestige',
              icon: '',
              ngIcon: 'phosphorArrowFatLinesUpBold',
              title: `PRESTIGE #${res.prestige_number} ACHIEVED`,
              message: `All progress reset & +${res.pp_earned} Prestige Points awarded`,
            },
            6000,
          );
          if (res.newly_unlocked?.length) this.toast.fromAchievements(res.newly_unlocked, 2500);
          this.prestigeFlash.set(true);
          setTimeout(() => this.prestigeFlash.set(false), 1500);
          this.load();
        },
        error: (err) => {
          this.prestiging.set(false);
          this.toast.showError(
            'Prestige Upgrade Failed',
            err,
            'Could not upgrade prestige. Please try again.',
          );
        },
      });
  }

  // Constant & utility functions
  protected attrColor = attrColor;

  // Attribute hex color
  attrHex(code: string): string {
    return ATTR_HEX[code] ?? '#f59e0b';
  }

  // Constant & utility functions
  protected fmt = fmt;
  protected attrIcon = attrIcon;
}
