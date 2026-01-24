"""
Shared utilities for Dividend Recovery System.
"""
from .recovery_analysis import find_recovery, analyze_all_dividends, calculate_recovery_statistics
from src.database.database import get_database_session, get_price_dataframe, session_scope, DatabaseError
from .validation import validate_price_data, validate_dividend_data, ValidationError
from .logging_config import get_logger, OperationLogger, setup_logging
from .pattern_analysis import (
    extract_pre_dividend_features,
    calculate_recovery_metrics as calculate_pattern_recovery_metrics,
    analyze_dividend,
    find_correlations,
    find_similar_patterns,
    WindowFeatures,
    RecoveryMetrics,
)
from .clustering import (
    analyze_dividend_clusters,
    get_cluster_interpretation,
    predict_cluster_for_new_dividend,
    ClusterMethod,
    ClusterStats,
    ClusteringResult,
)

__all__ = [
    'find_recovery',
    'analyze_all_dividends',
    'calculate_recovery_statistics',
    'get_database_session',
    'get_price_dataframe',
    'session_scope',
    'DatabaseError',
    'validate_price_data',
    'validate_dividend_data',
    'ValidationError',
    'get_logger',
    'OperationLogger',
    'setup_logging',
    'extract_pre_dividend_features',
    'calculate_pattern_recovery_metrics',
    'analyze_dividend',
    'find_correlations',
    'find_similar_patterns',
    'WindowFeatures',
    'RecoveryMetrics',
    'analyze_dividend_clusters',
    'get_cluster_interpretation',
    'predict_cluster_for_new_dividend',
    'ClusterMethod',
    'ClusterStats',
    'ClusteringResult',
]
