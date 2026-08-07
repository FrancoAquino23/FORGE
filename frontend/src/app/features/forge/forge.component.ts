/* ==================================================================
   FORGE COMPONENT LOGIC
   ================================================================== */

import { Component, DestroyRef, OnInit, inject, signal, computed } from '@angular/core';
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
import {
  ATTR_COLORS,
  ATTR_ICONS,
  ATTR_BAR_COLORS,
  fmt,
  attrColor,
  attrIcon,
} from '../../shared/ui-constants';
import { ApiService, PlayerProfile } from '../../core/api.service';
import { RelicWorkshopComponent } from '../relic-workshop/relic-workshop.component';
import { ToastService } from '../../core/toast.service';
import { SoundService } from '../../core/sound.service';

// Size steps available on the slider
const BATCH_STEPS = [1, 5, 10, 25, 50, 100];

// Attribute codes
const ORDINARY_CODES = ['S', 'P', 'E', 'C', 'I', 'A'];

// Row border color constants
const ROW_OK_BORDER = 'border-green-500/30';
const ROW_BAD_BORDER = 'border-red-500/25';
const ROW_NEUTRAL_BORDER = 'border-forge-border';

@Component({
  selector: 'app-forge',
  imports: [NgIconComponent, RelicWorkshopComponent],
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
  templateUrl: './forge.component.html',
  styleUrl: './forge.component.scss',
})
export class ForgeComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private sound = inject(SoundService);
  private destroyRef = inject(DestroyRef);

  profile = signal<PlayerProfile | null>(null);
  loading = signal(true);
  loadError = signal(false);
  transmuting = signal(false);
  sliderIndex = signal(0);

  readonly BATCH_STEPS = BATCH_STEPS;
  readonly ORDINARY_CODES = ORDINARY_CODES;
  readonly StardustIcon = ATTR_ICONS['L'];

  batchSize = computed(() => BATCH_STEPS[this.sliderIndex()]);
  costEach = computed(() => this.batchSize() * 150);
  minReward = computed(() => this.batchSize() * 20);
  maxReward = computed(() => this.batchSize() * 30);
  sliderPct = computed(() => (this.sliderIndex() / (BATCH_STEPS.length - 1)) * 100);

  ordinary = computed(() =>
    (this.profile()?.attributes ?? []).filter((a) => ORDINARY_CODES.includes(a.code)),
  );

  stardust = computed(() => this.profile()?.attributes?.find((a) => a.code === 'L') ?? null);

  canTransmute = computed(
    () =>
      !this.transmuting() && this.ordinary().every((a) => a.material_balance >= this.costEach()),
  );

  // Initialize component
  ngOnInit(): void {
    this.load();
  }

  // Load component
  load(): void {
    this.loading.set(true);
    this.api
      .getProfile()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (p) => {
          this.profile.set(p);
          this.loading.set(false);
        },
        error: () => this.loadError.set(true),
      });
  }

  // Function to handle slider changes
  onSliderChange(event: Event): void {
    const idx = parseInt((event.target as HTMLInputElement).value, 10);
    this.sliderIndex.set(idx);
  }

  // Function to perform material transmutation
  transmute(): void {
    if (!this.canTransmute()) return;
    this.transmuting.set(true);

    this.api
      .transmute(this.batchSize())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.sound.playStardust();
          this.transmuting.set(false);
          this.toast.fromTransmute(res);
          this.load();
        },
        error: (err: { error?: { detail?: string } }) => {
          this.transmuting.set(false);
          this.toast.showError(
            'Stardust Forge Failed',
            err,
            'Could not forge stardust. Please try again.',
          );
        },
      });
  }

  // Utility functions
  protected attrIcon = attrIcon;
  protected fmt = fmt;
  protected attrColor = attrColor;

  // Function to get bar color
  barColor(code: string): string {
    return ATTR_BAR_COLORS[code] ?? 'bg-forge-primary';
  }

  // Function to determine row border color
  rowBorder(balance: number): string {
    const cost = this.costEach();
    if (cost === 0) return ROW_NEUTRAL_BORDER;
    return balance >= cost ? ROW_OK_BORDER : ROW_BAD_BORDER;
  }

  // Function to determine text color
  balanceColor(balance: number): string {
    return balance >= this.costEach() ? 'text-forge-text' : 'text-red-400';
  }

  // Function to calculate fill percentage (Progress Bar)
  fillPct(balance: number): number {
    const cost = this.costEach();
    if (cost <= 0) return 100;
    return Math.min(100, Math.round((balance / cost) * 100));
  }
}
