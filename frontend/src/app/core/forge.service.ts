/* ==================================================================
   FORGE - (FORGE SERVICE)
   ================================================================== */

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { TransmuteResponse } from './api.service';

// Service (Handles forge-specific backend calls)
@Injectable({ providedIn: 'root' })
export class ForgeService {
  private http = inject(HttpClient);
  private readonly BASE = 'http://localhost:8000';

  // Method (Burn equal quantities of ordinary materials to gain Stardust)
  transmute(batchSize: number): Observable<TransmuteResponse> {
    return this.http.post<TransmuteResponse>(`${this.BASE}/forge/transmute`, {
      batch_size: batchSize,
    });
  }
}
