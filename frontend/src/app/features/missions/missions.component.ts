/* ==================================================================
   MISSIONS COMPONENT LOGIC
   ================================================================== */

import { Component, HostListener, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule, LucideIconData, Star, EllipsisVertical } from 'lucide-angular';
import {
  ApiService,
  CheckpointInfo,
  CheckpointUpdateItem,
  DeployMissionRequest,
  MissionHistoryItem,
  MissionListResponse,
  MissionProgress,
  UpdateMissionRequest,
} from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { PlayerStateService } from '../../core/player-state.service';
import { DatePickerComponent } from '../../shared/date-picker/date-picker.component';

import { ATTR_COLORS, ATTR_HEX, ATTR_ICONS, RELIC_NAMES } from '../../shared/attr-constants';

export type MissionTab = 'NEW_MISSION' | 'DAILY_GRIND' | 'MAIN_QUEST' | 'SIDE_QUEST' | 'HISTORY';

const CATEGORY_LABELS: Record<string, string> = {
  MAIN_QUEST: 'Main Quest',
  SIDE_QUEST: 'Side Quest',
  DAILY_GRIND: 'Daily Grind',
};

// Threat level maps
const THREAT_TEXT: Record<string, string> = {
  MINOR: 'text-sky-400',
  MAJOR: 'text-amber-400',
  CRITICAL: 'text-rose-500',
};

// MINOR/MAJOR/CRITICAL glow
const THREAT_GLOW: Record<string, string> = {
  MINOR: 'hover:shadow-[0_0_18px_rgba(56,189,248,0.22)]',
  MAJOR: 'hover:shadow-[0_0_18px_rgba(251,191,36,0.22)]',
  CRITICAL: 'shadow-[0_0_22px_rgba(244,63,94,0.32)]',
};

const THREAT_BORDER: Record<string, string> = {
  MINOR: 'border-sky-500/35',
  MAJOR: 'border-amber-500/40',
  CRITICAL: 'border-rose-500/50',
};

const THREAT_FAV_BG: Record<string, string> = {
  MINOR: 'bg-sky-950/30',
  MAJOR: 'bg-amber-950/30',
  CRITICAL: 'bg-rose-950/30',
};

// Hex values for progress bar fill
const THREAT_BAR: Record<string, string> = {
  MINOR: '#38bdf8',
  MAJOR: '#fbbf24',
  CRITICAL: '#f43f5e',
};

// Category labels for mission deployment toast
const _DEPLOY_CAT_LABEL: Record<string, string> = {
  MAIN_QUEST: 'Main Quest',
  SIDE_QUEST: 'Side Quest',
  DAILY_GRIND: 'Daily Grind',
};

@Component({
  selector: 'app-missions',
  imports: [LucideAngularModule, FormsModule, DatePickerComponent],
  templateUrl: './missions.component.html',
  styleUrl: './missions.component.scss',
})
export class MissionsComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private playerState = inject(PlayerStateService);

  data = signal<MissionListResponse | null>(null);
  historyData = signal<MissionHistoryItem[]>([]);
  historyLoaded = signal(false);
  historyPage = signal(1);
  historyTotalPages = signal(1);
  historyTotal = signal(0);
  loadError = signal('');
  claiming = signal('');
  activeTab = signal<MissionTab>('MAIN_QUEST');
  attrFilter = signal('');
  threatFilter = signal('');
  sortByDate = signal(false);

  private expandedSet = signal(new Set<string>());
  hoverCardId = signal('');
  menuOpenId = signal('');
  editingId = signal('');
  savingEdit = signal(false);
  deleteConfirmId = signal('');
  editForm: {
    objective: string;
    detail: string;
    due_date: string;
    category: string;
    threat_level: string;
    checkpoints: Array<{ id: string | null; description: string }>;
  } = {
    objective: '',
    detail: '',
    due_date: '',
    category: '',
    threat_level: 'MAJOR',
    checkpoints: [],
  };

  deploying = signal(false);
  logAttr = '';
  logCategory: 'MAIN_QUEST' | 'SIDE_QUEST' | 'DAILY_GRIND' = 'DAILY_GRIND';
  logThreatLevel: 'MINOR' | 'MAJOR' | 'CRITICAL' = 'MAJOR';
  logDesc = '';
  logDetail = '';
  logDueDate = '';
  logSteps = '';
  attrDropdownOpen = false;

  readonly todayStr = new Date().toISOString().split('T')[0];

  // Lucide icon references for use in template
  readonly starIcon: LucideIconData = Star;
  readonly moreVerticalIcon: LucideIconData = EllipsisVertical;

  // Tab definitions for template iteration
  readonly TABS: { value: MissionTab; label: string }[] = [
    { value: 'NEW_MISSION', label: 'New Mission' },
    { value: 'MAIN_QUEST', label: 'Main Quests' },
    { value: 'SIDE_QUEST', label: 'Side Quests' },
    { value: 'DAILY_GRIND', label: 'Daily Grinds' },
    { value: 'HISTORY', label: 'History' },
  ];

  // Attribute codes for filter buttons
  readonly ATTRS = ['S', 'P', 'E', 'C', 'I', 'A', 'L'];

  // Category options for new mission forms
  readonly CATEGORIES = [
    { value: 'MAIN_QUEST' as const, label: 'Main Quest' },
    { value: 'SIDE_QUEST' as const, label: 'Side Quest' },
    { value: 'DAILY_GRIND' as const, label: 'Daily Grind' },
  ];

  // Threat level options for new mission forms
  readonly THREAT_LEVELS: { value: string; label: string }[] = [
    { value: 'MINOR', label: 'Minor' },
    { value: 'MAJOR', label: 'Major' },
    { value: 'CRITICAL', label: 'Critical' },
  ];

  // Threat level options for mission edit forms
  readonly DEPLOY_THREAT_LEVELS: {
    value: 'MINOR' | 'MAJOR' | 'CRITICAL';
    label: string;
    color: string;
  }[] = [
    { value: 'MINOR', label: 'Minor', color: 'text-cyan-400' },
    { value: 'MAJOR', label: 'Major', color: 'text-amber-400' },
    { value: 'CRITICAL', label: 'Critical', color: 'text-red-400' },
  ];

  // Derived list of missions filtered by active tab and attribute selector
  readonly filteredMissions = computed<MissionProgress[]>(() => {
    const all = this.data()?.missions ?? [];
    const tab = this.activeTab();
    const attr = this.attrFilter();
    const threat = this.threatFilter();
    const sortDate = this.sortByDate();

    if (tab === 'NEW_MISSION' || tab === 'HISTORY') return [];

    let subset: MissionProgress[];
    switch (tab) {
      case 'MAIN_QUEST':
        subset = all.filter((m) => m.status === 'PENDING' && m.category === 'MAIN_QUEST');
        break;
      case 'SIDE_QUEST':
        subset = all.filter((m) => m.status === 'PENDING' && m.category === 'SIDE_QUEST');
        break;
      default:
        subset = all.filter(
          (m) => (m.status === 'PENDING' && m.category === 'DAILY_GRIND') || m.status === 'ACTIVE',
        );
    }

    if (attr) subset = subset.filter((m) => m.attribute_code === attr);
    if (threat) subset = subset.filter((m) => m.threat_level === threat);

    if (sortDate) {
      subset = [...subset].sort((a, b) => {
        if (!a.due_date && !b.due_date) return 0;
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
      });
    }

    return subset;
  });

  // Load component
  ngOnInit(): void {
    this.loadMissions();
    if (!this.playerState.profile()) {
      this.api.getProfile().subscribe({ next: (p) => this.playerState.profile.set(p) });
    }
  }

  // Close open overflow menu when clicking anywhere outside it
  @HostListener('document:click')
  onDocumentClick(): void {
    this.menuOpenId.set('');
    this.attrDropdownOpen = false;
  }

  // Function to load active missions from API
  private loadMissions(): void {
    this.api.getActiveMissions().subscribe({
      next: (res) => this.data.set(res),
      error: () => this.loadError.set('Could not load missions.'),
    });
  }

  // Function to load mission history for the given page
  private loadHistory(page: number = 1): void {
    this.historyLoaded.set(false);
    this.api.getMissionHistory(page).subscribe({
      next: (res) => {
        this.historyData.set(res.missions);
        this.historyPage.set(res.page);
        this.historyTotalPages.set(res.total_pages);
        this.historyTotal.set(res.total);
        this.historyLoaded.set(true);
      },
      error: () => this.loadError.set('Could not load history.'),
    });
  }

  // Navigate to previous history page
  historyPrev(): void {
    if (this.historyPage() > 1) this.loadHistory(this.historyPage() - 1);
  }

  // Navigate to next history page
  historyNext(): void {
    if (this.historyPage() < this.historyTotalPages()) this.loadHistory(this.historyPage() + 1);
  }

  // Toggle attribute dropdown
  toggleAttrDropdown(event: MouseEvent): void {
    event.stopPropagation();
    this.attrDropdownOpen = !this.attrDropdownOpen;
  }

  // Select attribute
  selectAttr(code: string): void {
    this.logAttr = code;
    this.attrDropdownOpen = false;
  }

  // Get attribute display name
  getAttrName(code: string): string {
    return this.playerState.profile()?.attributes.find((a) => a.code === code)?.name ?? code;
  }

  // Deploy a mission
  deployMission(): void {
    if (!this.logAttr || !this.logDesc.trim() || this.deploying()) return;
    this.deploying.set(true);

    const steps = this.logSteps
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    const payload: DeployMissionRequest = {
      attribute_code: this.logAttr,
      category: this.logCategory,
      threat_level: this.logThreatLevel,
      description: this.logDesc.trim(),
      detail: this.logDetail.trim() || undefined,
      due_date: this.logDueDate || undefined,
      steps: steps.length > 0 ? steps : undefined,
    };

    this.api.deployMission(payload).subscribe({
      next: (res) => {
        const catLabel = _DEPLOY_CAT_LABEL[res.category] ?? res.category;
        this.toast.show({
          type: 'claim',
          icon: '⚔',
          title: 'Mission Forged',
          message: `${catLabel} mission forged!`,
        });
        this.deploying.set(false);
        this.logAttr = '';
        this.logDesc = '';
        this.logDetail = '';
        this.logDueDate = '';
        this.logSteps = '';
        this.logCategory = 'DAILY_GRIND';
        this.logThreatLevel = 'MAJOR';
        this.loadMissions();
      },
      error: (err) => {
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Error',
          message: err.error?.detail ?? 'Could not dispatch mission',
        });
        this.deploying.set(false);
      },
    });
  }

  // Format "completed_at date"
  formatCompletedAt(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }

  // Function to compute progress percentage from checkpoints
  checkpointProgressPct(m: MissionProgress): number {
    if (m.checkpoints && m.checkpoints.length > 0) {
      const done = m.checkpoints.filter((c) => c.is_completed).length;
      return Math.round((done / m.checkpoints.length) * 100);
    }
    return this.progressPct(m);
  }

  // Function to return a "X/Y steps" summary string when a mission has checkpoints
  checkpointSummary(m: MissionProgress): string {
    if (!m.checkpoints || m.checkpoints.length === 0) return '';
    const done = m.checkpoints.filter((c) => c.is_completed).length;
    return `${done}/${m.checkpoints.length} steps`;
  }

  // Function that returns true when the mission can be finished/claimed
  canFinish(m: MissionProgress): boolean {
    if (m.checkpoints && m.checkpoints.length > 0) {
      return m.checkpoints.every((c) => c.is_completed);
    }
    return m.is_completable;
  }

  // Function to optimistically toggle a checkpoint
  toggleCheckpoint(m: MissionProgress, cp: CheckpointInfo): void {
    const updated = m.checkpoints.map((c) =>
      c.id === cp.id ? { ...c, is_completed: !c.is_completed } : c,
    );
    this.data.update((d) =>
      d
        ? {
            ...d,
            missions: d.missions.map((mission) =>
              mission.mission_id === m.mission_id ? { ...mission, checkpoints: updated } : mission,
            ),
          }
        : null,
    );

    this.api.toggleCheckpoint(cp.id).subscribe({
      error: () => {
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Error',
          message: 'Could not update checkpoint',
        });
        this.loadMissions();
      },
    });
  }

  // Function to claim a mission reward
  claim(mission: MissionProgress): void {
    if (this.claiming() || !this.canFinish(mission)) return;
    this.claiming.set(mission.mission_id);

    this.api.claimMission(mission.mission_id).subscribe({
      next: (res) => {
        this.toast.fromMissionClaim(res);
        if (res.newly_unlocked?.length) this.toast.fromAchievements(res.newly_unlocked);
        this.claiming.set('');
        this.loadMissions();
        this.api.getProfile().subscribe({ next: (p) => this.playerState.profile.set(p) });
      },
      error: (err) => {
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Error',
          message: err.error?.detail ?? 'Could not complete mission',
        });
        this.claiming.set('');
      },
    });
  }

  // Function to enter delete confirmation state for a mission card
  requestDeleteConfirm(m: MissionProgress): void {
    this.deleteConfirmId.set(m.mission_id);
  }

  // Function to confirm and execute mission deletion
  confirmDelete(m: MissionProgress): void {
    this.deleteConfirmId.set('');
    this.menuOpenId.set('');
    this.api.deleteMission(m.mission_id).subscribe({
      next: () => {
        this.toast.show({
          type: 'error',
          icon: '🗑',
          title: 'Mission Terminated',
          message: 'Mission terminated!',
        });
        this.loadMissions();
      },
      error: (err) => {
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Error',
          message: err.error?.detail ?? 'Could not delete mission',
        });
      },
    });
  }

  // Function to enter edit mode for a mission card
  startEdit(m: MissionProgress): void {
    this.menuOpenId.set('');
    this.editingId.set(m.mission_id);
    this.editForm = {
      objective: m.objective_description,
      detail: m.description ?? '',
      due_date: m.due_date ? m.due_date.substring(0, 10) : '',
      category: m.category ?? '',
      threat_level: m.threat_level ?? 'MAJOR',
      checkpoints: m.checkpoints.map((cp) => ({ id: cp.id, description: cp.description })),
    };
  }

  // Function to cancel inline edit without saving
  cancelEdit(): void {
    this.editingId.set('');
  }

  // Function to add a blank checkpoint row to the edit form
  addEditCheckpoint(): void {
    this.editForm.checkpoints.push({ id: null, description: '' });
  }

  // Function to remove a checkpoint row from the edit form by index
  removeEditCheckpoint(index: number): void {
    this.editForm.checkpoints.splice(index, 1);
  }

  // Function to save inline edit changes to the API and reload
  saveEdit(): void {
    if (this.savingEdit()) return;
    this.savingEdit.set(true);

    const checkpoints: CheckpointUpdateItem[] = this.editForm.checkpoints
      .filter((cp) => cp.description.trim())
      .map((cp, idx) => ({ id: cp.id, description: cp.description.trim(), order_index: idx }));

    const payload: UpdateMissionRequest = {
      objective_description: this.editForm.objective || undefined,
      detail: this.editForm.detail,
      due_date: this.editForm.due_date || null,
      threat_level: this.editForm.threat_level as 'MINOR' | 'MAJOR' | 'CRITICAL',
      checkpoints: this.editForm.category !== 'DAILY_GRIND' ? checkpoints : undefined,
    };
    this.api.updateMission(this.editingId(), payload).subscribe({
      next: () => {
        this.savingEdit.set(false);
        this.editingId.set('');
        this.loadMissions();
      },
      error: (err) => {
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Error',
          message: err.error?.detail ?? 'Could not save mission',
        });
        this.savingEdit.set(false);
      },
    });
  }

  // Function to toggle is_favorite on a daily mission; optimistically updates local data
  toggleFavorite(m: MissionProgress): void {
    this.api.toggleFavorite(m.mission_id).subscribe({
      next: (res) => {
        const current = this.data();
        if (current) {
          this.data.set({
            ...current,
            missions: current.missions.map((mission) =>
              mission.mission_id === m.mission_id
                ? { ...mission, is_favorite: res.is_favorite }
                : mission,
            ),
          });
        }
        if (res.is_favorite) {
          this.toast.show({
            type: 'claim',
            icon: '🔥',
            title: 'STREAK UNLOCKED',
            message: 'Rewards grow the longer your streak holds',
          });
        }
      },
      error: () => {
        this.toast.show({
          type: 'error',
          icon: '❌',
          title: 'Error',
          message: 'Could not update favorite',
        });
      },
    });
  }

  // Function to return streak multiplier label for a daily mission
  streakMultLabel(streak: number): string {
    if (streak >= 14) return '×2.0';
    if (streak >= 7) return '×1.6';
    if (streak >= 3) return '×1.3';
    return '×1.0';
  }

  // Function to toggle description expand/collapse for a card
  toggleExpand(id: string): void {
    const s = new Set(this.expandedSet());
    s.has(id) ? s.delete(id) : s.add(id);
    this.expandedSet.set(s);
  }

  // Function to return true when the description of a card is expanded
  isExpanded(id: string): boolean {
    return this.expandedSet().has(id);
  }

  // Function to toggle the overflow menu for a card; stops event bubbling to prevent immediate close
  toggleMenu(id: string, event: MouseEvent): void {
    event.stopPropagation();
    this.menuOpenId.set(this.menuOpenId() === id ? '' : id);
  }

  // Function to keep the overflow menu open when the user interacts with it
  stopPropagation(event: MouseEvent): void {
    event.stopPropagation();
  }

  // Function to switch the active tab and resets the attribute filter
  selectTab(tab: MissionTab): void {
    this.activeTab.set(tab);
    this.attrFilter.set('');
    this.threatFilter.set('');
    this.sortByDate.set(false);
    this.menuOpenId.set('');
    this.editingId.set('');
    this.deleteConfirmId.set('');
    if (tab === 'HISTORY' && !this.historyLoaded()) {
      this.loadHistory(1);
    }
  }

  // Function to return the number of missions visible in a given tab
  tabCount(tab: MissionTab): number {
    if (tab === 'NEW_MISSION') return 0;
    if (tab === 'HISTORY') return this.historyTotal();
    const all = this.data()?.missions ?? [];
    switch (tab) {
      case 'MAIN_QUEST':
        return all.filter((m) => m.status === 'PENDING' && m.category === 'MAIN_QUEST').length;
      case 'SIDE_QUEST':
        return all.filter((m) => m.status === 'PENDING' && m.category === 'SIDE_QUEST').length;
      default:
        return all.filter(
          (m) => (m.status === 'PENDING' && m.category === 'DAILY_GRIND') || m.status === 'ACTIVE',
        ).length;
    }
  }

  // Function to return true when the mission is player-dispatched (PENDING, awaiting manual completion)
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
    if (diff <= 0) return 'Expired';
    const d = Math.floor(diff / 86_400_000);
    if (d >= 1) return `${d}d`;
    const h = Math.floor(diff / 3_600_000);
    const m = Math.floor((diff % 3_600_000) / 60_000);
    return `${h}h ${m}m`;
  }

  // Function to map an attribute code to its relic display name
  relicName(code: string): string {
    return RELIC_NAMES[code] ?? code;
  }

  // Function to map an attribute code to its color class
  attrColor(code: string): string {
    return ATTR_COLORS[code] ?? 'text-forge-primary';
  }

  // Function to map an attribute code to its hex color
  attrBarColor(code: string): string {
    return ATTR_HEX[code] ?? '#f59e0b';
  }

  // Function to map a threat level to its hex color
  threatBarColor(level: string): string {
    return THREAT_BAR[level] ?? '#fbbf24';
  }

  // Function to map an attribute code to its icon
  getIcon(code: string): LucideIconData {
    return ATTR_ICONS[code] ?? ATTR_ICONS['L'];
  }

  // Function for building the border and hover-glow CSS for a mission card
  cardClass(m: MissionProgress): string {
    const level = m.threat_level ?? 'MAJOR';
    const border = THREAT_BORDER[level] ?? 'border-forge-border';
    const glow = THREAT_GLOW[level] ?? '';
    if (m.is_favorite) {
      const bg = THREAT_FAV_BG[level] ?? '';
      return `${border} ${glow} ${bg}`;
    }
    return `${border} ${glow}`;
  }

  // Function to map a threat level to its text color class
  threatTextClass(level: string): string {
    return THREAT_TEXT[level] ?? 'text-forge-muted';
  }

  // Function to build the active/inactive filter toggle button
  filterBtnClass(code: string): string {
    return this.attrFilter() === code
      ? `${this.attrColor(code)} border-current bg-forge-surface`
      : 'text-forge-muted border-forge-border/40 hover:text-forge-text hover:border-forge-border';
  }

  // Function to build the active/inactive filter button class for threat level filters
  threatBtnClass(level: string): string {
    return this.threatFilter() === level
      ? `${this.threatTextClass(level)} border-current bg-forge-surface`
      : 'text-forge-muted border-forge-border/40 hover:text-forge-text hover:border-forge-border';
  }

  // Function to format a due_date ISO string as "Month Day" (e.g. "May 6")
  formatDueDate(dueDate: string | null): string {
    if (!dueDate) return '';
    return new Date(dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  // Function to return the time remaining until local midnight (end of today's activity window)
  dailyTimeLeft(): string {
    const now = new Date();
    const midnight = new Date(now);
    midnight.setHours(24, 0, 0, 0);
    const diff = midnight.getTime() - now.getTime();
    const h = Math.floor(diff / 3_600_000);
    const m = Math.floor((diff % 3_600_000) / 60_000);
    return `${h}h ${m}m`;
  }

  // Function to map a mission's category code to a human-readable label
  categoryLabel(category: string | null): string {
    return category ? (CATEGORY_LABELS[category] ?? category) : '—';
  }

  // Function to check if the attribute linked to a mission is already at max level
  isAttrMaxed(code: string): boolean {
    return (this.playerState.profile()?.attributes.find((a) => a.code === code)?.level ?? 0) >= 10;
  }
}
