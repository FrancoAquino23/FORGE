/* ==================================================================
   RELIC WORKSHOP COMPONENT LOGIC
   ================================================================== */

import { Component, OnInit, inject, signal } from '@angular/core';
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
import { ApiService, RelicInfo } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';

// Mappings for relic names, colors, icons, etc.
const ATTR_ICONS: Record<string, LucideIconData> = {
  S: Hammer,
  P: Eye,
  E: Shield,
  C: Gem,
  I: Cpu,
  A: Zap,
  L: Sparkles,
};

// Mapping of attribute codes to their display names for relics
const RELIC_NAMES: Record<string, string> = {
  S: 'Yunque de Poder',
  P: 'Faro de Claridad',
  E: 'Escudo de Eternidad',
  C: 'Cáliz de Armonía',
  I: 'Orbe de Lógica',
  A: 'Elixir de Velocidad',
  L: 'Tótem de Gracia',
};

// Color mappings for relic display based on attribute code
const ATTR_COLORS: Record<string, string> = {
  S: 'text-red-400',
  P: 'text-blue-400',
  E: 'text-green-400',
  C: 'text-yellow-300',
  I: 'text-purple-400',
  A: 'text-cyan-400',
  L: 'text-orange-400',
};

// Border color mappings for relic cards based on attribute code
const BORDER_COLORS: Record<string, string> = {
  S: 'border-red-500/30 hover:border-red-500/60',
  P: 'border-blue-500/30 hover:border-blue-500/60',
  E: 'border-green-500/30 hover:border-green-500/60',
  C: 'border-yellow-500/30 hover:border-yellow-500/60',
  I: 'border-purple-500/30 hover:border-purple-500/60',
  A: 'border-cyan-500/30 hover:border-cyan-500/60',
  L: 'border-orange-500/30 hover:border-orange-500/60',
};

// Color mappings for the XP bars in relic cards based on attribute code
const BAR_COLORS: Record<string, string> = {
  S: '#f87171',
  P: '#60a5fa',
  E: '#4ade80',
  C: '#fde047',
  I: '#c084fc',
  A: '#22d3ee',
  L: '#fb923c',
};

@Component({
  selector: 'app-relic-workshop',
  imports: [LucideAngularModule],
  templateUrl: './relic-workshop.component.html',
})
export class RelicWorkshopComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);

  relics = signal<RelicInfo[]>([]);
  loading = signal(false);
  upgrading = signal('');

  // Load component
  ngOnInit(): void {
    this.load();
  }

  // Function to load the player's relics from the API and update the component state
  load(): void {
    this.loading.set(true);
    this.api.getRelics().subscribe({
      next: (res) => {
        this.relics.set(res.relics);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  // Function to handle relic upgrade action, sends upgrade request to API and updates state based on response
  upgrade(relic: RelicInfo): void {
    if (this.upgrading() || !relic.can_upgrade) return;
    this.upgrading.set(relic.attribute_code);

    this.api.upgradeRelic(relic.attribute_code).subscribe({
      next: (res) => {
        this.upgrading.set('');
        this.toast.fromRelicUpgrade(res);
        this.load();
      },
      error: (err) => {
        this.upgrading.set('');
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Error',
          message: err.error?.detail ?? 'No se pudo mejorar la reliquia',
        });
      },
    });
  }

  // Function to get the display name of a relic
  relicName(code: string): string {
    return RELIC_NAMES[code] ?? code;
  }

  // Function to get the color class for a relic
  attrColor(code: string): string {
    return ATTR_COLORS[code] ?? 'text-forge-primary';
  }

  // Function to get the border color class for a relic card
  borderClass(code: string): string {
    return BORDER_COLORS[code] ?? 'border-forge-border';
  }

  // Function to get the color for the XP bar in a relic card
  barColor(code: string): string {
    return BAR_COLORS[code] ?? '#f59e0b';
  }

  // Function to get the appropriate icon for a relic
  getIcon(code: string): LucideIconData {
    return ATTR_ICONS[code] ?? Sparkles;
  }

  // Function to format the relic level with leading zeros for consistent display
  formatLevel(n: number): string {
    return String(n).padStart(2, '0');
  }

  // Function to calculate the percentage fill for the relic level bar based on its current level
  levelPct(relic: RelicInfo): number {
    return Math.min(100, (relic.level / 10) * 100);
  }
}
