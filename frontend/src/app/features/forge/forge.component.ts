/* ==================================================================
   FORGE COMPONENT LOGIC
   ================================================================== */

import { Component, OnInit, inject, signal, computed } from '@angular/core';
import {
  LucideAngularModule,
  LucideIconData,
  Hammer,
  Eye,
  Shield,
  Gem,
  Cpu,
  Zap,
  Sparkles,
} from 'lucide-angular';
import { ApiService, PlayerProfile } from '../../core/api.service';
import { ForgeService } from '../../core/forge.service';
import { ToastService } from '../../core/toast.service';

// Size steps available on the slider
const BATCH_STEPS = [1, 5, 10, 25, 50, 100];

// Attribute codes
const ORDINARY_CODES = ['S', 'P', 'E', 'C', 'I', 'A'];

// Icon & color mappings for attributes
const ATTR_ICONS: Record<string, LucideIconData> = {
  S: Hammer,
  P: Eye,
  E: Shield,
  C: Gem,
  I: Cpu,
  A: Zap,
  L: Sparkles,
};

const ATTR_COLORS: Record<string, string> = {
  S: 'text-red-400',
  P: 'text-blue-400',
  E: 'text-green-400',
  C: 'text-yellow-300',
  I: 'text-purple-400',
  A: 'text-cyan-400',
  L: 'text-orange-400',
};

const ATTR_BAR_COLORS: Record<string, string> = {
  S: 'bg-red-400',
  P: 'bg-blue-400',
  E: 'bg-green-400',
  C: 'bg-yellow-300',
  I: 'bg-purple-400',
  A: 'bg-cyan-400',
  L: 'bg-orange-400',
};

const ROW_OK_BORDER = 'border-green-500/30';
const ROW_BAD_BORDER = 'border-red-500/25';
const ROW_NEUTRAL_BORDER = 'border-forge-border';

@Component({
  selector: 'app-forge',
  standalone: true,
  imports: [LucideAngularModule],
  templateUrl: './forge.component.html',
  styleUrl: './forge.component.scss',
})
export class ForgeComponent implements OnInit {
  private api = inject(ApiService);
  private forgeApi = inject(ForgeService);
  private toast = inject(ToastService);

  profile = signal<PlayerProfile | null>(null);
  loading = signal(false);
  transmuting = signal(false);
  sliderIndex = signal(0);

  readonly BATCH_STEPS = BATCH_STEPS;
  readonly ORDINARY_CODES = ORDINARY_CODES;

  batchSize = computed(() => BATCH_STEPS[this.sliderIndex()]);
  costEach = computed(() => this.batchSize() * 10);
  minReward = computed(() => this.batchSize());
  maxReward = computed(() => this.batchSize() * 3);
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
    this.api.getProfile().subscribe({
      next: (p) => {
        this.profile.set(p);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
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

    this.forgeApi.transmute(this.batchSize()).subscribe({
      next: (res) => {
        this.transmuting.set(false);
        this.toast.fromTransmute(res);
        this.load();
      },
      error: (err) => {
        this.transmuting.set(false);
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Transmutation Failed',
          message: err.error?.detail ?? 'Insufficient materials',
        });
      },
    });
  }

  // Function to get UI icon for an attribute
  getIcon(code: string): LucideIconData {
    return ATTR_ICONS[code] ?? Sparkles;
  }

  // Function to get text color for an attribute
  attrColor(code: string): string {
    return ATTR_COLORS[code] ?? 'text-forge-primary';
  }

  // Function to get bar color
  barColor(code: string): string {
    return ATTR_BAR_COLORS[code] ?? 'bg-forge-primary';
  }

  // Function to determine row berder color
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
