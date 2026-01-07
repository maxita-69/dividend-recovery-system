"""
Unit tests for pattern analysis module.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.pattern_analysis import (
    calculate_window_features,
    extract_pre_dividend_features,
    calculate_recovery_metrics,
    analyze_dividend,
    find_correlations,
    WindowFeatures,
    RecoveryMetrics,
)


class TestCalculateWindowFeatures:
    """Test window feature extraction."""

    def create_price_data(self, days=60, base_price=10.0, trend='flat'):
        """Create test price data."""
        start_date = datetime(2024, 1, 1)
        dates = pd.date_range(start=start_date, periods=days, freq='D')

        if trend == 'flat':
            prices = [base_price] * days
        elif trend == 'uptrend':
            prices = [base_price + (i * 0.1) for i in range(days)]
        elif trend == 'downtrend':
            prices = [base_price - (i * 0.1) for i in range(days)]
        elif trend == 'volatile':
            prices = [base_price + ((-1) ** i * (i % 5) * 0.2) for i in range(days)]
        else:
            prices = [base_price] * days

        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': [1000000 + (i * 10000) for i in range(days)]
        })
        df = df.set_index('date')
        return df

    def test_flat_window(self):
        """Test features on flat price window."""
        df = self.create_price_data(trend='flat')
        ex_date = datetime(2024, 2, 10)  # 40 days after start

        features = calculate_window_features(df, -10, -5, ex_date)

        assert features is not None
        assert isinstance(features, WindowFeatures)
        assert abs(features.trend_pct) < 1.0  # Should be near zero
        assert features.volatility >= 0

    def test_uptrend_window(self):
        """Test features on uptrending window."""
        df = self.create_price_data(trend='uptrend')
        ex_date = datetime(2024, 2, 10)

        features = calculate_window_features(df, -10, -5, ex_date)

        assert features is not None
        assert features.trend_pct > 0  # Positive trend

    def test_downtrend_window(self):
        """Test features on downtrending window."""
        df = self.create_price_data(trend='downtrend')
        ex_date = datetime(2024, 2, 10)

        features = calculate_window_features(df, -10, -5, ex_date)

        assert features is not None
        assert features.trend_pct < 0  # Negative trend

    def test_volatile_window(self):
        """Test features on volatile window."""
        df = self.create_price_data(trend='volatile')
        ex_date = datetime(2024, 2, 10)

        features = calculate_window_features(df, -10, -5, ex_date)

        assert features is not None
        assert features.volatility > 0

    def test_insufficient_data(self):
        """Test with insufficient data."""
        df = self.create_price_data(days=5)
        ex_date = datetime(2024, 2, 10)  # Outside data range

        features = calculate_window_features(df, -10, -5, ex_date)

        assert features is None

    def test_volume_features(self):
        """Test volume-related features."""
        df = self.create_price_data()
        ex_date = datetime(2024, 2, 10)

        features = calculate_window_features(df, -10, -5, ex_date)

        assert features is not None
        assert features.avg_volume > 0
        assert features.volume_trend_pct is not None


class TestExtractPreDividendFeatures:
    """Test pre-dividend feature extraction."""

    def create_test_data(self):
        """Create test price data."""
        start_date = datetime(2024, 1, 1)
        dates = pd.date_range(start=start_date, periods=60, freq='D')
        prices = [10.0 + (i * 0.05) for i in range(60)]

        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': [1000000] * 60
        })
        df = df.set_index('date')
        return df

    def test_extract_multiple_windows(self):
        """Test extraction of features from multiple windows."""
        df = self.create_test_data()
        ex_date = datetime(2024, 2, 20)

        features = extract_pre_dividend_features(df, ex_date)

        assert isinstance(features, dict)
        assert len(features) > 0

        # Should have features for each window
        assert any('D-' in key for key in features.keys())
        assert any('trend_pct' in key for key in features.keys())
        assert any('volatility' in key for key in features.keys())

    def test_d_minus_1_features(self):
        """Test D-1 specific features."""
        df = self.create_test_data()
        ex_date = datetime(2024, 2, 20)

        features = extract_pre_dividend_features(df, ex_date)

        assert 'D-1_close' in features
        assert 'D-1_volume' in features
        assert features['D-1_close'] > 0
        assert features['D-1_volume'] > 0


class TestCalculateRecoveryMetrics:
    """Test recovery metrics calculation."""

    def create_test_data(self):
        """Create test data with dividend gap and recovery."""
        dates = pd.date_range('2024-01-01', '2024-02-29', freq='D')

        # Create price pattern: stable, gap down, recovery
        prices = []
        for i, date in enumerate(dates):
            if date < datetime(2024, 2, 1):
                prices.append(10.0)  # Pre-dividend stable
            elif date == datetime(2024, 2, 1):
                prices.append(9.5)  # Gap down (0.50 dividend)
            else:
                # Gradual recovery
                days_since_ex = (date - datetime(2024, 2, 1)).days
                recovery = min(days_since_ex * 0.05, 0.5)
                prices.append(9.5 + recovery)

        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': prices,
            'volume': [1000000] * len(dates)
        })
        df = df.set_index('date')
        return df

    def test_recovery_calculation(self):
        """Test recovery metrics calculation."""
        df = self.create_test_data()
        ex_date = datetime(2024, 2, 1)
        dividend = 0.50

        metrics = calculate_recovery_metrics(df, ex_date, dividend)

        assert metrics is not None
        assert isinstance(metrics, RecoveryMetrics)
        assert metrics.gap_pct < 0  # Should have negative gap
        assert metrics.d_minus_1_close == 10.0
        assert abs(metrics.expected_gap_pct - 5.0) < 0.1  # ~5% dividend

    def test_recovery_checkpoints(self):
        """Test recovery at specific checkpoints."""
        df = self.create_test_data()
        ex_date = datetime(2024, 2, 1)
        dividend = 0.50

        metrics = calculate_recovery_metrics(df, ex_date, dividend)

        # Should have recovery metrics
        assert metrics.recovery_d5_pct is not None
        assert metrics.recovery_d10_pct is not None

    def test_insufficient_post_data(self):
        """Test with insufficient post-dividend data."""
        df = self.create_test_data()
        # Use date near end of data
        ex_date = datetime(2024, 2, 25)
        dividend = 0.50

        metrics = calculate_recovery_metrics(df, ex_date, dividend)

        # Should still work but may have limited metrics
        assert metrics is not None


class TestAnalyzeDividend:
    """Test complete dividend analysis."""

    def create_full_test_data(self):
        """Create comprehensive test data."""
        dates = pd.date_range('2024-01-01', '2024-03-31', freq='D')
        prices = [10.0 + (i % 20) * 0.1 for i in range(len(dates))]

        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': [1000000] * len(dates)
        })
        df = df.set_index('date')
        return df

    def test_complete_analysis(self):
        """Test complete dividend analysis."""
        df = self.create_full_test_data()
        ex_date = datetime(2024, 2, 15)
        dividend = 0.50

        result = analyze_dividend(df, ex_date, dividend)

        assert result is not None
        assert isinstance(result, dict)

        # Should have basic info
        assert 'ex_date' in result
        assert 'dividend' in result

        # Should have pre-dividend features
        assert any('D-' in key for key in result.keys())

        # Should have recovery metrics
        assert 'gap_pct' in result

    def test_insufficient_pre_data(self):
        """Test with insufficient pre-dividend data."""
        df = self.create_full_test_data()
        # Use date too early
        ex_date = datetime(2024, 1, 5)
        dividend = 0.50

        result = analyze_dividend(df, ex_date, dividend)

        assert result is None


class TestFindCorrelations:
    """Test correlation finding."""

    def create_correlation_test_data(self):
        """Create test data with known correlations."""
        # Create data where pre-feature correlates with post-metric
        data = []
        for i in range(20):
            trend = i * 2  # Strong uptrend
            recovery = trend * 0.8 + (i % 3)  # Correlated recovery

            data.append({
                'ex_date': datetime(2024, 1, i + 1),
                'dividend': 0.50,
                'D-5_D-3_trend_pct': trend,
                'D-3_D-1_volatility': i * 0.5,
                'recovery_d5_pct': recovery,
                'gap_pct': -5.0,
            })

        return pd.DataFrame(data)

    def test_find_positive_correlation(self):
        """Test finding positive correlations."""
        df = self.create_correlation_test_data()

        correlations = find_correlations(df, min_correlation=0.5)

        assert not correlations.empty
        assert 'pre_feature' in correlations.columns
        assert 'post_metric' in correlations.columns
        assert 'correlation' in correlations.columns

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()

        correlations = find_correlations(df)

        assert correlations.empty

    def test_correlation_threshold(self):
        """Test minimum correlation threshold."""
        df = self.create_correlation_test_data()

        # High threshold
        high_corr = find_correlations(df, min_correlation=0.9)

        # Low threshold
        low_corr = find_correlations(df, min_correlation=0.3)

        assert len(high_corr) <= len(low_corr)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
