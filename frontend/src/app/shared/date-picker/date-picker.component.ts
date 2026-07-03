/* ==================================================================
   DATE PICKER LOGIC
   ================================================================== */

import {
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  computed,
  signal,
} from '@angular/core';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import {
  phosphorXCircleBold,
  phosphorCaretDownBold,
  phosphorCaretLeftBold,
  phosphorCaretRightBold,
  phosphorCalendarDotsBold,
} from '@ng-icons/phosphor-icons/bold';

// Constants for month names
const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

@Component({
  selector: 'app-date-picker',
  imports: [NgIconComponent],
  providers: [
    provideIcons({
      phosphorXCircleBold,
      phosphorCaretDownBold,
      phosphorCaretLeftBold,
      phosphorCaretRightBold,
      phosphorCalendarDotsBold,
    }),
  ],
  templateUrl: './date-picker.component.html',
})
export class DatePickerComponent implements OnChanges {
  @Input() value = '';
  @Output() valueChange = new EventEmitter<string>();
  @Input() min = '';

  readonly DAY_HEADERS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

  open = signal(false);
  viewYear = signal(new Date().getFullYear());
  viewMonth = signal(new Date().getMonth());

  // Returns formatted label for the current month and year
  readonly monthLabel = computed(() => `${MONTHS[this.viewMonth()]} ${this.viewYear()}`);

  // Computes the array of days to display in the calendar grid
  readonly calendarDays = computed((): (Date | null)[] => {
    const year = this.viewYear();
    const month = this.viewMonth();
    const startPad = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const days: (Date | null)[] = Array(startPad).fill(null);
    for (let d = 1; d <= daysInMonth; d++) {
      days.push(new Date(year, month, d));
    }
    return days;
  });

  // Returns the date value formatted as MM/DD/YYYY
  get displayValue(): string {
    if (!this.value) return '';
    const [y, m, d] = this.value.split('-');
    return `${m}/${d}/${y}`;
  }

  constructor(private readonly el: ElementRef) {}

  // Function to update internal calendar view
  ngOnChanges(changes: SimpleChanges): void {
    const v = changes['value']?.currentValue as string | undefined;
    if (v) {
      const [y, m] = v.split('-');
      this.viewYear.set(+y);
      this.viewMonth.set(+m - 1);
    }
  }

  // Function to close date picker dropdown when clicking anywhere outside the component
  @HostListener('document:click', ['$event'])
  onOutsideClick(e: MouseEvent): void {
    if (!this.el.nativeElement.contains(e.target as Node)) {
      this.open.set(false);
    }
  }

  // Function to toggle visibility of the calendar dropdown
  toggle(): void {
    this.open.update((v) => !v);
  }

  // Function to reset selected date
  clearDate(e: MouseEvent): void {
    e.stopPropagation();
    this.valueChange.emit('');
  }

  // Function to navigate calendar view to the previous month
  prevMonth(): void {
    if (this.viewMonth() === 0) {
      this.viewYear.update((y) => y - 1);
      this.viewMonth.set(11);
    } else {
      this.viewMonth.update((m) => m - 1);
    }
  }

  // Function to navigate calendar view to the next month
  nextMonth(): void {
    if (this.viewMonth() === 11) {
      this.viewYear.update((y) => y + 1);
      this.viewMonth.set(0);
    } else {
      this.viewMonth.update((m) => m + 1);
    }
  }

  // Function to select a specific day & converts it to ISO format
  selectDay(day: Date): void {
    if (this.isDisabled(day)) return;
    const iso = [
      day.getFullYear(),
      String(day.getMonth() + 1).padStart(2, '0'),
      String(day.getDate()).padStart(2, '0'),
    ].join('-');
    this.valueChange.emit(iso);
    this.open.set(false);
  }

  // Function to check if a specific date should be disabled
  isDisabled(day: Date): boolean {
    if (!this.min) return false;
    const [y, m, d] = this.min.split('-').map(Number);
    return day < new Date(y, m - 1, d);
  }

  // Function to determine if a specific day is currently selected by the user
  isSelected(day: Date): boolean {
    if (!this.value) return false;
    const [y, m, d] = this.value.split('-').map(Number);
    return day.getFullYear() === y && day.getMonth() === m - 1 && day.getDate() === d;
  }

  // Function to check if a specific date corresponds to the current real current date
  isToday(day: Date): boolean {
    const t = new Date();
    return (
      day.getFullYear() === t.getFullYear() &&
      day.getMonth() === t.getMonth() &&
      day.getDate() === t.getDate()
    );
  }

  // Function to return appropriate CSS classes for a day cell based on its state (disabled, selected, today)
  dayClass(day: Date): string {
    if (this.isDisabled(day)) return 'opacity-25 pointer-events-none text-forge-text';
    if (this.isSelected(day))
      return 'bg-amber-500/15 text-amber-400 border border-amber-500/40 cursor-pointer';
    if (this.isToday(day))
      return 'border border-forge-primary/30 text-forge-primary hover:bg-forge-primary/10 cursor-pointer';
    return 'text-forge-text hover:bg-white/5 cursor-pointer';
  }
}
