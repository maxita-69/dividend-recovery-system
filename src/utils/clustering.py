"""
Dividend Pattern Clustering - Identificazione cluster predittivi pre-dividend.

Questo modulo implementa clustering non supervisionato per identificare pattern
nei comportamenti pre-dividend che predicono performance post-dividend.

Approccio:
1. Estrazione features pre-dividend (trend, volatilità, volume, indicatori tecnici)
2. Normalizzazione e clustering (KMeans, HDBSCAN)
3. Analisi recovery per cluster
4. Identificazione cluster predittivi

Author: Dividend Recovery System
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from scipy import stats

from config import get_config
from .logging_config import get_logger

logger = get_logger(__name__)


class ClusterMethod(Enum):
    """Metodi di clustering disponibili."""
    KMEANS = "kmeans"
    DBSCAN = "dbscan"


@dataclass
class ClusterStats:
    """Statistiche di un singolo cluster."""
    cluster_id: int
    n_samples: int

    # Recovery metrics
    avg_gap_pct: float
    avg_recovery_d5_pct: float
    avg_recovery_d10_pct: float
    avg_recovery_d15_pct: float
    avg_recovery_d30_pct: float

    # Probabilità recovery
    pct_positive_d5: float  # % dividendi con recovery > 0 a D+5
    pct_positive_d10: float
    pct_positive_d15: float
    pct_recovery_50pct_d10: float  # % che recupera almeno 50% gap entro D+10
    pct_recovery_100pct_d30: float  # % che recupera 100% gap entro D+30

    # Statistiche pre-dividend
    avg_trend_pre: float
    avg_vol_pre: float
    avg_rsi_d1: float
    avg_stoch_k_d1: float

    # Qualità cluster
    cohesion: float  # Distanza media intra-cluster

    def __repr__(self) -> str:
        return (
            f"Cluster {self.cluster_id}: {self.n_samples} samples, "
            f"Rec D+10: {self.avg_recovery_d10_pct:.2f}%, "
            f"50% Recovery D+10: {self.pct_recovery_50pct_d10:.1f}%"
        )


@dataclass
class ClusteringResult:
    """Risultato completo dell'analisi di clustering."""
    method: ClusterMethod
    n_clusters: int
    labels: np.ndarray
    cluster_stats: List[ClusterStats]

    # Metriche qualità
    silhouette: float
    calinski_harabasz: float

    # Feature importance (per interpretabilità)
    feature_names: List[str]
    feature_importance: Dict[str, float]

    # Cluster più performanti
    best_cluster_id: int  # Cluster con miglior recovery
    worst_cluster_id: int  # Cluster con peggior recovery

    # DataFrame originale con labels
    df_labeled: pd.DataFrame = field(default_factory=pd.DataFrame)


def get_clustering_features() -> List[str]:
    """
    Definisce le features usate per il clustering.

    Usa features pre-dividend che possono predire il comportamento post-dividend.
    """
    return [
        # Trend pre-dividend
        'trend_pre',

        # Volatilità
        'vol_pre',

        # Indicatori tecnici
        'rsi_d1',
        'stoch_k_d1',

        # Gap (correlato a dividend yield)
        'gap_pct',

        # Volume
        'volume_mean_pre',
    ]


def prepare_features(
    df: pd.DataFrame,
    features: Optional[List[str]] = None,
    scaler_type: str = 'robust'
) -> Tuple[np.ndarray, List[str], Any]:
    """
    Prepara le features per il clustering.

    Args:
        df: DataFrame con metriche dividendi
        features: Lista features da usare (default: get_clustering_features())
        scaler_type: Tipo di scaler ('standard' o 'robust')

    Returns:
        X_scaled: Features normalizzate
        valid_features: Features effettivamente usate
        scaler: Scaler fitted (per inverse transform)
    """
    if features is None:
        features = get_clustering_features()

    # Filtra features presenti nel DataFrame
    valid_features = [f for f in features if f in df.columns]

    if len(valid_features) < 3:
        raise ValueError(
            f"Features insufficienti per clustering: {len(valid_features)} < 3. "
            f"Richieste: {features}, trovate: {list(df.columns)}"
        )

    logger.info(f"Usando {len(valid_features)} features: {valid_features}")

    # Estrai e gestisci NaN
    X = df[valid_features].copy()

    # Log missing values
    missing_pct = X.isnull().sum() / len(X) * 100
    for col, pct in missing_pct.items():
        if pct > 0:
            logger.warning(f"Feature {col}: {pct:.1f}% valori mancanti")

    # Imputa NaN con mediana (robusto agli outlier)
    X = X.fillna(X.median())

    # Normalizzazione
    if scaler_type == 'robust':
        scaler = RobustScaler()  # Robusto agli outlier
    else:
        scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    return X_scaled, valid_features, scaler


def find_optimal_k(
    X: np.ndarray,
    k_range: Tuple[int, int] = (2, 8)
) -> Tuple[int, Dict[int, float]]:
    """
    Trova il numero ottimale di cluster usando silhouette score.

    Args:
        X: Features normalizzate
        k_range: Range di k da testare (min, max)

    Returns:
        optimal_k: Numero ottimale di cluster
        scores: Silhouette scores per ogni k
    """
    if len(X) < k_range[1]:
        k_range = (2, max(2, len(X) - 1))

    scores = {}

    for k in range(k_range[0], k_range[1] + 1):
        if k >= len(X):
            break

        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        # Silhouette richiede almeno 2 cluster con samples
        unique_labels = np.unique(labels)
        if len(unique_labels) < 2:
            continue

        score = silhouette_score(X, labels)
        scores[k] = score
        logger.debug(f"k={k}: silhouette={score:.4f}")

    if not scores:
        return 2, {2: 0.0}

    optimal_k = max(scores, key=scores.get)
    logger.info(f"Numero ottimale cluster: {optimal_k} (silhouette={scores[optimal_k]:.4f})")

    return optimal_k, scores


def perform_clustering(
    X: np.ndarray,
    method: ClusterMethod = ClusterMethod.KMEANS,
    n_clusters: Optional[int] = None,
    **kwargs
) -> Tuple[np.ndarray, Any]:
    """
    Esegue il clustering.

    Args:
        X: Features normalizzate
        method: Metodo di clustering
        n_clusters: Numero cluster (auto se None per KMeans)
        **kwargs: Parametri aggiuntivi per il clusterer

    Returns:
        labels: Label cluster per ogni sample
        model: Modello fitted
    """
    if method == ClusterMethod.KMEANS:
        if n_clusters is None:
            n_clusters, _ = find_optimal_k(X)

        model = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
            **kwargs
        )
        labels = model.fit_predict(X)

    elif method == ClusterMethod.DBSCAN:
        eps = kwargs.get('eps', 0.5)
        min_samples = kwargs.get('min_samples', 3)

        model = DBSCAN(eps=eps, min_samples=min_samples)
        labels = model.fit_predict(X)

    else:
        raise ValueError(f"Metodo non supportato: {method}")

    n_clusters_found = len(np.unique(labels[labels >= 0]))
    logger.info(f"Clustering completato: {n_clusters_found} cluster trovati")

    return labels, model


def calculate_cluster_stats(
    df: pd.DataFrame,
    labels: np.ndarray,
    X_scaled: np.ndarray
) -> List[ClusterStats]:
    """
    Calcola statistiche dettagliate per ogni cluster.

    Args:
        df: DataFrame originale con metriche
        labels: Label cluster
        X_scaled: Features normalizzate (per calcolo cohesion)

    Returns:
        Lista di ClusterStats per ogni cluster
    """
    df_work = df.copy()
    df_work['cluster'] = labels

    stats_list = []

    for cluster_id in sorted(df_work['cluster'].unique()):
        if cluster_id == -1:  # Skip noise in DBSCAN
            continue

        cluster_df = df_work[df_work['cluster'] == cluster_id]
        n_samples = len(cluster_df)

        if n_samples == 0:
            continue

        # Calcola cohesion (distanza media intra-cluster)
        cluster_mask = labels == cluster_id
        if cluster_mask.sum() > 1:
            cluster_points = X_scaled[cluster_mask]
            centroid = cluster_points.mean(axis=0)
            distances = np.sqrt(((cluster_points - centroid) ** 2).sum(axis=1))
            cohesion = float(distances.mean())
        else:
            cohesion = 0.0

        # Helper per calcolo sicuro delle medie
        def safe_mean(series):
            valid = series.dropna()
            return float(valid.mean()) if len(valid) > 0 else np.nan

        def safe_pct(series, threshold=0):
            valid = series.dropna()
            if len(valid) == 0:
                return np.nan
            return float((valid > threshold).sum() / len(valid) * 100)

        # Recovery metrics
        avg_gap = safe_mean(cluster_df['gap_pct'])
        avg_rec_d5 = safe_mean(cluster_df['recovery_d5_pct'])
        avg_rec_d10 = safe_mean(cluster_df['recovery_d10_pct'])
        avg_rec_d15 = safe_mean(cluster_df['recovery_d15_pct'])
        avg_rec_d30 = safe_mean(cluster_df.get('recovery_d30_pct', pd.Series()))

        # Probabilità recovery
        pct_pos_d5 = safe_pct(cluster_df['recovery_d5_pct'])
        pct_pos_d10 = safe_pct(cluster_df['recovery_d10_pct'])
        pct_pos_d15 = safe_pct(cluster_df['recovery_d15_pct'])

        # Recovery 50% gap entro D+10
        if 'gap_pct' in cluster_df.columns and 'recovery_d10_pct' in cluster_df.columns:
            half_gap_target = cluster_df['gap_pct'].abs() * 0.5
            recovered_50 = cluster_df['recovery_d10_pct'] >= -half_gap_target
            pct_rec_50_d10 = float(recovered_50.sum() / n_samples * 100)
        else:
            pct_rec_50_d10 = np.nan

        # Recovery 100% gap entro D+30
        if 'gap_pct' in cluster_df.columns:
            rec_col = 'recovery_d30_pct' if 'recovery_d30_pct' in cluster_df.columns else 'recovery_d15_pct'
            if rec_col in cluster_df.columns:
                full_gap_target = cluster_df['gap_pct'].abs()
                recovered_100 = cluster_df[rec_col] >= -full_gap_target
                pct_rec_100_d30 = float(recovered_100.sum() / n_samples * 100)
            else:
                pct_rec_100_d30 = np.nan
        else:
            pct_rec_100_d30 = np.nan

        # Pre-dividend stats
        avg_trend = safe_mean(cluster_df.get('trend_pre', pd.Series()))
        avg_vol = safe_mean(cluster_df.get('vol_pre', pd.Series()))
        avg_rsi = safe_mean(cluster_df.get('rsi_d1', pd.Series()))
        avg_stoch = safe_mean(cluster_df.get('stoch_k_d1', pd.Series()))

        stats = ClusterStats(
            cluster_id=int(cluster_id),
            n_samples=n_samples,
            avg_gap_pct=avg_gap,
            avg_recovery_d5_pct=avg_rec_d5,
            avg_recovery_d10_pct=avg_rec_d10,
            avg_recovery_d15_pct=avg_rec_d15,
            avg_recovery_d30_pct=avg_rec_d30 if not np.isnan(avg_rec_d30) else avg_rec_d15,
            pct_positive_d5=pct_pos_d5,
            pct_positive_d10=pct_pos_d10,
            pct_positive_d15=pct_pos_d15,
            pct_recovery_50pct_d10=pct_rec_50_d10,
            pct_recovery_100pct_d30=pct_rec_100_d30,
            avg_trend_pre=avg_trend,
            avg_vol_pre=avg_vol,
            avg_rsi_d1=avg_rsi,
            avg_stoch_k_d1=avg_stoch,
            cohesion=cohesion
        )

        stats_list.append(stats)
        logger.debug(f"Cluster {cluster_id}: {stats}")

    return stats_list


def calculate_feature_importance(
    X: np.ndarray,
    labels: np.ndarray,
    feature_names: List[str]
) -> Dict[str, float]:
    """
    Calcola l'importanza di ogni feature per la separazione dei cluster.

    Usa ANOVA F-score per misurare quanto ogni feature discrimina tra cluster.

    Args:
        X: Features normalizzate
        labels: Label cluster
        feature_names: Nomi delle features

    Returns:
        Dict feature_name -> importance score (0-1 normalizzato)
    """
    importance = {}

    # Rimuovi noise labels (-1)
    valid_mask = labels >= 0
    X_valid = X[valid_mask]
    labels_valid = labels[valid_mask]

    if len(np.unique(labels_valid)) < 2:
        return {f: 0.0 for f in feature_names}

    for i, feature in enumerate(feature_names):
        # ANOVA F-test
        groups = [X_valid[labels_valid == c, i] for c in np.unique(labels_valid)]
        groups = [g for g in groups if len(g) > 0]

        if len(groups) < 2:
            importance[feature] = 0.0
            continue

        try:
            f_stat, p_value = stats.f_oneway(*groups)
            # Usa F-statistic come importanza (normalizzata dopo)
            importance[feature] = float(f_stat) if not np.isnan(f_stat) else 0.0
        except Exception:
            importance[feature] = 0.0

    # Normalizza a [0, 1]
    max_imp = max(importance.values()) if importance else 1.0
    if max_imp > 0:
        importance = {k: v / max_imp for k, v in importance.items()}

    # Ordina per importanza
    importance = dict(sorted(importance.items(), key=lambda x: -x[1]))

    logger.info(f"Feature importance: {importance}")

    return importance


def analyze_dividend_clusters(
    df: pd.DataFrame,
    method: ClusterMethod = ClusterMethod.KMEANS,
    n_clusters: Optional[int] = None,
    features: Optional[List[str]] = None
) -> ClusteringResult:
    """
    Analisi completa dei cluster di dividendi.

    Funzione principale che orchestra l'intero processo di clustering.

    Args:
        df: DataFrame con metriche dividendi (output di compute_metrics_for_dividend)
        method: Metodo di clustering
        n_clusters: Numero cluster (auto se None)
        features: Features da usare (auto se None)

    Returns:
        ClusteringResult con tutte le statistiche e interpretazioni

    Example:
        >>> result = analyze_dividend_clusters(metrics_df)
        >>> print(f"Best cluster: {result.best_cluster_id}")
        >>> print(f"Features: {result.feature_importance}")
    """
    if len(df) < 5:
        raise ValueError(f"Dati insufficienti per clustering: {len(df)} < 5 dividendi")

    logger.info(f"Avvio clustering su {len(df)} dividendi")

    # 1. Prepara features
    X_scaled, valid_features, scaler = prepare_features(df, features)

    # 2. Esegui clustering
    labels, model = perform_clustering(X_scaled, method, n_clusters)

    # 3. Calcola metriche qualità
    unique_labels = np.unique(labels[labels >= 0])
    n_clusters_found = len(unique_labels)

    if n_clusters_found < 2:
        logger.warning("Trovato solo 1 cluster - dati troppo omogenei")
        silhouette = 0.0
        calinski = 0.0
    else:
        valid_mask = labels >= 0
        silhouette = silhouette_score(X_scaled[valid_mask], labels[valid_mask])
        calinski = calinski_harabasz_score(X_scaled[valid_mask], labels[valid_mask])

    # 4. Calcola statistiche per cluster
    cluster_stats = calculate_cluster_stats(df, labels, X_scaled)

    # 5. Calcola feature importance
    feature_importance = calculate_feature_importance(X_scaled, labels, valid_features)

    # 6. Identifica best/worst cluster (basato su recovery D+10)
    if cluster_stats:
        valid_stats = [s for s in cluster_stats if not np.isnan(s.avg_recovery_d10_pct)]
        if valid_stats:
            best_cluster = max(valid_stats, key=lambda s: s.avg_recovery_d10_pct)
            worst_cluster = min(valid_stats, key=lambda s: s.avg_recovery_d10_pct)
            best_id = best_cluster.cluster_id
            worst_id = worst_cluster.cluster_id
        else:
            best_id = worst_id = 0
    else:
        best_id = worst_id = 0

    # 7. Crea DataFrame con labels
    df_labeled = df.copy()
    df_labeled['cluster'] = labels

    result = ClusteringResult(
        method=method,
        n_clusters=n_clusters_found,
        labels=labels,
        cluster_stats=cluster_stats,
        silhouette=silhouette,
        calinski_harabasz=calinski,
        feature_names=valid_features,
        feature_importance=feature_importance,
        best_cluster_id=best_id,
        worst_cluster_id=worst_id,
        df_labeled=df_labeled
    )

    logger.info(
        f"Clustering completato: {n_clusters_found} cluster, "
        f"silhouette={silhouette:.4f}, best_cluster={best_id}"
    )

    return result


def get_cluster_interpretation(result: ClusteringResult) -> Dict[int, str]:
    """
    Genera interpretazione testuale per ogni cluster.

    Args:
        result: Risultato del clustering

    Returns:
        Dict cluster_id -> descrizione testuale
    """
    interpretations = {}

    for stats in result.cluster_stats:
        cid = stats.cluster_id

        # Trend interpretation
        if stats.avg_trend_pre > 0.01:
            trend_desc = "trend positivo pre-dividend"
        elif stats.avg_trend_pre < -0.01:
            trend_desc = "trend negativo pre-dividend"
        else:
            trend_desc = "trend neutro pre-dividend"

        # RSI interpretation
        if stats.avg_rsi_d1 > 70:
            rsi_desc = "RSI in ipercomprato"
        elif stats.avg_rsi_d1 < 30:
            rsi_desc = "RSI in ipervenduto"
        else:
            rsi_desc = "RSI neutro"

        # Recovery interpretation
        if stats.pct_positive_d10 >= 80:
            recovery_desc = "ALTA probabilità recovery (>80%)"
        elif stats.pct_positive_d10 >= 60:
            recovery_desc = "MEDIA probabilità recovery (60-80%)"
        else:
            recovery_desc = "BASSA probabilità recovery (<60%)"

        # Label sintetica
        if cid == result.best_cluster_id:
            label = "BEST PERFORMER"
        elif cid == result.worst_cluster_id:
            label = "WORST PERFORMER"
        else:
            label = "NEUTRAL"

        interpretation = (
            f"[{label}] Cluster {cid}: {stats.n_samples} dividendi. "
            f"{trend_desc}, {rsi_desc}. "
            f"{recovery_desc}. "
            f"Recovery medio D+10: {stats.avg_recovery_d10_pct:.2f}%"
        )

        interpretations[cid] = interpretation

    return interpretations


def predict_cluster_for_new_dividend(
    new_metrics: Dict[str, float],
    result: ClusteringResult,
    scaler: Any
) -> Tuple[int, ClusterStats]:
    """
    Predice il cluster per un nuovo dividendo basandosi sulle metriche pre-dividend.

    Args:
        new_metrics: Metriche del nuovo dividendo
        result: Risultato clustering precedente
        scaler: Scaler usato per normalizzazione

    Returns:
        cluster_id: Cluster predetto
        cluster_stats: Statistiche del cluster (per inferenza recovery)
    """
    # Estrai features rilevanti
    X_new = np.array([[new_metrics.get(f, 0) for f in result.feature_names]])

    # Normalizza
    X_new_scaled = scaler.transform(X_new)

    # Trova cluster più vicino (usa centroidi da KMeans)
    if result.method == ClusterMethod.KMEANS:
        # Ricalcola centroidi dai dati
        df = result.df_labeled
        X_all, _, _ = prepare_features(df, result.feature_names)

        min_dist = float('inf')
        predicted_cluster = 0

        for stats in result.cluster_stats:
            cluster_mask = df['cluster'] == stats.cluster_id
            if cluster_mask.sum() == 0:
                continue
            centroid = X_all[cluster_mask].mean(axis=0)
            dist = np.sqrt(((X_new_scaled[0] - centroid) ** 2).sum())

            if dist < min_dist:
                min_dist = dist
                predicted_cluster = stats.cluster_id
    else:
        # Fallback: cluster con caratteristiche più simili
        predicted_cluster = result.best_cluster_id

    # Trova stats del cluster
    cluster_stats = next(
        (s for s in result.cluster_stats if s.cluster_id == predicted_cluster),
        result.cluster_stats[0] if result.cluster_stats else None
    )

    return predicted_cluster, cluster_stats


if __name__ == "__main__":
    # Test con dati mock
    import random

    np.random.seed(42)
    random.seed(42)

    # Genera dati mock simili a output di compute_metrics_for_dividend
    n_samples = 30
    mock_data = {
        'ex_date': pd.date_range('2020-01-01', periods=n_samples, freq='QE'),
        'trend_pre': np.random.normal(0.001, 0.01, n_samples),
        'vol_pre': np.random.uniform(0.01, 0.03, n_samples),
        'rsi_d1': np.random.uniform(30, 70, n_samples),
        'stoch_k_d1': np.random.uniform(20, 80, n_samples),
        'gap_pct': np.random.uniform(-5, -2, n_samples),
        'volume_mean_pre': np.random.uniform(1e6, 5e6, n_samples),
        'recovery_d5_pct': np.random.normal(-2, 1, n_samples),
        'recovery_d10_pct': np.random.normal(-1, 1.5, n_samples),
        'recovery_d15_pct': np.random.normal(0, 2, n_samples),
    }

    df = pd.DataFrame(mock_data)

    print("=== Test Clustering Module ===\n")

    try:
        result = analyze_dividend_clusters(df)

        print(f"Metodo: {result.method.value}")
        print(f"Cluster trovati: {result.n_clusters}")
        print(f"Silhouette Score: {result.silhouette:.4f}")
        print(f"Calinski-Harabasz: {result.calinski_harabasz:.2f}")
        print(f"\nBest Cluster: {result.best_cluster_id}")
        print(f"Worst Cluster: {result.worst_cluster_id}")

        print("\n--- Statistiche per Cluster ---")
        for stats in result.cluster_stats:
            print(f"\n{stats}")
            print(f"  Recovery D+10: {stats.avg_recovery_d10_pct:.2f}%")
            print(f"  % Positive D+10: {stats.pct_positive_d10:.1f}%")

        print("\n--- Feature Importance ---")
        for feat, imp in result.feature_importance.items():
            print(f"  {feat}: {imp:.4f}")

        print("\n--- Interpretazioni ---")
        interp = get_cluster_interpretation(result)
        for cid, desc in interp.items():
            print(f"  {desc}")

        print("\n=== Test completato con successo ===")

    except Exception as e:
        print(f"Errore: {e}")
        import traceback
        traceback.print_exc()
