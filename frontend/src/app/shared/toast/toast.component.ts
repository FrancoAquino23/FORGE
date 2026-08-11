/* ==================================================================
   TOAST COMPONENT LOGIC
   ================================================================== */

import { Component, computed, inject } from '@angular/core';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import {
  phosphorArrowCircleUpBold,
  phosphorArrowCounterClockwiseBold,
  phosphorArrowFatLinesUpBold,
  phosphorCheckCircleBold,
  phosphorClipboardTextBold,
  phosphorDnaBold,
  phosphorEyeBold,
  phosphorFlagBold,
  phosphorFlameBold,
  phosphorLightningBold,
  phosphorMedalBold,
  phosphorShieldBold,
  phosphorSketchLogoBold,
  phosphorSparkleBold,
  phosphorSwordBold,
  phosphorTrashBold,
  phosphorTrophyBold,
  phosphorWarningBold,
  phosphorXCircleBold,
  phosphorCalendarXBold,
} from '@ng-icons/phosphor-icons/bold';
import { Toast, ToastService, ToastType } from '../../core/toast.service';

// Icon color mappings for different toast types
const TYPE_ICON_COLOR: Record<ToastType, string> = {
  success: 'text-green-400',
  levelup: 'text-yellow-300',
  loot: 'text-purple-300',
  error: 'text-red-400',
  node: 'text-amber-300',
  prestige: '',
  expired: 'text-red-400',
};

// Border color mappings for different toast types
const TYPE_BORDER: Record<ToastType, string> = {
  success: 'border-green-500/50 text-green-400',
  levelup: 'border-yellow-400/70 text-yellow-300',
  loot: 'border-purple-500/60 text-purple-300',
  error: 'border-red-500/60 text-red-400',
  node: 'border-amber-400/60 text-amber-300',
  prestige: 'border-transparent toast-prestige',
  expired: 'border-red-500/60 text-red-400',
};

// Node level-specific border/text colors (must be static strings for Tailwind JIT)
const NODE_LEVEL_BORDERS: Record<string, string> = {
  'text-orange-500': 'border-orange-500/60 text-orange-500',
  'text-slate-400':  'border-slate-400/60 text-slate-400',
  'text-amber-500':  'border-amber-500/60 text-amber-500',
};

// Attribute-specific border/text colors for level-up toasts
const ATTR_TOAST_COLORS: Record<string, string> = {
  S: 'border-red-400/60 text-red-400',
  P: 'border-blue-400/60 text-blue-400',
  E: 'border-green-400/60 text-green-400',
  C: 'border-yellow-300/60 text-yellow-300',
  I: 'border-purple-400/60 text-purple-400',
  A: 'border-cyan-400/60 text-cyan-400',
  L: 'border-orange-400/60 text-orange-400',
};

// Main toast component that displays toast notifications
@Component({
  selector: 'app-toast',
  imports: [NgIconComponent],
  viewProviders: [
    provideIcons({
      phosphorArrowCircleUpBold,
      phosphorArrowCounterClockwiseBold,
      phosphorArrowFatLinesUpBold,
      phosphorCheckCircleBold,
      phosphorClipboardTextBold,
      phosphorDnaBold,
      phosphorEyeBold,
      phosphorFlagBold,
      phosphorFlameBold,
      phosphorLightningBold,
      phosphorMedalBold,
      phosphorShieldBold,
      phosphorSketchLogoBold,
      phosphorSparkleBold,
      phosphorSwordBold,
      phosphorTrashBold,
      phosphorTrophyBold,
      phosphorWarningBold,
      phosphorXCircleBold,
      phosphorCalendarXBold,
    }),
  ],
  templateUrl: './toast.component.html',
  styleUrl: './toast.component.scss',
})
export class ToastComponent {
  svc = inject(ToastService);

  regularToasts = computed(() => this.svc.toasts().filter(t => t.type !== 'loot'));
  achievementToasts = computed(() => [...this.svc.toasts().filter(t => t.type === 'loot')].reverse());

  // Function to get icon color class based on toast type or explicit override
  iconColorClass(toast: Toast): string {
    return toast.iconColor ?? TYPE_ICON_COLOR[toast.type] ?? 'text-forge-muted';
  }

  // Function to get border and text color classes based on toast type and optional attribute code
  borderClass(toast: Toast): string {
    if (toast.iconColor) {
      if (NODE_LEVEL_BORDERS[toast.iconColor]) return NODE_LEVEL_BORDERS[toast.iconColor];
      const colorToken = toast.iconColor.replace('text-', '');
      return `border-${colorToken}/60 ${toast.iconColor}`;
    }
    if (toast.attrCode && ATTR_TOAST_COLORS[toast.attrCode]) {
      return ATTR_TOAST_COLORS[toast.attrCode];
    }
    return TYPE_BORDER[toast.type] ?? TYPE_BORDER.success;
  }
}
