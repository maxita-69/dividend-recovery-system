"""
Unit tests for data validation utilities.
"""
import pytest
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.validation import validate_price_data, validate_dividend_data, validate_recovery_input, ValidationError


class TestValidatePriceData:
    """Test validate_price_data function."""

    def create_valid_df(self):
        """Create valid price DataFrame."""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        return pd.DataFrame({
            'open': [10.0] * 10,
            'high': [10.5] * 10,
            'low': [9.5] * 10,
            'close': [10.0] * 10,
            'volume': [1000000] * 10
        }, index=dates)

    def test_valid_data(self):
        """Test with valid data."""
        df = self.create_valid_df()
        result = validate_price_data(df, 'TEST.MI')

        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert result['stats']['total_rows'] == 10

    def test_missing_columns(self):
        """Test with missing columns."""
        df = pd.DataFrame({'close': [10.0] * 10})
        result = validate_price_data(df)

        assert result['valid'] is False
        assert any('Missing required columns' in err for err in result['errors'])

    def test_null_values(self):
        """Test with null values."""
        df = self.create_valid_df()
        df.loc[df.index[0], 'close'] = None

        result = validate_price_data(df)

        assert result['valid'] is False
        assert any('null values' in err for err in result['errors'])

    def test_invalid_high_low(self):
        """Test when high < low."""
        df = self.create_valid_df()
        df.loc[df.index[0], 'high'] = 8.0
        df.loc[df.index[0], 'low'] = 9.0

        result = validate_price_data(df)

        assert result['valid'] is False
        assert any('high < low' in err for err in result['errors'])

    def test_zero_prices(self):
        """Test with zero prices."""
        df = self.create_valid_df()
        df.loc[df.index[0], 'close'] = 0.0

        result = validate_price_data(df)

        assert result['valid'] is False
        assert any('zero or negative prices' in err for err in result['errors'])

    def test_negative_volume(self):
        """Test with negative volume."""
        df = self.create_valid_df()
        df.loc[df.index[0], 'volume'] = -1000

        result = validate_price_data(df)

        assert result['valid'] is False
        assert any('negative volume' in err for err in result['errors'])

    def test_large_price_jumps(self):
        """Test detection of large price jumps."""
        df = self.create_valid_df()
        df.loc[df.index[5], 'close'] = 20.0  # 100% jump

        result = validate_price_data(df)

        # Should be a warning, not an error
        assert any('50% daily price change' in warn for warn in result['warnings'])


class MockDividend:
    """Mock Dividend object."""
    def __init__(self, ex_date, amount, payment_date=None, record_date=None):
        self.ex_date = ex_date
        self.amount = amount
        self.payment_date = payment_date
        self.record_date = record_date


class TestValidateDividendData:
    """Test validate_dividend_data function."""

    def test_valid_dividends(self):
        """Test with valid dividend data."""
        dividends = [
            MockDividend(datetime(2024, 1, 15), 0.50, datetime(2024, 1, 30)),
            MockDividend(datetime(2024, 2, 15), 0.50, datetime(2024, 2, 28)),
        ]

        result = validate_dividend_data(dividends)

        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert result['stats']['total_dividends'] == 2

    def test_empty_dividends(self):
        """Test with no dividends."""
        result = validate_dividend_data([])

        assert result['valid'] is True
        assert any('No dividends found' in warn for warn in result['warnings'])

    def test_duplicate_ex_dates(self):
        """Test duplicate ex-dates detection."""
        dividends = [
            MockDividend(datetime(2024, 1, 15), 0.50),
            MockDividend(datetime(2024, 1, 15), 0.50),  # Duplicate
        ]

        result = validate_dividend_data(dividends)

        assert result['valid'] is False
        assert any('Duplicate ex-dates' in err for err in result['errors'])

    def test_invalid_amount(self):
        """Test invalid dividend amounts."""
        dividends = [
            MockDividend(datetime(2024, 1, 15), 0.0),  # Zero
            MockDividend(datetime(2024, 2, 15), -0.50),  # Negative
        ]

        result = validate_dividend_data(dividends)

        assert result['valid'] is False
        assert any('Invalid amount' in err for err in result['errors'])

    def test_date_order_validation(self):
        """Test date order validation."""
        dividends = [
            MockDividend(
                ex_date=datetime(2024, 2, 1),
                amount=0.50,
                payment_date=datetime(2024, 1, 1)  # Before ex-date
            )
        ]

        result = validate_dividend_data(dividends)

        # Should be a warning
        assert any('ex_date > payment_date' in warn for warn in result['warnings'])

    def test_cross_validation_with_prices(self):
        """Test cross-validation with price data."""
        dividends = [
            MockDividend(datetime(2024, 1, 15), 0.50),
        ]

        # Create price data without the ex-date
        dates = pd.date_range('2024-01-01', '2024-01-10', freq='D')
        df = pd.DataFrame({
            'close': [10.0] * len(dates)
        }, index=dates)

        result = validate_dividend_data(dividends, price_df=df)

        # Should have error or warning about missing ex-date
        all_messages = result['errors'] + result['warnings']
        assert any('not in price data' in msg for msg in all_messages)


class TestValidateRecoveryInput:
    """Test validate_recovery_input function."""

    def create_test_df(self):
        """Create test DataFrame."""
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        return pd.DataFrame({
            'close': [10.0] * 30
        }, index=dates)

    def test_valid_input(self):
        """Test with valid inputs."""
        df = self.create_test_df()
        # Should not raise
        validate_recovery_input(df, datetime(2024, 1, 1), 10.0, 30)

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()

        with pytest.raises(ValidationError, match="empty"):
            validate_recovery_input(df, datetime(2024, 1, 1), 10.0, 30)

    def test_invalid_target_price(self):
        """Test with invalid target price."""
        df = self.create_test_df()

        with pytest.raises(ValidationError, match="Invalid target price"):
            validate_recovery_input(df, datetime(2024, 1, 1), -10.0, 30)

        with pytest.raises(ValidationError, match="Invalid target price"):
            validate_recovery_input(df, datetime(2024, 1, 1), 0.0, 30)

    def test_invalid_max_days(self):
        """Test with invalid max_days."""
        df = self.create_test_df()

        with pytest.raises(ValidationError, match="Invalid max_days"):
            validate_recovery_input(df, datetime(2024, 1, 1), 10.0, 0)

        with pytest.raises(ValidationError, match="Invalid max_days"):
            validate_recovery_input(df, datetime(2024, 1, 1), 10.0, -5)

    def test_start_date_after_data(self):
        """Test when start date is after available data."""
        df = self.create_test_df()

        with pytest.raises(ValidationError, match="after last available"):
            validate_recovery_input(df, datetime(2025, 1, 1), 10.0, 30)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
