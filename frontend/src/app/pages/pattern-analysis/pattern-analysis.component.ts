import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { DividendService } from '../../services/dividend.service';
import { Stock } from '../../models';

@Component({
  selector: 'app-pattern-analysis',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule],
  templateUrl: './pattern-analysis.component.html',
  styleUrl: './pattern-analysis.component.scss',
})
export class PatternAnalysisComponent {
  private service = inject(DividendService);

  stocks = signal<Stock[]>([]);

  constructor() {
    this.service.getStocks().subscribe((data) => this.stocks.set(data));
  }
}
