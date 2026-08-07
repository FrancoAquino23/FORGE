/* ==================================================================
   FORGE - (TOAST SERVICE)
   ================================================================== */

import { Injectable, inject, signal } from '@angular/core';
import {
  AchievementUnlocked,
  MissionClaimResponse,
  RelicUpgradeResponse,
  TransmuteResponse,
} from './api.service';
import { ATTR_COLORS, ATTR_ICONS, ATTR_NAMES, RELIC_NAMES } from '../shared/ui-constants';
import { SoundService } from './sound.service';

// Types (Toast - For Notifications)
export type ToastType =
  | 'success'
  | 'levelup'
  | 'loot'
  | 'error'
  | 'node'
  | 'prestige'
  | 'expired';

// Interface (Toast - Data for Each Toast Notification)
export interface Toast {
  id: number;
  type: ToastType;
  icon: string;
  ngIcon?: string;
  iconColor?: string;
  title: string;
  message: string;
  attrCode?: string;
}

// Service (ToastService - Manages Toast Notifications)
@Injectable({ providedIn: 'root' })
export class ToastService {
  private sound = inject(SoundService);
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

  // Method (Show Error Toast)
  showError(title: string, err?: { error?: { detail?: string } }, fallback = 'An error occurred.'): void {
    this.sound.playError();
    this.show({
      type: 'error',
      icon: '',
      ngIcon: 'phosphorWarningBold',
      title,
      message: err?.error?.detail ?? fallback,
    });
  }

  // Method (Show Mission Completion, XP Gain, Material Gain, and Level Up Notifications)
  fromMissionClaim(res: MissionClaimResponse): void {
    const xpPart =
      res.new_attribute_level >= 10 && !res.leveled_up ? 'XP MAX' : `+${res.xp_earned} XP`;
    this.show({
      type: 'success',
      icon: '',
      ngIcon: 'phosphorCheckCircleBold',
      title: 'Mission Accomplished',
      message: `${xpPart} & +${res.material_earned} ${res.material_name}`,
    });
    if (res.leveled_up) {
      setTimeout(() => {
        this.show({
          type: 'levelup',
          icon: '',
          ngIcon: ATTR_ICONS[res.attribute_code] ?? 'phosphorSparkleBold',
          iconColor: ATTR_COLORS[res.attribute_code],
          title: `Level Up: ${ATTR_NAMES[res.attribute_code] ?? res.attribute_code}`,
          message: '',
          attrCode: res.attribute_code,
        }, 6000);
      }, 600);
    }
  }

  // Method (Show Relic Upgrade, New Level, and Bonus Percentage Notifications)
  fromRelicUpgrade(res: RelicUpgradeResponse): void {
    this.show({
      type: 'success',
      icon: '',
      ngIcon: ATTR_ICONS[res.attribute_code] ?? 'phosphorSparkleBold',
      iconColor: ATTR_COLORS[res.attribute_code],
      title: `Level Up: ${RELIC_NAMES[res.attribute_code] ?? res.attribute_code}`,
      message: '',
      attrCode: res.attribute_code,
    }, 6000);
  }

  // Method (Show Achievement Unlocked notifications)
  fromAchievements(unlocked: AchievementUnlocked[]): void {
    unlocked.forEach((a, i) => {
      setTimeout(() => {
        this.sound.playAchievement();
        this.show(
          {
            type: 'loot',
            icon: '',
            ngIcon: 'phosphorTrophyBold',
            iconColor: 'text-amber-300',
            title: 'Achievement Unlocked',
            message: a.title,
          },
          6000,
        );
      }, i * 800);
    });
  }

  // Method (Show Expired Mission — mission dismissed without rewards)
  showExpired(): void {
    this.sound.playError();
    this.show({
      type: 'expired',
      icon: '',
      ngIcon: 'phosphorCalendarXBold',
      title: 'Mission Failed',
      message: 'HR has been notified.',
    });
  }

  // Method (Show Transmutation Result — Stardust gained and new balance)
  fromTransmute(res: TransmuteResponse): void {
    this.show({
      type: 'loot',
      icon: '',
      ngIcon: 'phosphorSparkleBold',
      iconColor: ATTR_COLORS['L'],
      title: 'Stardust Forged',
      message: `+${res.stardust_gained} Stardust gained`,
      attrCode: 'L',
    });
  }
}
