import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { DividendService } from '../../services/dividend.service';
import { Stock } from '../../models';

@Component({
  selector: 'app-database-dashboard',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatTableModule, MatProgressSpinnerModule],
  templateUrl: './database-dashboard.component.html',
  styleUrl: './database-dashboard.component.scss',
})
export class DatabaseDashboardComponent implements OnInit {
  private service = inject(DividendService);

  stocks = signal<Stock[]>([]);
  isLoading = signal(true);

  displayedColumns: string[] = ['id', 'ticker', 'name', 'market', 'sector', 'currency'];

  ngOnInit(): void {
    this.service.getStocks().subscribe((data) => {
      this.stocks.set(data);
      this.isLoading.set(false);
    });
  }
}
