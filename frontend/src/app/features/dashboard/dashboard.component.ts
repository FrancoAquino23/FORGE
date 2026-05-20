/* ==================================================================
   DASHBOARD COMPONENT LOGIC
   ================================================================== */

import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  LucideAngularModule,
  LucideIconData,
  Hammer,
  Eye,
  Shield,
  Gem,
  Cpu,
  Zap,
  Sparkles,
} from 'lucide-angular';
import { ApiService, AttributeProfile, PlayerProfile } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { RelicWorkshopComponent } from '../relic-workshop/relic-workshop.component';
import { DatePickerComponent } from '../../shared/date-picker/date-picker.component';

// Category label map used for deploy-mission toast
const _DEPLOY_CAT_LABEL: Record<string, string> = {
  MAIN_QUEST: 'Main Quest',
  SIDE_QUEST: 'Side Quest',
  DAILY_GRIND: 'Daily Grind',
};

// Color mappings for attributes
const ATTR_COLORS: Record<string, string> = {
  S: 'text-red-400',
  P: 'text-blue-400',
  E: 'text-green-400',
  C: 'text-yellow-300',
  I: 'text-purple-400',
  A: 'text-cyan-400',
  L: 'text-orange-400',
};

// Glow effect mappings for attributes (used on hover)
const ATTR_GLOW: Record<string, string> = {
  S: 'hover:shadow-[0_0_18px_rgba(248,113,113,0.3)]',
  P: 'hover:shadow-[0_0_18px_rgba(96,165,250,0.3)]',
  E: 'hover:shadow-[0_0_18px_rgba(74,222,128,0.3)]',
  C: 'hover:shadow-[0_0_18px_rgba(253,224,71,0.3)]',
  I: 'hover:shadow-[0_0_18px_rgba(192,132,252,0.3)]',
  A: 'hover:shadow-[0_0_18px_rgba(34,211,238,0.3)]',
  L: 'hover:shadow-[0_0_18px_rgba(251,146,60,0.3)]',
};

// Hex color values
const ATTR_BAR_COLORS: Record<string, string> = {
  S: '#f87171',
  P: '#60a5fa',
  E: '#4ade80',
  C: '#fde047',
  I: '#c084fc',
  A: '#22d3ee',
  L: '#fb923c',
};

// Lucide icon map for material balance row
const ATTR_ICONS: Record<string, LucideIconData> = {
  S: Hammer,
  P: Eye,
  E: Shield,
  C: Gem,
  I: Cpu,
  A: Zap,
  L: Sparkles,
};

// Prestige gem border color thresholds
const GEM_COLORS = [
  { min: 10, color: '#bf00ff' },
  { min: 7, color: '#3b82f6' },
  { min: 3, color: '#10b981' },
  { min: 1, color: '#f59e0b' },
  { min: 0, color: '#475569' },
] as const;

// Number of segments in each attribute bar before reaching prestige
const PRESTIGE_THRESHOLD = 10;

// Main dashboard component that displays player profile, attributes, and inventory
@Component({
  selector: 'app-dashboard',
  imports: [RelicWorkshopComponent, LucideAngularModule, FormsModule, DatePickerComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);

  profile = signal<PlayerProfile | null>(null);
  loadError = signal('');
  deploying = signal(false);
  xpFlash = signal('');

  logAttr = '';
  logCategory: 'MAIN_QUEST' | 'SIDE_QUEST' | 'DAILY_GRIND' = 'DAILY_GRIND';
  logThreatLevel: 'MINOR' | 'MAJOR' | 'CRITICAL' = 'MAJOR';
  logDesc = '';
  logDetail = '';
  logDueDate = '';
  logSteps = '';
  attrDropdownOpen = false;

  readonly todayStr = new Date().toISOString().split('T')[0];

  readonly SEGMENTS = Array.from({ length: PRESTIGE_THRESHOLD }, (_, i) => i + 1);

  readonly CATEGORIES = [
    { value: 'MAIN_QUEST' as const, label: 'Main Quest' },
    { value: 'SIDE_QUEST' as const, label: 'Side Quest' },
    { value: 'DAILY_GRIND' as const, label: 'Daily Grind' },
  ];

  readonly THREAT_LEVELS: {
    value: 'MINOR' | 'MAJOR' | 'CRITICAL';
    label: string;
    color: string;
  }[] = [
    { value: 'MINOR', label: 'Minor', color: 'text-cyan-400' },
    { value: 'MAJOR', label: 'Major', color: 'text-amber-400' },
    { value: 'CRITICAL', label: 'Critical', color: 'text-red-400' },
  ];

  // Load component
  ngOnInit(): void {
    this.loadProfile();
  }

  // Load player profile from API
  private loadProfile(): void {
    this.api.getProfile().subscribe({
      next: (p) => this.profile.set(p),
      error: () => this.loadError.set('Could not load profile. Check your token.'),
    });
  }

  // Handle attribute selection from dropdown
  selectAttr(code: string): void {
    this.logAttr = code;
    this.attrDropdownOpen = false;
  }

  // Deploy a new mission based on user input
  deployMission(): void {
    if (!this.logAttr || this.deploying()) return;
    this.deploying.set(true);

    const steps = this.logSteps
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    this.api
      .deployMission({
        attribute_code: this.logAttr,
        category: this.logCategory,
        threat_level: this.logThreatLevel,
        description: this.logDesc.trim() || undefined,
        detail: this.logDetail.trim() || undefined,
        due_date: this.logDueDate || undefined,
        steps: steps.length > 0 ? steps : undefined,
      })
      .subscribe({
        next: (res) => {
          const catLabel = _DEPLOY_CAT_LABEL[res.category] ?? res.category;
          this.toast.show({
            type: 'claim',
            icon: '⚔',
            title: 'Mission Forged',
            message: `${catLabel} mission forged!`,
          });
          this.deploying.set(false);
          this.xpFlash.set(this.logAttr);
          setTimeout(() => this.xpFlash.set(''), 700);
          this.logAttr = '';
          this.logDesc = '';
          this.logDetail = '';
          this.logDueDate = '';
          this.logSteps = '';
          this.logCategory = 'DAILY_GRIND';
          this.logThreatLevel = 'MAJOR';
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

  // Function to determine the CSS class for each segment in the attribute bars
  segmentClass(attr: AttributeProfile, seg: number): string {
    if (attr.level >= PRESTIGE_THRESHOLD) return 'seg-prestige';
    return attr.level >= seg ? 'seg-active' : 'seg-off';
  }

  // Function to determine the color of the prestige gem based on the player's prestige count
  prestigeGemColor(count: number): string {
    return GEM_COLORS.find((g) => count >= g.min)!.color;
  }

  // Function to determine the glow effect of the prestige gem based on the player's prestige count
  prestigeGemGlow(count: number): string {
    if (count < PRESTIGE_THRESHOLD) return 'none';
    return `drop-shadow(0 0 10px ${this.prestigeGemColor(count)})`;
  }

  // Function to calculate the XP percentage for an attribute, used for the XP bar fill
  xpPct(attr: AttributeProfile): number {
    if (attr.level >= PRESTIGE_THRESHOLD) return 100;
    return attr.xp_to_next ? Math.min(100, (attr.xp_current / attr.xp_to_next) * 100) : 0;
  }

  // Function to get color class for an attribute based on its code
  xpBarColor(code: string): string {
    return ATTR_BAR_COLORS[code] ?? '#f59e0b';
  }

  // Function to get the text color class for an attribute based on its code
  attrColor(code: string): string {
    return ATTR_COLORS[code] ?? 'text-forge-primary';
  }

  // Function to get glow class for an attribute based on its code
  attrGlow(code: string): string {
    return ATTR_GLOW[code] ?? '';
  }

  // Function to get the appropriate icon for an attribute based on its code
  getIconName(code: string): LucideIconData {
    return ATTR_ICONS[code] ?? Sparkles;
  }

  // Function to get the display name of an attribute based on its code
  getAttrName(code: string): string {
    return this.profile()?.attributes.find((a) => a.code === code)?.name ?? code;
  }
}
