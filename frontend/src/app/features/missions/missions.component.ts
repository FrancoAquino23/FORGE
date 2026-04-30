/* ==================================================================
   MISSIONS COMPONENT LOGIC
   ================================================================== */

import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ApiService, MissionListResponse, MissionProgress } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';

// Main missions component that displays active missions and allows claiming rewards
@Component({
  selector: 'app-missions',
  imports: [RouterLink],
  templateUrl: './missions.component.html',
  styleUrl: './missions.component.scss',
})
export class MissionsComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);
  private toast = inject(ToastService);

  data = signal<MissionListResponse | null>(null);
  loadError = signal('');
  claiming = signal('');

  private pollTimer: ReturnType<typeof setTimeout> | null = null;

  // Load component
  ngOnInit(): void {
    this.loadMissions();
  }

  // Cleanup on destroy
  ngOnDestroy(): void {
    this.clearPoll();
  }

  // Function to load active missions from API with polling if AI generation is not ready
  private loadMissions(): void {
    this.api.getActiveMissions().subscribe({
      next: (res) => {
        this.data.set(res);
        this.clearPoll();
        if (!res.ai_ready) {
          this.pollTimer = setTimeout(() => this.loadMissions(), 3000);
        }
      },
      error: () => this.loadError.set('No se pudieron cargar las misiones.'),
    });
  }

  // Function to claim a mission reward
  claim(mission: MissionProgress): void {
    if (this.claiming() || !mission.is_completable) return;
    this.claiming.set(mission.mission_id);

    this.api.claimMission(mission.mission_id).subscribe({
      next: (res) => {
        this.toast.fromMissionClaim(res);
        this.claiming.set('');
        this.loadMissions();
      },
      error: (err) => {
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Error',
          message: err.error?.detail ?? 'No se pudo completar la misión',
        });
        this.claiming.set('');
      },
    });
  }

  // Function to determine if a mission is pending (ready to claim but not yet claimed)
  isPending(m: MissionProgress): boolean {
    return m.status === 'PENDING';
  }

  // Function to calculate the progress percentage of a mission
  progressPct(m: MissionProgress): number {
    if (this.isPending(m)) return 100;
    if (!m.objective_target) return 0;
    return Math.min(100, (m.current_progress / m.objective_target) * 100);
  }

  // Function to calculate the time left until a mission expires
  timeLeft(expiresAt: string): string {
    const diff = new Date(expiresAt).getTime() - Date.now();
    if (diff <= 0) return 'expirada';
    const d = Math.floor(diff / 86_400_000);
    if (d >= 1) return `${d}d`;
    const h = Math.floor(diff / 3_600_000);
    const m = Math.floor((diff % 3_600_000) / 60_000);
    return `${h}h ${m}m`;
  }

  // Function to get a user-friendly label for a mission category
  categoryLabel(cat: string | null): string {
    const labels: Record<string, string> = {
      MAIN_QUEST: 'Main Quest',
      SIDE_QUEST: 'Side Quest',
      DAILY_GRIND: 'Daily Grind',
    };
    return cat ? (labels[cat] ?? cat) : '';
  }

  attrIcon(code: string): string {
    const icons: Record<string, string> = {
      S: '💪',
      P: '👁',
      E: '🛡',
      C: '💬',
      I: '🧠',
      A: '⚡',
      L: '🍀',
    };
    return icons[code] ?? '⚔';
  }

  // Function to get color class for an attribute based on its code
  private clearPoll(): void {
    if (this.pollTimer !== null) {
      clearTimeout(this.pollTimer);
      this.pollTimer = null;
    }
  }
}
