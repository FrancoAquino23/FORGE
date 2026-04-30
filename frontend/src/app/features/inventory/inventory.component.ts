/* ==================================================================
   INVENTORY COMPONENT LOGIC
   ================================================================== */

import { Component, OnInit, inject, output, signal } from '@angular/core';
import { ApiService, ConsumableItem, UseConsumableResponse } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';

// Event emitted when a consumable item is used, containing the effect type and its active duration
export interface ConsumableUsedEvent {
  effectType: string;
  activeUntil: string | null;
}

// Inventory component that displays player's consumable items and allows using them
const ICONS: Record<string, string> = {
  STABILITY_POTION: '🧪',
  OVERCHARGE_CHIP: '⚡',
};

// Border color classes for different consumable effect types
const BORDER_CLASSES: Record<string, string> = {
  streak_shield: 'border-blue-500/40 hover:border-blue-400/60',
  overcharge: 'border-purple-500/40 hover:border-purple-400/60',
};

// Badge color classes for different consumable effect types and quantity states
const BADGE_CLASSES: Record<string, string> = {
  streak_shield: 'bg-blue-900/40 border-blue-500/40 text-blue-300',
  overcharge: 'bg-purple-900/40 border-purple-500/40 text-purple-300',
};

// Main inventory component that shows consumable items and handles their usage
@Component({
  selector: 'app-inventory',
  templateUrl: './inventory.component.html',
  styleUrl: './inventory.component.scss',
})
export class InventoryComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);

  readonly used = output<ConsumableUsedEvent>();

  items = signal<ConsumableItem[]>([]);
  loading = signal(false);
  using = signal('');

  // Load component
  ngOnInit(): void {
    this.load();
  }

  // Function to load inventory items from the API
  load(): void {
    this.loading.set(true);
    this.api.getInventory().subscribe({
      next: (res) => {
        this.items.set(res.items);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  // Function to handle using a consumable item
  use(item: ConsumableItem): void {
    if (this.using() || item.quantity === 0 || item.is_active) return;
    this.using.set(item.consumable_code);

    this.api.useConsumable(item.consumable_code).subscribe({
      next: (res: UseConsumableResponse) => {
        this.using.set('');
        this.toast.show({
          type: item.effect_type === 'overcharge' ? 'loot' : 'xp',
          icon: this.itemIcon(item),
          title: item.name,
          message: res.message,
        });
        this.load();
        this.used.emit({ effectType: item.effect_type, activeUntil: res.active_until });
      },
      error: (err) => {
        this.using.set('');
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Error',
          message: err.error?.detail ?? 'No se pudo usar el ítem',
        });
      },
    });
  }

  // Function to get the appropriate icon for a consumable item based on its code
  itemIcon(item: ConsumableItem): string {
    return ICONS[item.consumable_code] ?? '🔮';
  }

  // Function to determine the border class for a consumable item based on its effect type and quantity
  itemBorderClass(item: ConsumableItem): string {
    const base = BORDER_CLASSES[item.effect_type] ?? 'border-forge-border';
    return `${base} ${item.quantity === 0 ? 'opacity-50' : ''}`;
  }

  // Function to determine the badge class for the quantity display of a consumable item
  quantityBadgeClass(item: ConsumableItem): string {
    if (item.quantity === 0) return 'border-forge-border text-forge-muted';
    return BADGE_CLASSES[item.effect_type] ?? 'border-forge-primary/40 text-forge-primary';
  }

  // Function to determine the button class for a consumable item based on its effect type
  useButtonClass(item: ConsumableItem): string {
    if (item.effect_type === 'overcharge')
      return 'border border-purple-500/50 text-purple-300 hover:bg-purple-900/30 disabled:opacity-30';
    return 'border border-blue-500/50 text-blue-300 hover:bg-blue-900/30 disabled:opacity-30';
  }

  // Function to calculate remaining time for an active effect based on its expiration time
  timeLeft(until: string): string {
    const diff = new Date(until).getTime() - Date.now();
    if (diff <= 0) return 'expirado';
    const h = Math.floor(diff / 3_600_000);
    const m = Math.floor((diff % 3_600_000) / 60_000);
    return `${h}h ${m}m`;
  }
}
