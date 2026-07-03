/* ==================================================================
   METRICS COMPONENT LOGIC
   ================================================================== */

import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import {
  phosphorPresentationChartBold,
  phosphorCaretCircleLeftBold,
  phosphorCaretCircleRightBold,
} from '@ng-icons/phosphor-icons/bold';
import { ApiService, AttributeMetric, PlayerMetrics } from '../../core/api.service';
import {
  ATTR_HEX,
  CATEGORY_BAR_COLORS,
  CATEGORY_COLORS,
  THREAT_BAR_COLORS,
  THREAT_COLORS,
  fmt,
} from '../../shared/ui-constants';

@Component({
  selector: 'app-metrics',
  imports: [NgIconComponent],
  providers: [
    provideIcons({
      phosphorPresentationChartBold,
      phosphorCaretCircleLeftBold,
      phosphorCaretCircleRightBold,
    }),
  ],
  templateUrl: './metrics.component.html',
})
export class MetricsComponent implements OnInit {
  private api = inject(ApiService);
  private destroyRef = inject(DestroyRef);

  metrics = signal<PlayerMetrics | null>(null);
  loading = signal(false);
  weekOffset = signal(0);

  // Lifecycle hook
  ngOnInit(): void {
    this.load();
  }

  // Load component
  load(): void {
    if (this.loading()) return;
    this.loading.set(true);
    this.api
      .getMetrics(this.weekOffset())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (m) => {
          this.metrics.set(m);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  // Previous week navigation
  prevWeek(): void {
    this.weekOffset.update((o) => o - 1);
    this.load();
  }

  // Next week navigation
  nextWeek(): void {
    if (this.metrics()?.has_next) {
      this.weekOffset.update((o) => o + 1);
      this.load();
    }
  }

  // Percentage relative to the max value in the group
  barPct(value: number, max: number): string {
    if (max === 0) return '0%';
    return `${Math.round((value / max) * 100)}%`;
  }

  // Category values for scaling bars
  catMax(m: PlayerMetrics): number {
    const c = m.category_breakdown;
    return Math.max(c.main_quest, c.side_quest, c.daily_grind, 1);
  }

  // Threat values for scaling bars
  threatMax(m: PlayerMetrics): number {
    const t = m.threat_breakdown;
    return Math.max(t.minor, t.major, t.critical, 1);
  }

  // Max missions across attributes
  attrMax(attrs: AttributeMetric[]): number {
    return Math.max(...attrs.map((a) => a.missions_completed), 1);
  }

  // Format hours
  formatHours(h: number | null): string {
    if (h === null) return '—';
    if (h < 1) return `${Math.round(h * 60)}m`;
    if (h >= 48) return `${(h / 24).toFixed(1)}d`;
    return `${h.toFixed(1)}h`;
  }

  protected fmt = fmt;

  // Attribute hex color
  attrHex(code: string): string {
    return ATTR_HEX[code] ?? '#f59e0b';
  }

  // Category text color class
  catColor(category: string): string {
    return CATEGORY_COLORS[category] ?? 'text-forge-muted';
  }

  // Category bar bg color class
  catBarColor(category: string): string {
    return CATEGORY_BAR_COLORS[category] ?? 'bg-forge-primary';
  }

  // Threat text color class
  threatTextColor(level: string): string {
    return THREAT_COLORS[level] ?? 'text-forge-muted';
  }

  // Threat bar color (Backgrounds)
  threatBarBgColor(level: string): string {
    return THREAT_BAR_COLORS[level] ?? 'bg-forge-muted';
  }
}
