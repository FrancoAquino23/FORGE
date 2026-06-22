/* ==================================================================
   PROFILE LOGIC
   ================================================================== */

import { DatePipe } from '@angular/common';
import {
  Component,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  Output,
  inject,
  signal,
} from '@angular/core';
import { ApiService, PlayerAchievement, PlayerProfile, PlayerStats } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ATTR_COLORS, ATTR_HEX } from '../attr-constants';

// Visual Prestige tiers
const VISUAL_TIERS = [
  {
    min: 50,
    name: 'Singularity',
    color: '#e2e8f0',
    glow: 'drop-shadow(0 0 16px rgba(226,232,240,0.95))',
    animated: true,
  },
  {
    min: 35,
    name: 'Absolute Void',
    color: '#bf00ff',
    glow: 'drop-shadow(0 0 14px rgba(191,0,255,0.85))',
    animated: true,
  },
  {
    min: 20,
    name: 'Eternal Flame',
    color: '#ef4444',
    glow: 'drop-shadow(0 0 12px rgba(239,68,68,0.80))',
    animated: true,
  },
  {
    min: 10,
    name: 'Arcane Crystal',
    color: '#3b82f6',
    glow: 'drop-shadow(0 0 10px rgba(59,130,246,0.75))',
    animated: false,
  },
  {
    min: 6,
    name: 'Forged Obsidian',
    color: '#10b981',
    glow: 'drop-shadow(0 0 8px rgba(16,185,129,0.65))',
    animated: false,
  },
  {
    min: 3,
    name: 'Smelted Ore',
    color: '#f59e0b',
    glow: 'drop-shadow(0 0 6px rgba(245,158,11,0.55))',
    animated: false,
  },
  { min: 0, name: 'Scrap Metal', color: '#475569', glow: 'none', animated: false },
] as const;

// XP bar for SPECIAL attributes
const SEGMENTS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

@Component({
  selector: 'app-profile-modal',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './profile-modal.component.html',
  styleUrl: './profile-modal.component.scss',
})
export class ProfileModalComponent implements OnChanges {
  private api = inject(ApiService);
  private auth = inject(AuthService);

  @Input() open = false;
  @Output() closed = new EventEmitter<void>();

  profile = signal<PlayerProfile | null>(null);
  stats = signal<PlayerStats | null>(null);
  achievements = signal<PlayerAchievement[] | null>(null);
  confirmingLogout = signal(false);

  readonly SEGMENTS = SEGMENTS;

  // Load data when modal is opened
  ngOnChanges(): void {
    if (this.open && !this.profile()) {
      this.api.getProfile().subscribe({ next: (p) => this.profile.set(p) });
      this.api.getPlayerStats().subscribe({ next: (s) => this.stats.set(s) });
      this.api.getAchievements().subscribe({ next: (a) => this.achievements.set(a) });
    }
  }

  // Close on Escape key
  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.open) this.close();
  }

  // Close modal
  close(): void {
    this.confirmingLogout.set(false);
    this.closed.emit();
  }

  // Logout (inline confirm pattern)
  requestLogout(): void {
    this.confirmingLogout.set(true);
  }

  // Confirm logout action
  confirmLogout(): void {
    this.auth.logout();
    this.close();
  }

  // Cancel logout action
  cancelLogout(): void {
    this.confirmingLogout.set(false);
  }

  // Get initials from username
  initials(username: string): string {
    return username.slice(0, 2).toUpperCase();
  }

  // Get prestige tier data
  prestigeTier(count: number) {
    return VISUAL_TIERS.find((t) => count >= t.min) ?? VISUAL_TIERS[VISUAL_TIERS.length - 1];
  }

  // Get prestige gem color
  prestigeGemColor(count: number): string {
    return this.prestigeTier(count).color;
  }

  // Get prestige gem glow filter
  prestigeGemGlow(count: number): string {
    return this.prestigeTier(count).glow;
  }

  // Get prestige gem animated flag
  prestigeGemAnimated(count: number): boolean {
    return this.prestigeTier(count).animated;
  }

  // Get prestige tier name
  prestigeTierName(count: number): string {
    return this.prestigeTier(count).name;
  }

  // Get attribute text color class
  attrColor(code: string): string {
    return ATTR_COLORS[code] ?? 'text-forge-primary';
  }

  // Get attribute hex color
  attrHex(code: string): string {
    return ATTR_HEX[code] ?? '#f59e0b';
  }

  // Get segment fill class for SPECIAL bars
  segmentClass(level: number, seg: number): string {
    return level >= seg ? 'opacity-100' : 'opacity-10 bg-forge-border';
  }

  // Format large numbers with comma separator
  formatNumber(n: number): string {
    return n.toLocaleString('en-US');
  }
}
