import { Component, OnInit } from '@angular/core';
import { CommonModule, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { ApiService } from '../../services/api.service';
import { ChartService } from '../../services/chart.service';
import { CostBreakdownComponent } from '../shared/cost-breakdown/cost-breakdown.component';
import { SimulationRequest, SimulationResult, Stock, MOCK_STOCKS, COST_CONSTANTS } from '../../models/stock.model';

@Component({
  selector: 'app-simulator',
  standalone: true,
  imports: [CommonModule, FormsModule, BaseChartDirective, CostBreakdownComponent, NgClass],
  template: `
    <div class="space-y-6">
      <!-- Header -->
      <div>
        <h1 class="text-2xl font-bold text-dc-text">Simulatore Profitto</h1>
        <p class="text-dc-text-secondary text-sm mt-0.5">Calcola il profitto netto della strategia dividend capture</p>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-5 gap-6">
        <!-- Input Panel -->
        <div class="xl:col-span-2 space-y-6">
          <div class="dc-card">
            <h2 class="dc-section-title mb-5">
              <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
              </svg>
              Parametri Simulazione
            </h2>
            <div class="space-y-5">
              <!-- Stock Selector -->
              <div>
                <label class="block text-sm font-medium text-dc-text mb-2">Seleziona Stock</label>
                <select [(ngModel)]="request.ticker" (change)="onStockChange()" class="dc-select">
                  <option *ngFor="let s of stocks" [value]="s.ticker">{{ s.ticker }} - {{ s.name }} (EUR {{ s.price | number:'1.2-2' }})</option>
                </select>
              </div>

              <!-- Shares Input -->
              <div>
                <label class="block text-sm font-medium text-dc-text mb-2">Quantita Azioni</label>
                <div class="flex items-center gap-2">
                  <button (click)="adjustShares(-100)" class="dc-btn-secondary px-3 py-2.5 text-lg">-</button>
                  <input type="number" [(ngModel)]="request.shares" (change)="onSharesChange()" 
                         class="dc-input text-center text-lg font-semibold flex-1" min="1" step="100">
                  <button (click)="adjustShares(100)" class="dc-btn-secondary px-3 py-2.5 text-lg">+</button>
                </div>
                <div class="flex gap-2 mt-2">
                  <button *ngFor="let preset of sharePresets" (click)="request.shares = preset; onSharesChange()"
                          class="px-2.5 py-1 rounded-md text-xs font-medium transition-all"
                          [class.bg-dc-accent]="request.shares === preset"
                          [class.text-white]="request.shares === preset"
                          [class.bg-dc-border]="request.shares !== preset"
                          [class.text-dc-text-secondary]="request.shares !== preset">
                    {{ preset }}
                  </button>
                </div>
              </div>

              <!-- Entry Timing -->
              <div>
                <label class="block text-sm font-medium text-dc-text mb-2">Timing Ingresso</label>
                <div class="grid grid-cols-3 gap-2">
                  <button *ngFor="let t of entryTimings" 
                          (click)="request.entry_timing = t.value"
                          class="p-3 rounded-lg border text-xs font-medium text-center transition-all"
                          [class.border-dc-accent]="request.entry_timing === t.value"
                          [ngClass]="{'bg-dc-accent/10': request.entry_timing === t.value}"
                          [class.text-dc-accent]="request.entry_timing === t.value"
                          [class.border-dc-border]="request.entry_timing !== t.value"
                          [class.bg-dc-card]="request.entry_timing !== t.value"
                          [class.text-dc-text-secondary]="request.entry_timing !== t.value">
                    {{ t.label }}
                  </button>
                </div>
              </div>

              <!-- Exit Timing -->
              <div>
                <label class="block text-sm font-medium text-dc-text mb-2">Timing Uscita</label>
                <div class="grid grid-cols-3 gap-2">
                  <button *ngFor="let t of exitTimings" 
                          (click)="request.exit_timing = t.value"
                          class="p-3 rounded-lg border text-xs font-medium text-center transition-all"
                          [class.border-dc-accent]="request.exit_timing === t.value"
                          [ngClass]="{'bg-dc-accent/10': request.exit_timing === t.value}"
                          [class.text-dc-accent]="request.exit_timing === t.value"
                          [class.border-dc-border]="request.exit_timing !== t.value"
                          [class.bg-dc-card]="request.exit_timing !== t.value"
                          [class.text-dc-text-secondary]="request.exit_timing !== t.value">
                    {{ t.label }}
                  </button>
                </div>
              </div>

              <!-- Price Drop Slider -->
              <div>
                <label class="block text-sm font-medium text-dc-text mb-2">
                  Drop Prezzo Previsto (% del dividendo)
                </label>
                <div class="flex items-center gap-4">
                  <input type="range" [(ngModel)]="request.expected_price_drop_pct" 
                         min="0" max="120" step="5"
                         class="flex-1 h-2 bg-dc-border rounded-full appearance-none cursor-pointer accent-dc-accent">
                  <span class="text-lg font-bold text-dc-accent w-14 text-right">{{ request.expected_price_drop_pct }}%</span>
                </div>
                <div class="flex justify-between text-xs text-dc-text-secondary mt-1">
                  <span>0%</span>
                  <span>60%</span>
                  <span>120%</span>
                </div>
              </div>

              <!-- Run Button -->
              <button (click)="runSimulation()" class="dc-btn-primary w-full justify-center py-3 text-base">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
                Calcola Simulazione
              </button>
            </div>
          </div>

          <!-- Stock Info Card -->
          <div class="dc-card" *ngIf="selectedStock">
            <h3 class="text-sm font-semibold mb-3">Info Stock Selezionato</h3>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-dc-text-secondary">Prezzo Corrente</span>
                <span class="font-medium">EUR {{ selectedStock.price | number:'1.2-2' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-dc-text-secondary">Cap. di Mercato</span>
                <span class="font-medium">EUR {{ selectedStock.market_cap | number:'1.0-0' }}M</span>
              </div>
              <div class="flex justify-between">
                <span class="text-dc-text-secondary">Tobin Tax</span>
                <span class="font-medium" [class.text-dc-accent]="selectedStock.market_cap >= 500" [class.text-dc-danger]="selectedStock.market_cap < 500">
                  {{ selectedStock.market_cap >= 500 ? '0.20% si' : '0% no' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-dc-text-secondary">Commissione</span>
                <span class="font-medium">0.19% (min EUR 2.95 - max EUR 19)</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Results Panel -->
        <div class="xl:col-span-3 space-y-6" *ngIf="result">
          <!-- Main Result Cards -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="dc-card border-dc-accent/30 bg-dc-accent/5">
              <div class="dc-kpi-label">Capitale Investito</div>
              <div class="dc-kpi-value text-dc-text mt-1">EUR {{ result.capital_invested | number:'1.2-2' }}</div>
              <div class="text-xs text-dc-text-secondary mt-1">{{ result.shares }} azioni a EUR {{ result.entry_price | number:'1.2-2' }}</div>
            </div>
            <div class="dc-card" [ngClass]="{'border-dc-accent/30': result.profit_net > 0, 'border-dc-danger/30': result.profit_net < 0, 'bg-dc-accent/5': result.profit_net > 0, 'bg-dc-danger/5': result.profit_net < 0}">
              <div class="dc-kpi-label">Profitto Netto</div>
              <div class="dc-kpi-value mt-1" [class.text-dc-accent]="result.profit_net > 0" [class.text-dc-danger]="result.profit_net < 0">
                EUR {{ result.profit_net | number:'1.2-2' }}
              </div>
              <div class="text-xs mt-1" [class.text-dc-accent]="result.profit_net > 0" [class.text-dc-danger]="result.profit_net < 0">
                {{ result.profit_net > 0 ? 'Profitto' : 'Perdita' }} dopo tutti i costi
              </div>
            </div>
            <div class="dc-card border-dc-secondary/30 bg-dc-secondary/5">
              <div class="dc-kpi-label">Return on Capital</div>
              <div class="dc-kpi-value text-dc-secondary mt-1">{{ result.return_on_capital | number:'1.2-2' }}%</div>
              <div class="text-xs text-dc-text-secondary mt-1">Annualizzato: ~{{ result.return_on_capital * 6 | number:'1.2-2' }}%</div>
            </div>
          </div>

          <!-- Dividend Flow -->
          <div class="dc-card">
            <h3 class="dc-section-title mb-4">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Flusso Dividendo
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
              <div class="text-center p-4 rounded-xl bg-dc-bg/50">
                <div class="text-xs text-dc-text-secondary mb-1">Dividendo per Azione</div>
                <div class="text-2xl font-bold text-dc-accent">EUR {{ result.dividend_per_share | number:'1.4-4' }}</div>
              </div>
              <div class="flex items-center justify-center">
                <svg class="w-8 h-8 text-dc-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
                </svg>
              </div>
              <div class="text-center p-4 rounded-xl bg-dc-bg/50">
                <div class="text-xs text-dc-text-secondary mb-1">Dividendo Lordo Totale</div>
                <div class="text-2xl font-bold text-dc-accent">EUR {{ result.dividend_gross | number:'1.2-2' }}</div>
              </div>
            </div>
            <!-- Tax bar -->
            <div class="mt-4">
              <div class="flex justify-between text-xs mb-2">
                <span class="text-dc-text-secondary">Tassa 26%: EUR {{ result.tax_26pct | number:'1.2-2' }}</span>
                <span class="text-dc-secondary font-semibold">Netto: EUR {{ result.dividend_net | number:'1.2-2' }}</span>
              </div>
              <div class="dc-progress-bar h-4">
                <div class="dc-progress-bar-fill bg-dc-accent" [style.width.%]="74">
                  <span class="text-[10px] text-white font-medium px-1">Lordo</span>
                </div>
              </div>
              <div class="dc-progress-bar h-4 mt-1">
                <div class="dc-progress-bar-fill bg-dc-secondary" [style.width.%]="(result.dividend_net / result.dividend_gross) * 74">
                  <span class="text-[10px] text-white font-medium px-1">Netto (74%)</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Cost Breakdown -->
          <app-cost-breakdown
            [commissionBuy]="result.commission_buy"
            [commissionSell]="result.commission_sell"
            [tobinTax]="result.tobin_tax"
            [tax26]="result.tax_26pct"
            [totalCosts]="result.total_costs">
          </app-cost-breakdown>

          <!-- Cost Comparison Chart -->
          <div class="dc-card">
            <h3 class="dc-section-title mb-4">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
              Confronto Costi per Dimensione Posizione
            </h3>
            <div class="h-64">
              <canvas baseChart
                [data]="comparisonChartData"
                [options]="comparisonChartOptions"
                [type]="'bar'">
              </canvas>
            </div>
          </div>

          <!-- Scenario Details -->
          <div class="dc-card">
            <h3 class="dc-section-title mb-4">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
              </svg>
              Dettaglio Scenario
            </h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="p-3 rounded-lg bg-dc-bg/50">
                <div class="text-xs text-dc-text-secondary">Data Ingresso</div>
                <div class="text-sm font-semibold">{{ result.entry_date | date:'dd MMM yyyy' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dc-bg/50">
                <div class="text-xs text-dc-text-secondary">Data Ex-Dividendo</div>
                <div class="text-sm font-semibold">{{ result.ex_date | date:'dd MMM yyyy' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dc-bg/50">
                <div class="text-xs text-dc-text-secondary">Data Uscita</div>
                <div class="text-sm font-semibold">{{ result.exit_date | date:'dd MMM yyyy' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dc-bg/50">
                <div class="text-xs text-dc-text-secondary">Durata Operazione</div>
                <div class="text-sm font-semibold">{{ getDaysDiff(result.entry_date, result.exit_date) }} giorni</div>
              </div>
              <div class="p-3 rounded-lg bg-dc-bg/50">
                <div class="text-xs text-dc-text-secondary">Prezzo Ingresso</div>
                <div class="text-sm font-semibold">EUR {{ result.entry_price | number:'1.2-2' }}</div>
              </div>
              <div class="p-3 rounded-lg bg-dc-bg/50">
                <div class="text-xs text-dc-text-secondary">Prezzo Uscita (stim.)</div>
                <div class="text-sm font-semibold" [class.text-dc-danger]="result.exit_price < result.entry_price">
                  EUR {{ result.exit_price | number:'1.2-2' }}
                </div>
              </div>
              <div class="p-3 rounded-lg bg-dc-bg/50">
                <div class="text-xs text-dc-text-secondary">Drop Prezzo</div>
                <div class="text-sm font-semibold text-dc-danger">{{ result.price_drop_actual | number:'1.2-2' }}%</div>
              </div>
              <div class="p-3 rounded-lg bg-dc-bg/50">
                <div class="text-xs text-dc-text-secondary">Costi Totali</div>
                <div class="text-sm font-semibold text-dc-danger">EUR {{ result.total_costs | number:'1.2-2' }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div class="xl:col-span-3 flex items-center justify-center" *ngIf="!result">
          <div class="dc-card text-center py-16">
            <div class="w-20 h-20 rounded-full bg-dc-accent/10 flex items-center justify-center mx-auto mb-4">
              <svg class="w-10 h-10 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
              </svg>
            </div>
            <h3 class="text-lg font-semibold text-dc-text mb-2">Configura la Simulazione</h3>
            <p class="text-dc-text-secondary text-sm max-w-sm mx-auto">
              Seleziona uno stock, imposta il numero di azioni e scegli i timing di ingresso/uscita per calcolare il profitto netto stimato.
            </p>
          </div>
        </div>
      </div>
    </div>
  `
})
export class SimulatorComponent implements OnInit {
  stocks = MOCK_STOCKS;
  selectedStock: Stock | null = null;
  sharePresets = [100, 500, 1000, 5000, 10000];

  entryTimings = [
    { label: '3 giorni prima', value: '3_days_before' as const },
    { label: '1 giorno prima', value: '1_day_before' as const },
    { label: 'Chiusura giorno prima', value: 'day_before_close' as const },
  ];

  exitTimings = [
    { label: 'Apertura ex-date', value: 'ex_date_open' as const },
    { label: 'Chiusura ex-date', value: 'ex_date_close' as const },
    { label: '1 giorno dopo', value: '1_day_after' as const },
    { label: '3 giorni dopo', value: '3_days_after' as const },
    { label: '1 settimana dopo', value: '1_week_after' as const },
  ];

  request: SimulationRequest = {
    ticker: 'ENAV.MI',
    shares: 1000,
    entry_timing: '1_day_before',
    exit_timing: 'ex_date_open',
    expected_price_drop_pct: 80,
  };

  result: SimulationResult | null = null;

  // Comparison chart
  comparisonChartData: ChartData<'bar'> = { labels: [], datasets: [] };
  comparisonChartOptions: ChartConfiguration<'bar'>['options'] = {};

  constructor(private api: ApiService, private chartService: ChartService) {}

  ngOnInit(): void {
    this.onStockChange();
    // Auto-run simulation on load
    this.runSimulation();
  }

  onStockChange(): void {
    this.selectedStock = this.stocks.find(s => s.ticker === this.request.ticker) || null;
  }

  onSharesChange(): void {
    this.request.shares = Math.max(1, Math.round(this.request.shares / 1) * 1);
  }

  adjustShares(delta: number): void {
    this.request.shares = Math.max(1, this.request.shares + delta);
  }

  runSimulation(): void {
    this.api.runSimulation(this.request).subscribe(result => {
      this.result = result;
      this.updateComparisonChart();
    });
  }

  updateComparisonChart(): void {
    const sizes = [100, 500, 1000, 5000, 10000];
    const labels = sizes.map(s => s.toLocaleString());

    // Calculate costs for each size
    const commissionData = sizes.map(s => {
      const cap = (this.selectedStock?.price || 7) * s;
      const comm = Math.min(19, Math.max(2.95, cap * 0.0019));
      return Math.round(comm * 2 * 100) / 100; // buy + sell
    });

    const tobinData = sizes.map(s => {
      const cap = (this.selectedStock?.price || 7) * s;
      return (this.selectedStock?.market_cap || 600) >= 500 ? Math.round(cap * 0.002 * 100) / 100 : 0;
    });

    const taxData = sizes.map(s => {
      const divPerShare = this.result?.dividend_per_share || 0.20;
      return Math.round(divPerShare * s * 0.26 * 100) / 100;
    });

    this.comparisonChartData = {
      labels,
      datasets: [
        {
          label: 'Commissioni',
          data: commissionData,
          backgroundColor: '#f57c00',
          borderRadius: 4,
        },
        {
          label: 'Tobin Tax',
          data: tobinData,
          backgroundColor: '#d32f2f',
          borderRadius: 4,
        },
        {
          label: 'Tassa 26%',
          data: taxData,
          backgroundColor: '#7c3aed',
          borderRadius: 4,
        }
      ]
    };

    this.comparisonChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#9ca3af', font: { family: 'Inter', size: 11 }, usePointStyle: true }
        },
        tooltip: {
          backgroundColor: '#111827',
          titleColor: '#f3f4f6',
          bodyColor: '#9ca3af',
          borderColor: '#1f2937',
          borderWidth: 1,
          cornerRadius: 8,
          callbacks: {
            title: (items) => `${items[0].label} azioni`,
            footer: (items) => {
              const total = items.reduce((s, i) => s + (i.parsed.y ?? 0), 0);
              return `Totale: EUR ${total.toFixed(2)}`;
            }
          }
        }
      },
      scales: {
        x: {
          stacked: true,
          grid: { color: '#1f2937' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 } },
          border: { display: false }
        },
        y: {
          stacked: true,
          grid: { color: '#1f2937' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 } },
          border: { display: false }
        }
      }
    };
  }

  getDaysDiff(date1: string, date2: string): number {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    return Math.ceil(Math.abs(d2.getTime() - d1.getTime()) / (1000 * 60 * 60 * 24));
  }
}
