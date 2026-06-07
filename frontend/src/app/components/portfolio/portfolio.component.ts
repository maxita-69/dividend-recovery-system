import { Component, OnInit } from '@angular/core';
import { CommonModule, NgClass } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { DataService } from '../../services/data.service';
import { ChartService } from '../../services/chart.service';
import { PortfolioPosition, MOCK_STOCKS } from '../../models/stock.model';
import { Observable, combineLatest, map } from 'rxjs';

@Component({
  selector: 'app-portfolio',
  standalone: true,
  imports: [CommonModule, BaseChartDirective, NgClass],
  template: `
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-dc-text">Portfolio</h1>
          <p class="text-dc-text-secondary text-sm mt-0.5">Tracciamento posizioni simulate dividend capture</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-dc-accent/15 text-dc-accent">
            {{ openCount }} Aperte
          </span>
          <span class="px-3 py-1 rounded-full text-xs font-medium bg-dc-border text-dc-text-secondary">
            {{ closedCount }} Chiuse
          </span>
        </div>
      </div>

      <!-- KPI Row -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="dc-card border-dc-accent/30 bg-dc-accent/5">
          <div class="dc-kpi-label">Capitale Totale Impiegato</div>
          <div class="dc-kpi-value text-dc-text mt-1">EUR {{ totalCapital | number:'1.2-2' }}</div>
        </div>
        <div class="dc-card" [ngClass]="{'border-dc-accent/30': totalProfit > 0, 'border-dc-danger/30': totalProfit < 0, 'bg-dc-accent/5': totalProfit > 0, 'bg-dc-danger/5': totalProfit < 0}">
          <div class="dc-kpi-label">Profitto Netto Totale</div>
          <div class="dc-kpi-value mt-1" [class.text-dc-accent]="totalProfit > 0" [class.text-dc-danger]="totalProfit < 0">
            EUR {{ totalProfit | number:'1.2-2' }}
          </div>
        </div>
        <div class="dc-card border-dc-secondary/30 bg-dc-secondary/5">
          <div class="dc-kpi-label">Return Medio</div>
          <div class="dc-kpi-value text-dc-secondary mt-1">{{ avgReturn | number:'1.2-2' }}%</div>
        </div>
        <div class="dc-card">
          <div class="dc-kpi-label">Commissioni Totali</div>
          <div class="dc-kpi-value text-dc-text mt-1">EUR {{ totalCommissions | number:'1.2-2' }}</div>
          <div class="text-xs text-dc-text-secondary mt-1">+ Tobin Tax: EUR {{ totalTobin | number:'1.2-2' }}</div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="dc-card">
          <h3 class="dc-section-title mb-4">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"/>
            </svg>
            Distribuzione Profitto
          </h3>
          <div class="h-56">
            <canvas baseChart
              [data]="profitChartData"
              [options]="profitChartOptions"
              [type]="'doughnut'">
            </canvas>
          </div>
        </div>
        <div class="dc-card">
          <h3 class="dc-section-title mb-4">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
            P&L per Posizione
          </h3>
          <div class="h-56">
            <canvas baseChart
              [data]="pnlChartData"
              [options]="pnlChartOptions"
              [type]="'bar'">
            </canvas>
          </div>
        </div>
      </div>

      <!-- Positions Table -->
      <div class="dc-card">
        <h3 class="dc-section-title mb-4">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
          Posizioni
        </h3>
        <div class="overflow-x-auto">
          <table class="dc-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Azioni</th>
                <th>Data Ingresso</th>
                <th>Prezzo Ingresso</th>
                <th>Data Uscita</th>
                <th>Prezzo Uscita</th>
                <th>Dividendo Netto</th>
                <th>Commissioni</th>
                <th>Tobin Tax</th>
                <th>P&L Netto</th>
                <th>Stato</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let p of positions" 
                  class="transition-colors"
                  [ngClass]="{'bg-dc-accent/5': p.status === 'OPEN', 'bg-dc-bg/30': p.status === 'CLOSED'}">
                <td>
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-lg bg-dc-accent/10 flex items-center justify-center">
                      <span class="text-dc-accent text-[10px] font-bold">{{ p.ticker.split('.')[0] }}</span>
                    </div>
                    <div>
                      <div class="font-medium text-sm">{{ p.ticker }}</div>
                      <div class="text-xs text-dc-text-secondary">{{ p.name }}</div>
                    </div>
                  </div>
                </td>
                <td class="font-medium">{{ p.shares | number }}</td>
                <td>{{ p.entry_date | date:'dd MMM yyyy' }}</td>
                <td>EUR {{ p.entry_price | number:'1.2-2' }}</td>
                <td>
                  <span *ngIf="p.exit_date">{{ p.exit_date | date:'dd MMM yyyy' }}</span>
                  <span *ngIf="!p.exit_date" class="text-dc-text-secondary">-</span>
                </td>
                <td>
                  <span *ngIf="p.exit_price">EUR {{ p.exit_price | number:'1.2-2' }}</span>
                  <span *ngIf="!p.exit_price" class="text-dc-text-secondary">-</span>
                </td>
                <td class="text-dc-secondary font-medium">EUR {{ p.dividend_net | number:'1.2-2' }}</td>
                <td class="text-dc-warning">EUR {{ (p.commission_buy + p.commission_sell) | number:'1.2-2' }}</td>
                <td class="text-dc-danger">EUR {{ p.tobin_tax | number:'1.2-2' }}</td>
                <td class="font-semibold" [class.text-dc-accent]="p.profit_net > 0" [class.text-dc-danger]="p.profit_net < 0">
                  EUR {{ p.profit_net | number:'1.2-2' }}
                </td>
                <td>
                  <span class="dc-badge text-xs" 
                        [ngClass]="{'bg-green-500/15': p.status === 'OPEN', 'bg-gray-500/15': p.status === 'CLOSED'}"
                        [class.text-green-400]="p.status === 'OPEN'"
                        [class.text-gray-400]="p.status === 'CLOSED'">
                    {{ p.status === 'OPEN' ? 'Aperta' : 'Chiusa' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Cost Summary -->
      <div class="dc-card">
        <h3 class="dc-section-title mb-4">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/>
          </svg>
          Riepilogo Costi
        </h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="p-4 rounded-xl bg-dc-bg/50 text-center">
            <div class="text-xs text-dc-text-secondary mb-1">Commissioni Acquisto</div>
            <div class="text-xl font-bold text-dc-warning">EUR {{ totalCommissionBuy | number:'1.2-2' }}</div>
          </div>
          <div class="p-4 rounded-xl bg-dc-bg/50 text-center">
            <div class="text-xs text-dc-text-secondary mb-1">Commissioni Vendita</div>
            <div class="text-xl font-bold text-dc-warning">EUR {{ totalCommissionSell | number:'1.2-2' }}</div>
          </div>
          <div class="p-4 rounded-xl bg-dc-bg/50 text-center">
            <div class="text-xs text-dc-text-secondary mb-1">Tobin Tax Totale</div>
            <div class="text-xl font-bold text-dc-danger">EUR {{ totalTobin | number:'1.2-2' }}</div>
          </div>
          <div class="p-4 rounded-xl bg-dc-bg/50 text-center">
            <div class="text-xs text-dc-text-secondary mb-1">Tasse Dividendo</div>
            <div class="text-xl font-bold text-purple-400">EUR {{ totalDividendTax | number:'1.2-2' }}</div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class PortfolioComponent implements OnInit {
  positions: PortfolioPosition[] = [];
  totalCapital = 0;
  totalProfit = 0;
  avgReturn = 0;
  totalCommissions = 0;
  totalCommissionBuy = 0;
  totalCommissionSell = 0;
  totalTobin = 0;
  totalDividendTax = 0;
  openCount = 0;
  closedCount = 0;

  profitChartData: ChartData<'doughnut'> = { labels: [], datasets: [] };
  profitChartOptions: ChartConfiguration<'doughnut'>['options'] = {};
  pnlChartData: ChartData<'bar'> = { labels: [], datasets: [] };
  pnlChartOptions: ChartConfiguration<'bar'>['options'] = {};

  constructor(private data: DataService, private chartService: ChartService) {}

  ngOnInit(): void {
    this.data.getPortfolio().subscribe(positions => {
      this.positions = positions;
      this.calculateStats();
      this.updateCharts();
    });
  }

  calculateStats(): void {
    this.totalCapital = this.positions.reduce((s, p) => s + p.entry_price * p.shares, 0);
    this.totalProfit = this.positions.reduce((s, p) => s + p.profit_net, 0);
    this.totalCommissionBuy = this.positions.reduce((s, p) => s + p.commission_buy, 0);
    this.totalCommissionSell = this.positions.reduce((s, p) => s + p.commission_sell, 0);
    this.totalCommissions = this.totalCommissionBuy + this.totalCommissionSell;
    this.totalTobin = this.positions.reduce((s, p) => s + p.tobin_tax, 0);
    this.totalDividendTax = this.positions.reduce((s, p) => s + (p.dividend_gross - p.dividend_net), 0);
    this.avgReturn = this.positions.length > 0 ? this.positions.reduce((s, p) => s + p.profit_net, 0) / this.totalCapital * 100 : 0;
    this.openCount = this.positions.filter(p => p.status === 'OPEN').length;
    this.closedCount = this.positions.filter(p => p.status === 'CLOSED').length;
  }

  updateCharts(): void {
    // Doughnut: profit sources
    const totalDividendNet = this.positions.reduce((s, p) => s + p.dividend_net, 0);
    const totalCosts = this.totalCommissions + this.totalTobin;
    this.profitChartData = {
      labels: ['Dividendo Netto', 'Commissioni', 'Tobin Tax'],
      datasets: [{
        data: [totalDividendNet, this.totalCommissions, this.totalTobin],
        backgroundColor: ['#4caf50', '#f57c00', '#d32f2f'],
        borderColor: '#111827',
        borderWidth: 2,
      }]
    };
    this.profitChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#9ca3af', font: { family: 'Inter', size: 11 }, usePointStyle: true, padding: 12 }
        },
        tooltip: {
          backgroundColor: '#111827',
          titleColor: '#f3f4f6',
          bodyColor: '#9ca3af',
          borderColor: '#1f2937',
          borderWidth: 1,
          cornerRadius: 8,
        }
      }
    };

    // Bar: P&L per position
    this.pnlChartData = {
      labels: this.positions.map(p => p.ticker.split('.')[0]),
      datasets: [{
        label: 'P&L Netto (EUR)',
        data: this.positions.map(p => p.profit_net),
        backgroundColor: this.positions.map(p => p.profit_net > 0 ? '#4caf50' : '#d32f2f'),
        borderRadius: 6,
      }]
    };
    this.pnlChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#111827',
          titleColor: '#f3f4f6',
          bodyColor: '#9ca3af',
          borderColor: '#1f2937',
          borderWidth: 1,
          cornerRadius: 8,
        }
      },
      scales: {
        x: {
          grid: { color: '#1f2937' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 } },
          border: { display: false }
        },
        y: {
          grid: { color: '#1f2937' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 10 } },
          border: { display: false }
        }
      }
    };
  }
}
