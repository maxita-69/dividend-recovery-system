"""
Data validation utilities.
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_price_data(df: pd.DataFrame, stock_ticker: str = "") -> Dict[str, any]:
    """
    Validate price data for consistency and quality.

    Checks:
        - Required columns present
        - No null values in critical fields
        - Price relationships (high >= low, etc.)
        - No zero or negative prices (configurable)
        - Volume is non-negative

    Args:
        df: Price DataFrame
        stock_ticker: Stock ticker for error messages

    Returns:
        Dictionary with:
            - valid: bool
            - errors: list of error messages
            - warnings: list of warning messages
            - stats: basic statistics

    Example:
        >>> result = validate_price_data(df, 'ENEL.MI')
        >>> if not result['valid']:
        >>>     print("Errors:", result['errors'])
    """
    errors = []
    warnings = []

    required_columns = ['open', 'high', 'low', 'close', 'volume']

    # Check columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return {'valid': False, 'errors': errors, 'warnings': warnings, 'stats': {}}

    # Check for null values
    null_counts = df[required_columns].isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            errors.append(f"{col} has {count} null values")

    # Check price relationships
    invalid_high_low = (df['high'] < df['low']).sum()
    if invalid_high_low > 0:
        errors.append(f"{invalid_high_low} rows where high < low")

    invalid_high_close = (df['high'] < df['close']).sum()
    if invalid_high_close > 0:
        warnings.append(f"{invalid_high_close} rows where high < close")

    invalid_low_close = (df['low'] > df['close']).sum()
    if invalid_low_close > 0:
        warnings.append(f"{invalid_low_close} rows where low > close")

    invalid_high_open = (df['high'] < df['open']).sum()
    if invalid_high_open > 0:
        warnings.append(f"{invalid_high_open} rows where high < open")

    invalid_low_open = (df['low'] > df['open']).sum()
    if invalid_low_open > 0:
        warnings.append(f"{invalid_low_open} rows where low > open")

    # Check for zero or negative prices
    zero_prices = (df[['open', 'high', 'low', 'close']] <= 0).any(axis=1).sum()
    if zero_prices > 0:
        errors.append(f"{zero_prices} rows with zero or negative prices")

    # Check volume
    negative_volume = (df['volume'] < 0).sum()
    if negative_volume > 0:
        errors.append(f"{negative_volume} rows with negative volume")

    # Check for suspicious price jumps (>50% daily change)
    if 'close' in df.columns and len(df) > 1:
        df_sorted = df.sort_index()
        pct_change = df_sorted['close'].pct_change().abs()
        large_jumps = (pct_change > 0.5).sum()
        if large_jumps > 0:
            warnings.append(f"{large_jumps} rows with >50% daily price change (possible data error or split)")

    # Statistics
    stats = {
        'total_rows': len(df),
        'date_range': (df.index.min(), df.index.max()) if len(df) > 0 else (None, None),
        'avg_close': df['close'].mean() if 'close' in df.columns else None,
        'avg_volume': df['volume'].mean() if 'volume' in df.columns else None,
    }

    valid = len(errors) == 0

    return {
        'valid': valid,
        'errors': errors,
        'warnings': warnings,
        'stats': stats
    }


def validate_dividend_data(
    dividends: List,
    price_df: Optional[pd.DataFrame] = None,
    stock_ticker: str = ""
) -> Dict[str, any]:
    """
    Validate dividend data.

    Checks:
        - Dividend amount is positive
        - Ex-date is present
        - Dates are in logical order (ex_date <= payment_date)
        - No duplicate ex-dates
        - If price_df provided: check that ex-date exists in price data

    Args:
        dividends: List of Dividend ORM objects
        price_df: Optional price DataFrame for cross-validation
        stock_ticker: Stock ticker for error messages

    Returns:
        Dictionary with validation results
    """
    errors = []
    warnings = []

    if not dividends:
        warnings.append("No dividends found")
        return {'valid': True, 'errors': errors, 'warnings': warnings, 'stats': {}}

    # Check for duplicates
    ex_dates = [d.ex_date for d in dividends]
    if len(ex_dates) != len(set(ex_dates)):
        duplicates = [date for date in ex_dates if ex_dates.count(date) > 1]
        errors.append(f"Duplicate ex-dates found: {set(duplicates)}")

    # Check each dividend
    for i, div in enumerate(dividends):
        # Amount check
        if div.amount is None or div.amount <= 0:
            errors.append(f"Dividend {i}: Invalid amount {div.amount}")

        # Date check
        if div.ex_date is None:
            errors.append(f"Dividend {i}: Missing ex_date")
        else:
            # Check date ordering
            if div.payment_date and div.ex_date > div.payment_date:
                warnings.append(f"Dividend {i}: ex_date > payment_date")

            if div.record_date and div.ex_date > div.record_date:
                warnings.append(f"Dividend {i}: ex_date > record_date")

        # Cross-check with price data
        if price_df is not None and div.ex_date:
            ex_date_ts = pd.Timestamp(div.ex_date)
            if ex_date_ts not in price_df.index:
                # Check if it's close (within 5 days)
                nearby_dates = price_df[
                    (price_df.index >= ex_date_ts - pd.Timedelta(days=5)) &
                    (price_df.index <= ex_date_ts + pd.Timedelta(days=5))
                ]
                if nearby_dates.empty:
                    errors.append(f"Dividend {i}: ex_date {div.ex_date} not found in price data (no nearby dates)")
                else:
                    warnings.append(f"Dividend {i}: ex_date {div.ex_date} not in price data (closest: {nearby_dates.index[0].date()})")

    stats = {
        'total_dividends': len(dividends),
        'total_amount': sum(d.amount for d in dividends if d.amount),
        'avg_amount': sum(d.amount for d in dividends if d.amount) / len(dividends) if dividends else 0,
        'date_range': (min(d.ex_date for d in dividends if d.ex_date),
                      max(d.ex_date for d in dividends if d.ex_date)) if dividends else (None, None)
    }

    valid = len(errors) == 0

    return {
        'valid': valid,
        'errors': errors,
        'warnings': warnings,
        'stats': stats
    }


def validate_recovery_input(
    df: pd.DataFrame,
    start_date,
    target_price: float,
    max_days: int
) -> None:
    """
    Validate inputs for recovery analysis.

    Raises ValidationError if inputs are invalid.

    Args:
        df: Price DataFrame
        start_date: Recovery start date
        target_price: Target price to recover
        max_days: Maximum days to search
    """
    if df is None or df.empty:
        raise ValidationError("Price DataFrame is empty")

    if target_price <= 0:
        raise ValidationError(f"Invalid target price: {target_price}")

    if max_days <= 0:
        raise ValidationError(f"Invalid max_days: {max_days}")

    start_date = pd.Timestamp(start_date)
    if start_date > df.index.max():
        raise ValidationError(f"Start date {start_date} is after last available price date {df.index.max()}")
