"""
Recovery analysis utilities - shared logic for dividend recovery calculation.
Eliminates code duplication between Streamlit pages.
"""
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from config import get_config


def find_recovery(
    df: pd.DataFrame,
    start_date: datetime,
    target_price: float,
    max_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    Find the FIRST day when close price >= target_price.

    This is the core recovery detection algorithm used throughout the system.

    Args:
        df: DataFrame with prices (index = date, must be sorted)
        start_date: Start date (D0 - dividend ex-date)
        target_price: Target price to recover (typically D-1 close)
        max_days: Maximum days to search (defaults to config value)

    Returns:
        dict with:
            - recovery_date: Date when recovery occurred (or last available date)
            - recovery_days: Days from start_date to recovery (0 = same day)
            - recovery_price: Price at recovery date
            - recovered: True if target was reached, False otherwise
            - reason: 'recovered', 'not_recovered', 'insufficient_data', or 'no_data'

    Examples:
        >>> df = get_price_dataframe(session, stock_id)
        >>> result = find_recovery(df, ex_date, d_minus_1_close)
        >>> if result['recovered']:
        >>>     print(f"Recovered in {result['recovery_days']} days")
    """
    if max_days is None:
        cfg = get_config()
        max_days = cfg.analysis.max_recovery_days

    start_date = pd.Timestamp(start_date)

    # Filter data >= start_date and take max_days
    future_data = df[df.index >= start_date].head(max_days)

    if future_data.empty:
        return {
            'recovery_date': None,
            'recovery_days': None,
            'recovery_price': None,
            'recovered': False,
            'reason': 'no_data'
        }

    # Search for first day with close >= target
    # enumerate starts from 0: day 0 = same day (D0)
    for i, (date, row) in enumerate(future_data.iterrows()):
        if row['close'] >= target_price:
            return {
                'recovery_date': date,
                'recovery_days': i,  # 0 = same day, 1 = next day, etc.
                'recovery_price': row['close'],
                'recovered': True,
                'reason': 'recovered'
            }

    # Did not recover within max_days
    # Return the last available day
    last_date = future_data.index[-1]
    last_price = future_data.iloc[-1]['close']

    # Calculate real days passed from start_date to last day
    days_passed = (last_date - start_date).days

    return {
        'recovery_date': last_date,
        'recovery_days': days_passed,
        'recovery_price': last_price,
        'recovered': False,
        'reason': 'not_recovered' if len(future_data) >= max_days else 'insufficient_data'
    }


def analyze_all_dividends(
    df: pd.DataFrame,
    dividends: List,
    max_days: Optional[int] = None
) -> pd.DataFrame:
    """
    Analyze ALL historical dividends and calculate recovery for each.

    This function is used by the Recovery Analysis page to generate
    comprehensive statistics about dividend recovery patterns.

    Args:
        df: DataFrame with price data (index = date)
        dividends: List of Dividend ORM objects
        max_days: Maximum recovery window (defaults to config)

    Returns:
        DataFrame with columns:
            - ex_date: Dividend ex-date
            - dividend: Dividend amount
            - div_yield: Dividend yield %
            - d_minus_1_close: Close price on D-1 (target)
            - d0_open: Open price on D0
            - d0_close: Close price on D0
            - gap: Price gap (D-1 close - D0 open)
            - gap_pct: Gap as percentage
            - recovery_days: Days to recover
            - recovery_date: Date of recovery
            - recovery_price: Price at recovery
            - recovered: Boolean flag
            - reason: Recovery outcome reason

    Examples:
        >>> analysis = analyze_all_dividends(df, dividends)
        >>> win_rate = (analysis['recovered'].sum() / len(analysis)) * 100
        >>> print(f"Win rate: {win_rate:.1f}%")
    """
    if max_days is None:
        cfg = get_config()
        max_days = cfg.analysis.max_recovery_days

    results = []

    for div in dividends:
        ex_date = pd.Timestamp(div.ex_date)

        # Find D-1 close (recovery target)
        dates_before = df[df.index < ex_date]
        if dates_before.empty:
            continue

        d_minus_1 = dates_before.index[-1]
        target_price = df.loc[d_minus_1, 'close']

        # D0 prices
        if ex_date not in df.index:
            continue

        d0_open = df.loc[ex_date, 'open']
        d0_close = df.loc[ex_date, 'close']

        # Gap calculation
        gap = target_price - d0_open
        gap_pct = (gap / target_price) * 100

        # Recovery from D0
        recovery = find_recovery(df, ex_date, target_price, max_days=max_days)

        # Calculate dividend yield
        div_yield = (div.amount / target_price) * 100

        results.append({
            'ex_date': div.ex_date,
            'dividend': div.amount,
            'div_yield': div_yield,
            'd_minus_1_close': target_price,
            'd0_open': d0_open,
            'd0_close': d0_close,
            'gap': gap,
            'gap_pct': gap_pct,
            'recovery_days': recovery['recovery_days'],
            'recovery_date': recovery['recovery_date'],
            'recovery_price': recovery['recovery_price'],
            'recovered': recovery['recovered'],
            'reason': recovery.get('reason', 'unknown')
        })

    return pd.DataFrame(results)


def calculate_recovery_statistics(analysis_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate aggregate statistics from recovery analysis.

    Args:
        analysis_df: Output from analyze_all_dividends()

    Returns:
        Dictionary with:
            - total_events: Total dividend events
            - recovered_count: Number of successful recoveries
            - win_rate: Percentage of recoveries
            - avg_recovery_days: Average recovery time (recovered only)
            - median_recovery_days: Median recovery time (recovered only)
            - max_recovery_days: Longest recovery time
            - fast_recoveries: Count of recoveries <= 3 days
            - normal_recoveries: Count of recoveries 4-7 days
            - slow_recoveries: Count of recoveries > 7 days
    """
    # Handle empty DataFrame
    if analysis_df.empty:
        return {
            'total_events': 0,
            'recovered_count': 0,
            'win_rate': 0,
            'avg_recovery_days': None,
            'median_recovery_days': None,
            'max_recovery_days': None,
            'fast_recoveries': 0,
            'normal_recoveries': 0,
            'slow_recoveries': 0,
        }

    truly_recovered = analysis_df[
        (analysis_df['recovered'] == True) &
        (analysis_df['reason'] == 'recovered')
    ]

    total_events = len(analysis_df)
    recovered_count = len(truly_recovered)

    stats = {
        'total_events': total_events,
        'recovered_count': recovered_count,
        'win_rate': (recovered_count / total_events * 100) if total_events > 0 else 0,
        'avg_recovery_days': truly_recovered['recovery_days'].mean() if not truly_recovered.empty else None,
        'median_recovery_days': truly_recovered['recovery_days'].median() if not truly_recovered.empty else None,
        'max_recovery_days': analysis_df['recovery_days'].max() if not analysis_df.empty else None,
        'fast_recoveries': len(truly_recovered[truly_recovered['recovery_days'] <= 3]) if not truly_recovered.empty else 0,
        'normal_recoveries': len(truly_recovered[(truly_recovered['recovery_days'] > 3) & (truly_recovered['recovery_days'] <= 7)]) if not truly_recovered.empty else 0,
        'slow_recoveries': len(truly_recovered[truly_recovered['recovery_days'] > 7]) if not truly_recovered.empty else 0,
    }

    return stats


def calculate_price_evolution(
    df: pd.DataFrame,
    ex_date: datetime,
    d_minus_1_close: float,
    windows: Optional[List[int]] = None
) -> Dict[int, Dict[str, float]]:
    """
    Calculate price evolution at specific time windows after dividend.

    Args:
        df: Price DataFrame
        ex_date: Dividend ex-date
        d_minus_1_close: Reference price (D-1 close)
        windows: List of days to check (e.g., [5, 10, 15, 20, 30])

    Returns:
        Dictionary mapping days -> {price, pct_change, date}
        Example: {5: {'price': 10.5, 'pct_change': 2.3, 'date': '2024-01-10'}}
    """
    if windows is None:
        cfg = get_config()
        windows = cfg.analysis.evolution_windows

    ex_date = pd.Timestamp(ex_date)
    evolution = {}

    for days in windows:
        future_date = ex_date + pd.Timedelta(days=days)
        future_prices = df[df.index >= future_date]

        if not future_prices.empty:
            actual_date = future_prices.index[0]
            price = future_prices.iloc[0]['close']
            pct_change = ((price - d_minus_1_close) / d_minus_1_close) * 100

            evolution[days] = {
                'price': price,
                'pct_change': pct_change,
                'date': actual_date
            }
        else:
            evolution[days] = {
                'price': None,
                'pct_change': None,
                'date': None
            }

    return evolution
