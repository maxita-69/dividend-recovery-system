import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import {
  Stock,
  Dividend,
  PriceData,
  StrategyComparison,
  DashboardSummary,
} from '../models';

const API_BASE = 'http://localhost:8000/api';

@Injectable({ providedIn: 'root' })
export class DividendService {
  private http = inject(HttpClient);

  getStocks(q?: string): Observable<Stock[]> {
    let params = new HttpParams();
    if (q) params = params.set('q', q);
    return this.http
      .get<Stock[]>(`${API_BASE}/stocks`, { params })
      .pipe(catchError(() => of([])));
  }

  getStock(id: number): Observable<Stock | null> {
    return this.http
      .get<Stock>(`${API_BASE}/stocks/${id}`)
      .pipe(catchError(() => of(null)));
  }

  getDividends(stockId: number): Observable<Dividend[]> {
    return this.http
      .get<Dividend[]>(`${API_BASE}/stocks/${stockId}/dividends`)
      .pipe(catchError(() => of([])));
  }

  getPrices(stockId: number, start?: string, end?: string): Observable<PriceData[]> {
    let params = new HttpParams();
    if (start) params = params.set('start', start);
    if (end) params = params.set('end', end);
    return this.http
      .get<PriceData[]>(`${API_BASE}/stocks/${stockId}/prices`, { params })
      .pipe(catchError(() => of([])));
  }

  getStrategyComparison(stockId: number): Observable<StrategyComparison[]> {
    return this.http
      .get<StrategyComparison[]>(`${API_BASE}/strategy/${stockId}/compare`)
      .pipe(catchError(() => of([])));
  }

  getDashboardSummary(): Observable<DashboardSummary | null> {
    return this.http
      .get<DashboardSummary>(`${API_BASE}/dashboard/summary`)
      .pipe(catchError(() => of(null)));
  }

  getRecentDividends(limit: number = 10): Observable<Dividend[]> {
    return this.http
      .get<Dividend[]>(`${API_BASE}/dividends/recent`, {
        params: new HttpParams().set('limit', String(limit)),
      })
      .pipe(catchError(() => of([])));
  }
}
