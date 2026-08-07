/* ==================================================================
   MISSIONS COMPONENT LOGIC
   ================================================================== */

import {
  Component,
  DestroyRef,
  HostListener,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import {
  phosphorSwordBold,
  phosphorEyeBold,
  phosphorShieldBold,
  phosphorSketchLogoBold,
  phosphorDnaBold,
  phosphorLightningBold,
  phosphorSparkleBold,
  phosphorCompassBold,
  phosphorFlaskBold,
  phosphorNutBold,
  phosphorDotsThreeVerticalBold,
  phosphorRepeatBold,
  phosphorStarBold,
  phosphorClockBold,
  phosphorSpinnerBold,
  phosphorPlugsBold,
  phosphorScrollBold,
  phosphorCaretCircleLeftBold,
  phosphorCaretCircleRightBold,
  phosphorCaretDownBold,
  phosphorXCircleBold,
  phosphorPlusBold,
  phosphorWarningBold,
} from '@ng-icons/phosphor-icons/bold';
import { phosphorStarFill } from '@ng-icons/phosphor-icons/fill';
import {
  ActivateMissionResponse,
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
import { SoundService } from '../../core/sound.service';
import { TutorialService } from '../../core/tutorial.service';
import { DatePickerComponent } from '../../shared/date-picker/date-picker.component';

import {
  ATTR_HEX,
  CATEGORY_COLORS,
  RELIC_NAMES,
  THREAT_GLOW,
  THREAT_BORDER,
  THREAT_FAV_BG,
  fmt,
  attrColor,
  attrIcon,
  threatBarColor,
  threatTextClass,
  formatDueDate,
  isDueSoon,
  dueDateLabel,
  isExpired,
} from '../../shared/ui-constants';

export type MissionTab = 'NEW_MISSION' | 'DRAFTS' | 'DAILY_GRIND' | 'MAIN_QUEST' | 'SIDE_QUEST' | 'HISTORY';

const CATEGORY_LABELS: Record<string, string> = {
  MAIN_QUEST: 'Main Quest',
  SIDE_QUEST: 'Side Quest',
  DAILY_GRIND: 'Daily Grind',
};

@Component({
  selector: 'app-missions',
  imports: [NgIconComponent, FormsModule, DatePickerComponent],
  providers: [
    provideIcons({
      phosphorSwordBold,
      phosphorEyeBold,
      phosphorShieldBold,
      phosphorSketchLogoBold,
      phosphorDnaBold,
      phosphorLightningBold,
      phosphorSparkleBold,
      phosphorCompassBold,
      phosphorFlaskBold,
      phosphorNutBold,
      phosphorDotsThreeVerticalBold,
      phosphorRepeatBold,
      phosphorStarBold,
      phosphorStarFill,
      phosphorClockBold,
      phosphorSpinnerBold,
      phosphorPlugsBold,
      phosphorScrollBold,
      phosphorCaretCircleLeftBold,
      phosphorCaretCircleRightBold,
      phosphorCaretDownBold,
      phosphorXCircleBold,
      phosphorPlusBold,
      phosphorWarningBold,
    }),
  ],
  templateUrl: './missions.component.html',
  styleUrl: './missions.component.scss',
})
export class MissionsComponent implements OnInit {
  private api = inject(ApiService);
  private destroyRef = inject(DestroyRef);
  private toast = inject(ToastService);
  private playerState = inject(PlayerStateService);
  private sound = inject(SoundService);
  protected tutorial = inject(TutorialService);

  data = signal<MissionListResponse | null>(null);
  historyData = signal<MissionHistoryItem[]>([]);
  historyLoaded = signal(false);
  historyPage = signal(1);
  historyTotalPages = signal(1);
  historyTotal = signal(0);

  loadError = signal(false);
  historyLoadError = signal(false);
  claiming = signal('');
  activeTab = signal<MissionTab>('NEW_MISSION');
  attrFilter = signal('');
  threatFilter = signal('');
  sortByDate = signal(false);

  private expandedSet = signal(new Set<string>());
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
  saveAsDraft = signal(false);
  activating = signal('');
  formSubmitted = signal(false);
  logAttr = signal('');
  logCategory = signal<'MAIN_QUEST' | 'SIDE_QUEST' | 'DAILY_GRIND'>('DAILY_GRIND');
  logThreatLevel = signal<'MINOR' | 'MAJOR' | 'CRITICAL'>('MAJOR');
  logDesc = signal('');
  logDetail = signal('');
  logDueDate = signal('');
  logSteps = signal('');
  attrDropdownOpen = signal(false);

  readonly todayStr = new Date().toISOString().split('T')[0];

  // Tab definitions for template iteration
  readonly TABS: { value: MissionTab; label: string }[] = [
    { value: 'NEW_MISSION', label: 'New Mission' },
    { value: 'DRAFTS', label: 'Drafts' },
    { value: 'MAIN_QUEST', label: 'Main Quests' },
    { value: 'SIDE_QUEST', label: 'Side Quests' },
    { value: 'DAILY_GRIND', label: 'Daily Grinds' },
    { value: 'HISTORY', label: 'History' },
  ];

  // Attribute codes for filter buttons
  readonly ATTRS = ['S', 'P', 'E', 'C', 'I', 'A'];

  // Category options for new mission forms
  readonly CATEGORIES = [
    { value: 'MAIN_QUEST' as const, label: 'Main Quest' },
    { value: 'SIDE_QUEST' as const, label: 'Side Quest' },
    { value: 'DAILY_GRIND' as const, label: 'Daily Grind' },
  ];

  // Threat level for new mission forms & filter buttons
  readonly THREAT_LEVELS: {
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
      case 'DRAFTS':
        return all.filter((m) => m.status === 'DRAFT');
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
      this.api
        .getProfile()
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({ next: (p) => this.playerState.profile.set(p) });
    }
  }

  // Close open overflow menu when clicking anywhere outside it
  @HostListener('document:click')
  onDocumentClick(): void {
    this.menuOpenId.set('');
    this.attrDropdownOpen.set(false);
  }

  // Function to load active missions from API
  private loadMissions(): void {
    this.api
      .getActiveMissions()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => this.data.set(res),
        error: () => this.loadError.set(true),
      });
  }

  // Function to load mission history for the given page
  private loadHistory(page: number = 1): void {
    this.historyLoaded.set(false);
    this.api
      .getMissionHistory(page, 5)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.historyData.set(res.missions);
          this.historyPage.set(res.page);
          this.historyTotalPages.set(res.total_pages);
          this.historyTotal.set(res.total);
          this.historyLoaded.set(true);
        },
        error: () => this.historyLoadError.set(true),
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
    this.attrDropdownOpen.set(!this.attrDropdownOpen());
  }

  // Select attribute
  selectAttr(code: string): void {
    this.logAttr.set(code);
    this.attrDropdownOpen.set(false);
  }

  // Get attribute display name
  getAttrName(code: string): string {
    return this.playerState.profile()?.attributes.find((a) => a.code === code)?.name ?? code;
  }

  // Deploy a mission
  deployMission(): void {
    this.formSubmitted.set(true);
    if (!this.logAttr() || !this.logDesc().trim() || this.deploying()) return;
    if (this.logCategory() !== 'DAILY_GRIND' && !this.saveAsDraft() && !this.logDueDate()) return;
    this.deploying.set(true);

    const steps = this.logSteps()
      .split('\n')
      .map((s: string) => s.trim())
      .filter(Boolean);
    const isDraft = this.saveAsDraft() && this.logCategory() !== 'DAILY_GRIND';
    const payload: DeployMissionRequest = {
      attribute_code: this.logAttr(),
      category: this.logCategory(),
      threat_level: this.logThreatLevel(),
      description: this.logDesc().trim(),
      detail: this.logDetail().trim() || undefined,
      due_date: this.logDueDate() || undefined,
      steps: steps.length > 0 ? steps : undefined,
      is_draft: isDraft,
    };

    this.api
      .deployMission(payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (_res) => {
          this.sound.playMission();
          if (isDraft) {
            this.toast.show({
              type: 'success',
              icon: '',
              ngIcon: 'phosphorClipboardTextBold',
              title: 'Mission Drafted',
              message: 'Activate when ready to start the timer',
            });
          } else {
            this.toast.show({
              type: 'success',
              icon: '',
              ngIcon: 'phosphorClipboardTextBold',
              title: 'Mission Created',
              message: '',
            });
          }
          this.deploying.set(false);
          this.formSubmitted.set(false);
          this.saveAsDraft.set(false);
          this.logAttr.set('');
          this.logDesc.set('');
          this.logDetail.set('');
          this.logDueDate.set('');
          this.logSteps.set('');
          this.logCategory.set('DAILY_GRIND');
          this.logThreatLevel.set('MAJOR');
          this.historyLoaded.set(false);
          this.loadMissions();
        },
        error: (err) => {
          this.toast.showError(
            'Mission Deploy Failed',
            err,
            'Could not deploy mission. Please try again.',
          );
          this.deploying.set(false);
        },
      });
  }

  // Function to activate a DRAFT mission and start its timer
  activateMission(m: MissionProgress): void {
    if (this.activating()) return;
    this.activating.set(m.mission_id);
    this.api
      .activateMission(m.mission_id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (_res: ActivateMissionResponse) => {
          this.sound.playMission();
          this.toast.show({
            type: 'success',
            icon: '',
            ngIcon: 'phosphorClipboardTextBold',
            title: 'Mission Activated',
            message: '',
          });
          this.activating.set('');
          this.loadMissions();
        },
        error: (err) => {
          this.toast.showError('Activation Failed', err, 'Could not activate mission.');
          this.activating.set('');
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

    this.api
      .toggleCheckpoint(cp.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        error: () => {
          this.toast.showError('Error', undefined, 'Could not update checkpoint');
          this.loadMissions();
        },
      });
  }

  // Function to claim a mission reward
  claim(mission: MissionProgress): void {
    if (this.claiming() || !this.canFinish(mission)) return;

    if (isExpired(mission.due_date)) {
      this.claiming.set(mission.mission_id);
      this.api
        .deleteMission(mission.mission_id)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: () => {
            this.claiming.set('');
            this.toast.showExpired();
            this.loadMissions();
          },
          error: (err) => {
            this.claiming.set('');
            this.toast.showError('Mission Delete Failed', err, 'Could not dismiss mission.');
          },
        });
      return;
    }

    this.claiming.set(mission.mission_id);

    this.api
      .claimMission(mission.mission_id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.sound.playMission();
          if (res.leveled_up) setTimeout(() => this.sound.playUpgrade(), 600);
          this.toast.fromMissionClaim(res);
          if (res.newly_unlocked?.length) this.toast.fromAchievements(res.newly_unlocked);
          this.claiming.set('');
          this.historyLoaded.set(false);
          this.loadMissions();
          this.api
            .getProfile()
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe({ next: (p) => this.playerState.profile.set(p) });
        },
        error: (err) => {
          this.toast.showError(
            'Mission Claim Failed',
            err,
            'Could not claim mission. Please try again.',
          );
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
    this.api
      .deleteMission(m.mission_id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.sound.playMission();
          this.toast.show({
            type: 'success',
            icon: '',
            ngIcon: 'phosphorTrashBold',
            iconColor: 'text-red-400',
            title: 'Mission Deleted',
            message: '',
          });
          this.loadMissions();
        },
        error: (err) => {
          this.toast.showError(
            'Mission Delete Failed',
            err,
            'Could not delete mission. Please try again.',
          );
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
    this.api
      .updateMission(this.editingId(), payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.sound.playMission();
          this.savingEdit.set(false);
          this.editingId.set('');
          this.toast.show({
            type: 'success',
            icon: '',
            ngIcon: 'phosphorCheckCircleBold',
            title: 'Mission Updated',
            message: 'Changes saved successfully',
          });
          this.loadMissions();
        },
        error: (err) => {
          this.toast.showError(
            'Mission Update Failed',
            err,
            'Could not update mission. Please try again.',
          );
          this.savingEdit.set(false);
        },
      });
  }

  // Function to toggle is_favorite on a daily mission; optimistically updates local data
  toggleFavorite(m: MissionProgress): void {
    this.api
      .toggleFavorite(m.mission_id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
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
            this.sound.playStreak();
            this.toast.show({
              type: 'success',
              icon: '',
              ngIcon: 'phosphorFlameBold',
              iconColor: 'text-amber-400',
              title: 'Streak Unlocked',
              message: 'Rewards grow the longer your streak holds',
            });
          }
        },
        error: () => {
          this.toast.showError(
            'Mission Toggle Favorite Failed',
            undefined,
            'Could not toggle favorite',
          );
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
      case 'DRAFTS':
        return all.filter((m) => m.status === 'DRAFT').length;
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

  // Constants & utility functions
  protected fmt = fmt;
  protected attrColor = attrColor;

  // Function to map a category to its color class
  catColor(category: string): string {
    return CATEGORY_COLORS[category] ?? 'text-forge-primary';
  }

  // Function to map an attribute code to its hex color
  attrBarColor(code: string): string {
    return ATTR_HEX[code] ?? '#f59e0b';
  }

  // Constants & utility functions
  protected threatBarColor = threatBarColor;
  protected attrIcon = attrIcon;

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

  // Constants & utility functions
  protected threatTextClass = threatTextClass;

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
  protected formatDueDate = formatDueDate;
  protected isDueSoon = isDueSoon;
  protected dueDateLabel = dueDateLabel;
  protected isExpired = isExpired;

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
