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
  prestige_points_total: number;
  prestige_points_available: number;
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
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED';
  category: 'MAIN_QUEST' | 'SIDE_QUEST' | 'DAILY_GRIND' | null;
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
  category: 'MAIN_QUEST' | 'SIDE_QUEST' | 'DAILY_GRIND';
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

// Interface (Mission History Item - Data)
export interface MissionHistoryItem {
  mission_id: string;
  title: string;
  objective_description: string;
  attribute_code: string;
  attribute_name: string;
  category: 'MAIN_QUEST' | 'SIDE_QUEST' | 'DAILY_GRIND' | null;
  threat_level: 'MINOR' | 'MAJOR' | 'CRITICAL';
  reward_xp: number;
  reward_material_qty: number;
  completed_at: string;
}

// Interface (Mission History Response - Data)
export interface MissionHistoryResponse {
  missions: MissionHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
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

// Interface (Prestige Status Response - Data)
export interface PrestigeStatusResponse {
  prestige_count: number;
  threshold_level: number;
  material_cost: number;
  prestige_points_total: number;
  prestige_points_available: number;
}

// Interface (Prestige Up Response - Data)
export interface PrestigeUpResponse {
  prestige_number: number;
  attributes_reset: string[];
  pp_earned: number;
}

// Interface (Skill Node Info - Data)
export interface SkillNodeInfo {
  node_id: string;
  path: string;
  display_name: string;
  description: string;
  current_level: number;
  max_level: number;
  cost_to_upgrade: number | null;
  bonus_at_current: number;
  bonus_at_next: number | null;
  current_effect: string;
  next_effect: string | null;
}

// Interface (Skill Tree Response - Data)
export interface SkillTreeResponse {
  nodes: SkillNodeInfo[];
  pp_total: number;
  pp_available: number;
}

// Interface (Upgrade Node Request - Data)
export interface UpgradeNodeRequest {
  node_id: string;
}

// Interface (Upgrade Node Response - Data)
export interface UpgradeNodeResponse {
  node_id: string;
  new_level: number;
  pp_spent: number;
  pp_available: number;
}

// Interface (Reset Tree Response - Data)
export interface ResetTreeResponse {
  pp_refunded: number;
  pp_available: number;
}

// Interface (Transmute Response - Data)
export interface TransmuteResponse {
  batch_size: number;
  materials_consumed_each: number;
  stardust_gained: number;
  new_stardust_balance: number;
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

  // Method (Get Mission History)
  getMissionHistory(page: number = 1, pageSize: number = 10): Observable<MissionHistoryResponse> {
    return this.http.get<MissionHistoryResponse>(
      `${this.BASE}/missions/history?page=${page}&page_size=${pageSize}`,
    );
  }

  // Method (Deploy Mission)
  deployMission(payload: DeployMissionRequest): Observable<DeployMissionResponse> {
    return this.http.post<DeployMissionResponse>(`${this.BASE}/missions/deploy`, payload);
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
  prestigeUp(): Observable<PrestigeUpResponse> {
    return this.http.post<PrestigeUpResponse>(`${this.BASE}/prestige/prestige-up`, {});
  }

  // Method (Get Skill Tree)
  getSkillTree(): Observable<SkillTreeResponse> {
    return this.http.get<SkillTreeResponse>(`${this.BASE}/prestige/tree`);
  }

  // Method (Upgrade Skill Node)
  upgradeNode(node_id: string): Observable<UpgradeNodeResponse> {
    return this.http.post<UpgradeNodeResponse>(`${this.BASE}/prestige/tree/upgrade`, { node_id });
  }

  // Method (Reset Skill Tree)
  resetSkillTree(): Observable<ResetTreeResponse> {
    return this.http.post<ResetTreeResponse>(`${this.BASE}/prestige/tree/reset`, {});
  }
}
