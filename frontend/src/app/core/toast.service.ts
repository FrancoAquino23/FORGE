/* ==================================================================
   FORGE - (TOAST SERVICE)
   ================================================================== */

import { Injectable, signal } from '@angular/core';
import { Sparkles, LucideIconData } from 'lucide-angular';
import { MissionClaimResponse, RelicUpgradeResponse, TransmuteResponse } from './api.service';

// Types (Toast - For Notifications)
export type ToastType = 'xp' | 'levelup' | 'loot' | 'claim' | 'error' | 'node-bronze' | 'node-silver' | 'node-gold';

// Interface (Toast - Data for Each Toast Notification)
export interface Toast {
  id: number;
  type: ToastType;
  icon: string;
  lucideIcon?: LucideIconData;
  title: string;
  message: string;
  attrCode?: string;
}

const ATTR_NAMES: Record<string, string> = {
  S: 'Strength',
  P: 'Perception',
  E: 'Endurance',
  C: 'Charisma',
  I: 'Intelligence',
  A: 'Agility',
  L: 'Luck',
};

// Service (ToastService - Manages Toast Notifications)
@Injectable({ providedIn: 'root' })
export class ToastService {
  readonly toasts = signal<Toast[]>([]);
  private counter = 0;

  // Method (Show Toast - Add Toast to List with Auto-Dismiss After Duration)
  show(toast: Omit<Toast, 'id'>, durationMs = 4500): void {
    const id = ++this.counter;
    this.toasts.update((list) => {
      const capped = list.length >= 2 ? list.slice(1) : list;
      return [...capped, { ...toast, id }];
    });
    setTimeout(() => this.dismiss(id), durationMs);
  }

  // Method (Dismiss Toast - Remove Toast from List by ID)
  dismiss(id: number): void {
    this.toasts.update((list) => list.filter((t) => t.id !== id));
  }

  // Method (Show Mission Completion, XP Gain, Material Gain, and Level Up Notifications)
  fromMissionClaim(res: MissionClaimResponse): void {
    const xpPart =
      res.new_attribute_level >= 10 && !res.leveled_up ? 'XP MAX' : `+${res.xp_earned} XP`;
    this.show({
      type: 'claim',
      icon: '✅',
      title: 'Mission Accomplished',
      message: `${xpPart} · +${res.material_earned} ${res.material_name}`,
    });
    if (res.leveled_up) {
      setTimeout(() => {
        this.show({
          type: 'levelup',
          icon: '⚡',
          title: `Level Up: ${ATTR_NAMES[res.attribute_code] ?? res.attribute_code}!`,
          message: `Now at Level ${res.new_attribute_level}`,
          attrCode: res.attribute_code,
        });
      }, 600);
    }
  }

  // Method (Show Relic Upgrade, New Level, and Bonus Percentage Notifications)
  fromRelicUpgrade(res: RelicUpgradeResponse): void {
    this.show({
      type: 'claim',
      icon: '⚒',
      title: 'Relic Upgraded',
      message: `Level ${res.new_level} · +${res.new_bonus_pct}% active bonus`,
      attrCode: res.attribute_code,
    });
  }

  // Method (Show Transmutation Result — Stardust gained and new balance)
  fromTransmute(res: TransmuteResponse): void {
    this.show({
      type: 'loot',
      icon: '',
      lucideIcon: Sparkles,
      title: 'Stardust Obtained',
      message: `+${res.stardust_gained} ✦ Balance: ${res.new_stardust_balance}`,
      attrCode: 'L',
    });
  }
}
