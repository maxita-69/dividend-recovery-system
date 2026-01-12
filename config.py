"""
Centralized configuration for Dividend Recovery System.
All hardcoded values should be managed here.
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

# External data providers configuration
FMP_API_KEY = os.getenv("FMP_API_KEY")
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"


# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
DATABASE_PATH = DATA_DIR / "dividend_recovery.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


@dataclass
class TradingCosts:
    """Fineco trading costs configuration."""

    # Commission rate (0.19% with min/max bounds)
    commission_rate: float = 0.0019
    commission_min: float = 2.95  # EUR
    commission_max: float = 19.00  # EUR

    # Italian Tobin Tax
    tobin_tax_rate: float = 0.001  # 0.1%

    # Overnight financing costs
    euribor_1m: float = 0.025  # 2.5% - Update monthly from ECB
    overnight_spread: float = 0.0799  # 7.99%

    @property
    def total_overnight_rate(self) -> float:
        """Total overnight financing rate (Euribor + spread)."""
        return self.euribor_1m + self.overnight_spread

    def calculate_commission(self, transaction_value: float) -> float:
        """Calculate commission with min/max bounds."""
        commission = transaction_value * self.commission_rate
        return max(self.commission_min, min(commission, self.commission_max))

    def calculate_tobin_tax(self, transaction_value: float) -> float:
        """Calculate Italian Tobin Tax."""
        return transaction_value * self.tobin_tax_rate

    def calculate_overnight_cost(self, position_value: float, days: int) -> float:
        """Calculate overnight financing cost."""
        daily_rate = self.total_overnight_rate / 365
        return position_value * daily_rate * days


@dataclass
class AnalysisConfig:
    """Configuration for recovery analysis."""

    # Recovery analysis parameters
    max_recovery_days: int = 30  # Maximum days to wait for recovery
    recovery_threshold: float = 1.0  # Target price multiplier (1.0 = break-even)

    # Price evolution analysis windows
    evolution_windows: list[int] = field(default_factory=lambda: [5, 10, 15, 20, 30])

    # Statistics parameters
    percentiles: list[float] = field(default_factory=lambda: [0.25, 0.5, 0.75])

    # Data quality filters
    min_price_history_days: int = 60  # Minimum price history required
    min_volume: int = 0  # Minimum daily volume (0 = no filter)


@dataclass
class PatternAnalysisConfig:
    """Configuration for pattern analysis (pre-dividend → post-dividend correlations)."""

    # Pre-dividend lookback period
    lookback_days: int = 40  # Days to analyze before dividend

    # Post-dividend recovery period
    recovery_days: int = 15  # Days to analyze after dividend

    # Time windows for feature extraction (relative to ex-date)
    # Format: (start_day, end_day) where negative = before ex-date
    time_windows: dict = field(default_factory=lambda: {
        'D-40_D-30': (-40, -30),
        'D-30_D-20': (-30, -20),
        'D-20_D-15': (-20, -15),
        'D-15_D-5': (-15, -5),
        'D-5_D-3': (-5, -3),
        'D-3_D-1': (-3, -1),
    })

    # Pattern matching parameters
    similarity_threshold: float = 0.8  # Cosine similarity threshold for pattern matching
    min_patterns_for_analysis: int = 3  # Minimum dividends needed for pattern analysis

    # Feature extraction
    extract_volume_features: bool = True
    extract_volatility_features: bool = True
    extract_trend_features: bool = True

    # Correlation analysis
    min_correlation_threshold: float = 0.3  # Minimum correlation to report
    correlation_method: str = 'pearson'  # 'pearson', 'spearman', or 'kendall'


@dataclass
class DataCollectionConfig:
    """Configuration for data download and updates."""

    # Yahoo Finance parameters
    start_date: str = "2020-01-01"  # Default start date for downloads

    # Rate limiting
    download_delay: float = 3.0  # Seconds between downloads
    max_retries: int = 3
    retry_delay: float = 5.0  # Seconds

    # Data validation
    validate_prices: bool = True  # Check for price consistency
    allow_zero_prices: bool = False

    # Update scheduling
    update_hour: int = 18  # Hour to run daily updates (after market close)

    # Logging
    log_to_file: bool = True
    log_level: str = "INFO"


@dataclass
class StreamlitConfig:
    """Configuration for Streamlit dashboard."""

    # UI defaults
    default_stock: str = "ENEL.MI"
    default_max_recovery_days: int = 30

    # Chart settings
    chart_height: int = 600
    chart_theme: str = "plotly"

    # Caching
    cache_ttl: int = 3600  # Cache time-to-live in seconds

    # Display options
    show_debug_info: bool = False
    date_format: str = "%Y-%m-%d"
    currency_format: str = "€{:.2f}"
    percent_format: str = "{:.2f}%"


class Config:
    """Main configuration class - singleton."""

    _instance: Optional['Config'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Initialize sub-configurations
        self.trading_costs = TradingCosts()
        self.analysis = AnalysisConfig()
        self.pattern_analysis = PatternAnalysisConfig()
        self.data_collection = DataCollectionConfig()
        self.streamlit = StreamlitConfig()

        # Database configuration
        self.database_url = f"sqlite:///{DATABASE_PATH}"
        self.database_echo = False  # SQLAlchemy echo (debug SQL)

        # Environment overrides
        self._load_from_environment()

        self._initialized = True

    def _load_from_environment(self):
        """Load configuration from environment variables if present."""

        # Trading costs
        if euribor := os.getenv("EURIBOR_1M"):
            self.trading_costs.euribor_1m = float(euribor)

        if overnight_spread := os.getenv("OVERNIGHT_SPREAD"):
            self.trading_costs.overnight_spread = float(overnight_spread)

        # Analysis
        if max_days := os.getenv("MAX_RECOVERY_DAYS"):
            self.analysis.max_recovery_days = int(max_days)

        # Data collection
        if start_date := os.getenv("START_DATE"):
            self.data_collection.start_date = start_date

        # Database
        if db_path := os.getenv("DATABASE_PATH"):
            self.database_url = f"sqlite:///{db_path}"

        if db_echo := os.getenv("DATABASE_ECHO"):
            self.database_echo = db_echo.lower() in ("true", "1", "yes")

    def get_database_session(self):
        """Create a new database session."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(self.database_url, echo=self.database_echo)
        Session = sessionmaker(bind=engine)
        return Session()

    def update_euribor(self, new_rate: float):
        """Update Euribor rate (should be done monthly)."""
        self.trading_costs.euribor_1m = new_rate
        self._log_config_change("euribor_1m", new_rate)

    def _log_config_change(self, key: str, value):
        """Log configuration changes."""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} - Config updated: {key} = {value}\n"

        log_file = LOGS_DIR / "config_changes.log"
        with open(log_file, "a") as f:
            f.write(log_entry)

    def to_dict(self) -> dict:
        """Export configuration as dictionary for logging/debugging."""
        return {
            "trading_costs": {
                "commission_rate": self.trading_costs.commission_rate,
                "commission_min": self.trading_costs.commission_min,
                "commission_max": self.trading_costs.commission_max,
                "tobin_tax_rate": self.trading_costs.tobin_tax_rate,
                "euribor_1m": self.trading_costs.euribor_1m,
                "overnight_spread": self.trading_costs.overnight_spread,
            },
            "analysis": {
                "max_recovery_days": self.analysis.max_recovery_days,
                "recovery_threshold": self.analysis.recovery_threshold,
                "evolution_windows": self.analysis.evolution_windows,
            },
            "pattern_analysis": {
                "lookback_days": self.pattern_analysis.lookback_days,
                "recovery_days": self.pattern_analysis.recovery_days,
                "similarity_threshold": self.pattern_analysis.similarity_threshold,
                "min_correlation_threshold": self.pattern_analysis.min_correlation_threshold,
            },
            "data_collection": {
                "start_date": self.data_collection.start_date,
                "download_delay": self.data_collection.download_delay,
                "max_retries": self.data_collection.max_retries,
            },
            "database_url": self.database_url,
        }


# Global singleton instance
config = Config()


# Convenience functions for backward compatibility
def get_config() -> Config:
    """Get global configuration instance."""
    return config


def get_database_path() -> Path:
    """Get database file path."""
    return DATABASE_PATH


def get_trading_costs() -> TradingCosts:
    """Get trading costs configuration."""
    return config.trading_costs


if __name__ == "__main__":
    # Test configuration
    cfg = get_config()
    print("Configuration loaded successfully:")
    print(f"Database: {DATABASE_PATH}")
    print(f"Trading costs: Commission={cfg.trading_costs.commission_rate}, Tobin={cfg.trading_costs.tobin_tax_rate}")
    print(f"Overnight rate: {cfg.trading_costs.total_overnight_rate:.4f} ({cfg.trading_costs.total_overnight_rate*100:.2f}%)")
    print(f"Max recovery days: {cfg.analysis.max_recovery_days}")

    # Test cost calculations
    print("\nExample cost calculations:")
    trade_value = 10000  # €10,000 trade
    print(f"Trade value: €{trade_value:,.2f}")
    print(f"Commission: €{cfg.trading_costs.calculate_commission(trade_value):.2f}")
    print(f"Tobin tax: €{cfg.trading_costs.calculate_tobin_tax(trade_value):.2f}")
    print(f"Overnight cost (10 days): €{cfg.trading_costs.calculate_overnight_cost(trade_value, 10):.2f}")
