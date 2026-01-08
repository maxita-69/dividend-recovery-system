"""
Pattern Analysis - Pre-dividend behavior correlation with post-dividend recovery.

This module analyzes historical dividend events to find correlations between
pre-dividend price/volume patterns and post-dividend recovery outcomes.

Key capabilities:
- Extract features from pre-dividend windows (D-40 to D-1)
- Calculate recovery metrics post-dividend (D0 to D+15)
- Find similar historical patterns using cosine similarity
- Identify predictive correlations

Author: Dividend Recovery System
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from config import get_config
from .database import get_price_dataframe
from .recovery_analysis import find_recovery
from .validation import validate_price_data, ValidationError
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class WindowFeatures:
    """Features extracted from a price window."""
    trend_pct: float  # Price change %
    volatility: float  # Std dev of returns
    avg_volume: float  # Average volume
    volume_trend_pct: float  # Volume change %
    max_drawdown_pct: float  # Maximum drawdown
    num_up_days: int  # Days with positive returns
    num_down_days: int  # Days with negative returns


@dataclass
class RecoveryMetrics:
    """Post-dividend recovery metrics."""
    gap_pct: float  # Gap on ex-date
    expected_gap_pct: float  # Expected gap (= dividend yield)
    d_minus_1_close: float  # Close price before dividend
    d0_open: float  # Open price on ex-date
    recovery_d5_pct: Optional[float] = None
    recovery_d10_pct: Optional[float] = None
    recovery_d15_pct: Optional[float] = None
    gap_recovery_d5_pct: Optional[float] = None
    gap_recovery_d10_pct: Optional[float] = None
    gap_recovery_d15_pct: Optional[float] = None
    days_to_50pct_gap: Optional[int] = None
    days_to_100pct_gap: Optional[int] = None


def calculate_window_features(
    df: pd.DataFrame,
    start_day: int,
    end_day: int,
    ex_date: datetime
) -> Optional[WindowFeatures]:
    """
    Calculate features for a specific time window relative to ex-date.

    Args:
        df: Price DataFrame (index = date)
        start_day: Window start (negative = days before ex-date)
        end_day: Window end (negative = days before ex-date)
        ex_date: Dividend ex-date

    Returns:
        WindowFeatures object or None if insufficient data

    Example:
        >>> # Analyze D-5 to D-3 window
        >>> features = calculate_window_features(df, -5, -3, ex_date)
        >>> print(f"Trend: {features.trend_pct:.2f}%")
    """
    ex_date = pd.Timestamp(ex_date)

    # Calculate date range
    start_date = ex_date + pd.Timedelta(days=start_day)
    end_date = ex_date + pd.Timedelta(days=end_day)

    # Filter window
    window = df[(df.index >= start_date) & (df.index <= end_date)].copy()

    if len(window) < 2:
        logger.warning(
            f"Insufficient data for window {start_day} to {end_day}",
            extra={'ex_date': str(ex_date), 'window_size': len(window)}
        )
        return None

    # Sort by date
    window = window.sort_index()

    # Calculate returns
    window['returns'] = window['close'].pct_change()

    # Extract features
    try:
        trend_pct = ((window['close'].iloc[-1] / window['close'].iloc[0]) - 1) * 100
        volatility = window['returns'].std() * 100 if not window['returns'].empty else 0
        avg_volume = window['volume'].mean()

        volume_first = window['volume'].iloc[0]
        volume_last = window['volume'].iloc[-1]
        volume_trend_pct = ((volume_last / volume_first) - 1) * 100 if volume_first > 0 else 0

        max_drawdown_pct = ((window['close'].min() / window['close'].max()) - 1) * 100 if window['close'].max() > 0 else 0

        num_up_days = (window['returns'] > 0).sum()
        num_down_days = (window['returns'] < 0).sum()

        return WindowFeatures(
            trend_pct=trend_pct,
            volatility=volatility,
            avg_volume=avg_volume,
            volume_trend_pct=volume_trend_pct,
            max_drawdown_pct=max_drawdown_pct,
            num_up_days=num_up_days,
            num_down_days=num_down_days
        )

    except Exception as e:
        logger.error(f"Error calculating window features: {e}", exc_info=True)
        return None


def extract_pre_dividend_features(
    df: pd.DataFrame,
    ex_date: datetime,
    windows: Optional[Dict[str, Tuple[int, int]]] = None
) -> Dict[str, float]:
    """
    Extract all pre-dividend features for multiple time windows.

    Args:
        df: Price DataFrame
        ex_date: Dividend ex-date
        windows: Time windows to analyze (defaults to config)

    Returns:
        Dictionary with all features (flat structure for ML/analysis)

    Example:
        >>> features = extract_pre_dividend_features(df, ex_date)
        >>> print(features['D-5_D-3_trend_pct'])  # Trend in last 3 days
    """
    if windows is None:
        cfg = get_config()
        windows = cfg.pattern_analysis.time_windows

    features = {}

    for window_name, (start, end) in windows.items():
        window_features = calculate_window_features(df, start, end, ex_date)

        if window_features:
            features[f'{window_name}_trend_pct'] = window_features.trend_pct
            features[f'{window_name}_volatility'] = window_features.volatility
            features[f'{window_name}_avg_volume'] = window_features.avg_volume
            features[f'{window_name}_volume_trend_pct'] = window_features.volume_trend_pct
            features[f'{window_name}_max_drawdown_pct'] = window_features.max_drawdown_pct
            features[f'{window_name}_num_up_days'] = window_features.num_up_days
            features[f'{window_name}_num_down_days'] = window_features.num_down_days

    # Additional features: D-1 price and volume
    ex_date_ts = pd.Timestamp(ex_date)
    d_minus_1 = df[df.index < ex_date_ts]

    if not d_minus_1.empty:
        last_row = d_minus_1.iloc[-1]
        features['D-1_close'] = last_row['close']
        features['D-1_volume'] = last_row['volume']

    return features


def calculate_recovery_metrics(
    df: pd.DataFrame,
    ex_date: datetime,
    dividend_amount: float,
    recovery_days: Optional[int] = None
) -> Optional[RecoveryMetrics]:
    """
    Calculate post-dividend recovery metrics.

    Args:
        df: Price DataFrame
        ex_date: Dividend ex-date
        dividend_amount: Dividend amount
        recovery_days: Days to track recovery (defaults to config)

    Returns:
        RecoveryMetrics object or None if insufficient data
    """
    if recovery_days is None:
        cfg = get_config()
        recovery_days = cfg.pattern_analysis.recovery_days

    ex_date_ts = pd.Timestamp(ex_date)

    # Get D-1 close (target price)
    d_minus_1 = df[df.index < ex_date_ts]
    if d_minus_1.empty:
        logger.warning("No data before ex-date", extra={'ex_date': str(ex_date)})
        return None

    d_minus_1_close = d_minus_1.iloc[-1]['close']

    # Get D0 open
    d0 = df[df.index >= ex_date_ts]
    if d0.empty:
        logger.warning("No data on/after ex-date", extra={'ex_date': str(ex_date)})
        return None

    d0_open = d0.iloc[0]['open']

    # Calculate gaps
    gap_pct = ((d0_open - d_minus_1_close) / d_minus_1_close) * 100
    expected_gap_pct = (dividend_amount / d_minus_1_close) * 100

    metrics = RecoveryMetrics(
        gap_pct=gap_pct,
        expected_gap_pct=expected_gap_pct,
        d_minus_1_close=d_minus_1_close,
        d0_open=d0_open
    )

    # Calculate recovery at different checkpoints
    for days in [5, 10, 15]:
        if days > recovery_days:
            continue

        checkpoint_date = ex_date_ts + pd.Timedelta(days=days)
        checkpoint_data = df[df.index >= checkpoint_date]

        if not checkpoint_data.empty:
            close_price = checkpoint_data.iloc[0]['close']
            recovery_pct = ((close_price - d0_open) / d0_open) * 100

            setattr(metrics, f'recovery_d{days}_pct', recovery_pct)

            # Gap recovery percentage
            if gap_pct != 0:
                gap_recovered = (recovery_pct / abs(gap_pct)) * 100
                setattr(metrics, f'gap_recovery_d{days}_pct', min(gap_recovered, 100))

    # Find days to 50% and 100% gap recovery
    future_data = df[df.index >= ex_date_ts].head(recovery_days + 5)

    for idx, row in enumerate(future_data.itertuples()):
        recovery_pct = ((row.close - d0_open) / d0_open) * 100
        gap_recovered = (recovery_pct / abs(gap_pct)) * 100 if gap_pct != 0 else 0

        if metrics.days_to_50pct_gap is None and gap_recovered >= 50:
            metrics.days_to_50pct_gap = idx

        if metrics.days_to_100pct_gap is None and gap_recovered >= 100:
            metrics.days_to_100pct_gap = idx

        if metrics.days_to_50pct_gap and metrics.days_to_100pct_gap:
            break

    return metrics


def analyze_dividend(
    df: pd.DataFrame,
    ex_date: datetime,
    dividend_amount: float
) -> Optional[Dict[str, Any]]:
    """
    Complete analysis of a single dividend event.

    Combines pre-dividend features and post-dividend recovery metrics.

    Args:
        df: Price DataFrame
        ex_date: Dividend ex-date
        dividend_amount: Dividend amount

    Returns:
        Dictionary with all features and metrics, or None if insufficient data
    """
    # Validate inputs
    cfg = get_config()

    # Check if we have enough data before ex-date
    ex_date_ts = pd.Timestamp(ex_date)
    data_before = df[df.index < ex_date_ts]

    if len(data_before) < cfg.pattern_analysis.lookback_days:
        logger.warning(
            f"Insufficient pre-dividend data: {len(data_before)} < {cfg.pattern_analysis.lookback_days}",
            extra={'ex_date': str(ex_date)}
        )
        return None

    # Extract pre-dividend features
    pre_features = extract_pre_dividend_features(df, ex_date)

    if not pre_features:
        logger.warning("Failed to extract pre-dividend features", extra={'ex_date': str(ex_date)})
        return None

    # Calculate post-dividend recovery
    recovery = calculate_recovery_metrics(df, ex_date, dividend_amount)

    if not recovery:
        logger.warning("Failed to calculate recovery metrics", extra={'ex_date': str(ex_date)})
        return None

    # Combine all data
    result = {
        'ex_date': ex_date,
        'dividend': dividend_amount,
        **pre_features,
        'gap_pct': recovery.gap_pct,
        'expected_gap_pct': recovery.expected_gap_pct,
        'D0_open': recovery.d0_open,
    }

    # Add recovery metrics
    for attr in ['recovery_d5_pct', 'recovery_d10_pct', 'recovery_d15_pct',
                 'gap_recovery_d5_pct', 'gap_recovery_d10_pct', 'gap_recovery_d15_pct',
                 'days_to_50pct_gap', 'days_to_100pct_gap']:
        value = getattr(recovery, attr, None)
        if value is not None:
            result[attr] = value

    return result


def analyze_all_dividends(
    session,
    stock_id: int,
    dividends: List
) -> pd.DataFrame:
    """
    Analyze all dividends for a stock to create pattern dataset.

    Args:
        session: Database session
        stock_id: Stock ID
        dividends: List of Dividend ORM objects

    Returns:
        DataFrame with features for all analyzable dividends

    Example:
        >>> df = analyze_all_dividends(session, stock.id, dividends)
        >>> print(f"Analyzed {len(df)} dividends")
        >>> print(f"Features: {len(df.columns)}")
    """
    cfg = get_config()

    if len(dividends) < cfg.pattern_analysis.min_patterns_for_analysis:
        logger.warning(
            f"Insufficient dividends for pattern analysis: {len(dividends)} < {cfg.pattern_analysis.min_patterns_for_analysis}"
        )
        return pd.DataFrame()

    # Get price data
    price_df = get_price_dataframe(session, stock_id)

    if price_df is None:
        logger.error("No price data available", extra={'stock_id': stock_id})
        return pd.DataFrame()

    # Validate price data
    validation = validate_price_data(price_df)
    if not validation['valid']:
        logger.error(f"Invalid price data: {validation['errors']}")
        raise ValidationError(f"Price data validation failed: {validation['errors']}")

    results = []

    logger.info(f"Analyzing {len(dividends)} dividends", extra={'stock_id': stock_id})

    for div in dividends:
        result = analyze_dividend(price_df, div.ex_date, div.amount)

        if result:
            results.append(result)

    logger.info(
        f"Successfully analyzed {len(results)}/{len(dividends)} dividends",
        extra={'stock_id': stock_id, 'success_rate': len(results) / len(dividends) * 100}
    )

    return pd.DataFrame(results)


def find_correlations(
    df: pd.DataFrame,
    min_correlation: Optional[float] = None,
    method: Optional[str] = None
) -> pd.DataFrame:
    """
    Find correlations between pre-dividend features and recovery metrics.

    Args:
        df: Pattern analysis DataFrame
        min_correlation: Minimum correlation threshold (defaults to config)
        method: Correlation method - 'pearson', 'spearman', or 'kendall'

    Returns:
        DataFrame with top correlations sorted by absolute value
    """
    if min_correlation is None:
        cfg = get_config()
        min_correlation = cfg.pattern_analysis.min_correlation_threshold

    if method is None:
        cfg = get_config()
        method = cfg.pattern_analysis.correlation_method

    # Identify pre and post columns
    pre_cols = [col for col in df.columns if any(w in col for w in ['D-', 'D_'])]
    post_cols = [
        'recovery_d5_pct', 'recovery_d10_pct', 'recovery_d15_pct',
        'gap_recovery_d5_pct', 'gap_recovery_d10_pct', 'gap_recovery_d15_pct',
        'days_to_50pct_gap', 'days_to_100pct_gap', 'gap_pct'
    ]
    post_cols = [col for col in post_cols if col in df.columns]

    if not pre_cols or not post_cols:
        logger.warning("Insufficient columns for correlation analysis")
        return pd.DataFrame()

    # Calculate correlations
    corr_matrix = df[pre_cols + post_cols].corr(method=method)
    correlations = corr_matrix.loc[pre_cols, post_cols]

    # Flatten and filter
    corr_flat = correlations.unstack().reset_index()
    corr_flat.columns = ['post_metric', 'pre_feature', 'correlation']

    # Filter by minimum threshold
    corr_flat = corr_flat[corr_flat['correlation'].abs() >= min_correlation]

    # Sort by absolute correlation
    corr_flat['abs_correlation'] = corr_flat['correlation'].abs()
    corr_flat = corr_flat.sort_values('abs_correlation', ascending=False)

    logger.info(
        f"Found {len(corr_flat)} significant correlations (|r| >= {min_correlation})",
        extra={'method': method}
    )

    return corr_flat[['pre_feature', 'post_metric', 'correlation']]


def find_similar_patterns(
    df: pd.DataFrame,
    target_idx: int,
    similarity_threshold: Optional[float] = None,
    top_n: int = 5
) -> pd.DataFrame:
    """
    Find historical dividends with similar pre-dividend patterns.

    Uses cosine similarity on normalized pre-dividend features.

    Args:
        df: Pattern analysis DataFrame
        target_idx: Index of target dividend to compare against
        similarity_threshold: Minimum similarity (0-1, defaults to config)
        top_n: Number of similar patterns to return

    Returns:
        DataFrame with similar patterns and their recovery outcomes
    """
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity

    if similarity_threshold is None:
        cfg = get_config()
        similarity_threshold = cfg.pattern_analysis.similarity_threshold

    # Extract pre-dividend features
    pre_cols = [col for col in df.columns if any(w in col for w in ['D-', 'D_'])]
    pre_cols = [col for col in pre_cols if col not in ['D0_open', 'D-1_close']]

    if not pre_cols:
        logger.warning("No pre-dividend features for similarity analysis")
        return pd.DataFrame()

    # Normalize features
    scaler = StandardScaler()
    X = df[pre_cols].fillna(0)
    X_scaled = scaler.fit_transform(X)

    # Calculate similarity to target
    target_vector = X_scaled[target_idx].reshape(1, -1)
    similarities = cosine_similarity(target_vector, X_scaled)[0]

    # Create results DataFrame
    results = df.copy()
    results['similarity'] = similarities

    # Filter and sort
    results = results[results['similarity'] >= similarity_threshold]
    results = results[results.index != target_idx]  # Exclude target itself
    results = results.sort_values('similarity', ascending=False).head(top_n)

    logger.info(
        f"Found {len(results)} similar patterns (similarity >= {similarity_threshold})",
        extra={'target_idx': target_idx}
    )

    return results
