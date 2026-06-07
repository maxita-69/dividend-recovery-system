import { Component, OnInit } from '@angular/core';
import { CommonModule, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { CalendarMonth, CalendarDay, DividendEvent, MOCK_STOCKS } from '../../models/stock.model';

@Component({
  selector: 'app-dividend-calendar',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, NgClass],
  template: `
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-dc-text">Calendario Dividendi</h1>
          <p class="text-dc-text-secondary text-sm mt-0.5">Ex-date dividendi H2 2026 - Borsa Italiana</p>
        </div>
        <div class="flex items-center gap-2">
          <button (click)="prevMonth()" class="dc-btn-secondary px-3">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
          <span class="text-lg font-semibold px-4 py-2 bg-dc-card border border-dc-border rounded-lg min-w-[140px] text-center">
            {{ currentCalendar?.monthName }} {{ currentCalendar?.year }}
          </span>
          <button (click)="nextMonth()" class="dc-btn-secondary px-3">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Calendar Grid -->
        <div class="lg:col-span-2">
          <div class="dc-card">
            <!-- Day headers -->
            <div class="grid grid-cols-7 gap-1 mb-2">
              <div *ngFor="let day of dayNames" class="text-center text-xs font-semibold text-dc-text-secondary uppercase py-2">
                {{ day }}
              </div>
            </div>
            <!-- Calendar days -->
            <div class="grid grid-cols-7 gap-1">
              <div *ngFor="let day of calendarDays" 
                   class="aspect-square p-2 rounded-lg border transition-all cursor-pointer relative"
                   [class.bg-dc-card]="!day.isToday && day.dividends.length > 0"
                   [class.border-dc-border]="!day.isToday"
                   [class.opacity-40]="day.isWeekend"
                   [ngClass]="{'bg-dc-accent/10': day.isToday, 'border-dc-accent/30': day.isToday, 'hover:bg-dc-border/30': !day.isWeekend, 'bg-dc-bg/30': day.dividends.length === 0 && !day.isToday}"
                   (click)="selectDay(day)">
                <div class="text-sm font-medium" [class.text-dc-accent]="day.isToday">{{ day.day }}</div>
                <div class="flex flex-wrap gap-0.5 mt-1" *ngIf="day.dividends.length > 0">
                  <div *ngFor="let d of day.dividends.slice(0, 4)" 
                       class="w-2 h-2 rounded-full" [style.background-color]="d.color"
                       [title]="d.ticker + ' - EUR ' + d.dividend_amount"></div>
                  <div *ngIf="day.dividends.length > 4" class="text-[8px] text-dc-text-secondary">+{{ day.dividends.length - 4 }}</div>
                </div>
              </div>
            </div>
            <!-- Legend -->
            <div class="flex flex-wrap items-center gap-4 mt-4 pt-4 border-t border-dc-border">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-dc-accent"></div>
                <span class="text-xs text-dc-text-secondary">Ex-Date oggi</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-[#f57c00]"></div>
                <span class="text-xs text-dc-text-secondary">FTSE MIB</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-[#0288d1]"></div>
                <span class="text-xs text-dc-text-secondary">MID CAP</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-dc-border border border-dc-text-secondary"></div>
                <span class="text-xs text-dc-text-secondary">Weekend</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Side Panel -->
        <div class="space-y-6">
          <!-- Selected Day Detail -->
          <div class="dc-card" *ngIf="selectedDay">
            <h3 class="dc-section-title mb-4">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
              {{ selectedDay.day }} {{ currentCalendar?.monthName }} {{ currentCalendar?.year }}
            </h3>
            <div *ngIf="selectedDay.dividends.length > 0" class="space-y-3">
              <div *ngFor="let d of selectedDay.dividends" 
                   [routerLink]="['/stocks', d.ticker]"
                   class="p-3 rounded-lg bg-dc-bg/50 hover:bg-dc-border/30 transition-colors cursor-pointer">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-lg flex items-center justify-center" [style.background-color]="d.color + '20'">
                      <span class="text-[10px] font-bold" [style.color]="d.color">{{ d.ticker.split('.')[0] }}</span>
                    </div>
                    <div>
                      <div class="text-sm font-medium">{{ d.ticker }}</div>
                      <div class="text-xs text-dc-text-secondary">{{ d.name }}</div>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-semibold text-dc-accent">EUR {{ d.dividend_amount | number:'1.4-4' }}</div>
                    <div class="text-xs text-dc-secondary">{{ d.yield_net | number:'1.2-2' }}% net</div>
                  </div>
                </div>
              </div>
            </div>
            <div *ngIf="selectedDay.dividends.length === 0" class="text-center py-6 text-dc-text-secondary text-sm">
              Nessun dividendo in questa data.
            </div>
          </div>

          <!-- List View Grouped by Month -->
          <div class="dc-card">
            <h3 class="dc-section-title mb-4">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/>
              </svg>
              Lista per Mese
            </h3>
            <div class="space-y-4 max-h-[500px] overflow-y-auto pr-1">
              <div *ngFor="let month of groupedDividends | keyvalue">
                <div class="text-xs font-semibold text-dc-accent uppercase tracking-wider mb-2">{{ month.key }}</div>
                <div class="space-y-2">
                  <div *ngFor="let d of month.value" 
                       [routerLink]="['/stocks', d.stock?.ticker]"
                       class="flex items-center justify-between p-2.5 rounded-lg bg-dc-bg/50 hover:bg-dc-border/30 transition-colors cursor-pointer">
                    <div class="flex items-center gap-2">
                      <div class="w-7 h-7 rounded-md bg-dc-accent/10 flex items-center justify-center">
                        <span class="text-dc-accent text-[9px] font-bold">{{ getTickerBase(d.stock?.ticker) }}</span>
                      </div>
                      <div>
                        <div class="text-xs font-medium">{{ d.stock?.ticker }}</div>
                        <div class="text-[10px] text-dc-text-secondary">{{ d.ex_date | date:'dd MMM' }}</div>
                      </div>
                    </div>
                    <div class="text-right">
                      <div class="text-xs font-semibold">EUR {{ d.dividend_amount | number:'1.4-4' }}</div>
                      <div class="text-[10px] text-dc-secondary">{{ d.yield_net | number:'1.2-2' }}% net</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Stats -->
          <div class="dc-card">
            <h3 class="text-sm font-semibold mb-3">Riepilogo</h3>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-dc-text-secondary">Dividendi totali H2</span>
                <span class="font-medium">{{ allDividends.length }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dc-text-secondary">FTSE MIB</span>
                <span class="font-medium">{{ ftseMibCount }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dc-text-secondary">MID CAP</span>
                <span class="font-medium">{{ midCapCount }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-dc-text-secondary">Media yield net</span>
                <span class="font-medium text-dc-secondary">{{ avgYield | number:'1.2-2' }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class DividendCalendarComponent implements OnInit {
  dayNames = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'];
  currentMonth = 6;
  currentYear = 2026;
  currentCalendar: CalendarMonth | null = null;
  calendarDays: CalendarDay[] = [];
  selectedDay: CalendarDay | null = null;
  allDividends: DividendEvent[] = [];
  groupedDividends: { [key: string]: DividendEvent[] } = {};
  ftseMibCount = 0;
  midCapCount = 0;
  avgYield = 0;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadCalendar();
    this.loadAllDividends();
  }

  loadCalendar(): void {
    this.api.getCalendar(this.currentYear, this.currentMonth).subscribe(cal => {
      this.currentCalendar = cal;
      // Pad with empty days to align with Monday start
      const firstDayOfWeek = new Date(this.currentYear, this.currentMonth - 1, 1).getDay();
      const offset = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;
      const emptyDays: CalendarDay[] = Array(offset).fill(null).map((_, i) => ({
        date: '', day: 0, isWeekend: false, isToday: false, dividends: []
      }));
      this.calendarDays = [...emptyDays, ...cal.days];
    });
  }

  loadAllDividends(): void {
    this.api.getDividends(true).subscribe(divs => {
      this.allDividends = divs;
      // Group by month
      const grouped: { [key: string]: DividendEvent[] } = {};
      divs.forEach(d => {
        const monthKey = this.getMonthName(d.ex_date);
        if (!grouped[monthKey]) grouped[monthKey] = [];
        grouped[monthKey].push(d);
      });
      this.groupedDividends = grouped;
      // Stats
      this.ftseMibCount = divs.filter(d => MOCK_STOCKS.find(s => s.id === d.stock_id)?.is_ftse_mib).length;
      this.midCapCount = divs.length - this.ftseMibCount;
      this.avgYield = divs.reduce((s, d) => s + d.yield_net, 0) / (divs.length || 1);
    });
  }

  getMonthName(dateStr: string): string {
    const monthNames = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'];
    const month = parseInt(dateStr.split('-')[1]) - 1;
    return monthNames[month] || '';
  }

  selectDay(day: CalendarDay): void {
    if (day.day === 0) return;
    this.selectedDay = day;
  }

  prevMonth(): void {
    this.currentMonth--;
    if (this.currentMonth < 1) { this.currentMonth = 12; this.currentYear--; }
    this.loadCalendar();
  }

  nextMonth(): void {
    this.currentMonth++;
    if (this.currentMonth > 12) { this.currentMonth = 1; this.currentYear++; }
    this.loadCalendar();
  }

  getTickerBase(ticker?: string): string {
    return ticker?.split('.')[0] || '';
  }
}
