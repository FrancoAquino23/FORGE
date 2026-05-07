/* ==================================================================
   TOAST COMPONENT LOGIC
   ================================================================== */

import { Component, inject } from '@angular/core';
import { Toast, ToastService, ToastType } from '../../core/toast.service';

// Border color mappings for different toast types
const TYPE_BORDER: Record<ToastType, string> = {
  xp: 'border-forge-primary/40 text-forge-text',
  levelup: 'border-yellow-400/70 text-yellow-300',
  loot: 'border-purple-500/60 text-purple-300',
  claim: 'border-green-500/50 text-green-400',
  error: 'border-red-500/60 text-red-400',
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
  templateUrl: './toast.component.html',
  styleUrl: './toast.component.scss',
})
export class ToastComponent {
  svc = inject(ToastService);

  // Function to get border and text color classes based on toast type and optional attribute code
  borderClass(toast: Toast): string {
    if (toast.attrCode && ATTR_TOAST_COLORS[toast.attrCode]) {
      return ATTR_TOAST_COLORS[toast.attrCode];
    }
    return TYPE_BORDER[toast.type] ?? TYPE_BORDER.xp;
  }
}
