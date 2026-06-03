import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { map } from 'rxjs/operators';
import {
  Stock, DividendEvent, MLPrediction, Opportunity, PortfolioPosition,
  MOCK_STOCKS, MOCK_DIVIDENDS, MOCK_PREDICTIONS, MOCK_OPPORTUNITIES, MOCK_PORTFOLIO
} from '../models/stock.model';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  private stocks$ = new BehaviorSubject<Stock[]>(MOCK_STOCKS);
  private dividends$ = new BehaviorSubject<DividendEvent[]>(MOCK_DIVIDENDS);
  private predictions$ = new BehaviorSubject<MLPrediction[]>(MOCK_PREDICTIONS);
  private opportunities$ = new BehaviorSubject<Opportunity[]>(MOCK_OPPORTUNITIES);
  private portfolio$ = new BehaviorSubject<PortfolioPosition[]>(MOCK_PORTFOLIO);

  // Stocks
  getStocks(): Observable<Stock[]> {
    return this.stocks$.asObservable();
  }

  getStock(ticker: string): Observable<Stock | undefined> {
    return this.stocks$.pipe(map(stocks => stocks.find(s => s.ticker === ticker)));
  }

  // Dividends
  getDividends(): Observable<DividendEvent[]> {
    return this.dividends$.asObservable();
  }

  getUpcomingDividends(): Observable<DividendEvent[]> {
    return this.dividends$.pipe(map(d => d.filter(x => x.status === 'upcoming')));
  }

  // Predictions
  getPredictions(): Observable<MLPrediction[]> {
    return this.predictions$.asObservable();
  }

  // Opportunities
  getOpportunities(): Observable<Opportunity[]> {
    return this.opportunities$.asObservable();
  }

  // Portfolio
  getPortfolio(): Observable<PortfolioPosition[]> {
    return this.portfolio$.asObservable();
  }

  addPosition(position: PortfolioPosition): void {
    const current = this.portfolio$.value;
    this.portfolio$.next([...current, position]);
  }

  closePosition(id: number, exitPrice: number): void {
    const current = this.portfolio$.value;
    const updated = current.map(p => {
      if (p.id === id) {
        const commissionSell = Math.min(19, Math.max(2.95, exitPrice * p.shares * 0.0019));
        const profitNet = p.dividend_net - p.commission_buy - commissionSell - p.tobin_tax;
        return { ...p, exit_price: exitPrice, commission_sell: commissionSell, profit_net: profitNet, status: 'CLOSED' as const };
      }
      return p;
    });
    this.portfolio$.next(updated);
  }

  // Computed values
  getTotalPortfolioValue(): Observable<number> {
    return this.portfolio$.pipe(
      map(positions => positions.reduce((sum, p) => sum + p.entry_price * p.shares, 0))
    );
  }

  getTotalPortfolioProfit(): Observable<number> {
    return this.portfolio$.pipe(
      map(positions => positions.reduce((sum, p) => sum + p.profit_net, 0))
    );
  }

  getOpenPositionsCount(): Observable<number> {
    return this.portfolio$.pipe(
      map(positions => positions.filter(p => p.status === 'OPEN').length)
    );
  }

  getClosedPositionsCount(): Observable<number> {
    return this.portfolio$.pipe(
      map(positions => positions.filter(p => p.status === 'CLOSED').length)
    );
  }

  getNextExDate(): Observable<string> {
    return this.dividends$.pipe(
      map(divs => {
        const upcoming = divs.filter(d => d.status === 'upcoming').sort((a, b) => a.ex_date.localeCompare(b.ex_date));
        return upcoming.length > 0 ? upcoming[0].ex_date : '';
      })
    );
  }
}
