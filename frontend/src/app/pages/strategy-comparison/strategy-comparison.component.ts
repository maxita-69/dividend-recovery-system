import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';

import { DividendService } from '../../services/dividend.service';
import { Stock, StrategyComparison } from '../../models';

@Component({
  selector: 'app-strategy-comparison',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatIconModule,
    MatTableModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatFormFieldModule,
  ],
  templateUrl: './strategy-comparison.component.html',
  styleUrl: './strategy-comparison.component.scss',
})
export class StrategyComparisonComponent implements OnInit {
  private service = inject(DividendService);

  stocks = signal<Stock[]>([]);
  selectedStockId: number | null = null;
  results = signal<StrategyComparison[]>([]);
  isLoading = signal(false);

  displayedColumns: string[] = [
    'ex_date',
    'dividend',
    'long_roi',
    'long_profit',
    'flip_roi',
    'flip_profit',
    'winner',
  ];

  ngOnInit(): void {
    this.service.getStocks().subscribe((data) => {
      this.stocks.set(data);
      if (data.length > 0) {
        this.selectedStockId = data[0].id;
        this.loadComparison();
      }
    });
  }

  loadComparison(): void {
    if (!this.selectedStockId) return;
    this.isLoading.set(true);
    this.service.getStrategyComparison(this.selectedStockId).subscribe((data) => {
      this.results.set(data);
      this.isLoading.set(false);
    });
  }
}
