import { Injectable } from '@angular/core';
import { ChartConfiguration, ChartOptions, ChartDataset } from 'chart.js';

@Injectable({
  providedIn: 'root'
})
export class ChartService {
  readonly colors = {
    primary: '#1a5f2a',
    secondary: '#2e7d32',
    accent: '#4caf50',
    danger: '#d32f2f',
    warning: '#f57c00',
    bg: '#0a0e17',
    card: '#111827',
    border: '#1f2937',
    text: '#f3f4f6',
    textSecondary: '#9ca3af',
    chartGrid: '#1f2937',
    yieldGross: '#4caf50',
    yieldNet: '#2e7d32',
    costComm: '#f57c00',
    costTobin: '#d32f2f',
    costTax: '#7c3aed',
  };

  getDefaultOptions(): ChartOptions<'line'> {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: this.colors.textSecondary,
            font: { family: 'Inter', size: 11 },
            usePointStyle: true,
            padding: 16,
          }
        },
        tooltip: {
          backgroundColor: this.colors.card,
          titleColor: this.colors.text,
          bodyColor: this.colors.textSecondary,
          borderColor: this.colors.border,
          borderWidth: 1,
          cornerRadius: 8,
          padding: 12,
          titleFont: { family: 'Inter', size: 13, weight: 'bold' },
          bodyFont: { family: 'Inter', size: 12 },
        }
      },
      scales: {
        x: {
          grid: { color: this.colors.chartGrid },
          ticks: { color: this.colors.textSecondary, font: { family: 'Inter', size: 10 }, maxTicksLimit: 8 },
          border: { display: false }
        },
        y: {
          grid: { color: this.colors.chartGrid },
          ticks: { color: this.colors.textSecondary, font: { family: 'Inter', size: 10 } },
          border: { display: false }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      }
    };
  }

  getLineChartConfig(labels: string[], datasets: ChartDataset<'line'>[]): ChartConfiguration<'line'> {
    return {
      type: 'line',
      data: { labels, datasets },
      options: this.getDefaultOptions()
    };
  }

  getBarChartConfig(labels: string[], datasets: ChartDataset<'bar'>[]): ChartConfiguration<'bar'> {
    return {
      type: 'bar',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: this.colors.textSecondary,
              font: { family: 'Inter', size: 11 },
              usePointStyle: true,
            }
          },
          tooltip: {
            backgroundColor: this.colors.card,
            titleColor: this.colors.text,
            bodyColor: this.colors.textSecondary,
            borderColor: this.colors.border,
            borderWidth: 1,
            cornerRadius: 8,
            padding: 12,
          }
        },
        scales: {
          x: {
            grid: { color: this.colors.chartGrid },
            ticks: { color: this.colors.textSecondary, font: { family: 'Inter', size: 10 } },
            border: { display: false }
          },
          y: {
            grid: { color: this.colors.chartGrid },
            ticks: { color: this.colors.textSecondary, font: { family: 'Inter', size: 10 } },
            border: { display: false }
          }
        }
      }
    };
  }

  getDoughnutConfig(labels: string[], data: number[], bgColors: string[]): ChartConfiguration<'doughnut'> {
    return {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: bgColors,
          borderColor: this.colors.card,
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: this.colors.textSecondary,
              font: { family: 'Inter', size: 11 },
              usePointStyle: true,
              padding: 12,
            }
          },
          tooltip: {
            backgroundColor: this.colors.card,
            titleColor: this.colors.text,
            bodyColor: this.colors.textSecondary,
            borderColor: this.colors.border,
            borderWidth: 1,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => {
                const total = ctx.dataset.data.reduce((a: number, b: number) => a + b, 0);
                const pct = ((ctx.parsed / total) * 100).toFixed(1);
                return `${ctx.label}: EUR ${ctx.parsed.toFixed(2)} (${pct}%)`;
              }
            }
          }
        }
      }
    };
  }

  getHorizontalBarConfig(labels: string[], datasets: ChartDataset<'bar'>[]): ChartConfiguration<'bar'> {
    return {
      type: 'bar',
      data: { labels, datasets },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: this.colors.textSecondary, font: { family: 'Inter', size: 11 }, usePointStyle: true }
          },
          tooltip: {
            backgroundColor: this.colors.card,
            titleColor: this.colors.text,
            bodyColor: this.colors.textSecondary,
            borderColor: this.colors.border,
            borderWidth: 1,
            cornerRadius: 8,
          }
        },
        scales: {
          x: {
            grid: { color: this.colors.chartGrid },
            ticks: { color: this.colors.textSecondary, font: { family: 'Inter', size: 10 } },
            border: { display: false }
          },
          y: {
            grid: { display: false },
            ticks: { color: this.colors.textSecondary, font: { family: 'Inter', size: 11 } },
            border: { display: false }
          }
        }
      }
    };
  }
}
