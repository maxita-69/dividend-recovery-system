import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { DividendService } from '../../services/dividend.service';
import { Stock, Dividend, PriceData } from '../../models';

@Component({
  selector: 'app-recovery-single-stock',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatTableModule, MatProgressSpinnerModule],
  templateUrl: './recovery-single-stock.component.html',
  styleUrl: './recovery-single-stock.component.scss',
})
export class RecoverySingleStockComponent implements OnInit {
  private service = inject(DividendService);
  private route = inject(ActivatedRoute);

  stock = signal<Stock | null>(null);
  dividends = signal<Dividend[]>([]);
  prices = signal<PriceData[]>([]);
  isLoading = signal(true);

  divColumns: string[] = ['ex_date', 'amount', 'payment_date', 'status'];
  priceColumns: string[] = ['date', 'open', 'high', 'low', 'close', 'volume'];

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) return;

    this.service.getStock(id).subscribe((s) => {
      this.stock.set(s);
      this.isLoading.set(false);
    });

    this.service.getDividends(id).subscribe((d) => this.dividends.set(d));
    this.service.getPrices(id).subscribe((p) => this.prices.set(p));
  }
}
