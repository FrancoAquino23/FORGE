/* ==================================================================
   PRESTIGE COMPONENT LOGIC
   ================================================================== */

import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  ApiService,
  AttributeProfile,
  PlayerProfile,
  PrestigeSacrificeResponse,
  PrestigeStatusResponse,
} from '../../core/api.service';
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

// Main prestige component that allows players to sacrifice attributes for buffs and displays prestige status
@Component({
  selector: 'app-prestige',
  imports: [FormsModule],
  templateUrl: './prestige.component.html',
  styleUrl: './prestige.component.scss',
})
export class PrestigeComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);

  profile = signal<PlayerProfile | null>(null);
  status = signal<PrestigeStatusResponse | null>(null);
  sacrificing = signal('');
  prestigeFlash = signal(false);

  selectedBuff: Record<string, string> = {};

  // Load component
  ngOnInit(): void {
    this.load();
  }

  // Load player profile and prestige status from API
  private load(): void {
    this.api.getProfile().subscribe({ next: (p) => this.profile.set(p) });
    this.api.getPrestigeStatus().subscribe({ next: (s) => this.status.set(s) });
  }

  // Function to check if an attribute is eligible for sacrifice based on its level and prestige threshold
  isEligible(attr: AttributeProfile): boolean {
    return attr.level >= (this.status()?.threshold_level ?? 10);
  }

  // Function to calculate overall progress percentage towards next prestige
  progressPct(attr: AttributeProfile): number {
    const threshold = this.status()?.threshold_level ?? 10;
    return Math.min(100, (attr.level / threshold) * 100);
  }

  // Function to check if an attribute can currently be sacrificed
  canSacrifice(attr: AttributeProfile): boolean {
    return this.isEligible(attr) && !!this.selectedBuff[attr.code] && !this.sacrificing();
  }

  // Function to handle the sacrifice action for an attribute
  sacrifice(attr: AttributeProfile): void {
    const buffCode = this.selectedBuff[attr.code];
    if (!buffCode || this.sacrificing()) return;
    this.sacrificing.set(attr.code);

    this.api.sacrifice({ attribute_code: attr.code, buff_type_code: buffCode }).subscribe({
      next: (res: PrestigeSacrificeResponse) => {
        this.sacrificing.set('');
        delete this.selectedBuff[attr.code];
        this.toast.show(
          {
            type: 'levelup',
            icon: '🔥',
            title: '¡SACRIFICIO COMPLETADO!',
            message: `${attr.name} reiniciado · ${res.buff_display_name} +${res.new_total_bonus}%`,
          },
          6000,
        );
        this.prestigeFlash.set(true);
        setTimeout(() => this.prestigeFlash.set(false), 1200);
        this.load();
      },
      error: (err) => {
        this.sacrificing.set('');
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Sacrificio Fallido',
          message: err.error?.detail ?? 'No se pudo completar el sacrificio',
        });
      },
    });
  }

  // Function to get the bonus percentage of the currently selected buff
  buffPreviewBonus(attrCode: string): string {
    const code = this.selectedBuff[attrCode];
    if (!code) return '?';
    const bt = this.status()?.available_buff_types.find((b) => b.code === code);
    return bt ? String(bt.bonus_percent) : '?';
  }

  // Function to get the glow class for the prestige artifact based on the player's prestige count
  artifactGlowClass(): string {
    const n = this.status()?.prestige_count ?? 0;
    if (n === 0) return 'shadow-[0_0_30px_rgba(245,158,11,0.15)]';
    if (n < 3) return 'shadow-[0_0_50px_rgba(245,158,11,0.4)]';
    if (n < 7) return 'shadow-[0_0_80px_rgba(245,158,11,0.65)]';
    return 'shadow-[0_0_120px_rgba(245,158,11,0.9)] animate-forge-pulse';
  }

  // Function to get the color class for a buff type based on its code
  attrColor(code: string): string {
    return ATTR_COLORS[code] ?? 'text-forge-primary';
  }
}
