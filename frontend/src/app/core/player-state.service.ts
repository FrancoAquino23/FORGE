/* ==================================================================
   PLAYER STATE SERVICE
   ================================================================== */

import { Injectable, inject, signal } from '@angular/core';
import { ApiService, PlayerProfile } from './api.service';

@Injectable({ providedIn: 'root' })
export class PlayerStateService {
  private api = inject(ApiService);

  // Prestige count (Updated by the prestige component after load or prestige-up)
  readonly prestigeCount = signal(0);
  // Shared player profile (Udated by dashboard/missions on load/claim)
  readonly profile = signal<PlayerProfile | null>(null);

  // Load profile update the shared profile signal
  loadProfile(): void {
    this.api.getProfile().subscribe({ next: (p) => this.profile.set(p) });
  }
}
