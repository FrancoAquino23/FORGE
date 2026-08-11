/* ==================================================================
   DASHBOARD COMPONENT LOGIC
   ================================================================== */

import { Component, DestroyRef, OnInit, inject, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import {
  phosphorSwordBold,
  phosphorEyeBold,
  phosphorShieldBold,
  phosphorSketchLogoBold,
  phosphorDnaBold,
  phosphorLightningBold,
  phosphorSparkleBold,
  phosphorWarningBold,
  phosphorFlaskBold,
  phosphorNutBold,
  phosphorSpinnerBold,
  phosphorPlugsBold,
  phosphorCaretCircleLeftBold,
  phosphorCaretCircleRightBold,
} from '@ng-icons/phosphor-icons/bold';
import {
  ApiService,
  AttributeProfile,
  MissionProgress,
  PlayerProfile,
} from '../../core/api.service';
import { MetricsComponent } from '../metrics/metrics.component';
import {
  ATTR_HEX,
  fmt,
  attrColor,
  attrIcon,
  threatBarColor,
  threatTextClass,
  formatDueDate,
  isDueSoon,
  dueDateLabel,
} from '../../shared/ui-constants';

// Main dashboard component
@Component({
  selector: 'app-dashboard',
  imports: [MetricsComponent, NgIconComponent],
  providers: [
    provideIcons({
      phosphorSwordBold,
      phosphorEyeBold,
      phosphorShieldBold,
      phosphorSketchLogoBold,
      phosphorDnaBold,
      phosphorLightningBold,
      phosphorSparkleBold,
      phosphorWarningBold,
      phosphorFlaskBold,
      phosphorNutBold,
      phosphorSpinnerBold,
      phosphorPlugsBold,
      phosphorCaretCircleLeftBold,
      phosphorCaretCircleRightBold,
    }),
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);
  private destroyRef = inject(DestroyRef);

  profile = signal<PlayerProfile | null>(null);
  missions = signal<MissionProgress[]>([]);
  loadError = signal(false);

  readonly threshold = computed(() => this.profile()?.threshold_level ?? 10);

  missionsPage = signal(0);
  readonly MISSIONS_PER_PAGE = 3;

  // All active missions sorted by priority:
  urgentMissions = computed<MissionProgress[]>(() => {
    const all = this.missions().filter((m) => m.status !== 'DRAFT');
    const threatOrder: Record<string, number> = { CRITICAL: 0, MAJOR: 1, MINOR: 2 };
    return [...all].sort((a, b) => {
      const aIsDaily = a.category === 'DAILY_GRIND';
      const bIsDaily = b.category === 'DAILY_GRIND';
      if (aIsDaily && !bIsDaily) return 1;
      if (!aIsDaily && bIsDaily) return -1;
      const aDay = a.due_date ? new Date(a.due_date).getTime() : Infinity;
      const bDay = b.due_date ? new Date(b.due_date).getTime() : Infinity;
      if (aDay !== bDay) return aDay - bDay;
      return (threatOrder[a.threat_level] ?? 1) - (threatOrder[b.threat_level] ?? 1);
    });
  });

  pagedMissions = computed<MissionProgress[]>(() => {
    const start = this.missionsPage() * this.MISSIONS_PER_PAGE;
    return this.urgentMissions().slice(start, start + this.MISSIONS_PER_PAGE);
  });

  missionsTotalPages = computed(() =>
    Math.ceil(this.urgentMissions().length / this.MISSIONS_PER_PAGE),
  );

  // Previous page navigation for active missions
  prevMissionsPage(): void {
    if (this.missionsPage() > 0) this.missionsPage.update((p) => p - 1);
  }

  // Next page navigation for active missions
  nextMissionsPage(): void {
    if (this.missionsPage() < this.missionsTotalPages() - 1) this.missionsPage.update((p) => p + 1);
  }

  // Load component
  ngOnInit(): void {
    this.loadProfile();
    this.loadMissions();
  }

  // Load player profile from API
  private loadProfile(): void {
    this.api
      .getProfile()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (p) => this.profile.set(p),
        error: () => this.loadError.set(true),
      });
  }

  // Load active missions from API
  private loadMissions(): void {
    this.api
      .getActiveMissions()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => this.missions.set(res.missions),
        error: () => {},
      });
  }

  // Function to determine glow effect for attribute bars based on level
  attrMaxGlow(attr: AttributeProfile): string {
    if (attr.level < this.threshold()) return 'none';
    const color = this.xpBarColor(attr.code);
    return `0 0 5px ${color}99, 0 0 12px ${color}33`;
  }

  // XP progress of the lowest ordinary attribute (Drives Luck sync bar)
  private luckSyncPct(): number {
    const attrs = this.profile()?.attributes ?? [];
    const ordinary = attrs.filter((a) => a.code !== 'L');
    if (!ordinary.length) return 0;
    const lowest = ordinary.reduce((min, a) => {
      if (a.level < min.level) return a;
      if (a.level === min.level && a.xp_current < min.xp_current) return a;
      return min;
    });
    return lowest.xp_to_next > 0
      ? Math.min(100, (lowest.xp_current / lowest.xp_to_next) * 100)
      : 100;
  }

  // Function to calculate XP percentage for progress bars
  xpPct(attr: AttributeProfile): number {
    if (attr.level >= this.threshold()) return 100;
    if (attr.code === 'L') return this.luckSyncPct();
    return attr.xp_to_next > 0 ? Math.min(100, (attr.xp_current / attr.xp_to_next) * 100) : 0;
  }

  // Function to get color class for an attribute based on its code
  xpBarColor(code: string): string {
    return ATTR_HEX[code] ?? '#f59e0b';
  }

  // Constants & utility functions
  protected attrColor = attrColor;
  protected attrIcon = attrIcon;
  protected threatBarColor = threatBarColor;
  protected threatTextClass = threatTextClass;
  protected fmt = fmt;
  protected formatDueDate = formatDueDate;
  protected isDueSoon = isDueSoon;
  protected dueDateLabel = dueDateLabel;

  // Mission helper (Checkpoint completion count)
  completedCount(m: MissionProgress): number {
    return m.checkpoints.filter((c) => c.is_completed).length;
  }

  // Mission helper (Checkpoint completion percentage)
  checkpointPct(m: MissionProgress): number {
    if (!m.checkpoints.length) return 0;
    return Math.round((this.completedCount(m) / m.checkpoints.length) * 100);
  }
}
