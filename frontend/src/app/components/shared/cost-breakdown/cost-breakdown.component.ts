import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';

@Component({
  selector: 'app-cost-breakdown',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  template: `
    <div class="dc-card">
      <h3 class="dc-section-title mb-4">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"/>
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"/>
        </svg>
        Breakdown Costi
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="h-48">
          <canvas baseChart
            [data]="doughnutChart.data"
            [options]="doughnutChart.options"
            [type]="'doughnut'">
          </canvas>
        </div>
        <div class="space-y-3 flex flex-col justify-center">
          <div class="flex items-center justify-between p-2 rounded-lg bg-dc-bg/50">
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full bg-[#f57c00]"></div>
              <span class="text-sm text-dc-text-secondary">Commissione acquisto</span>
            </div>
            <span class="text-sm font-semibold text-dc-text">EUR {{ commissionBuy | number:'1.2-2' }}</span>
          </div>
          <div class="flex items-center justify-between p-2 rounded-lg bg-dc-bg/50">
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full bg-[#f57c00]"></div>
              <span class="text-sm text-dc-text-secondary">Commissione vendita</span>
            </div>
            <span class="text-sm font-semibold text-dc-text">EUR {{ commissionSell | number:'1.2-2' }}</span>
          </div>
          <div class="flex items-center justify-between p-2 rounded-lg bg-dc-bg/50">
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full bg-[#d32f2f]"></div>
              <span class="text-sm text-dc-text-secondary">Tobin Tax (0.20%)</span>
            </div>
            <span class="text-sm font-semibold text-dc-text">EUR {{ tobinTax | number:'1.2-2' }}</span>
          </div>
          <div class="flex items-center justify-between p-2 rounded-lg bg-dc-bg/50">
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full bg-[#7c3aed]"></div>
              <span class="text-sm text-dc-text-secondary">Tasse dividendo (26%)</span>
            </div>
            <span class="text-sm font-semibold text-dc-text">EUR {{ tax26 | number:'1.2-2' }}</span>
          </div>
          <div class="flex items-center justify-between p-2 rounded-lg bg-dc-border/50 border border-dc-border">
            <span class="text-sm font-semibold text-dc-text">Totale Costi</span>
            <span class="text-sm font-bold text-dc-danger">EUR {{ totalCosts | number:'1.2-2' }}</span>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [``]
})
export class CostBreakdownComponent {
  @Input() commissionBuy = 0;
  @Input() commissionSell = 0;
  @Input() tobinTax = 0;
  @Input() tax26 = 0;
  @Input() totalCosts = 0;

  doughnutChart: ChartConfiguration<'doughnut'> = {
    type: 'doughnut',
    data: { labels: [], datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: '#111827',
          titleColor: '#f3f4f6',
          bodyColor: '#9ca3af',
          borderColor: '#1f2937',
          borderWidth: 1,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => {
              const total = ctx.dataset.data.reduce((a: number, b: number) => a + b, 0);
              const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : '0.0';
              return `${ctx.label}: EUR ${ctx.parsed.toFixed(2)} (${pct}%)`;
            }
          }
        }
      }
    }
  };

  ngOnChanges(): void {
    const data = [this.commissionBuy, this.commissionSell, this.tobinTax, this.tax26];
    const total = data.reduce((a, b) => a + b, 0);
    this.doughnutChart = {
      ...this.doughnutChart,
      data: {
        labels: ['Comm. Acquisto', 'Comm. Vendita', 'Tobin Tax', 'Tassa 26%'],
        datasets: [{
          data: total > 0 ? data : [1, 0, 0, 0],
          backgroundColor: ['#f57c00', '#f57c00aa', '#d32f2f', '#7c3aed'],
          borderColor: '#111827',
          borderWidth: 2,
        }]
      }
    };
  }
}
