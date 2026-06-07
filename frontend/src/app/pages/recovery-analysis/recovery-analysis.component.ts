import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { DividendService } from '../../services/dividend.service';
import { Stock, Dividend } from '../../models';

@Component({
  selector: 'app-recovery-analysis',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatTableModule, MatProgressSpinnerModule],
  templateUrl: './recovery-analysis.component.html',
  styleUrl: './recovery-analysis.component.scss',
})
export class RecoveryAnalysisComponent implements OnInit {
  private service = inject(DividendService);

  stocks = signal<Stock[]>([]);
  selectedStockId: number | null = null;
  dividends = signal<Dividend[]>([]);
  isLoading = signal(false);

  displayedColumns: string[] = ['ex_date', 'amount', 'status', 'confidence'];

  ngOnInit(): void {
    this.service.getStocks().subscribe((data) => {
      this.stocks.set(data);
      if (data.length > 0) {
        this.selectedStockId = data[0].id;
        this.loadDividends();
      }
    });
  }

  loadDividends(): void {
    if (!this.selectedStockId) return;
    this.isLoading.set(true);
    this.service.getDividends(this.selectedStockId).subscribe((data) => {
      this.dividends.set(data);
      this.isLoading.set(false);
    });
  }

  onStockChange(id: number): void {
    this.selectedStockId = id;
    this.loadDividends();
  }
}
