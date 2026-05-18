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
  attributes: AttributeProfile[];
}

// Interface (Checkpoint Info - Data)
export interface CheckpointInfo {
  id: string;
  description: string;
  is_completed: boolean;
  order_index: number;
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
  status: string;
  category: string | null;
  due_date: string | null;
  description: string | null;
  is_favorite: boolean;
  checkpoints: CheckpointInfo[];
  threat_level: 'MINOR' | 'MAJOR' | 'CRITICAL';
}

// Interface (Mission List Response - Data)
export interface MissionListResponse {
  missions: MissionProgress[];
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
  detail?: string;
  due_date?: string;
  steps?: string[];
  threat_level?: 'MINOR' | 'MAJOR' | 'CRITICAL';
}

// Interface (Toggle Checkpoint Response - Data)
export interface ToggleCheckpointResponse {
  checkpoint_id: string;
  is_completed: boolean;
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

// Interface (Checkpoint Update Item - Data)
export interface CheckpointUpdateItem {
  id: string | null;
  description: string;
  order_index: number;
}

// Interface (Update Mission Request - Data)
export interface UpdateMissionRequest {
  objective_description?: string;
  detail?: string;
  due_date?: string | null;
  checkpoints?: CheckpointUpdateItem[];
  threat_level?: 'MINOR' | 'MAJOR' | 'CRITICAL';
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
  material_balance: number;
}

// Interface (Relic Info - Data)
export interface RelicInfo {
  attribute_code: string;
  attribute_name: string;
  level: number;
  total_invested: number;
  bonus_pct: number;
  upgrade_cost: number | null;
  can_upgrade: boolean;
  material_balance: number;
  is_luck: boolean;
}

// Interface (Relic List Response - Data)
export interface RelicListResponse {
  relics: RelicInfo[];
}

// Interface (Relic Upgrade Response - Data)
export interface RelicUpgradeResponse {
  attribute_code: string;
  new_level: number;
  material_spent: number;
  new_balance: number;
  new_bonus_pct: number;
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

// Interface (Prestige Up Request - Data)
export interface PrestigeUpRequest {
  buff_type_code: string;
}

// Interface (Prestige Up Response - Data)
export interface PrestigeUpResponse {
  prestige_number: number;
  attributes_reset: string[];
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

  // Method (Delete Mission)
  deleteMission(missionId: string): Observable<void> {
    return this.http.delete<void>(`${this.BASE}/missions/${missionId}`);
  }

  // Method (Update Mission)
  updateMission(missionId: string, payload: UpdateMissionRequest): Observable<{ ok: boolean }> {
    return this.http.patch<{ ok: boolean }>(`${this.BASE}/missions/${missionId}`, payload);
  }

  // Method (Toggle Checkpoint)
  toggleCheckpoint(checkpointId: string): Observable<ToggleCheckpointResponse> {
    return this.http.patch<ToggleCheckpointResponse>(
      `${this.BASE}/missions/checkpoints/${checkpointId}/toggle`,
      {},
    );
  }

  // Method (Toggle Favorite)
  toggleFavorite(missionId: string): Observable<{ is_favorite: boolean }> {
    return this.http.post<{ is_favorite: boolean }>(
      `${this.BASE}/missions/${missionId}/favorite`,
      {},
    );
  }

  // Method (Get Relics)
  getRelics(): Observable<RelicListResponse> {
    return this.http.get<RelicListResponse>(`${this.BASE}/relics`);
  }

  // Method (Upgrade Relic)
  upgradeRelic(attribute_code: string): Observable<RelicUpgradeResponse> {
    return this.http.post<RelicUpgradeResponse>(
      `${this.BASE}/relics/${attribute_code}/upgrade`,
      {},
    );
  }

  // Method (Get Prestige Status)
  getPrestigeStatus(): Observable<PrestigeStatusResponse> {
    return this.http.get<PrestigeStatusResponse>(`${this.BASE}/prestige/status`);
  }

  // Method (Prestige Up)
  prestigeUp(payload: PrestigeUpRequest): Observable<PrestigeUpResponse> {
    return this.http.post<PrestigeUpResponse>(`${this.BASE}/prestige/prestige-up`, payload);
  }
}
