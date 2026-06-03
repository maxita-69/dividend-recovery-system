import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { ApiService } from '../../services/api.service';
import { DataService } from '../../services/data.service';
import { ChartService } from '../../services/chart.service';
import { KpiCardComponent } from '../shared/kpi-card/kpi-card.component';
import { YieldBarComponent } from '../shared/yield-bar/yield-bar.component';
import { RecommendationBadgeComponent } from '../shared/recommendation-badge/recommendation-badge.component';
import { Opportunity, MLPrediction, DividendEvent, Stock, MOCK_STOCKS, enrichOpportunity } from '../../models/stock.model';
import { Observable, combineLatest, map } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule, FormsModule, RouterLink, BaseChartDirective,
    KpiCardComponent, YieldBarComponent, RecommendationBadgeComponent
  ],
  template: `
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-dc-text">Dashboard</h1>
          <p class="text-dc-text-secondary text-sm mt-0.5">Panoramica strategia dividend capture</p>
        </div>
        <div class="text-right">
          <p class="text-xs text-dc-text-secondary">Ultimo aggiornamento</p>
          <p class="text-sm text-dc-text font-medium">{{ now | date:'dd/MM/yyyy HH:mm' }}</p>
        </div>
      </div>

      <!-- KPI Row -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <app-kpi-card 
          label="Opportunita Totali" 
          [value]="(opportunities$ | async)?.length || 0" 
          [change]="12.5"
          icon="OP"
          [isPositive]="true"
          subtitle="H2 2026 dividendi attesi">
        </app-kpi-card>
        <app-kpi-card 
          label="Rendimento Netto Medio" 
          [value]="avgYieldNet + '%'" 
          [change]="2.3"
          icon="Y"
          [isPositive]="true"
          subtitle="Dopo tasse e commissioni">
        </app-kpi-card>
        <app-kpi-card 
          label="Migliore Opportunita" 
          [value]="bestOpportunity?.stock?.ticker || 'N/A'" 
          [change]="bestOpportunity?.expected_return || 0"
          changeLabel="% return"
          icon="★"
          [isPositive]="true"
          subtitle="Raccomandazione: {{ bestOpportunity?.prediction?.recommendation || 'N/A' }}">
        </app-kpi-card>
        <app-kpi-card 
          label="Prossimo Ex-Date" 
          [value]="daysToNextExDate + ' giorni'" 
          icon="📅"
          [isPositive]="daysToNextExDate <= 7"
          subtitle="{{ nextExDate | date:'dd MMM yyyy' }} - {{ nextExDateStocks }}">
        </app-kpi-card>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <!-- Top Opportunities Table -->
        <div class="xl:col-span-2 space-y-6">
          <div class="dc-card">
            <div class="flex items-center justify-between mb-4">
              <h2 class="dc-section-title">
                <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                </svg>
                Top 5 Opportunita
              </h2>
              <a routerLink="/predictions" class="text-dc-accent text-sm hover:underline">Vedi tutte</a>
            </div>
            <div class="overflow-x-auto">
              <table class="dc-table">
                <thead>
                  <tr>
                    <th class="cursor-pointer" (click)="sortTable('ticker')">Ticker</th>
                    <th class="cursor-pointer" (click)="sortTable('ex_date')">Ex-Date</th>
                    <th class="cursor-pointer" (click)="sortTable('yield_net')">Yield Net</th>
                    <th class="cursor-pointer" (click)="sortTable('predicted_drop')">Drop Prev.</th>
                    <th>ML Rec.</th>
                    <th class="cursor-pointer" (click)="sortTable('expected_profit')">Profit Att.</th>
                  </tr>
                </thead>
                <tbody>
                  <tr *ngFor="let opp of sortedOpportunities" class="cursor-pointer hover:bg-dc-border/40 transition-colors"
                      [routerLink]="['/stocks', opp.stock?.ticker]">
                    <td>
                      <div class="flex items-center gap-2">
                        <div class="w-8 h-8 rounded-lg bg-dc-accent/10 flex items-center justify-center">
                          <span class="text-dc-accent text-xs font-bold">{{ getTickerBase(opp.stock?.ticker) }}</span>
                        </div>
                        <div>
                          <div class="font-medium text-sm">{{ opp.stock?.ticker }}</div>
                          <div class="text-xs text-dc-text-secondary">{{ opp.stock?.name }}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span class="text-sm">{{ opp.dividend_event?.ex_date | date:'dd MMM' }}</span>
                    </td>
                    <td>
                      <span class="text-dc-accent font-semibold">{{ opp.dividend_event?.yield_net | number:'1.2-2' }}%</span>
                    </td>
                    <td>
                      <span class="text-dc-warning">{{ opp.prediction?.predicted_drop_pct || 0 }}%</span>
                    </td>
                    <td>
                      <app-recommendation-badge [recommendation]="opp.prediction?.recommendation || 'HOLD'"></app-recommendation-badge>
                    </td>
                    <td>
                      <span class="text-dc-accent font-semibold">EUR {{ opp.prediction?.expected_profit_net | number:'1.2-2' }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Monthly Dividend Distribution Chart -->
          <div class="dc-card">
            <h2 class="dc-section-title mb-4">
              <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
              Distribuzione Mensile Dividendi
            </h2>
            <div class="h-64">
              <canvas baseChart
                [data]="monthlyChartData"
                [options]="monthlyChartOptions"
                [type]="'bar'">
              </canvas>
            </div>
          </div>
        </div>

        <!-- Right Column -->
        <div class="space-y-6">
          <!-- Quick Simulator Widget -->
          <div class="dc-card">
            <h2 class="dc-section-title mb-4">
              <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
              </svg>
              Simulatore Rapido
            </h2>
            <div class="space-y-4">
              <div>
                <label class="block text-xs text-dc-text-secondary mb-1.5">Seleziona Stock</label>
                <select [(ngModel)]="quickTicker" class="dc-select">
                  <option *ngFor="let s of stocks" [value]="s.ticker">{{ s.ticker }} - {{ s.name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-xs text-dc-text-secondary mb-1.5">Quantita Azioni</label>
                <div class="flex items-center gap-2">
                  <button (click)="decrementQuickShares()" class="dc-btn-secondary px-3 py-2">-</button>
                  <input type="number" [(ngModel)]="quickShares" class="dc-input text-center flex-1" min="100" step="100">
                  <button (click)="incrementQuickShares()" class="dc-btn-secondary px-3 py-2">+</button>
                </div>
              </div>
              <button (click)="runQuickSim()" class="dc-btn-primary w-full justify-center">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
                Calcola Profitto
              </button>
              <div *ngIf="quickResult" class="mt-4 p-4 rounded-xl bg-dc-bg border border-dc-border space-y-3">
                <div class="flex justify-between">
                  <span class="text-xs text-dc-text-secondary">Capitale Investito</span>
                  <span class="text-sm font-semibold">EUR {{ quickResult.capital_invested | number:'1.2-2' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-xs text-dc-text-secondary">Dividendo Lordo</span>
                  <span class="text-sm text-dc-accent">EUR {{ quickResult.dividend_gross | number:'1.2-2' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-xs text-dc-text-secondary">Dividendo Netto</span>
                  <span class="text-sm text-dc-secondary">EUR {{ quickResult.dividend_net | number:'1.2-2' }}</span>
                </div>
                <div class="h-px bg-dc-border"></div>
                <div class="flex justify-between items-center">
                  <span class="text-sm font-semibold">Profitto Netto</span>
                  <span class="text-lg font-bold" [class.text-dc-accent]="quickResult.profit_net > 0" [class.text-dc-danger]="quickResult.profit_net < 0">
                    EUR {{ quickResult.profit_net | number:'1.2-2' }}
                  </span>
                </div>
                <div class="flex justify-between">
                  <span class="text-xs text-dc-text-secondary">Return on Capital</span>
                  <span class="text-sm font-bold" [class.text-dc-accent]="quickResult.return_on_capital > 0" [class.text-dc-danger]="quickResult.return_on_capital < 0">
                    {{ quickResult.return_on_capital | number:'1.2-2' }}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Upcoming Ex-Dates -->
          <div class="dc-card">
            <h2 class="dc-section-title mb-4">
              <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Prossimi Ex-Date
            </h2>
            <div class="space-y-3">
              <div *ngFor="let div of upcomingDividends.slice(0, 6)" 
                   class="flex items-center justify-between p-3 rounded-lg bg-dc-bg/50 hover:bg-dc-border/30 transition-colors cursor-pointer"
                   [routerLink]="['/stocks', div.stock?.ticker]">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-lg bg-dc-accent/10 flex items-center justify-center">
                    <span class="text-dc-accent text-[10px] font-bold">{{ getTickerBase(div.stock?.ticker) }}</span>
                  </div>
                  <div>
                    <div class="text-sm font-medium">{{ div.stock?.ticker }}</div>
                    <div class="text-xs text-dc-text-secondary">{{ div.stock?.name }}</div>
                  </div>
                </div>
                <div class="text-right">
                  <div class="text-sm font-semibold text-dc-accent">{{ div.ex_date | date:'dd MMM' }}</div>
                  <div class="text-xs text-dc-text-secondary">{{ div.yield_net | number:'1.2-2' }}% net</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Market Summary -->
          <div class="dc-card">
            <h2 class="dc-section-title mb-4">
              <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
              Riepilogo Mercato
            </h2>
            <div class="space-y-3">
              <div class="flex justify-between items-center p-2 rounded-lg bg-dc-bg/50">
                <span class="text-sm text-dc-text-secondary">FTSE MIB</span>
                <span class="text-sm font-semibold text-dc-accent">34,562.80 +0.45%</span>
              </div>
              <div class="flex justify-between items-center p-2 rounded-lg bg-dc-bg/50">
                <span class="text-sm text-dc-text-secondary">Dividendi H2 2026</span>
                <span class="text-sm font-semibold">17 eventi</span>
              </div>
              <div class="flex justify-between items-center p-2 rounded-lg bg-dc-bg/50">
                <span class="text-sm text-dc-text-secondary">Media Yield Net</span>
                <span class="text-sm font-semibold text-dc-secondary">3.24%</span>
              </div>
              <div class="flex justify-between items-center p-2 rounded-lg bg-dc-bg/50">
                <span class="text-sm text-dc-text-secondary">Raccomandazioni Positive</span>
                <span class="text-sm font-semibold text-dc-accent">3/6</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class DashboardComponent implements OnInit {
  now = new Date();
  stocks = MOCK_STOCKS;
  opportunities$: Observable<Opportunity[]>;
  opportunities: Opportunity[] = [];
  sortedOpportunities: Opportunity[] = [];
  predictions: MLPrediction[] = [];
  upcomingDividends: DividendEvent[] = [];
  avgYieldNet = 3.24;
  bestOpportunity: Opportunity | null = null;
  daysToNextExDate = 0;
  nextExDate = '';
  nextExDateStocks = '';

  // Quick simulator
  quickTicker = 'ENAV.MI';
  quickShares = 1000;
  quickResult: any = null;

  // Monthly chart
  monthlyChartData: ChartData<'bar'> = { labels: [], datasets: [] };
  monthlyChartOptions: ChartConfiguration<'bar'>['options'] = {};

  sortColumn = 'rank';
  sortAsc = true;

  constructor(
    private api: ApiService,
    private data: DataService,
    private chart: ChartService
  ) {
    this.opportunities$ = this.data.getOpportunities();
  }

  ngOnInit(): void {
    this.loadData();
    this.initMonthlyChart();
  }

  loadData(): void {
    this.api.getOpportunities().subscribe(opps => {
      this.opportunities = opps;
      this.sortedOpportunities = [...opps];
      this.bestOpportunity = opps.length > 0 ? opps[0] : null;
    });

    this.api.getPredictions().subscribe(preds => {
      this.predictions = preds;
    });

    this.api.getUpcomingDividends().subscribe(divs => {
      this.upcomingDividends = divs;
      if (divs.length > 0) {
        const sorted = [...divs].sort((a, b) => a.ex_date.localeCompare(b.ex_date));
        const next = sorted[0];
        this.nextExDate = next.ex_date;
        const diff = new Date(next.ex_date).getTime() - new Date().getTime();
        this.daysToNextExDate = Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
        const sameDay = sorted.filter(d => d.ex_date === next.ex_date);
        this.nextExDateStocks = sameDay.map(d => d.stock?.ticker?.split('.')[0]).join(', ') || 'N/A';
      }
    });
  }

  initMonthlyChart(): void {
    const labels = ['Giu 2026', 'Lug 2026', 'Set 2026'];
    const dividendCounts = [14, 2, 1];
    const avgYields = [3.5, 4.5, 1.5];

    this.monthlyChartData = {
      labels,
      datasets: [
        {
          label: 'Numero Dividendi',
          data: dividendCounts,
          backgroundColor: '#4caf50',
          borderRadius: 6,
          yAxisID: 'y'
        },
        {
          label: 'Yield Net Medio (%)',
          data: avgYields,
          backgroundColor: '#2e7d32',
          borderRadius: 6,
          yAxisID: 'y1'
        }
      ]
    };

    this.monthlyChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#9ca3af', font: { family: 'Inter', size: 11 }, usePointStyle: true }
        }
      },
      scales: {
        x: {
          grid: { color: '#1f2937' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 } },
          border: { display: false }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          grid: { color: '#1f2937' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 }, stepSize: 5 },
          border: { display: false }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: { display: false },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 } },
          border: { display: false }
        }
      }
    };
  }

  sortTable(column: string): void {
    if (this.sortColumn === column) {
      this.sortAsc = !this.sortAsc;
    } else {
      this.sortColumn = column;
      this.sortAsc = true;
    }

    this.sortedOpportunities = [...this.sortedOpportunities].sort((a, b) => {
      let valA: any, valB: any;
      switch (column) {
        case 'ticker': valA = a.stock?.ticker || ''; valB = b.stock?.ticker || ''; break;
        case 'ex_date': valA = a.dividend_event?.ex_date || ''; valB = b.dividend_event?.ex_date || ''; break;
        case 'yield_net': valA = a.dividend_event?.yield_net || 0; valB = b.dividend_event?.yield_net || 0; break;
        case 'predicted_drop': valA = a.prediction?.predicted_drop_pct || 0; valB = b.prediction?.predicted_drop_pct || 0; break;
        case 'expected_profit': valA = a.prediction?.expected_profit_net || 0; valB = b.prediction?.expected_profit_net || 0; break;
        default: valA = a.rank; valB = b.rank;
      }
      if (valA < valB) return this.sortAsc ? -1 : 1;
      if (valA > valB) return this.sortAsc ? 1 : -1;
      return 0;
    });
  }

  runQuickSim(): void {
    this.api.runSimulation({
      ticker: this.quickTicker,
      shares: this.quickShares,
      entry_timing: '1_day_before',
      exit_timing: 'ex_date_open',
      expected_price_drop_pct: 80
    }).subscribe(result => {
      this.quickResult = result;
    });
  }

  incrementQuickShares(): void {
    this.quickShares += 100;
  }

  decrementQuickShares(): void {
    this.quickShares = Math.max(100, this.quickShares - 100);
  }

  getTickerBase(ticker?: string): string {
    return ticker?.split('.')[0] || '';
  }

  closeSidebar(): void {
    // Close sidebar on mobile after navigation
  }
}
