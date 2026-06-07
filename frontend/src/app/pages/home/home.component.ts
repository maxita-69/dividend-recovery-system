import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';

import { DividendService } from '../../services/dividend.service';
import { Stock, Dividend, DashboardSummary, KpiCard } from '../../models';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTableModule,
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent implements OnInit {
  private service = inject(DividendService);

  isLoading = signal(true);
  summary = signal<DashboardSummary | null>(null);
  stocks = signal<Stock[]>([]);
  recentDividends = signal<Dividend[]>([]);

  displayedColumns: string[] = ['ticker', 'name', 'market', 'sector'];
  divColumns: string[] = ['ex_date', 'amount', 'currency', 'status'];

  ngOnInit(): void {
    this.service.getDashboardSummary().subscribe((data) => {
      this.summary.set(data);
    });

    this.service.getStocks().subscribe((data) => {
      this.stocks.set(data);
      this.isLoading.set(false);
    });

    this.service.getRecentDividends(5).subscribe((data) => {
      this.recentDividends.set(data);
    });
  }

  getKpis(): KpiCard[] {
    const s = this.summary();
    if (!s) return [];
    return [
      { icon: 'show_chart', label: 'Titoli', value: s.total_stocks, colorClass: 'kpi-blue' },
      { icon: 'payments', label: 'Dividendi', value: s.total_dividends, colorClass: 'kpi-green' },
      { icon: 'timeline', label: 'Prezzi', value: s.total_price_records, colorClass: 'kpi-orange' },
      { icon: 'percent', label: 'Yield Medio', value: s.avg_dividend_yield, colorClass: 'kpi-red' },
    ];
  }
}
