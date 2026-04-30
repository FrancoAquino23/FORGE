/* ==================================================================
   TOAST COMPONENT LOGIC
   ================================================================== */

import { Component, inject } from '@angular/core';
import { ToastService, ToastType } from '../../core/toast.service';

// Border color mappings for different toast types
const TYPE_BORDER: Record<ToastType, string> = {
  xp: 'border-forge-primary/40 text-forge-text',
  levelup: 'border-yellow-400/70 text-yellow-300',
  loot: 'border-purple-500/60 text-purple-300',
  claim: 'border-green-500/50 text-green-400',
  error: 'border-red-500/60 text-red-400',
};

// Main toast component that displays toast notifications
@Component({
  selector: 'app-toast',
  templateUrl: './toast.component.html',
  styleUrl: './toast.component.scss',
})
export class ToastComponent {
  svc = inject(ToastService);

  // Function to get border and text color classes based on toast type
  borderClass(type: ToastType): string {
    return TYPE_BORDER[type] ?? TYPE_BORDER.xp;
  }
}
