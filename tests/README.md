# Test Suite

Unit tests for the Dividend Recovery System.

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_recovery_analysis.py -v

# Run specific test
pytest tests/test_recovery_analysis.py::TestFindRecovery::test_immediate_recovery -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Test Structure

- `test_recovery_analysis.py` - Tests for recovery analysis logic
  - `TestFindRecovery` - Core recovery detection algorithm
  - `TestCalculateRecoveryStatistics` - Statistical calculations
  - `TestAnalyzeAllDividends` - Historical dividend analysis

- `test_validation.py` - Tests for data validation
  - `TestValidatePriceData` - Price data quality checks
  - `TestValidateDividendData` - Dividend data validation
  - `TestValidateRecoveryInput` - Input parameter validation

## Test Coverage

Current coverage: **35 tests** covering:
- ✅ Recovery detection (immediate, delayed, no recovery)
- ✅ Edge cases (empty data, insufficient data, invalid inputs)
- ✅ Statistical calculations (win rate, averages, percentiles)
- ✅ Data validation (prices, dividends, cross-validation)
- ✅ Error handling

## Adding New Tests

1. Create test file: `test_<module_name>.py`
2. Import pytest and modules to test
3. Create test classes (optional but recommended)
4. Write test methods starting with `test_`
5. Run tests to verify

Example:
```python
def test_my_function():
    result = my_function(input_data)
    assert result == expected_output
```
