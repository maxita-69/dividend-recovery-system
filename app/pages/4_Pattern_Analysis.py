# pattern_analysis.py
"""
Pattern Analysis - Analisi comportamento titolo attorno ai dividendi
Sostituzione totale: statistiche di affidabilità, grafici pre/post, curva media normalizzata.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import timedelta

# Aggiungi src al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'app'))

# Import dal progetto
from src.database.models import Stock, Dividend, PriceData
from src.utils import get_database_session, get_logger, OperationLogger
from src.utils.database import get_price_dataframe
from config import get_config
from auth import require_authentication

logger = get_logger(__name__)
cfg = get_config()

st.set_page_config(page_title="Pattern Analysis", page_icon="🔍", layout="wide")

# Authentication
require_authentication()

# ---------------------------------------------------------------------
# FUNZIONI DI UTILITÀ
# ---------------------------------------------------------------------
def get_session():
    """Restituisce una nuova sessione DB (non cached)."""
    return get_database_session()

def safe_pct(a, b):
    """Percentuale sicura: (a - b) / b, gestisce divisione per zero."""
    try:
        return (a - b) / b
    except Exception:
        return np.nan

def rolling_trend(series):
    """Semplice pendenza lineare su una serie (regressione OLS su index)."""
    if series.dropna().shape[0] < 2:
        return np.nan
    x = np.arange(len(series))
    y = series.values
    # rimuovi NaN
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return np.nan
    x = x[mask]
    y = y[mask]
    A = np.vstack([x, np.ones(len(x))]).T
    m, _ = np.linalg.lstsq(A, y, rcond=None)[0]
    return m

def compute_technical_indicators(df):
    """Calcola RSI e Stocastico semplici su DataFrame con colonne 'close' e 'high'/'low'."""
    out = {}
    close = df['close']
    # RSI (14)
    delta = close.diff()
    up = delta.clip(lower=0).rolling(14).mean()
    down = -delta.clip(upper=0).rolling(14).mean()
    rs = up / down
    rsi = 100 - (100 / (1 + rs))
    out['rsi_d1'] = float(rsi.iloc[-1]) if not rsi.iloc[-1:].isna().all() else np.nan

    # Stocastico %K (14,3)
    low14 = df['low'].rolling(14).min()
    high14 = df['high'].rolling(14).max()
    stoch_k = 100 * (close - low14) / (high14 - low14)
    out['stoch_k_d1'] = float(stoch_k.iloc[-1]) if not stoch_k.iloc[-1:].isna().all() else np.nan

    return out

# ---------------------------------------------------------------------
# ESTRAZIONE DATI E PREPARAZIONE
# ---------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_stocks():
    """Carica lista titoli (cached per 5 minuti)."""
    session = get_session()
    try:
        return session.query(Stock).all()
    finally:
        session.close()

def load_dividends_for_stock(stock_id):
    """Carica dividendi ordinati per data."""
    session = get_session()
    try:
        return session.query(Dividend).filter_by(stock_id=stock_id).order_by(Dividend.ex_date).all()
    finally:
        session.close()

def load_price_window(stock_id, start_date, end_date):
    """
    Carica OHLCV tra start_date e end_date usando la funzione esistente.
    Restituisce DataFrame con index=date.
    """
    session = get_session()
    try:
        df = get_price_dataframe(
            session,
            stock_id,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        if df is None:
            return pd.DataFrame()
        return df
    finally:
        session.close()

# ---------------------------------------------------------------------
# METRICHE PER OGNI DIVIDENDO
# ---------------------------------------------------------------------
def compute_metrics_for_dividend(stock, dividend, pre_window=10, post_window=45):
    """
    Calcola metriche per un singolo dividendo:
    - gap %
    - recovery a D+5, D+10, D+15, D+30
    - giorni per recuperare 50% gap
    - trend pre (D-pre_window -> D-1)
    - volatilità pre (std dei rendimenti)
    - volume medio pre
    - RSI e Stocastico a D-1
    - minimo entro D+3 (boolean)
    """
    ex_date = dividend.ex_date
    d_minus_1 = ex_date - timedelta(days=1)
    start_pre = ex_date - timedelta(days=pre_window)
    end_post = ex_date + timedelta(days=post_window)

    # Carica finestra prezzi
    try:
        prices = load_price_window(stock.id, start_pre, end_post)
    except Exception as e:
        logger.error(f"Errore caricamento prezzi per {stock.ticker} {ex_date}: {e}")
        return None

    if prices.empty:
        logger.warning(f"Nessun dato prezzo per {stock.ticker} nel periodo {start_pre} → {end_post} (dividendo {ex_date})")
        return None

    # Assicuriamoci che le date siano DatetimeIndex e ordinate
    prices = prices.sort_index()

    # Prezzi di riferimento
    try:
        p_d1 = float(prices.loc[d_minus_1]['close'])
    except Exception:
        # Se manca D-1, prendi il valore più vicino precedente
        try:
            p_d1 = float(prices[prices.index < ex_date]['close'].iloc[-1])
        except Exception:
            return None

    try:
        p_d0 = float(prices.loc[ex_date]['close'])
    except Exception:
        # Se manca D0, prendi il primo valore >= ex_date
        try:
            p_d0 = float(prices[prices.index >= ex_date]['close'].iloc[0])
        except Exception:
            return None

    gap_pct = safe_pct(p_d1, p_d0) * -1  # definisco gap come perdita

    # Recovery: (P_{D+n} - P_D0) / P_{D-1}
    def recovery_at(n):
        target_date = ex_date + timedelta(days=n)
        subset = prices[prices.index >= target_date]
        if subset.empty:
            return np.nan
        p_dn = float(subset['close'].iloc[0])
        return safe_pct(p_dn, p_d1)

    rec_d5 = recovery_at(5)
    rec_d10 = recovery_at(10)
    rec_d15 = recovery_at(15)
    rec_d30 = recovery_at(30)

    # Giorni per recuperare 50% del gap
    half_target_price = p_d0 + 0.5 * (p_d1 - p_d0)
    days_to_50 = np.nan
    post_prices = prices[prices.index >= ex_date]
    for i, (dt, row) in enumerate(post_prices.iterrows()):
        if row['close'] >= half_target_price:
            days_to_50 = (dt - ex_date).days
            break

    # Trend pre
    pre_prices = prices[(prices.index >= start_pre) & (prices.index < ex_date)]['close']
    trend_pre = rolling_trend(pre_prices)

    # Volatilità pre (std dei rendimenti)
    pre_returns = pre_prices.pct_change().dropna()
    vol_pre = float(pre_returns.std()) if not pre_returns.empty else np.nan

    # Volume medio pre
    vol_mean_pre = float(prices[(prices.index >= start_pre) & (prices.index < ex_date)]['volume'].mean())

    # Indicatori tecnici a D-1
    tech = compute_technical_indicators(prices[(prices.index >= start_pre) & (prices.index <= d_minus_1)])

    # Minimo entro D+3
    min_within_3 = np.nan
    subset_3 = prices[(prices.index > ex_date) & (prices.index <= ex_date + timedelta(days=3))]
    if not subset_3.empty:
        min_within_3 = float(subset_3['close'].min())

    min_within_3_flag = False
    if not np.isnan(min_within_3):
        min_within_3_flag = min_within_3 < p_d0

    metrics = {
        'ex_date': ex_date,
        'dividend': float(dividend.amount) if hasattr(dividend, 'amount') else np.nan,
        'p_d1': p_d1,
        'p_d0': p_d0,
        'gap_pct': gap_pct * 100,
        'recovery_d5_pct': rec_d5 * 100 if not np.isnan(rec_d5) else np.nan,
        'recovery_d10_pct': rec_d10 * 100 if not np.isnan(rec_d10) else np.nan,
        'recovery_d15_pct': rec_d15 * 100 if not np.isnan(rec_d15) else np.nan,
        'recovery_d30_pct': rec_d30 * 100 if not np.isnan(rec_d30) else np.nan,
        'days_to_50pct_gap': days_to_50,
        'trend_pre': trend_pre,
        'vol_pre': vol_pre,
        'volume_mean_pre': vol_mean_pre,
        'rsi_d1': tech.get('rsi_d1', np.nan),
        'stoch_k_d1': tech.get('stoch_k_d1', np.nan),
        'min_within_d3_flag': min_within_3_flag
    }

    return metrics

# ---------------------------------------------------------------------
# STATISTICHE DI AFFIDABILITÀ
# ---------------------------------------------------------------------
def compute_reliability_stats(metrics_df, last_n=5):
    """
    Calcola percentuali di affidabilità su comportamenti:
    - Recupera 50% gap entro 10 giorni
    - Recupera 100% gap entro 30 giorni
    - Sale nei 10 giorni prima (trend_pre > 0)
    - Fa minimo entro D+3 (min_within_d3_flag True)
    - Volume in aumento pre-div (volume_mean_pre > median)
    """
    if metrics_df.empty:
        return pd.DataFrame(columns=['behavior', 'storico_pct', 'recent_pct'])

    df = metrics_df.copy()

    # Comportamenti booleani
    df['rec50_d10'] = df['recovery_d10_pct'] >= (0.5 * df['gap_pct'] * -1)
    df['rec100_d30'] = df['recovery_d30_pct'] >= (-df['gap_pct'])
    df['trend_up_pre'] = df['trend_pre'] > 0
    df['min_within_d3'] = df['min_within_d3_flag'] == True

    # Volume in aumento: confronta volume_mean_pre con mediana storica
    vol_median = df['volume_mean_pre'].median()
    df['vol_increase_pre'] = df['volume_mean_pre'] > vol_median

    behaviors = {
        'Recupera 50% gap entro 10 giorni': 'rec50_d10',
        'Recupera 100% gap entro 30 giorni': 'rec100_d30',
        'Sale nei 10 giorni prima': 'trend_up_pre',
        'Fa minimo entro D+3': 'min_within_d3',
        'Volume in aumento pre-div': 'vol_increase_pre'
    }

    results = []
    total = len(df)
    recent_df = df.tail(last_n) if last_n > 0 else df

    for label, col in behaviors.items():
        storico_pct = 100.0 * df[col].sum() / total if total > 0 else np.nan
        recent_pct = 100.0 * recent_df[col].sum() / len(recent_df) if len(recent_df) > 0 else np.nan
        results.append({'behavior': label, 'storico_pct': storico_pct, 'recent_pct': recent_pct})

    return pd.DataFrame(results)

# ---------------------------------------------------------------------
# CURVA MEDIA NORMALIZZATA
# ---------------------------------------------------------------------
def build_normalized_curves(stock, dividends, pre_window=10, post_window=45):
    """
    Costruisce una matrice con prezzi normalizzati rispetto a P_{D-1}.
    Restituisce: index_days, curves dict con mean, median, pct25, pct75
    """
    windows = []
    index_days = np.arange(-pre_window, post_window + 1)

    for div in dividends:
        ex_date = div.ex_date
        start = ex_date - timedelta(days=pre_window)
        end = ex_date + timedelta(days=post_window)

        try:
            prices = load_price_window(stock.id, start, end)
        except Exception:
            continue

        if prices.empty:
            continue

        prices = prices.sort_index()

        # estrai close aligned to index_days
        series = []
        for d in index_days:
            target = ex_date + timedelta(days=int(d))
            subset = prices[prices.index >= target]
            if subset.empty:
                series.append(np.nan)
            else:
                series.append(float(subset['close'].iloc[0]))

        series = np.array(series, dtype=float)

        # normalizza rispetto a P_{D-1}
        try:
            p_d1 = float(prices[prices.index < ex_date]['close'].iloc[-1])
        except Exception:
            continue

        if np.isnan(p_d1) or p_d1 == 0:
            continue

        norm = (series - p_d1) / p_d1 * 100
        windows.append(norm)

    if len(windows) == 0:
        return index_days, None

    arr = np.vstack(windows)
    mean_curve = np.nanmean(arr, axis=0)
    median_curve = np.nanmedian(arr, axis=0)
    pct25 = np.nanpercentile(arr, 25, axis=0)
    pct75 = np.nanpercentile(arr, 75, axis=0)

    return index_days, {
        'mean': mean_curve,
        'median': median_curve,
        'pct25': pct25,
        'pct75': pct75
    }

# ---------------------------------------------------------------------
# GRAFICI
# ---------------------------------------------------------------------
def plot_prepost_candles(prices, ex_date, pre_window=10, post_window=45):
    """Crea un grafico candlestick + volume per la finestra."""
    start = ex_date - timedelta(days=pre_window)
    end = ex_date + timedelta(days=post_window)
    window = prices[(prices.index >= start) & (prices.index <= end)].copy()

    if window.empty:
        st.warning("Dati prezzi insufficienti per il grafico.")
        return

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=window.index,
        open=window['open'],
        high=window['high'],
        low=window['low'],
        close=window['close'],
        name='Prezzo'
    ))

    # Volume come barre secondarie
    fig.add_trace(go.Bar(
        x=window.index,
        y=window['volume'],
        name='Volume',
        marker_color='lightgrey',
        yaxis='y2',
        opacity=0.5
    ))

    # Layout con secondo asse per volume
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        yaxis_title='Prezzo',
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right',
            showgrid=False,
            position=0.15
        ),
        height=500
    )

    # Linee verticali
    fig.add_vline(
        x=ex_date,
        line=dict(color='red', dash='dash'),
        annotation_text='D-DAY',
        annotation_position='top left'
    )
    fig.add_vline(
        x=ex_date - timedelta(days=pre_window),
        line=dict(color='blue', dash='dot'),
        annotation_text=f'D-{pre_window}',
        annotation_position='top left'
    )
    fig.add_vline(
        x=ex_date + timedelta(days=post_window),
        line=dict(color='green', dash='dot'),
        annotation_text=f'D+{post_window}',
        annotation_position='top left'
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_mean_normalized(index_days, curves):
    """Grafico della curva media normalizzata con area percentili."""
    if curves is None:
        st.info("Dati insufficienti per costruire la curva media normalizzata.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=index_days,
        y=curves['mean'],
        mode='lines',
        name='Media',
        line=dict(color='blue')
    ))
    fig.add_trace(go.Scatter(
        x=index_days,
        y=curves['median'],
        mode='lines',
        name='Mediana',
        line=dict(color='black', dash='dash')
    ))

    # Area 25-75
    fig.add_trace(go.Scatter(
        x=np.concatenate([index_days, index_days[::-1]]),
        y=np.concatenate([curves['pct75'], curves['pct25'][::-1]]),
        fill='toself',
        fillcolor='rgba(173,216,230,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=True,
        name='25-75 percentile'
    ))

    fig.add_vline(
        x=0,
        line=dict(color='red', dash='dash'),
        annotation_text='D-DAY',
        annotation_position='top left'
    )

    fig.update_layout(
        title='Curva media normalizzata attorno ai dividendi (% vs P_{D-1})',
        xaxis_title='Giorni relativi al dividendo (D)',
        yaxis_title='% rispetto a P_{D-1}',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------
# STREAMLIT UI
# ---------------------------------------------------------------------
def main():
    st.title("🔍 Pattern Analysis")
    st.markdown("Analisi del comportamento del titolo attorno ai dividendi: statistiche di affidabilità, grafici pre/post e curva media normalizzata.")

    stocks = load_stocks()
    if not stocks:
        st.error("Nessun titolo disponibile nel database.")
        st.stop()

    stock_options = {f"{s.ticker} - {s.name}": s for s in stocks}
    selected = st.selectbox("Seleziona Titolo", list(stock_options.keys()))
    stock = stock_options[selected]

    # Slider per ultimi N dividendi
    last_n = st.slider(
        "Usa ultimi N dividendi per confronto recente",
        min_value=3,
        max_value=10,
        value=5,
        step=1
    )

    # Carica dividendi
    dividends = load_dividends_for_stock(stock.id)
    if not dividends:
        st.warning(f"Nessun dividendo per {stock.ticker}")
        st.stop()

    # Converti in DataFrame di supporto per selezione
    div_map = {
        f"{d.ex_date} - €{getattr(d, 'amount', 0):.4f}": d
        for d in dividends
    }
    selected_div_label = st.selectbox(
        "Seleziona Dividendo per analisi dettagliata",
        list(div_map.keys())
    )
    selected_dividend = div_map[selected_div_label]

    # Bottone per avviare calcoli
    if st.button("🔁 Calcola analisi"):
        with st.spinner("Calcolo metriche..."):
            try:
                with OperationLogger(logger, "pattern_analysis_new", stock_ticker=stock.ticker):
                    # Calcola metriche per tutti i dividendi
                    metrics_list = []
                    total_divs = len(dividends)
                    for i, d in enumerate(dividends, 1):
                        m = compute_metrics_for_dividend(stock, d)
                        if m:
                            metrics_list.append(m)

                    st.info(f"✅ Calcolate metriche per {len(metrics_list)} dividendi su {total_divs} totali")
                    metrics_df = pd.DataFrame(metrics_list)
                    if metrics_df.empty:
                        st.error("❌ Impossibile calcolare metriche: nessun dato di prezzo disponibile per i dividendi selezionati.")
                        st.warning(f"""
                        **Possibili cause:**
                        - Il database non contiene dati di prezzo per il periodo dei dividendi
                        - I dividendi sono troppo vecchi (es. {dividends[0].ex_date if dividends else 'N/D'})
                        - Prova a selezionare un titolo con dati più recenti o scarica i dati storici mancanti
                        """)
                        st.stop()

                    # Ordina per ex_date
                    metrics_df = metrics_df.sort_values('ex_date').reset_index(drop=True)
                    st.session_state['metrics_df'] = metrics_df
                    st.session_state['stock'] = stock
                    st.success("Metriche calcolate e salvate in sessione.")

            except Exception as e:
                st.error(f"Errore durante il calcolo: {e}")
                logger.error("Errore pattern analysis new", exc_info=True)
                import traceback
                st.code(traceback.format_exc())
                st.stop()

    # Se abbiamo metriche in session_state, mostriamo le tab
    if 'metrics_df' in st.session_state:
        metrics_df = st.session_state['metrics_df']
        stock = st.session_state['stock']

        # Prepara dati per grafici
        try:
            ex_date = selected_dividend.ex_date
            prices_full = load_price_window(
                stock.id,
                ex_date - timedelta(days=30),
                ex_date + timedelta(days=60)
            )
        except Exception as e:
            st.error(f"Errore caricamento prezzi per grafico: {e}")
            prices_full = pd.DataFrame()

        tabs = st.tabs([
            "Grafico Pre/Post",
            "Metriche Pre-Dividendo",
            "Metriche Post-Dividendo",
            "Statistiche Affidabilità",
            "Interpretazione Automatica",
            "Comportamento Medio"
        ])

        # TAB 1: Grafico Pre/Post
        with tabs[0]:
            st.header("Grafico Pre/Post Dividendo (D-10 → D+45)")
            if not prices_full.empty:
                plot_prepost_candles(prices_full, ex_date, pre_window=10, post_window=45)
            else:
                st.info("Dati prezzi non disponibili per il grafico.")

        # TAB 2: Metriche Pre-Dividendo
        with tabs[1]:
            st.header("Metriche Pre-Dividendo (dividendo selezionato)")
            row = metrics_df[metrics_df['ex_date'] == selected_dividend.ex_date]
            if row.empty:
                st.info("Metriche non disponibili per il dividendo selezionato.")
            else:
                r = row.iloc[0]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Trend D-10 → D-1 (slope)",
                        f"{r['trend_pre']:.4f}" if not np.isnan(r['trend_pre']) else "N/A"
                    )
                    st.metric(
                        "Volatilità pre (std returns)",
                        f"{r['vol_pre']:.4f}" if not np.isnan(r['vol_pre']) else "N/A"
                    )
                with col2:
                    st.metric(
                        "Volume medio pre",
                        f"{r['volume_mean_pre']:.0f}" if not np.isnan(r['volume_mean_pre']) else "N/A"
                    )
                    st.metric(
                        "RSI D-1",
                        f"{r['rsi_d1']:.2f}" if not np.isnan(r['rsi_d1']) else "N/A"
                    )
                with col3:
                    st.metric(
                        "Stocastico %K D-1",
                        f"{r['stoch_k_d1']:.2f}" if not np.isnan(r['stoch_k_d1']) else "N/A"
                    )
                    st.metric(
                        "Gap % (D0 vs D-1)",
                        f"{r['gap_pct']:.2f}%" if not np.isnan(r['gap_pct']) else "N/A"
                    )

                st.markdown("**Dettaglio**")
                st.dataframe(row.T, use_container_width=True, height=200)

        # TAB 3: Metriche Post-Dividendo
        with tabs[2]:
            st.header("Metriche Post-Dividendo (dividendo selezionato)")
            row = metrics_df[metrics_df['ex_date'] == selected_dividend.ex_date]
            if row.empty:
                st.info("Metriche non disponibili per il dividendo selezionato.")
            else:
                r = row.iloc[0]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Recovery D+5",
                        f"{r['recovery_d5_pct']:.2f}%" if not np.isnan(r['recovery_d5_pct']) else "N/A"
                    )
                    st.metric(
                        "Recovery D+10",
                        f"{r['recovery_d10_pct']:.2f}%" if not np.isnan(r['recovery_d10_pct']) else "N/A"
                    )
                with col2:
                    st.metric(
                        "Recovery D+15",
                        f"{r['recovery_d15_pct']:.2f}%" if not np.isnan(r['recovery_d15_pct']) else "N/A"
                    )
                    st.metric(
                        "Recovery D+30",
                        f"{r['recovery_d30_pct']:.2f}%" if not np.isnan(r['recovery_d30_pct']) else "N/A"
                    )
                with col3:
                    st.metric(
                        "Giorni per 50% gap",
                        f"{r['days_to_50pct_gap']:.1f}" if not np.isnan(r['days_to_50pct_gap']) else "N/A"
                    )
                    st.metric(
                        "Minimo entro D+3",
                        "Sì" if r['min_within_d3_flag'] else "No"
                    )

                st.markdown("**Dettaglio**")
                st.dataframe(row.T, use_container_width=True, height=200)

        # TAB 4: Statistiche di Affidabilità
        with tabs[3]:
            st.header("Statistiche di Affidabilità (Storico + Ultimi N)")
            stats_df = compute_reliability_stats(metrics_df, last_n=last_n)
            if stats_df.empty:
                st.info("Nessuna statistica disponibile.")
            else:
                # Formattazione percentuali
                stats_df_display = stats_df.copy()
                stats_df_display['storico_pct'] = stats_df_display['storico_pct'].apply(
                    lambda x: f"{x:.1f}%" if not np.isnan(x) else "N/A"
                )
                stats_df_display['recent_pct'] = stats_df_display['recent_pct'].apply(
                    lambda x: f"{x:.1f}%" if not np.isnan(x) else "N/A"
                )
                st.table(stats_df_display.rename(columns={
                    'behavior': 'Comportamento',
                    'storico_pct': 'Storico',
                    'recent_pct': f'Ultimi {last_n}'
                }))

                # Sintesi
                st.markdown("### Sintesi")
                rec50_row = stats_df[stats_df['behavior'] == 'Recupera 50% gap entro 10 giorni']
                if not rec50_row.empty:
                    storico_val = rec50_row['storico_pct'].values[0]
                    recent_val = rec50_row['recent_pct'].values[0]
                    st.write(
                        f"**Recupero 50% entro 10 giorni** — Storico: **{storico_val:.1f}%**, "
                        f"Ultimi {last_n}: **{recent_val:.1f}%**"
                    )

        # TAB 5: Interpretazione Automatica
        with tabs[4]:
            st.header("Interpretazione Automatica")
            if metrics_df.empty:
                st.info("Nessuna metrica per interpretare.")
            else:
                stats_df = compute_reliability_stats(metrics_df, last_n=last_n)
                lines = []

                rec50 = stats_df[stats_df['behavior'] == 'Recupera 50% gap entro 10 giorni']
                rec100 = stats_df[stats_df['behavior'] == 'Recupera 100% gap entro 30 giorni']
                trend_up = stats_df[stats_df['behavior'] == 'Sale nei 10 giorni prima']

                if not rec50.empty:
                    s = rec50['storico_pct'].values[0]
                    r = rec50['recent_pct'].values[0]
                    lines.append(
                        f"Storicamente il titolo recupera il 50% del gap entro 10 giorni nel **{s:.1f}%** "
                        f"dei casi; negli ultimi {last_n} dividendi questa percentuale è **{r:.1f}%**."
                    )
                if not rec100.empty:
                    s = rec100['storico_pct'].values[0]
                    r = rec100['recent_pct'].values[0]
                    lines.append(
                        f"Storicamente il recupero completo entro 30 giorni avviene nel **{s:.1f}%** "
                        f"dei casi; ultimi {last_n}: **{r:.1f}%**."
                    )
                if not trend_up.empty:
                    s = trend_up['storico_pct'].values[0]
                    r = trend_up['recent_pct'].values[0]
                    lines.append(
                        f"In {s:.1f}% dei casi il titolo mostrava trend positivo nei 10 giorni prima "
                        f"del dividendo; negli ultimi {last_n} questa percentuale è {r:.1f}%."
                    )

                if len(lines) == 0:
                    st.info("Dati insufficienti per generare un'interpretazione automatica.")
                else:
                    for p in lines:
                        st.markdown(f"- {p}")

        # TAB 6: Comportamento Medio
        with tabs[5]:
            st.header("Comportamento Medio Attorno ai Dividendi")
            index_days, curves = build_normalized_curves(
                stock,
                dividends,
                pre_window=10,
                post_window=45
            )
            plot_mean_normalized(index_days, curves)

            if curves is not None:
                # Statistiche sintetiche
                mean = curves['mean']
                idx = {d: i for i, d in enumerate(index_days)}

                def mean_at(day):
                    i = idx.get(day, None)
                    return mean[i] if i is not None else np.nan

                rec5 = mean_at(5)
                rec10 = mean_at(10)
                rec30 = mean_at(30)

                st.markdown("### Statistiche dalla curva media")
                st.write(f"Recovery medio D+5: **{rec5:.2f}%**")
                st.write(f"Recovery medio D+10: **{rec10:.2f}%**")
                st.write(f"Recovery medio D+30: **{rec30:.2f}%**")

    else:
        st.info("Premi 'Calcola analisi' per generare le metriche e le statistiche del titolo selezionato.")

if __name__ == "__main__":
    main()
