export interface Stock {
  id: number;
  ticker: string;
  name?: string;
  market?: string;
  sector?: string;
  currency: string;
}

export interface Dividend {
  id: number;
  stock_id: number;
  ex_date: string;
  amount: number;
  payment_date?: string;
  record_date?: string;
  currency: string;
  status: string;
  confidence: number;
}

export interface PriceData {
  id: number;
  stock_id: number;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface StrategyComparison {
  ex_date: string;
  dividend: number;
  long_roi: number;
  long_profit: number;
  flip_roi: number;
  flip_profit: number;
  winner: string;
}

export interface DashboardSummary {
  total_stocks: number;
  total_dividends: number;
  avg_dividend_yield: number;
  total_price_records: number;
  recent_dividends: Dividend[];
}

export interface KpiCard {
  icon: string;
  label: string;
  value: number;
  colorClass: string;
}
