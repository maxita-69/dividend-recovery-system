import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { RecommendationBadgeComponent } from '../shared/recommendation-badge/recommendation-badge.component';
import { MLPrediction, MOCK_STOCKS, enrichPrediction } from '../../models/stock.model';

@Component({
  selector: 'app-predictions',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RecommendationBadgeComponent],
  template: `
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-dc-text">Predizioni Machine Learning</h1>
          <p class="text-dc-text-secondary text-sm mt-0.5">Raccomandazioni del modello XGBoost + Random Forest</p>
        </div>
        <div class="flex items-center gap-3">
          <button (click)="triggerTraining()" class="dc-btn-secondary">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Ricalcola
          </button>
          <button (click)="showFilters = !showFilters" class="dc-btn-primary">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/>
            </svg>
            Filtri
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div *ngIf="showFilters" class="dc-card">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs text-dc-text-secondary mb-1.5">Raccomandazione</label>
            <select [(ngModel)]="filterRec" (change)="applyFilters()" class="dc-select">
              <option value="">Tutte</option>
              <option value="STRONG_BUY">STRONG BUY</option>
              <option value="BUY">BUY</option>
              <option value="HOLD">HOLD</option>
              <option value="SELL">SELL</option>
              <option value="AVOID">AVOID</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-dc-text-secondary mb-1.5">Confidenza Minima (%)</label>
            <input type="range" [(ngModel)]="filterConfidence" (input)="applyFilters()" min="0" max="100" step="5" class="w-full accent-dc-accent">
            <div class="text-xs text-dc-text-secondary mt-1">{{ filterConfidence }}%</div>
          </div>
          <div>
            <label class="block text-xs text-dc-text-secondary mb-1.5">Ordina per</label>
            <select [(ngModel)]="sortBy" (change)="applyFilters()" class="dc-select">
              <option value="confidence">Confidenza</option>
              <option value="expected_profit">Profit Atteso</option>
              <option value="expected_return">Return %</option>
              <option value="predicted_drop">Drop Previsto</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div *ngFor="let stat of recStats" class="dc-card py-3 px-4">
          <div class="flex items-center justify-between">
            <span class="text-xs text-dc-text-secondary">{{ stat.label }}</span>
            <span class="text-lg font-bold" [style.color]="stat.color">{{ stat.count }}</span>
          </div>
        </div>
      </div>

      <!-- Predictions Table -->
      <div class="dc-card">
        <div class="overflow-x-auto">
          <table class="dc-table">
            <thead>
              <tr>
                <th class="cursor-pointer" (click)="sort('ticker')">
                  Ticker
                  <span *ngIf="sortBy === 'ticker'" class="text-dc-accent ml-1">{{ sortAsc ? '↑' : '↓' }}</span>
                </th>
                <th class="cursor-pointer" (click)="sort('ex_date')">
                  Ex-Date
                  <span *ngIf="sortBy === 'ex_date'" class="text-dc-accent ml-1">{{ sortAsc ? '↑' : '↓' }}</span>
                </th>
                <th class="cursor-pointer" (click)="sort('predicted_drop')">
                  Drop Prev.
                  <span *ngIf="sortBy === 'predicted_drop'" class="text-dc-accent ml-1">{{ sortAsc ? '↑' : '↓' }}</span>
                </th>
                <th>Confidenza</th>
                <th>ML Rec.</th>
                <th class="cursor-pointer" (click)="sort('expected_profit')">
                  Profit Att.
                  <span *ngIf="sortBy === 'expected_profit'" class="text-dc-accent ml-1">{{ sortAsc ? '↑' : '↓' }}</span>
                </th>
                <th class="cursor-pointer" (click)="sort('expected_return')">
                  Return %
                  <span *ngIf="sortBy === 'expected_return'" class="text-dc-accent ml-1">{{ sortAsc ? '↑' : '↓' }}</span>
                </th>
                <th>G. Rec.</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let p of filteredPredictions" [routerLink]="['/stocks', p.stock?.ticker]" class="cursor-pointer">
                <td>
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-lg bg-dc-accent/10 flex items-center justify-center">
                      <span class="text-dc-accent text-[10px] font-bold">{{ getTickerBase(p.stock?.ticker) }}</span>
                    </div>
                    <div>
                      <div class="font-medium text-sm">{{ p.stock?.ticker }}</div>
                      <div class="text-xs text-dc-text-secondary">{{ p.stock?.name }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="text-sm">{{ p.dividend_event?.ex_date | date:'dd MMM yyyy' }}</span>
                </td>
                <td>
                  <span class="text-sm font-medium text-dc-warning">{{ p.predicted_drop_pct }}%</span>
                </td>
                <td>
                  <div class="flex items-center gap-2">
                    <div class="w-16 h-2 bg-dc-border rounded-full overflow-hidden">
                      <div class="h-full rounded-full transition-all"
                           [style.width.%]="p.confidence_score * 100"
                           [style.background-color]="getConfidenceColor(p.confidence_score)">
                      </div>
                    </div>
                    <span class="text-xs font-medium">{{ p.confidence_score * 100 | number:'1.0-0' }}%</span>
                  </div>
                </td>
                <td>
                  <app-recommendation-badge [recommendation]="p.recommendation"></app-recommendation-badge>
                </td>
                <td>
                  <span class="text-sm font-semibold" [class.text-dc-accent]="p.expected_profit_net > 0" [class.text-dc-danger]="p.expected_profit_net < 0">
                    EUR {{ p.expected_profit_net | number:'1.2-2' }}
                  </span>
                </td>
                <td>
                  <span class="text-sm font-semibold" [class.text-dc-accent]="p.expected_return_pct > 0" [class.text-dc-danger]="p.expected_return_pct < 0">
                    {{ p.expected_return_pct | number:'1.2-2' }}%
                  </span>
                </td>
                <td>
                  <span class="text-sm">{{ p.predicted_recovery_days }}gg</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div *ngIf="filteredPredictions.length === 0" class="text-center py-8 text-dc-text-secondary">
          Nessuna predizione trovata con i filtri selezionati.
        </div>
      </div>
    </div>
  `
})
export class PredictionsComponent implements OnInit {
  predictions: MLPrediction[] = [];
  filteredPredictions: MLPrediction[] = [];
  showFilters = false;
  filterRec = '';
  filterConfidence = 0;
  sortBy = 'confidence';
  sortAsc = false;
  trainingMessage = '';

  recStats: { label: string; count: number; color: string }[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadPredictions();
  }

  loadPredictions(): void {
    this.api.getPredictions().subscribe(preds => {
      this.predictions = preds;
      this.updateStats();
      this.applyFilters();
    });
  }

  updateStats(): void {
    const counts: { [key: string]: number } = {};
    this.predictions.forEach(p => {
      counts[p.recommendation] = (counts[p.recommendation] || 0) + 1;
    });
    const recColors: { [key: string]: string } = {
      'STRONG_BUY': '#4caf50',
      'BUY': '#66bb6a',
      'HOLD': '#f57c00',
      'SELL': '#d32f2f',
      'AVOID': '#b71c1c',
    };
    this.recStats = ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'AVOID'].map(rec => ({
      label: rec.replace('_', ' '),
      count: counts[rec] || 0,
      color: recColors[rec] || '#9ca3af'
    }));
  }

  applyFilters(): void {
    let result = [...this.predictions];
    if (this.filterRec) {
      result = result.filter(p => p.recommendation === this.filterRec);
    }
    if (this.filterConfidence > 0) {
      result = result.filter(p => p.confidence_score * 100 >= this.filterConfidence);
    }
    result.sort((a, b) => {
      let valA: number, valB: number;
      switch (this.sortBy) {
        case 'confidence': valA = a.confidence_score; valB = b.confidence_score; break;
        case 'expected_profit': valA = a.expected_profit_net; valB = b.expected_profit_net; break;
        case 'expected_return': valA = a.expected_return_pct; valB = b.expected_return_pct; break;
        case 'predicted_drop': valA = a.predicted_drop_pct; valB = b.predicted_drop_pct; break;
        default: valA = a.confidence_score; valB = b.confidence_score;
      }
      return this.sortAsc ? valA - valB : valB - valA;
    });
    this.filteredPredictions = result;
  }

  sort(column: string): void {
    if (this.sortBy === column) {
      this.sortAsc = !this.sortAsc;
    } else {
      this.sortBy = column;
      this.sortAsc = true;
    }
    this.applyFilters();
  }

  getConfidenceColor(score: number): string {
    if (score >= 0.8) return '#4caf50';
    if (score >= 0.6) return '#f57c00';
    return '#d32f2f';
  }

  triggerTraining(): void {
    this.api.triggerTraining().subscribe(msg => {
      this.trainingMessage = msg.message;
      setTimeout(() => this.trainingMessage = '', 3000);
    });
  }

  getTickerBase(ticker?: string): string {
    return ticker?.split('.')[0] || '';
  }
}
