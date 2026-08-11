/* ==================================================================
   SKILL TREE COMPONENT LOGIC
   ================================================================== */

import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import {
  phosphorArrowCounterClockwiseBold,
  phosphorMagnifyingGlassBold,
  phosphorSpinnerBold,
  phosphorPlugsBold,
  phosphorBiohazardBold,
  phosphorGearSixBold,
  phosphorGraphBold,
  phosphorMedalBold,
  phosphorStarBold,
  phosphorTimerBold,
  phosphorProhibitBold,
  phosphorCaretCircleLeftBold,
  phosphorCaretCircleRightBold,
  phosphorCrownBold,
} from '@ng-icons/phosphor-icons/bold';
import {
  ApiService,
  SkillNodeInfo,
  SkillTreeResponse,
  UpgradeNodeResponse,
} from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { PlayerStateService } from '../../core/player-state.service';
import { SoundService } from '../../core/sound.service';

type PathGroup = { path: string; nodes: SkillNodeInfo[] };

// Phosphor Bold icon name for each path
const PATH_ICONS: Record<string, string> = {
  'Stellar Mastery': 'phosphorStarBold',
  'Industrial Mastery': 'phosphorGearSixBold',
  'Cycle Mastery': 'phosphorTimerBold',
  'Operative Mastery': 'phosphorBiohazardBold',
  'Prestige Mastery': 'phosphorMedalBold',
  'Royal Mastery': 'phosphorCrownBold',
};

// Unified color for all paths (slate white — distinct from all S.P.E.C.I.A.L. attribute colors)
const PATH_COLORS: Record<string, string> = {
  'Stellar Mastery': '#e2e8f0',
  'Industrial Mastery': '#e2e8f0',
  'Cycle Mastery': '#e2e8f0',
  'Operative Mastery': '#e2e8f0',
  'Prestige Mastery': '#e2e8f0',
  'Royal Mastery': '#e2e8f0',
};

// Desired order of paths displayed (UI)
const PATH_ORDER = [
  'Stellar Mastery',
  'Industrial Mastery',
  'Cycle Mastery',
  'Operative Mastery',
  'Prestige Mastery',
  'Royal Mastery',
];

@Component({
  selector: 'app-skill-tree',
  standalone: true,
  imports: [NgIconComponent],
  viewProviders: [
    provideIcons({
      phosphorArrowCounterClockwiseBold,
      phosphorMagnifyingGlassBold,
      phosphorSpinnerBold,
      phosphorPlugsBold,
      phosphorStarBold,
      phosphorGearSixBold,
      phosphorTimerBold,
      phosphorBiohazardBold,
      phosphorMedalBold,
      phosphorGraphBold,
      phosphorProhibitBold,
      phosphorCaretCircleLeftBold,
      phosphorCaretCircleRightBold,
      phosphorCrownBold,
    }),
  ],
  templateUrl: './skill-tree.component.html',
  styleUrl: './skill-tree.component.scss',
})
export class SkillTreeComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private destroyRef = inject(DestroyRef);
  private playerState = inject(PlayerStateService);
  private sound = inject(SoundService);

  readonly prestigeCount = this.playerState.prestigeCount;

  readonly tree = signal<SkillTreeResponse | null>(null);
  readonly loading = signal(true);
  readonly loadError = signal(false);
  readonly upgradingNode = signal<string | null>(null);
  readonly resetting = signal(false);
  readonly confirmReset = signal(false);
  hoverNode = signal<string | null>(null);

  // Property to get the currently hovered node data
  readonly hoveredNodeData = computed(() => {
    const id = this.hoverNode();
    if (!id) return null;
    return this.tree()?.nodes.find((n) => n.node_id === id) ?? null;
  });

  // Property to get the list of paths & nodes
  readonly paths = computed<PathGroup[]>(() => {
    const nodes = this.tree()?.nodes ?? [];
    const map = new Map<string, SkillNodeInfo[]>();
    for (const n of nodes) {
      const list = map.get(n.path) ?? [];
      list.push(n);
      map.set(n.path, list);
    }
    return PATH_ORDER.filter((p) => map.has(p)).map((p) => ({ path: p, nodes: map.get(p)! }));
  });

  // Property to get the current path index
  readonly currentPathIndex = signal(0);

  // Property to get the current path data
  readonly currentPath = computed<PathGroup | null>(() => {
    const list = this.paths();
    const idx = this.currentPathIndex();
    return list[idx] ?? null;
  });

  // Function no navigate to the previous path
  prevPath(): void {
    const len = this.paths().length;
    this.currentPathIndex.update((i) => (i - 1 + len) % len);
    this.hoverNode.set(null);
  }

  // Function to navigate to the next path
  nextPath(): void {
    const len = this.paths().length;
    this.currentPathIndex.update((i) => (i + 1) % len);
    this.hoverNode.set(null);
  }

  // Initialize component
  ngOnInit(): void {
    this.loadTree();
  }

  // Load component
  loadTree(): void {
    this.loading.set(true);
    this.api
      .getSkillTree()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          this.tree.set(data);
          this.loading.set(false);
        },
        error: () => this.loadError.set(true),
      });
  }

  // Function to get icon for a path
  pathIcon(path: string): string {
    return PATH_ICONS[path] ?? '';
  }

  // Function to get the CSS color for a path
  pathColor(path: string): string {
    return PATH_COLORS[path] ?? '#f59e0b';
  }

  // Function to get icon color for a path — gold if any node is maxed
  pathIconColor(group: PathGroup): string {
    return group.nodes.some((n) => n.current_level >= n.max_level)
      ? '#f59e0b'
      : this.pathColor(group.path);
  }

  // Function to derive visual state for a node
  nodeState(node: SkillNodeInfo): 'locked' | 'available' | 'active' | 'maxed' | 'choice-locked' {
    if (node.current_level === node.max_level) return 'maxed';
    if (node.current_level > 0) return 'active';
    if (node.locked_by_choice) return 'choice-locked';
    if (node.cost_to_upgrade !== null) return 'available';
    return 'locked';
  }

  // Function to return the hex outer class string including state
  nodeHexClass(node: SkillNodeInfo): string {
    return `node-hex-outer node--${this.nodeState(node)}`;
  }

  // Function to return icon/border color based on current level (bronze / silver / gold)
  nodeIconColor(node: SkillNodeInfo): string | null {
    if (node.current_level === 0) return null;
    if (node.current_level >= node.max_level) return '#f59e0b';
    if (node.current_level === 1) return '#f97316';
    return '#94a3b8';
  }

  // Function to return colored box-shadow glow for leveled nodes (lv1 / lv2)
  nodeLevelGlow(node: SkillNodeInfo): string | null {
    if (node.current_level === 0 || node.current_level >= node.max_level) return null;
    if (node.current_level === 1)
      return '0 0 16px rgba(249, 115, 22, 0.7), 0 0 36px rgba(249, 115, 22, 0.25)';
    return '0 0 16px rgba(148, 163, 184, 0.7), 0 0 36px rgba(148, 163, 184, 0.25)';
  }

  // Function to derive connector state between node[fromIndex] and the next
  connectorState(nodes: SkillNodeInfo[], fromIndex: number): 'locked' | 'partial' | 'active' {
    const from = nodes[fromIndex];
    if (!from) return 'locked';
    if (from.current_level === from.max_level) return 'active';
    if (from.current_level > 0) return 'partial';
    return 'locked';
  }

  // Function to return the connector class string including state
  connectorClass(nodes: SkillNodeInfo[], fromIndex: number): string {
    return `node-connector connector--${this.connectorState(nodes, fromIndex)}`;
  }

  // Function to determine how many dots to fill for a node based on its current level
  nodeDots(node: SkillNodeInfo): boolean[] {
    return Array.from({ length: node.max_level }, (_, i) => i < node.current_level);
  }

  // Function to check if a node can be upgraded
  canUpgrade(node: SkillNodeInfo): boolean {
    const pp = this.tree()?.pp_available ?? 0;
    return node.cost_to_upgrade !== null && pp >= node.cost_to_upgrade && !node.locked_by_choice;
  }

  // Function to check if a node is currently being upgraded
  isUpgrading(nodeId: string): boolean {
    return this.upgradingNode() === nodeId;
  }

  // Function to handle node upgrade action
  upgrade(node: SkillNodeInfo): void {
    if (!this.canUpgrade(node) || this.upgradingNode()) return;
    this.upgradingNode.set(node.node_id);

    this.api
      .upgradeNode(node.node_id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res: UpgradeNodeResponse) => {
          this.tree.update((t) =>
            t
              ? {
                  ...t,
                  nodes: t.nodes.map((n) =>
                    n.node_id === res.node_id
                      ? {
                          ...n,
                          current_level: res.new_level,
                          cost_to_upgrade: res.new_level < n.max_level ? res.new_level + 1 : null,
                          current_effect: n.next_effect ?? n.current_effect,
                          next_effect: res.new_level < n.max_level ? res.next_effect : null,
                        }
                      : n,
                  ),
                  pp_available: res.pp_available,
                }
              : t,
          );
          this.upgradingNode.set(null);
          const isMaxed = res.new_level >= node.max_level;
          const isFirstChoice = node.current_level === 0;
          if (isFirstChoice && !isMaxed) this.sound.playPath();
          else this.sound.playUpgrade();
          const medalColor = isMaxed
            ? 'text-amber-500'
            : res.new_level === 1
              ? 'text-orange-500'
              : 'text-slate-400';
          this.toast.show({
            type: 'node',
            icon: '',
            ngIcon: 'phosphorMedalBold',
            iconColor: medalColor,
            title: isMaxed
              ? `Maxed: ${node.display_name}`
              : `Level ${res.new_level}: ${node.display_name}`,
            message: isFirstChoice && !isMaxed ? 'Path committed' : '',
          });
          this.loadTree();
        },
        error: (err: { error?: { detail?: string } }) => {
          this.upgradingNode.set(null);
          this.toast.showError(
            'Node Upgrade Failed',
            err,
            'Could not upgrade node. Please try again.',
          );
        },
      });
  }

  // Function to request reset confirmation
  requestReset(): void {
    this.confirmReset.set(true);
  }

  // Function to cancel pending reset
  cancelReset(): void {
    this.confirmReset.set(false);
  }

  // Function to handle skill tree reset
  resetTree(): void {
    if (this.resetting()) return;
    this.confirmReset.set(false);
    this.resetting.set(true);
    this.api
      .resetSkillTree()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.sound.playPerkReset();
          this.resetting.set(false);
          this.toast.show({
            type: 'success',
            icon: '',
            ngIcon: 'phosphorArrowCounterClockwiseBold',
            iconColor: 'text-slate-400',
            title: 'Perks Reset',
            message: `+${res.pp_refunded} PP refunded`,
          });
          this.loadTree();
        },
        error: () => {
          this.resetting.set(false);
          this.toast.showError(
            'Perk Reset Failed',
            undefined,
            'Could not reset perk. Please try again.',
          );
        },
      });
  }
}
