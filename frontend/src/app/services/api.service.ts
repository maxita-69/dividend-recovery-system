import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { catchError, map, delay } from 'rxjs/operators';
import {
  Stock, DividendEvent, StockPrice, TechnicalIndicator,
  MLPrediction, SimulationRequest, SimulationResult, Opportunity, CalendarMonth, CalendarDay,
  MOCK_STOCKS, MOCK_DIVIDENDS, MOCK_PREDICTIONS, MOCK_OPPORTUNITIES,
  enrichPrediction, enrichOpportunity
} from '../models/stock.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000/api';
  private useMocks = true; // Set to false when backend is available

  constructor(private http: HttpClient) {}

  // ============ STOCKS ============

  getStocks(filters?: { sector?: string; ftse_mib?: boolean; min_yield?: number }): Observable<Stock[]> {
    if (this.useMocks) {
      let stocks = [...MOCK_STOCKS];
      if (filters?.sector) stocks = stocks.filter(s => s.sector === filters.sector);
      if (filters?.ftse_mib !== undefined) stocks = stocks.filter(s => s.is_ftse_mib === filters.ftse_mib);
      return of(stocks).pipe(delay(200));
    }
    let params = new HttpParams();
    if (filters?.sector) params = params.set('sector', filters.sector);
    if (filters?.ftse_mib !== undefined) params = params.set('ftse_mib', filters.ftse_mib.toString());
    if (filters?.min_yield) params = params.set('min_yield', filters.min_yield.toString());
    return this.http.get<Stock[]>(`${this.baseUrl}/stocks`, { params })
      .pipe(catchError(this.handleError));
  }

  getStock(ticker: string): Observable<Stock> {
    if (this.useMocks) {
      const stock = MOCK_STOCKS.find(s => s.ticker === ticker);
      return stock ? of(stock).pipe(delay(150)) : throwError(() => new Error('Stock not found'));
    }
    return this.http.get<Stock>(`${this.baseUrl}/stocks/${ticker}`)
      .pipe(catchError(this.handleError));
  }

  getPrices(ticker: string, start?: string, end?: string, interval: string = '1d'): Observable<StockPrice[]> {
    if (this.useMocks) {
      return of(this.generateMockPrices(ticker, 90)).pipe(delay(300));
    }
    let params = new HttpParams().set('interval', interval);
    if (start) params = params.set('start', start);
    if (end) params = params.set('end', end);
    return this.http.get<StockPrice[]>(`${this.baseUrl}/stocks/${ticker}/prices`, { params })
      .pipe(catchError(this.handleError));
  }

  getIndicators(ticker: string): Observable<TechnicalIndicator[]> {
    if (this.useMocks) {
      return of(this.generateMockIndicators(ticker, 90)).pipe(delay(300));
    }
    return this.http.get<TechnicalIndicator[]>(`${this.baseUrl}/stocks/${ticker}/indicators`)
      .pipe(catchError(this.handleError));
  }

  // ============ DIVIDENDS ============

  getDividends(upcomingOnly?: boolean, month?: string, minYieldNet?: number): Observable<DividendEvent[]> {
    if (this.useMocks) {
      let divs = [...MOCK_DIVIDENDS];
      if (upcomingOnly) divs = divs.filter(d => d.status === 'upcoming');
      if (month) divs = divs.filter(d => d.ex_date.startsWith(month));
      if (minYieldNet) divs = divs.filter(d => d.yield_net >= minYieldNet);
      // Enrich with stock data
      divs = divs.map(d => ({
        ...d,
        stock: MOCK_STOCKS.find(s => s.id === d.stock_id)
      }));
      return of(divs).pipe(delay(200));
    }
    let params = new HttpParams();
    if (upcomingOnly) params = params.set('upcoming_only', 'true');
    if (month) params = params.set('month', month);
    if (minYieldNet) params = params.set('min_yield_net', minYieldNet.toString());
    return this.http.get<DividendEvent[]>(`${this.baseUrl}/dividends`, { params })
      .pipe(catchError(this.handleError));
  }

  getDividendCalendar(): Observable<{ [month: string]: DividendEvent[] }> {
    if (this.useMocks) {
      const grouped: { [month: string]: DividendEvent[] } = {};
      MOCK_DIVIDENDS.forEach(d => {
        const month = d.ex_date.substring(0, 7);
        if (!grouped[month]) grouped[month] = [];
        grouped[month].push({ ...d, stock: MOCK_STOCKS.find(s => s.id === d.stock_id) });
      });
      return of(grouped).pipe(delay(200));
    }
    return this.http.get<{ [month: string]: DividendEvent[] }>(`${this.baseUrl}/dividends/calendar`)
      .pipe(catchError(this.handleError));
  }

  getUpcomingDividends(): Observable<DividendEvent[]> {
    return this.getDividends(true);
  }

  // ============ PREDICTIONS ============

  getPredictions(): Observable<MLPrediction[]> {
    if (this.useMocks) {
      const preds = MOCK_PREDICTIONS.map(enrichPrediction);
      return of(preds).pipe(delay(200));
    }
    return this.http.get<MLPrediction[]>(`${this.baseUrl}/predictions`)
      .pipe(
        map(preds => preds.map(enrichPrediction)),
        catchError(this.handleError)
      );
  }

  getPredictionsForStock(ticker: string): Observable<MLPrediction[]> {
    if (this.useMocks) {
      const stock = MOCK_STOCKS.find(s => s.ticker === ticker);
      if (!stock) return of([]);
      const preds = MOCK_PREDICTIONS.filter(p => p.stock_id === stock.id).map(enrichPrediction);
      return of(preds).pipe(delay(150));
    }
    return this.http.get<MLPrediction[]>(`${this.baseUrl}/predictions/${ticker}`)
      .pipe(
        map(preds => preds.map(enrichPrediction)),
        catchError(this.handleError)
      );
  }

  triggerTraining(): Observable<{ message: string }> {
    if (this.useMocks) {
      return of({ message: 'Training started in background. Models will be updated in ~5 minutes.' }).pipe(delay(500));
    }
    return this.http.post<{ message: string }>(`${this.baseUrl}/predictions/train`, {})
      .pipe(catchError(this.handleError));
  }

  // ============ SIMULATOR ============

  runSimulation(request: SimulationRequest): Observable<SimulationResult> {
    if (this.useMocks) {
      return of(this.calculateSimulation(request)).pipe(delay(400));
    }
    return this.http.post<SimulationResult>(`${this.baseUrl}/simulator/calculate`, request)
      .pipe(catchError(this.handleError));
  }

  // ============ STRATEGY / OPPORTUNITIES ============

  getOpportunities(): Observable<Opportunity[]> {
    if (this.useMocks) {
      const opps = MOCK_OPPORTUNITIES.map(enrichOpportunity);
      return of(opps).pipe(delay(200));
    }
    return this.http.get<Opportunity[]>(`${this.baseUrl}/strategy/opportunities`)
      .pipe(
        map(opps => opps.map(enrichOpportunity)),
        catchError(this.handleError)
      );
  }

  getOpportunityDetail(id: number): Observable<Opportunity> {
    if (this.useMocks) {
      const opp = MOCK_OPPORTUNITIES.find(o => o.id === id);
      return opp ? of(enrichOpportunity(opp)).pipe(delay(150)) : throwError(() => new Error('Not found'));
    }
    return this.http.get<Opportunity>(`${this.baseUrl}/strategy/opportunities/${id}/detail`)
      .pipe(
        map(enrichOpportunity),
        catchError(this.handleError)
      );
  }

  // ============ CALENDAR ============

  getCalendar(year?: number, month?: number): Observable<CalendarMonth> {
    if (this.useMocks) {
      const now = new Date();
      const y = year || now.getFullYear();
      const m = month || now.getMonth() + 1;
      return of(this.generateCalendarMonth(y, m)).pipe(delay(200));
    }
    let params = new HttpParams();
    if (year) params = params.set('year', year.toString());
    if (month) params = params.set('month', month.toString());
    return this.http.get<CalendarMonth>(`${this.baseUrl}/calendar`, { params })
      .pipe(catchError(this.handleError));
  }

  // ============ PRIVATE HELPERS ============

  private handleError(error: any): Observable<never> {
    console.error('API Error:', error);
    return throwError(() => new Error(error.message || 'Server error'));
  }

  private generateMockPrices(ticker: string, days: number): StockPrice[] {
    const stock = MOCK_STOCKS.find(s => s.ticker === ticker) || MOCK_STOCKS[0];
    const prices: StockPrice[] = [];
    let price = stock.price;
    const now = new Date();
    for (let i = days; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      if (date.getDay() === 0 || date.getDay() === 6) continue;
      const change = (Math.random() - 0.48) * 0.03;
      price = price * (1 + change);
      const open = price * (1 + (Math.random() - 0.5) * 0.01);
      const high = Math.max(open, price) * (1 + Math.random() * 0.01);
      const low = Math.min(open, price) * (1 - Math.random() * 0.01);
      prices.push({
        id: prices.length + 1,
        stock_id: stock.id,
        date: date.toISOString().split('T')[0],
        open: Math.round(open * 100) / 100,
        high: Math.round(high * 100) / 100,
        low: Math.round(low * 100) / 100,
        close: Math.round(price * 100) / 100,
        volume: Math.floor(Math.random() * 10000000) + 1000000,
        adjusted_close: Math.round(price * 100) / 100
      });
    }
    return prices;
  }

  private generateMockIndicators(ticker: string, days: number): TechnicalIndicator[] {
    const stock = MOCK_STOCKS.find(s => s.ticker === ticker) || MOCK_STOCKS[0];
    const indicators: TechnicalIndicator[] = [];
    const now = new Date();
    let rsi = 50, macd = 0, macdSignal = 0, price = stock.price;
    for (let i = days; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      if (date.getDay() === 0 || date.getDay() === 6) continue;
      rsi = Math.max(20, Math.min(80, rsi + (Math.random() - 0.5) * 5));
      macd += (Math.random() - 0.5) * 0.1;
      macdSignal += (Math.random() - 0.5) * 0.05;
      price *= (1 + (Math.random() - 0.48) * 0.02);
      const bbWidth = price * 0.04;
      indicators.push({
        id: indicators.length + 1,
        stock_id: stock.id,
        date: date.toISOString().split('T')[0],
        rsi_14: Math.round(rsi * 100) / 100,
        macd: Math.round(macd * 100) / 100,
        macd_signal: Math.round(macdSignal * 100) / 100,
        macd_histogram: Math.round((macd - macdSignal) * 100) / 100,
        bb_upper: Math.round((price + bbWidth) * 100) / 100,
        bb_middle: Math.round(price * 100) / 100,
        bb_lower: Math.round((price - bbWidth) * 100) / 100,
        sma_20: Math.round(price * (1 + (Math.random() - 0.5) * 0.02) * 100) / 100,
        sma_50: Math.round(price * (1 + (Math.random() - 0.5) * 0.03) * 100) / 100,
        ema_12: Math.round(price * (1 + (Math.random() - 0.5) * 0.015) * 100) / 100,
        ema_26: Math.round(price * (1 + (Math.random() - 0.5) * 0.025) * 100) / 100,
        atr_14: Math.round(price * 0.015 * 100) / 100,
      });
    }
    return indicators;
  }

  private calculateSimulation(request: SimulationRequest): SimulationResult {
    const stock = MOCK_STOCKS.find(s => s.ticker === request.ticker) || MOCK_STOCKS[0];
    const dividend = MOCK_DIVIDENDS.find(d => d.stock_id === stock.id && d.status === 'upcoming');
    const dividendPerShare = dividend?.dividend_amount || 0.20;
    const entryPrice = stock.price;
    const dropPct = request.expected_price_drop_pct / 100;
    const exitPrice = entryPrice * (1 - (dividendPerShare * dropPct / entryPrice));
    const capitalInvested = entryPrice * request.shares;
    const dividendGross = dividendPerShare * request.shares;
    const tax26 = dividendGross * 0.26;
    const dividendNet = dividendGross - tax26;
    const commissionBuy = Math.min(19, Math.max(2.95, capitalInvested * 0.0019));
    const capitalSell = exitPrice * request.shares;
    const commissionSell = Math.min(19, Math.max(2.95, capitalSell * 0.0019));
    const tobinTax = stock.market_cap >= 500 ? capitalInvested * 0.002 : 0;
    const totalCosts = commissionBuy + commissionSell + tobinTax + tax26;
    const priceLoss = (entryPrice - exitPrice) * request.shares;
    const profitNet = dividendNet - priceLoss - commissionBuy - commissionSell - tobinTax;
    const returnOnCapital = (profitNet / capitalInvested) * 100;

    return {
      ticker: request.ticker,
      shares: request.shares,
      entry_price: Math.round(entryPrice * 100) / 100,
      exit_price: Math.round(exitPrice * 100) / 100,
      capital_invested: Math.round(capitalInvested * 100) / 100,
      dividend_gross: Math.round(dividendGross * 100) / 100,
      dividend_net: Math.round(dividendNet * 100) / 100,
      commission_buy: Math.round(commissionBuy * 100) / 100,
      commission_sell: Math.round(commissionSell * 100) / 100,
      tobin_tax: Math.round(tobinTax * 100) / 100,
      tax_26pct: Math.round(tax26 * 100) / 100,
      total_costs: Math.round(totalCosts * 100) / 100,
      profit_net: Math.round(profitNet * 100) / 100,
      return_on_capital: Math.round(returnOnCapital * 100) / 100,
      price_drop_actual: Math.round((entryPrice - exitPrice) / entryPrice * 100 * 100) / 100,
      entry_date: '2026-06-19',
      exit_date: '2026-06-23',
      ex_date: dividend?.ex_date || '2026-06-22',
      dividend_per_share: dividendPerShare,
    };
  }

  private generateCalendarMonth(year: number, month: number): CalendarMonth {
    const monthNames = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'];
    const daysInMonth = new Date(year, month, 0).getDate();
    const firstDay = new Date(year, month - 1, 1).getDay();
    const monthKey = `${year}-${String(month).padStart(2, '0')}`;
    const monthDivs = MOCK_DIVIDENDS.filter(d => d.ex_date.startsWith(monthKey));
    const dayMap = new Map<number, typeof monthDivs>();
    monthDivs.forEach(d => {
      const day = parseInt(d.ex_date.split('-')[2]);
      if (!dayMap.has(day)) dayMap.set(day, []);
      dayMap.get(day)!.push(d);
    });

    const days: CalendarDay[] = [];
    const today = new Date().toISOString().split('T')[0];
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${monthKey}-${String(d).padStart(2, '0')}`;
      const divs = dayMap.get(d) || [];
      days.push({
        date: dateStr,
        day: d,
        isWeekend: new Date(year, month - 1, d).getDay() === 0 || new Date(year, month - 1, d).getDay() === 6,
        isToday: dateStr === today,
        dividends: divs.map((dv, i) => {
          const stock = MOCK_STOCKS.find(s => s.id === dv.stock_id);
          const colors = ['#4caf50', '#2e7d32', '#f57c00', '#d32f2f', '#7c3aed', '#0288d1'];
          return {
            ticker: stock?.ticker || '',
            name: stock?.name || '',
            dividend_amount: dv.dividend_amount,
            yield_net: dv.yield_net,
            status: dv.status,
            color: colors[i % colors.length]
          };
        })
      });
    }

    return { month, year, monthName: monthNames[month - 1], days };
  }
}
