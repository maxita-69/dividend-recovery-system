import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { DividendService } from '../../services/dividend.service';
import { DashboardSummary, KpiCard } from '../../models';

@Component({
  selector: 'app-master-dashboard',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule],
  templateUrl: './master-dashboard.component.html',
  styleUrl: './master-dashboard.component.scss',
})
export class MasterDashboardComponent implements OnInit {
  private service = inject(DividendService);

  summary = signal<DashboardSummary | null>(null);

  ngOnInit(): void {
    this.service.getDashboardSummary().subscribe((data) => this.summary.set(data));
  }

  getKpis(): KpiCard[] {
    const s = this.summary();
    if (!s) return [];
    return [
      { icon: 'show_chart', label: 'Titoli', value: s.total_stocks, colorClass: 'kpi-blue' },
      { icon: 'payments', label: 'Dividendi', value: s.total_dividends, colorClass: 'kpi-green' },
      { icon: 'timeline', label: 'Prezzi', value: s.total_price_records, colorClass: 'kpi-orange' },
      { icon: 'savings', label: 'Yield Medio', value: s.avg_dividend_yield, colorClass: 'kpi-red' },
    ];
  }
}
