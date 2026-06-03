// ============ DATA MODELS ============
// Matches SPEC.md exactly

export interface Stock {
  id: number;
  ticker: string;
  name: string;
  sector: string;
  market_cap: number;
  is_ftse_mib: boolean;
  price: number;
  updated_at: string;
}

export interface DividendEvent {
  id: number;
  stock_id: number;
  declaration_date: string;
  ex_date: string;
  record_date: string;
  pay_date: string;
  dividend_amount: number;
  dividend_type: 'ordinary' | 'special';
  currency: 'EUR' | 'USD';
  yield_gross: number;
  yield_net: number;
  status: 'upcoming' | 'paid' | 'cancelled';
  stock?: Stock;
}

export interface StockPrice {
  id: number;
  stock_id: number;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adjusted_close: number;
}

export interface TechnicalIndicator {
  id: number;
  stock_id: number;
  date: string;
  rsi_14: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  sma_20: number;
  sma_50: number;
  ema_12: number;
  ema_26: number;
  atr_14: number;
}

export interface MLPrediction {
  id: number;
  stock_id: number;
  dividend_event_id: number;
  prediction_date: string;
  model_type: 'price_regressor' | 'signal_classifier';
  predicted_drop_pct: number;
  predicted_recovery_days: number;
  confidence_score: number;
  recommendation: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'AVOID';
  expected_profit_net: number;
  expected_return_pct: number;
  stock?: Stock;
  dividend_event?: DividendEvent;
}

export interface StrategySimulation {
  id: number;
  stock_id: number;
  dividend_event_id: number;
  shares: number;
  entry_price: number;
  exit_price: number;
  exit_date: string;
  commission_buy: number;
  commission_sell: number;
  tobin_tax: number;
  dividend_gross: number;
  dividend_net: number;
  profit_net: number;
  return_on_capital: number;
  created_at: string;
  stock?: Stock;
  dividend_event?: DividendEvent;
}

export interface SimulationRequest {
  ticker: string;
  shares: number;
  entry_timing: '3_days_before' | '1_day_before' | 'day_before_close';
  exit_timing: 'ex_date_open' | 'ex_date_close' | '1_day_after' | '3_days_after' | '1_week_after';
  expected_price_drop_pct: number;
}

export interface SimulationResult {
  ticker: string;
  shares: number;
  entry_price: number;
  exit_price: number;
  capital_invested: number;
  dividend_gross: number;
  dividend_net: number;
  commission_buy: number;
  commission_sell: number;
  tobin_tax: number;
  tax_26pct: number;
  total_costs: number;
  profit_net: number;
  return_on_capital: number;
  price_drop_actual: number;
  entry_date: string;
  exit_date: string;
  ex_date: string;
  dividend_per_share: number;
}

export interface Opportunity {
  id: number;
  stock_id: number;
  dividend_event_id: number;
  rank: number;
  score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  expected_profit: number;
  expected_return: number;
  stock?: Stock;
  dividend_event?: DividendEvent;
  prediction?: MLPrediction;
}

export interface CalendarDay {
  date: string;
  day: number;
  isWeekend: boolean;
  isToday: boolean;
  dividends: CalendarDividend[];
}

export interface CalendarDividend {
  ticker: string;
  name: string;
  dividend_amount: number;
  yield_net: number;
  status: string;
  color: string;
}

export interface CalendarMonth {
  month: number;
  year: number;
  monthName: string;
  days: CalendarDay[];
}

export interface PortfolioPosition {
  id: number;
  ticker: string;
  name: string;
  shares: number;
  entry_date: string;
  entry_price: number;
  exit_date?: string;
  exit_price?: number;
  dividend_gross: number;
  dividend_net: number;
  commission_buy: number;
  commission_sell: number;
  tobin_tax: number;
  profit_net: number;
  status: 'OPEN' | 'CLOSED';
}

// ============ COST CONSTANTS ============
export const COST_CONSTANTS = {
  COMMISSION_RATE: 0.0019,
  COMMISSION_MIN: 2.95,
  COMMISSION_MAX: 19.00,
  TOBIN_TAX_RATE: 0.0020,
  TOBIN_TAX_CAP_MIN: 500_000_000,
  DIVIDEND_TAX_RATE: 0.26,
  SETTLEMENT_DAYS: 2,
} as const;

// ============ MOCK DATA ============

export const MOCK_STOCKS: Stock[] = [
  { id: 1, ticker: 'ENEL.MI', name: 'Enel S.p.A.', sector: 'Utility', market_cap: 58000, is_ftse_mib: true, price: 7.42, updated_at: '2026-06-01T10:00:00Z' },
  { id: 2, ticker: 'PST.MI', name: 'Poste Italiane', sector: 'Servizi', market_cap: 16000, is_ftse_mib: true, price: 14.80, updated_at: '2026-06-01T10:00:00Z' },
  { id: 3, ticker: 'SRG.MI', name: 'Snam', sector: 'Energy infra', market_cap: 15500, is_ftse_mib: true, price: 4.52, updated_at: '2026-06-01T10:00:00Z' },
  { id: 4, ticker: 'ENI.MI', name: 'Eni', sector: 'Oil & Gas', market_cap: 48000, is_ftse_mib: true, price: 13.65, updated_at: '2026-06-01T10:00:00Z' },
  { id: 5, ticker: 'HERA.MI', name: 'Hera', sector: 'Utility', market_cap: 3800, is_ftse_mib: true, price: 3.85, updated_at: '2026-06-01T10:00:00Z' },
  { id: 6, ticker: 'TRN.MI', name: 'Terna', sector: 'Energy infra', market_cap: 14500, is_ftse_mib: true, price: 8.15, updated_at: '2026-06-01T10:00:00Z' },
  { id: 7, ticker: 'LDO.MI', name: 'Leonardo', sector: 'Aerospace', market_cap: 28000, is_ftse_mib: true, price: 48.50, updated_at: '2026-06-01T10:00:00Z' },
  { id: 8, ticker: 'STM.MI', name: 'STMicroelectronics', sector: 'Tech', market_cap: 32000, is_ftse_mib: true, price: 28.40, updated_at: '2026-06-01T10:00:00Z' },
  { id: 9, ticker: 'PIRC.MI', name: 'Pirelli', sector: 'Automotive', market_cap: 6500, is_ftse_mib: true, price: 6.12, updated_at: '2026-06-01T10:00:00Z' },
  { id: 10, ticker: 'ENAV.MI', name: 'Enav', sector: 'Aerospace serv.', market_cap: 3200, is_ftse_mib: false, price: 3.95, updated_at: '2026-06-01T10:00:00Z' },
  { id: 11, ticker: 'OVS.MI', name: 'OVS', sector: 'Retail', market_cap: 1800, is_ftse_mib: false, price: 2.85, updated_at: '2026-06-01T10:00:00Z' },
  { id: 12, ticker: 'IRE.MI', name: 'Iren', sector: 'Utility', market_cap: 4200, is_ftse_mib: false, price: 2.78, updated_at: '2026-06-01T10:00:00Z' },
  { id: 13, ticker: 'ACE.MI', name: 'Acea', sector: 'Utility', market_cap: 3900, is_ftse_mib: false, price: 18.45, updated_at: '2026-06-01T10:00:00Z' },
  { id: 14, ticker: 'ASC.MI', name: 'Ascopiave', sector: 'Utility', market_cap: 850, is_ftse_mib: false, price: 7.20, updated_at: '2026-06-01T10:00:00Z' },
  { id: 15, ticker: 'YACHT.MI', name: 'Ferretti', sector: 'Luxury', market_cap: 2100, is_ftse_mib: false, price: 29.50, updated_at: '2026-06-01T10:00:00Z' },
  { id: 16, ticker: 'TIP.MI', name: 'Tamburi Inv. Partners', sector: 'Finance', market_cap: 1600, is_ftse_mib: false, price: 8.95, updated_at: '2026-06-01T10:00:00Z' },
  { id: 17, ticker: 'CRL.MI', name: 'Carel Industries', sector: 'Industrial', market_cap: 2400, is_ftse_mib: false, price: 12.30, updated_at: '2026-06-01T10:00:00Z' },
];

export const MOCK_DIVIDENDS: DividendEvent[] = [
  { id: 1, stock_id: 1, declaration_date: '2026-05-15', ex_date: '2026-07-20', record_date: '2026-07-22', pay_date: '2026-07-24', dividend_amount: 0.26, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 3.50, yield_net: 2.59, status: 'upcoming' },
  { id: 2, stock_id: 2, declaration_date: '2026-05-10', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.85, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 5.74, yield_net: 4.25, status: 'upcoming' },
  { id: 3, stock_id: 3, declaration_date: '2026-05-12', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.1813, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 4.01, yield_net: 2.97, status: 'upcoming' },
  { id: 4, stock_id: 4, declaration_date: '2026-05-20', ex_date: '2026-09-21', record_date: '2026-09-23', pay_date: '2026-09-25', dividend_amount: 0.27, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 1.98, yield_net: 1.47, status: 'upcoming' },
  { id: 5, stock_id: 5, declaration_date: '2026-05-08', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.16, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 4.16, yield_net: 3.08, status: 'upcoming' },
  { id: 6, stock_id: 6, declaration_date: '2026-05-11', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.277, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 3.40, yield_net: 2.52, status: 'upcoming' },
  { id: 7, stock_id: 7, declaration_date: '2026-05-18', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.63, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 1.30, yield_net: 0.96, status: 'upcoming' },
  { id: 8, stock_id: 8, declaration_date: '2026-05-25', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.09, dividend_type: 'ordinary', currency: 'USD', yield_gross: 0.29, yield_net: 0.21, status: 'upcoming' },
  { id: 9, stock_id: 9, declaration_date: '2026-05-14', ex_date: '2026-07-20', record_date: '2026-07-22', pay_date: '2026-07-24', dividend_amount: 0.34, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 5.56, yield_net: 4.11, status: 'upcoming' },
  { id: 10, stock_id: 10, declaration_date: '2026-05-09', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.29, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 7.34, yield_net: 5.43, status: 'upcoming' },
  { id: 11, stock_id: 11, declaration_date: '2026-05-05', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.14, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 4.91, yield_net: 3.63, status: 'upcoming' },
  { id: 12, stock_id: 12, declaration_date: '2026-05-07', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.1386, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 4.99, yield_net: 3.69, status: 'upcoming' },
  { id: 13, stock_id: 13, declaration_date: '2026-05-06', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 1.20, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 6.50, yield_net: 4.81, status: 'upcoming' },
  { id: 14, stock_id: 14, declaration_date: '2026-05-03', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.16, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 2.22, yield_net: 1.64, status: 'upcoming' },
  { id: 15, stock_id: 15, declaration_date: '2026-05-01', ex_date: '2026-06-15', record_date: '2026-06-17', pay_date: '2026-06-19', dividend_amount: 0.11, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 0.37, yield_net: 0.27, status: 'upcoming' },
  { id: 16, stock_id: 16, declaration_date: '2026-05-04', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.26, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 2.91, yield_net: 2.15, status: 'upcoming' },
  { id: 17, stock_id: 17, declaration_date: '2026-05-02', ex_date: '2026-06-22', record_date: '2026-06-24', pay_date: '2026-06-26', dividend_amount: 0.195, dividend_type: 'ordinary', currency: 'EUR', yield_gross: 1.59, yield_net: 1.17, status: 'upcoming' },
];

export const MOCK_PREDICTIONS: MLPrediction[] = [
  { id: 1, stock_id: 10, dividend_event_id: 10, prediction_date: '2026-06-01T08:00:00Z', model_type: 'signal_classifier', predicted_drop_pct: 85, predicted_recovery_days: 5, confidence_score: 0.92, recommendation: 'STRONG_BUY', expected_profit_net: 125.50, expected_return_pct: 8.12 },
  { id: 2, stock_id: 13, dividend_event_id: 13, prediction_date: '2026-06-01T08:00:00Z', model_type: 'signal_classifier', predicted_drop_pct: 78, predicted_recovery_days: 4, confidence_score: 0.88, recommendation: 'BUY', expected_profit_net: 420.75, expected_return_pct: 6.05 },
  { id: 3, stock_id: 2, dividend_event_id: 2, prediction_date: '2026-06-01T08:00:00Z', model_type: 'signal_classifier', predicted_drop_pct: 82, predicted_recovery_days: 6, confidence_score: 0.85, recommendation: 'BUY', expected_profit_net: 185.30, expected_return_pct: 3.82 },
  { id: 4, stock_id: 12, dividend_event_id: 12, prediction_date: '2026-06-01T08:00:00Z', model_type: 'signal_classifier', predicted_drop_pct: 88, predicted_recovery_days: 7, confidence_score: 0.79, recommendation: 'HOLD', expected_profit_net: 28.40, expected_return_pct: 2.75 },
  { id: 5, stock_id: 5, dividend_event_id: 5, prediction_date: '2026-06-01T08:00:00Z', model_type: 'signal_classifier', predicted_drop_pct: 91, predicted_recovery_days: 8, confidence_score: 0.72, recommendation: 'HOLD', expected_profit_net: 18.90, expected_return_pct: 2.18 },
  { id: 6, stock_id: 15, dividend_event_id: 15, prediction_date: '2026-06-01T08:00:00Z', model_type: 'signal_classifier', predicted_drop_pct: 95, predicted_recovery_days: 10, confidence_score: 0.55, recommendation: 'AVOID', expected_profit_net: -15.20, expected_return_pct: -0.35 },
];

export const MOCK_OPPORTUNITIES: Opportunity[] = [
  { id: 1, stock_id: 10, dividend_event_id: 10, rank: 1, score: 95, risk_level: 'LOW', expected_profit: 125.50, expected_return: 8.12 },
  { id: 2, stock_id: 13, dividend_event_id: 13, rank: 2, score: 88, risk_level: 'LOW', expected_profit: 420.75, expected_return: 6.05 },
  { id: 3, stock_id: 2, dividend_event_id: 2, rank: 3, score: 82, risk_level: 'LOW', expected_profit: 185.30, expected_return: 3.82 },
  { id: 4, stock_id: 12, dividend_event_id: 12, rank: 4, score: 71, risk_level: 'MEDIUM', expected_profit: 28.40, expected_return: 2.75 },
  { id: 5, stock_id: 5, dividend_event_id: 5, rank: 5, score: 65, risk_level: 'MEDIUM', expected_profit: 18.90, expected_return: 2.18 },
];

export const MOCK_PORTFOLIO: PortfolioPosition[] = [
  { id: 1, ticker: 'PST.MI', name: 'Poste Italiane', shares: 1000, entry_date: '2026-06-19', entry_price: 14.65, dividend_gross: 850.00, dividend_net: 629.00, commission_buy: 27.84, commission_sell: 0, tobin_tax: 29.30, profit_net: 571.86, status: 'OPEN' },
  { id: 2, ticker: 'ENAV.MI', name: 'Enav', shares: 2000, entry_date: '2026-06-17', entry_price: 3.88, exit_date: '2026-06-23', exit_price: 3.75, dividend_gross: 580.00, dividend_net: 429.20, commission_buy: 14.74, commission_sell: 14.25, tobin_tax: 15.52, profit_net: 384.69, status: 'CLOSED' },
  { id: 3, ticker: 'ACE.MI', name: 'Acea', shares: 500, entry_date: '2026-06-18', entry_price: 18.60, dividend_gross: 600.00, dividend_net: 444.00, commission_buy: 17.67, commission_sell: 0, tobin_tax: 18.60, profit_net: 407.73, status: 'OPEN' },
];

export function getStockByTicker(ticker: string): Stock | undefined {
  return MOCK_STOCKS.find(s => s.ticker === ticker);
}

export function getStockById(id: number): Stock | undefined {
  return MOCK_STOCKS.find(s => s.id === id);
}

export function getDividendsForStock(stockId: number): DividendEvent[] {
  return MOCK_DIVIDENDS.filter(d => d.stock_id === stockId);
}

export function enrichPrediction(pred: MLPrediction): MLPrediction {
  return {
    ...pred,
    stock: getStockById(pred.stock_id),
    dividend_event: MOCK_DIVIDENDS.find(d => d.id === pred.dividend_event_id)
  };
}

export function enrichOpportunity(opp: Opportunity): Opportunity {
  return {
    ...opp,
    stock: getStockById(opp.stock_id),
    dividend_event: MOCK_DIVIDENDS.find(d => d.id === opp.dividend_event_id),
    prediction: MOCK_PREDICTIONS.find(p => p.stock_id === opp.stock_id)
  };
}
