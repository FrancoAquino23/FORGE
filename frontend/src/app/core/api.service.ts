/* ==================================================================
   FORGE - (API SERVICE)
   ================================================================== */

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Interface (Attribute Profile - Data)
export interface AttributeProfile {
  code: string;
  name: string;
  level: number;
  xp_current: number;
  xp_to_next: number;
  material_name: string;
  material_balance: number;
}

// Interface (Player Profile - Data)
export interface PlayerProfile {
  username: string;
  prestige_count: number;
  streak_current: number;
  streak_max: number;
  attributes: AttributeProfile[];
}

// Interfaces (Missions - Data)
export interface MissionProgress {
  mission_id: string;
  title: string;
  objective_description: string;
  objective_type: string;
  objective_target: number;
  current_progress: number;
  attribute_code: string;
  attribute_name: string;
  reward_xp: number;
  reward_material_qty: number;
  expires_at: string;
  is_completable: boolean;
  ai_generated: boolean;
  status: string;
  category: string | null;
}

// Interface (Mission List Response - Data)
export interface MissionListResponse {
  missions: MissionProgress[];
  ai_ready: boolean;
}

// Interface (Mission Claim Response - Data)
export interface MissionClaimResponse {
  mission_id: string;
  attribute_code: string;
  material_name: string;
  xp_earned: number;
  material_earned: number;
  new_attribute_level: number;
  leveled_up: boolean;
}

// Interface (Deploy Mission Request - Data)
export interface DeployMissionRequest {
  attribute_code: string;
  category: 'MAIN_QUEST' | 'SIDE_QUEST' | 'DAILY_GRIND';
  description?: string;
}

// Interface (Deploy Mission Response - Data)
export interface DeployMissionResponse {
  mission_id: string;
  title: string;
  category: string;
  attribute_code: string;
  reward_xp: number;
  reward_material_qty: number;
}

// Interface (Activity Log Request - Data)
export interface ActivityLogRequest {
  attribute_code: string;
  description?: string;
}

// Interface (Activity Log Response - Data)
export interface ActivityLogResponse {
  activity_id: string;
  attribute_code: string;
  material_name: string;
  xp_earned: number;
  material_earned: number;
  new_attribute_level: number;
  new_attribute_xp: number;
  xp_to_next_level: number;
  level_up: { occurred: boolean; new_level: number };
  streak_current: number;
  streak_broken: boolean;
  streak_shield_used: boolean;
  material_balance: number;
  overcharge_was_active: boolean;
  dropped_consumable: string | null;
}

// Interface (Consumable Item - Data)
export interface ConsumableItem {
  consumable_code: string;
  name: string;
  description: string | null;
  effect_type: string;
  quantity: number;
  is_active: boolean;
  active_until: string | null;
}

// Interface (Inventory Response - Data)
export interface InventoryResponse {
  items: ConsumableItem[];
}

// Interface (Use Consumable Response - Data)
export interface UseConsumableResponse {
  consumable_code: string;
  name: string;
  effect_type: string;
  quantity_remaining: number;
  active_until: string | null;
  message: string;
}

// Interface (Buff Type Info - Data)
export interface BuffTypeInfo {
  code: string;
  display_name: string;
  target_type: string;
  bonus_percent: number;
  attribute_code: string | null;
}

// Interface (Player Buff Info - Data)
export interface PlayerBuffInfo {
  buff_type_code: string;
  display_name: string;
  target_type: string;
  stack_count: number;
  total_bonus: number;
}

// Interface (Prestige Status Response - Data)
export interface PrestigeStatusResponse {
  prestige_count: number;
  threshold_level: number;
  active_buffs: PlayerBuffInfo[];
  available_buff_types: BuffTypeInfo[];
}

// Interface (Prestige Sacrifice Request - Data)
export interface PrestigeSacrificeRequest {
  attribute_code: string;
  buff_type_code: string;
}

// Interface (Prestige Sacrifice Response - Data)
export interface PrestigeSacrificeResponse {
  prestige_number: number;
  attribute_reset_code: string;
  level_before: number;
  buff_type_code: string;
  buff_display_name: string;
  new_stack_count: number;
  new_total_bonus: number;
}

// Service (API Service - Data)
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly BASE = 'http://localhost:8000';
  private http = inject(HttpClient);

  // Method (Get Player Profile)
  getProfile(): Observable<PlayerProfile> {
    return this.http.get<PlayerProfile>(`${this.BASE}/player/profile`);
  }

  // Method (Get Active Missions)
  getActiveMissions(): Observable<MissionListResponse> {
    return this.http.get<MissionListResponse>(`${this.BASE}/missions/active`);
  }

  // Method (Deploy Mission)
  deployMission(payload: DeployMissionRequest): Observable<DeployMissionResponse> {
    return this.http.post<DeployMissionResponse>(`${this.BASE}/missions/deploy`, payload);
  }

  // Method (Log Activity)
  logActivity(payload: ActivityLogRequest): Observable<ActivityLogResponse> {
    return this.http.post<ActivityLogResponse>(`${this.BASE}/activities/log`, payload);
  }

  // Method (Claim Mission)
  claimMission(missionId: string): Observable<MissionClaimResponse> {
    return this.http.post<MissionClaimResponse>(`${this.BASE}/missions/${missionId}/claim`, {});
  }

  // Method (Get Inventory)
  getInventory(): Observable<InventoryResponse> {
    return this.http.get<InventoryResponse>(`${this.BASE}/consumables/inventory`);
  }

  // Method (Use Consumable)
  useConsumable(consumable_code: string): Observable<UseConsumableResponse> {
    return this.http.post<UseConsumableResponse>(`${this.BASE}/consumables/use`, {
      consumable_code,
    });
  }

  // Method (Get Prestige Status)
  getPrestigeStatus(): Observable<PrestigeStatusResponse> {
    return this.http.get<PrestigeStatusResponse>(`${this.BASE}/prestige/status`);
  }

  // Method (Perform Prestige Sacrifice)
  sacrifice(payload: PrestigeSacrificeRequest): Observable<PrestigeSacrificeResponse> {
    return this.http.post<PrestigeSacrificeResponse>(`${this.BASE}/prestige/sacrifice`, payload);
  }
}
