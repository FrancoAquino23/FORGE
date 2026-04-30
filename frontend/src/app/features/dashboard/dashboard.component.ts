/* ==================================================================
   DASHBOARD COMPONENT LOGIC
   ================================================================== */

import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService, AttributeProfile, PlayerProfile } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { InventoryComponent, ConsumableUsedEvent } from '../inventory/inventory.component';

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

// Main dashboard component that displays player profile, attributes, and allows quick activity logging
@Component({
  selector: 'app-dashboard',
  imports: [FormsModule, RouterLink, InventoryComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);

  profile = signal<PlayerProfile | null>(null);
  loadError = signal('');
  logging = signal(false);
  staminaPulse = signal(false);
  overchargeActive = signal(false);
  xpFlash = signal('');
  logAttr = '';
  logMinutes: number | null = null;
  logDesc = '';

  // Load component
  ngOnInit(): void {
    this.loadProfile();
  }

  // Load player profile from API
  private loadProfile(): void {
    this.api.getProfile().subscribe({
      next: (p) => this.profile.set(p),
      error: () => this.loadError.set('No se pudo cargar el perfil. Verifica tu token.'),
    });
  }

  // Handle activity log submission
  submitLog(): void {
    if (!this.logAttr || this.logging()) return;
    const targetCode = this.logAttr;
    this.logging.set(true);

    this.api
      .logActivity({
        attribute_code: targetCode,
        duration_minutes: this.logMinutes ?? undefined,
        description: this.logDesc || undefined,
      })
      .subscribe({
        next: (res) => {
          this.toast.fromActivityLog(res);
          this.logging.set(false);
          this.logAttr = '';
          this.logMinutes = null;
          this.logDesc = '';
          this.xpFlash.set(targetCode);
          setTimeout(() => this.xpFlash.set(''), 700);
          this.loadProfile();
        },
        error: (err) => {
          this.toast.show({
            type: 'error',
            icon: '❌',
            title: 'Error',
            message: err.error?.detail ?? 'No se pudo registrar la actividad',
          });
          this.logging.set(false);
        },
      });
  }

  // Function to handle effects when a consumable item is used
  onConsumableUsed(event: ConsumableUsedEvent): void {
    if (event.effectType === 'streak_shield') {
      this.staminaPulse.set(true);
      setTimeout(() => this.staminaPulse.set(false), 3200);
      this.loadProfile();
    }
    if (event.effectType === 'overcharge') {
      this.overchargeActive.set(true);
      if (event.activeUntil) {
        const msLeft = new Date(event.activeUntil).getTime() - Date.now();
        setTimeout(() => this.overchargeActive.set(false), msLeft);
      }
    }
  }

  // Function to calculate XP percentage for an attribute
  xpPct(attr: AttributeProfile): number {
    return attr.xp_to_next ? Math.min(100, (attr.xp_current / attr.xp_to_next) * 100) : 0;
  }

  // General percentage function (used for stamina bar)
  pct(value: number, max: number): number {
    return Math.min(100, (value / max) * 100);
  }

  // Function to determine stamina bar color based on current percentage
  staminaBarColor(current: number, max: number): string {
    const p = (current / max) * 100;
    if (p > 60) return 'bg-green-500';
    if (p > 30) return 'bg-yellow-500';
    return 'bg-red-500';
  }

  // Function to get color class for an attribute based on its code
  attrColor(code: string): string {
    return ATTR_COLORS[code] ?? 'text-forge-primary';
  }

  // Function to get glow class for an attribute based on its code
  attrGlow(code: string): string {
    return ATTR_GLOW[code] ?? '';
  }
}
