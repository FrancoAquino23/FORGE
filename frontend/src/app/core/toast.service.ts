/* ==================================================================
   FORGE - (TOAST SERVICE)
   ================================================================== */

import { Injectable, signal } from '@angular/core';
import { ActivityLogResponse, MissionClaimResponse } from './api.service';

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

// |
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

    // Show Loot Drop Toast if a Consumable was Dropped
    if (res.dropped_consumable) {
      setTimeout(() => {
        this.show(
          {
            type: 'loot',
            icon: '💎',
            title: '¡LOOT DROP!',
            message: `${res.dropped_consumable} cayó en tu Saco de Forja`,
          },
          5500,
        );
      }, 700);
    }

    if (res.streak_broken && !res.streak_shield_used) {
      this.show(
        {
          type: 'error',
          icon: '💔',
          title: 'Racha Rota',
          message: 'Tu racha se ha reiniciado a 0',
        },
        5000,
      );
    } else if (res.streak_shield_used) {
      this.show(
        {
          type: 'claim',
          icon: '🧪',
          title: 'Racha Protegida',
          message: 'Tu Poción de Estabilidad absorbió el golpe',
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
}
