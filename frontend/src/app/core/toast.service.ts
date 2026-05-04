/* ==================================================================
   FORGE - (TOAST SERVICE)
   ================================================================== */

import { Injectable, signal } from '@angular/core';
import { ActivityLogResponse, MissionClaimResponse, RelicUpgradeResponse } from './api.service';

// Types (Toast - For Notifications)
export type ToastType = 'xp' | 'levelup' | 'loot' | 'claim' | 'error';

// Interface (Toast - Data for Each Toast Notification)
export interface Toast {
  id: number;
  type: ToastType;
  icon: string;
  title: string;
  message: string;
}

// Service (ToastService - Manages Toast Notifications)
@Injectable({ providedIn: 'root' })
export class ToastService {
  readonly toasts = signal<Toast[]>([]);
  private counter = 0;

  // Method (Show Toast - Add Toast to List with Auto-Dismiss After Duration)
  show(toast: Omit<Toast, 'id'>, durationMs = 4500): void {
    const id = ++this.counter;
    this.toasts.update((list) => [...list, { ...toast, id }]);
    setTimeout(() => this.dismiss(id), durationMs);
  }

  // Method (Dismiss Toast - Remove Toast from List by ID)
  dismiss(id: number): void {
    this.toasts.update((list) => list.filter((t) => t.id !== id));
  }

  // Method (From Activity Log Response - Show XP Gain, Level Up, Loot Drop, and Streak Notifications)
  fromActivityLog(res: ActivityLogResponse): void {
    if (res.level_up.occurred) {
      this.show({
        type: 'levelup',
        icon: '⚡',
        title: '¡LEVEL UP!',
        message: `${res.material_name} ahora en Nivel ${res.level_up.new_level}`,
      });
    } else {
      this.show({
        type: 'xp',
        icon: '🔥',
        title: 'Actividad Registrada',
        message: `+${res.xp_earned} XP · +${res.material_earned} ${res.material_name}`,
      });
    }
    if (res.streak_broken) {
      this.show(
        {
          type: 'error',
          icon: '💔',
          title: 'Racha Rota',
          message: 'Tu racha se ha reiniciado a 0',
        },
        5000,
      );
    }
  }

  // Method (Show Mission Completion, XP Gain, Material Gain, and Level Up Notifications)
  fromMissionClaim(res: MissionClaimResponse): void {
    this.show({
      type: 'claim',
      icon: '✅',
      title: 'Misión Completada',
      message: `+${res.xp_earned} XP · +${res.material_earned} ${res.material_name}`,
    });
    if (res.leveled_up) {
      setTimeout(() => {
        this.show({
          type: 'levelup',
          icon: '⚡',
          title: '¡LEVEL UP!',
          message: `${res.material_name} ahora en Nivel ${res.new_attribute_level}`,
        });
      }, 600);
    }
  }

  // Method (Show Relic Upgrade, New Level, and Bonus Percentage Notifications)
  fromRelicUpgrade(res: RelicUpgradeResponse): void {
    this.show({
      type: 'claim',
      icon: '⚒',
      title: 'Reliquia Mejorada',
      message: `Nivel ${res.new_level} · +${res.new_bonus_pct}% bonus activo`,
    });
  }
}
