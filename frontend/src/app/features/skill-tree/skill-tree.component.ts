/* ==================================================================
   SKILL TREE COMPONENT LOGIC
   ================================================================== */

import { Component, OnInit, computed, inject, signal } from '@angular/core';
import {
  ApiService,
  SkillNodeInfo,
  SkillTreeResponse,
  UpgradeNodeResponse,
} from '../../core/api.service';
import { ToastService } from '../../core/toast.service';

type PathGroup = { path: string; nodes: SkillNodeInfo[] };

// Icons for each path
const PATH_ICONS: Record<string, string> = {
  'Stellar Alchemy': '✨',
  'Industrial Supply': '🔩',
  'Chronological Mastery': '⚡',
};

// Hex fill colors per path
const PATH_COLORS: Record<string, string> = {
  'Stellar Alchemy': '#f59e0b',
  'Industrial Supply': '#60a5fa',
  'Chronological Mastery': '#c084fc',
};

// Central symbol displayed inside each node hex
const PATH_SYMBOLS: Record<string, string> = {
  'Stellar Alchemy': '◈',
  'Industrial Supply': '⬡',
  'Chronological Mastery': '◎',
};

// Desired order of paths displayed (UI)
const PATH_ORDER = ['Stellar Alchemy', 'Industrial Supply', 'Chronological Mastery'];

@Component({
  selector: 'app-skill-tree',
  standalone: true,
  imports: [],
  templateUrl: './skill-tree.component.html',
  styleUrl: './skill-tree.component.scss',
})
export class SkillTreeComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);

  readonly tree = signal<SkillTreeResponse | null>(null);
  readonly loading = signal(true);
  readonly upgradingNode = signal<string | null>(null);
  readonly resetting = signal(false);
  hoverNode = signal<string | null>(null);

  readonly hoveredNodeData = computed(() => {
    const id = this.hoverNode();
    if (!id) return null;
    return this.tree()?.nodes.find((n) => n.node_id === id) ?? null;
  });

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

  // Initialize component
  ngOnInit(): void {
    this.loadTree();
  }

  // Load component
  loadTree(): void {
    this.loading.set(true);
    this.api.getSkillTree().subscribe({
      next: (data) => {
        this.tree.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  // Function to get icon for a path
  pathIcon(path: string): string {
    return PATH_ICONS[path] ?? '◆';
  }

  // Function to get the CSS color for a path
  pathColor(path: string): string {
    return PATH_COLORS[path] ?? '#f59e0b';
  }

  // Function to get the central symbol for a path's nodes
  nodeSymbol(path: string): string {
    return PATH_SYMBOLS[path] ?? '◆';
  }

  // Function to derive visual state for a node
  nodeState(node: SkillNodeInfo): 'locked' | 'available' | 'active' | 'maxed' {
    if (node.current_level === node.max_level) return 'maxed';
    if (node.current_level > 0) return 'active';
    if (node.cost_to_upgrade !== null) return 'available';
    return 'locked';
  }

  // Function to return the hex outer class string including state
  nodeHexClass(node: SkillNodeInfo): string {
    return `node-hex-outer node--${this.nodeState(node)}`;
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
    return node.cost_to_upgrade !== null && pp >= node.cost_to_upgrade;
  }

  // Function to check if a node is currently being upgraded
  isUpgrading(nodeId: string): boolean {
    return this.upgradingNode() === nodeId;
  }

  // Function to handle node upgrade action
  upgrade(node: SkillNodeInfo): void {
    if (!this.canUpgrade(node) || this.upgradingNode()) return;
    this.upgradingNode.set(node.node_id);

    this.api.upgradeNode(node.node_id).subscribe({
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
                        next_effect: res.new_level < n.max_level ? null : null,
                      }
                    : n,
                ),
                pp_available: res.pp_available,
              }
            : t,
        );
        this.upgradingNode.set(null);
        const isMaxed = res.new_level >= node.max_level;
        const tierType = isMaxed ? 'node-gold' : res.new_level === 1 ? 'node-bronze' : 'node-silver';
        const tierIcon = isMaxed ? '🥇' : res.new_level === 1 ? '🥉' : '🥈';
        this.toast.show({
          type: tierType,
          icon: tierIcon,
          title: isMaxed ? `${node.display_name} — MAXED` : 'Node Upgraded',
          message: isMaxed
            ? `Level ${res.new_level}/${node.max_level} · Fully Mastered`
            : `${node.display_name} → Level ${res.new_level}/${node.max_level}`,
        });
        this.loadTree();
      },
      error: () => this.upgradingNode.set(null),
    });
  }

  // Function to handle skill tree reset
  resetTree(): void {
    if (this.resetting()) return;
    this.resetting.set(true);
    this.api.resetSkillTree().subscribe({
      next: (res) => {
        this.resetting.set(false);
        this.toast.show({
          type: 'claim',
          icon: '↺',
          title: 'Skill Tree Reset',
          message: `+${res.pp_refunded} PP refunded`,
        });
        this.loadTree();
      },
      error: () => this.resetting.set(false),
    });
  }
}
