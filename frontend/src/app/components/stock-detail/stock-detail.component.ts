import { Component, OnInit, Input } from '@angular/core';
import { CommonModule, NgClass } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { ApiService } from '../../services/api.service';
import { ChartService } from '../../services/chart.service';
import { YieldBarComponent } from '../shared/yield-bar/yield-bar.component';
import { RecommendationBadgeComponent } from '../shared/recommendation-badge/recommendation-badge.component';
import { Stock, StockPrice, TechnicalIndicator, DividendEvent, MLPrediction, MOCK_STOCKS, MOCK_DIVIDENDS } from '../../models/stock.model';

@Component({
  selector: 'app-stock-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, BaseChartDirective, YieldBarComponent, RecommendationBadgeComponent, NgClass],
  template: `
    <div class="space-y-6" *ngIf="stock">
      <!-- Header -->
      <div class="flex items-start justify-between">
        <div class="flex items-center gap-4">
          <a routerLink="/dashboard" class="p-2 rounded-lg hover:bg-dc-border/50 text-dc-text-secondary transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
          </a>
          <div>
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-bold">{{ stock.ticker }}</h1>
              <span class="px-2 py-0.5 rounded-full text-xs font-medium" 
                    [ngClass]="{'bg-dc-accent/15': stock.is_ftse_mib}" 
                    [class.text-dc-accent]="stock.is_ftse_mib"
                    [class.bg-dc-border]="!stock.is_ftse_mib"
                    [class.text-dc-text-secondary]="!stock.is_ftse_mib">
                {{ stock.is_ftse_mib ? 'FTSE MIB' : 'MID CAP' }}
              </span>
            </div>
            <p class="text-dc-text-secondary">{{ stock.name }} | {{ stock.sector }}</p>
          </div>
        </div>
        <div class="text-right">
          <div class="text-3xl font-bold text-dc-text">EUR {{ stock.price | number:'1.2-2' }}</div>
          <div class="text-sm text-dc-accent flex items-center justify-end gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
            </svg>
            +1.24% oggi
          </div>
        </div>
      </div>

      <!-- Price Chart -->
      <div class="dc-card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="dc-section-title">
            <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"/>
            </svg>
            Prezzo - Ultimi 90 Giorni
          </h2>
          <div class="flex items-center gap-2">
            <button *ngFor="let r of ranges" 
                    (click)="activeRange = r.value; loadPrices()"
                    class="px-3 py-1 rounded-lg text-xs font-medium transition-all"
                    [class.bg-dc-accent]="activeRange === r.value"
                    [class.text-white]="activeRange === r.value"
                    [class.bg-dc-border]="activeRange !== r.value"
                    [class.text-dc-text-secondary]="activeRange !== r.value">
              {{ r.label }}
            </button>
          </div>
        </div>
        <div class="h-80">
          <canvas baseChart
            [data]="priceChartData"
            [options]="priceChartOptions"
            [type]="'line'">
          </canvas>
        </div>
      </div>

      <!-- Technical Indicators -->
      <div class="dc-card">
        <h2 class="dc-section-title mb-4">
          <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          Indicatori Tecnici
        </h2>
        <div class="h-64">
          <canvas baseChart
            [data]="indicatorChartData"
            [options]="indicatorChartOptions"
            [type]="'line'">
          </canvas>
        </div>
        <!-- Latest values -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4" *ngIf="latestIndicators">
          <div class="p-3 rounded-lg bg-dc-bg/50 text-center">
            <div class="text-xs text-dc-text-secondary">RSI (14)</div>
            <div class="text-lg font-bold" [class.text-dc-accent]="latestIndicators.rsi_14 < 70" [class.text-dc-danger]="latestIndicators.rsi_14 >= 70">
              {{ latestIndicators.rsi_14 | number:'1.1-1' }}
            </div>
          </div>
          <div class="p-3 rounded-lg bg-dc-bg/50 text-center">
            <div class="text-xs text-dc-text-secondary">MACD</div>
            <div class="text-lg font-bold" [class.text-dc-accent]="latestIndicators.macd > 0" [class.text-dc-danger]="latestIndicators.macd < 0">
              {{ latestIndicators.macd | number:'1.3-3' }}
            </div>
          </div>
          <div class="p-3 rounded-lg bg-dc-bg/50 text-center">
            <div class="text-xs text-dc-text-secondary">BB Upper</div>
            <div class="text-lg font-bold text-dc-text">
              {{ latestIndicators.bb_upper | number:'1.2-2' }}
            </div>
          </div>
          <div class="p-3 rounded-lg bg-dc-bg/50 text-center">
            <div class="text-xs text-dc-text-secondary">BB Lower</div>
            <div class="text-lg font-bold text-dc-text">
              {{ latestIndicators.bb_lower | number:'1.2-2' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Dividend History & Upcoming -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="dc-card">
          <h2 class="dc-section-title mb-4">
            <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            Storico Dividendi
          </h2>
          <table class="dc-table">
            <thead>
              <tr>
                <th>Ex-Date</th>
                <th>Importo</th>
                <th>Yield Lordo</th>
                <th>Yield Netto</th>
                <th>Stato</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let div of dividends">
                <td>{{ div.ex_date | date:'dd MMM yyyy' }}</td>
                <td class="font-medium">EUR {{ div.dividend_amount | number:'1.4-4' }}</td>
                <td class="text-dc-accent">{{ div.yield_gross | number:'1.2-2' }}%</td>
                <td class="text-dc-secondary">{{ div.yield_net | number:'1.2-2' }}%</td>
                <td>
                  <span class="dc-badge text-xs" 
                        [ngClass]="{'bg-green-500/15': div.status === 'upcoming', 'bg-gray-500/15': div.status === 'paid'}"
                        [class.text-green-400]="div.status === 'upcoming'"
                        [class.text-gray-400]="div.status === 'paid'">
                    {{ div.status === 'upcoming' ? 'In arrivo' : 'Pagato' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Upcoming Dividend Panel with ML -->
        <div class="dc-card" *ngIf="upcomingDividend">
          <h2 class="dc-section-title mb-4">
            <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
            Predizione ML - Prossimo Dividendo
          </h2>
          <div *ngIf="prediction; else noPrediction" class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-sm text-dc-text-secondary">Raccomandazione</span>
              <app-recommendation-badge [recommendation]="prediction.recommendation"></app-recommendation-badge>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-dc-text-secondary">Confidenza</span>
              <div class="flex items-center gap-2">
                <div class="w-24 h-2 bg-dc-border rounded-full overflow-hidden">
                  <div class="h-full bg-dc-accent rounded-full transition-all" [style.width.%]="prediction.confidence_score * 100"></div>
                </div>
                <span class="text-sm font-semibold">{{ prediction.confidence_score * 100 | number:'1.0-0' }}%</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-dc-text-secondary">Drop Previsto</span>
              <span class="text-sm font-semibold text-dc-warning">{{ prediction.predicted_drop_pct }}%</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-dc-text-secondary">Giorni Recupero</span>
              <span class="text-sm font-semibold">{{ prediction.predicted_recovery_days }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-dc-text-secondary">Profitto Atteso (netto)</span>
              <span class="text-sm font-bold" [class.text-dc-accent]="prediction.expected_profit_net > 0" [class.text-dc-danger]="prediction.expected_profit_net < 0">
                EUR {{ prediction.expected_profit_net | number:'1.2-2' }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-dc-text-secondary">Return Atteso</span>
              <span class="text-sm font-bold text-dc-accent">{{ prediction.expected_return_pct | number:'1.2-2' }}%</span>
            </div>
            <div class="mt-4 pt-4 border-t border-dc-border">
              <app-yield-bar [gross]="upcomingDividend.yield_gross" [net]="upcomingDividend.yield_net"></app-yield-bar>
            </div>
          </div>
          <ng-template #noPrediction>
            <div class="text-center text-dc-text-secondary py-6">
              <svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
              Nessuna predizione disponibile per questo titolo.
            </div>
          </ng-template>
        </div>
      </div>
    </div>
  `
})
export class StockDetailComponent implements OnInit {
  stock: Stock | null = null;
  prices: StockPrice[] = [];
  indicators: TechnicalIndicator[] = [];
  latestIndicators: TechnicalIndicator | null = null;
  dividends: DividendEvent[] = [];
  upcomingDividend: DividendEvent | null = null;
  prediction: MLPrediction | null = null;
  activeRange = 90;
  ranges = [{ label: '30G', value: 30 }, { label: '90G', value: 90 }, { label: '6M', value: 180 }];

  priceChartData: ChartData<'line'> = { labels: [], datasets: [] };
  priceChartOptions: ChartConfiguration<'line'>['options'] = {};
  indicatorChartData: ChartData<'line'> = { labels: [], datasets: [] };
  indicatorChartOptions: ChartConfiguration<'line'>['options'] = {};

  constructor(private route: ActivatedRoute, private api: ApiService, private chartService: ChartService) {}

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      const ticker = params['ticker'];
      if (ticker) {
        this.loadStock(ticker);
      }
    });
  }

  loadStock(ticker: string): void {
    this.api.getStock(ticker).subscribe(stock => {
      this.stock = stock;
      this.loadPrices();
      this.loadIndicators();
      this.loadDividends(ticker);
      this.loadPrediction(ticker);
    });
  }

  loadPrices(): void {
    if (!this.stock) return;
    this.api.getPrices(this.stock.ticker, undefined, undefined, '1d').subscribe(prices => {
      this.prices = prices.slice(-this.activeRange);
      this.updatePriceChart();
    });
  }

  loadIndicators(): void {
    if (!this.stock) return;
    this.api.getIndicators(this.stock.ticker).subscribe(indicators => {
      this.indicators = indicators.slice(-this.activeRange);
      this.latestIndicators = indicators.length > 0 ? indicators[indicators.length - 1] : null;
      this.updateIndicatorChart();
    });
  }

  loadDividends(ticker: string): void {
    this.api.getDividends(true).subscribe(divs => {
      this.dividends = divs.filter(d => d.stock_id === this.stock?.id);
      this.upcomingDividend = this.dividends.find(d => d.status === 'upcoming') || null;
    });
  }

  loadPrediction(ticker: string): void {
    this.api.getPredictionsForStock(ticker).subscribe(preds => {
      this.prediction = preds.length > 0 ? preds[0] : null;
    });
  }

  updatePriceChart(): void {
    const labels = this.prices.map(p => p.date.slice(5));
    const closes = this.prices.map(p => p.close);
    const sma20 = this.prices.map((_, i) => {
      if (i < 19) return null;
      const slice = this.prices.slice(i - 19, i + 1);
      return slice.reduce((s, p) => s + p.close, 0) / 20;
    });

    this.priceChartData = {
      labels,
      datasets: [
        {
          label: 'Prezzo Chiusura',
          data: closes,
          borderColor: '#4caf50',
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          fill: true,
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 1.5,
        },
        {
          label: 'SMA 20',
          data: sma20,
          borderColor: '#f57c00',
          backgroundColor: 'transparent',
          fill: false,
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1,
          borderDash: [5, 5],
        }
      ]
    };
    this.priceChartOptions = this.chartService.getDefaultOptions();
  }

  updateIndicatorChart(): void {
    const labels = this.indicators.map(i => i.date.slice(5));
    const rsi = this.indicators.map(i => i.rsi_14);
    const macd = this.indicators.map(i => i.macd);
    const macdSignal = this.indicators.map(i => i.macd_signal);

    this.indicatorChartData = {
      labels,
      datasets: [
        {
          label: 'RSI',
          data: rsi,
          borderColor: '#4caf50',
          backgroundColor: 'transparent',
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1.5,
          yAxisID: 'y'
        },
        {
          label: 'MACD',
          data: macd,
          borderColor: '#0288d1',
          backgroundColor: 'transparent',
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1.5,
          yAxisID: 'y1'
        },
        {
          label: 'MACD Signal',
          data: macdSignal,
          borderColor: '#f57c00',
          backgroundColor: 'transparent',
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1,
          borderDash: [3, 3],
          yAxisID: 'y1'
        }
      ]
    };

    this.indicatorChartOptions = {
      ...this.chartService.getDefaultOptions(),
      scales: {
        x: {
          grid: { color: '#1f2937' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 }, maxTicksLimit: 8 },
          border: { display: false }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          min: 0,
          max: 100,
          grid: { color: '#1f2937' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 } },
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
}
