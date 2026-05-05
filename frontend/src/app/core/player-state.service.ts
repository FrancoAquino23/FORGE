/* ==================================================================
   PLAYER STATE SERVICE
   ================================================================== */

import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class PlayerStateService {
  // Prestige count (Updated by the prestige component after load or sacrifice)
  readonly prestigeCount = signal(0);
}
