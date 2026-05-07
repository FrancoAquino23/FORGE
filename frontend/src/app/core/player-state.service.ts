/* ==================================================================
   PLAYER STATE SERVICE
   ================================================================== */

import { Injectable, signal } from '@angular/core';
import { PlayerProfile } from './api.service';

@Injectable({ providedIn: 'root' })
export class PlayerStateService {
  // Prestige count (Updated by the prestige component after load or sacrifice)
  readonly prestigeCount = signal(0);
  // Shared player profile (Udated by dashboard/missions on load/claim)
  readonly profile = signal<PlayerProfile | null>(null);
}
