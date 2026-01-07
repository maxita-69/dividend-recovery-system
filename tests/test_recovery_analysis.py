"""
Unit tests for recovery analysis utilities.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.recovery_analysis import find_recovery, analyze_all_dividends, calculate_recovery_statistics


class TestFindRecovery:
    """Test find_recovery function."""

    def create_price_data(self, start_date, days=30, base_price=10.0, pattern='flat'):
        """Helper to create test price data."""
        dates = pd.date_range(start=start_date, periods=days, freq='D')

        if pattern == 'flat':
            prices = [base_price] * days
        elif pattern == 'recovery_day_3':
            # Recovers on day 3
            prices = [base_price * 0.95] * 3 + [base_price] * (days - 3)
        elif pattern == 'recovery_day_0':
            # Recovers immediately
            prices = [base_price] * days
        elif pattern == 'no_recovery':
            # Never recovers
            prices = [base_price * 0.95] * days
        elif pattern == 'gradual':
            # Gradual recovery over 10 days
            prices = [base_price * (0.90 + 0.01 * i) for i in range(days)]
        else:
            prices = [base_price] * days

        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': [1000000] * days
        })
        df = df.set_index('date')
        return df

    def test_immediate_recovery(self):
        """Test when price recovers on same day (D0)."""
        df = self.create_price_data('2024-01-01', days=30, pattern='recovery_day_0')
        start_date = datetime(2024, 1, 1)
        target_price = 10.0

        result = find_recovery(df, start_date, target_price, max_days=30)

        assert result['recovered'] is True
        assert result['recovery_days'] == 0
        assert result['recovery_price'] == 10.0
        assert result['reason'] == 'recovered'

    def test_recovery_after_days(self):
        """Test when price recovers after 3 days."""
        df = self.create_price_data('2024-01-01', days=30, pattern='recovery_day_3')
        start_date = datetime(2024, 1, 1)
        target_price = 10.0

        result = find_recovery(df, start_date, target_price, max_days=30)

        assert result['recovered'] is True
        assert result['recovery_days'] == 3
        assert result['recovery_price'] >= target_price
        assert result['reason'] == 'recovered'

    def test_no_recovery(self):
        """Test when price never recovers."""
        df = self.create_price_data('2024-01-01', days=30, pattern='no_recovery')
        start_date = datetime(2024, 1, 1)
        target_price = 10.0

        result = find_recovery(df, start_date, target_price, max_days=30)

        assert result['recovered'] is False
        assert result['reason'] == 'not_recovered'
        assert result['recovery_price'] < target_price

    def test_insufficient_data(self):
        """Test when there's not enough data."""
        df = self.create_price_data('2024-01-01', days=5, pattern='no_recovery')
        start_date = datetime(2024, 1, 1)
        target_price = 10.0

        result = find_recovery(df, start_date, target_price, max_days=30)

        assert result['recovered'] is False
        assert result['reason'] == 'insufficient_data'

    def test_no_data(self):
        """Test when there's no data after start date."""
        df = self.create_price_data('2024-01-01', days=10)
        start_date = datetime(2024, 2, 1)  # After all data
        target_price = 10.0

        result = find_recovery(df, start_date, target_price, max_days=30)

        assert result['recovered'] is False
        assert result['reason'] == 'no_data'
        assert result['recovery_date'] is None

    def test_gradual_recovery(self):
        """Test gradual price recovery."""
        df = self.create_price_data('2024-01-01', days=30, pattern='gradual')
        start_date = datetime(2024, 1, 1)
        target_price = 10.0

        result = find_recovery(df, start_date, target_price, max_days=30)

        assert result['recovered'] is True
        assert 0 <= result['recovery_days'] <= 15
        assert result['recovery_price'] >= target_price

    def test_max_days_limit(self):
        """Test that max_days is respected."""
        df = self.create_price_data('2024-01-01', days=30, pattern='no_recovery')
        start_date = datetime(2024, 1, 1)
        target_price = 10.0

        result = find_recovery(df, start_date, target_price, max_days=10)

        assert result['recovered'] is False
        assert result['recovery_days'] <= 10


class TestCalculateRecoveryStatistics:
    """Test calculate_recovery_statistics function."""

    def create_analysis_df(self):
        """Create sample analysis DataFrame."""
        return pd.DataFrame([
            {'recovered': True, 'reason': 'recovered', 'recovery_days': 2},
            {'recovered': True, 'reason': 'recovered', 'recovery_days': 5},
            {'recovered': True, 'reason': 'recovered', 'recovery_days': 1},
            {'recovered': True, 'reason': 'recovered', 'recovery_days': 10},
            {'recovered': False, 'reason': 'not_recovered', 'recovery_days': 30},
            {'recovered': False, 'reason': 'insufficient_data', 'recovery_days': 15},
        ])

    def test_basic_statistics(self):
        """Test basic statistics calculation."""
        df = self.create_analysis_df()
        stats = calculate_recovery_statistics(df)

        assert stats['total_events'] == 6
        assert stats['recovered_count'] == 4
        assert stats['win_rate'] == pytest.approx(66.67, rel=0.1)

    def test_recovery_time_statistics(self):
        """Test recovery time calculations."""
        df = self.create_analysis_df()
        stats = calculate_recovery_statistics(df)

        assert stats['avg_recovery_days'] == pytest.approx(4.5, rel=0.1)
        assert stats['median_recovery_days'] == 3.5

    def test_recovery_categories(self):
        """Test categorization of recovery speeds."""
        df = self.create_analysis_df()
        stats = calculate_recovery_statistics(df)

        assert stats['fast_recoveries'] == 2  # Days 1, 2
        assert stats['normal_recoveries'] == 1  # Day 5
        assert stats['slow_recoveries'] == 1  # Day 10

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        stats = calculate_recovery_statistics(df)

        assert stats['total_events'] == 0
        assert stats['win_rate'] == 0

    def test_all_recovered(self):
        """Test when all dividends recovered."""
        df = pd.DataFrame([
            {'recovered': True, 'reason': 'recovered', 'recovery_days': 3},
            {'recovered': True, 'reason': 'recovered', 'recovery_days': 5},
        ])
        stats = calculate_recovery_statistics(df)

        assert stats['win_rate'] == 100.0
        assert stats['recovered_count'] == 2

    def test_none_recovered(self):
        """Test when no dividends recovered."""
        df = pd.DataFrame([
            {'recovered': False, 'reason': 'not_recovered', 'recovery_days': 30},
            {'recovered': False, 'reason': 'not_recovered', 'recovery_days': 30},
        ])
        stats = calculate_recovery_statistics(df)

        assert stats['win_rate'] == 0.0
        assert stats['recovered_count'] == 0
        assert stats['avg_recovery_days'] is None


class MockDividend:
    """Mock Dividend object for testing."""
    def __init__(self, ex_date, amount):
        self.ex_date = ex_date
        self.amount = amount


class TestAnalyzeAllDividends:
    """Test analyze_all_dividends function."""

    def create_test_data(self):
        """Create test price data and dividends."""
        # Create price data for 3 months
        dates = pd.date_range('2024-01-01', '2024-03-31', freq='D')
        prices = [10.0 + (i % 10) * 0.1 for i in range(len(dates))]

        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': [1000000] * len(dates)
        })
        df = df.set_index('date')

        # Create mock dividends
        dividends = [
            MockDividend(ex_date=datetime(2024, 1, 15), amount=0.50),
            MockDividend(ex_date=datetime(2024, 2, 15), amount=0.50),
        ]

        return df, dividends

    def test_analyze_multiple_dividends(self):
        """Test analyzing multiple dividends."""
        df, dividends = self.create_test_data()
        result = analyze_all_dividends(df, dividends, max_days=30)

        assert len(result) == 2
        assert 'ex_date' in result.columns
        assert 'dividend' in result.columns
        assert 'recovery_days' in result.columns
        assert 'recovered' in result.columns

    def test_dividend_yield_calculation(self):
        """Test dividend yield calculation."""
        df, dividends = self.create_test_data()
        result = analyze_all_dividends(df, dividends)

        assert 'div_yield' in result.columns
        assert all(result['div_yield'] > 0)

    def test_gap_calculation(self):
        """Test gap calculation."""
        df, dividends = self.create_test_data()
        result = analyze_all_dividends(df, dividends)

        assert 'gap' in result.columns
        assert 'gap_pct' in result.columns

    def test_empty_dividends(self):
        """Test with no dividends."""
        df, _ = self.create_test_data()
        result = analyze_all_dividends(df, [])

        assert len(result) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
