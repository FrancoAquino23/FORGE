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

// Desired order of paths displayed (UI)
const PATH_ORDER = ['Stellar Alchemy', 'Industrial Supply', 'Chronological Mastery'];

@Component({
  selector: 'app-skill-tree',
  standalone: true,
  imports: [],
  templateUrl: './skill-tree.component.html',
})
export class SkillTreeComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);

  readonly tree = signal<SkillTreeResponse | null>(null);
  readonly loading = signal(true);
  readonly upgradingNode = signal<string | null>(null);
  readonly resetting = signal(false);

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
        this.toast.show({
          type: 'loot',
          icon: '🌟',
          title: 'Node Upgraded',
          message: `${node.display_name} → Level ${res.new_level}`,
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
