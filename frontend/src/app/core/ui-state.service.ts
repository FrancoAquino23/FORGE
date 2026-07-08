/* ==================================================================
   FORGE - (UI STATE SERVICE)
   ================================================================== */

import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class UiStateService {
  profileOpen = signal(false);
}
