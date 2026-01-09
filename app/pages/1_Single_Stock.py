"""
Single Stock Analysis Page
Visualizzazione e analisi singolo titolo con indicatori tecnici
"""

import sys
from pathlib import Path
from datetime import datetime, date

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'app'))

from database.models import Stock, Dividend, PriceData  # noqa: E402

st.set_page_config(
    page_title="Single Stock Analysis",
    page_icon="📊",
    layout="wide"
)

# ============================================================================
# AUTHENTICATION - Must be after set_page_config
# ============================================================================
from auth import require_authentication  # noqa: E402

require_authentication()


# ============================================================================
# DATABASE CONNECTION - FIX CRITICO #1: Cache engine, non session
# ============================================================================

@st.cache_resource
def get_database_engine():
    """Cache engine, NON la sessione"""
    # Calcola percorso direttamente nella funzione cached
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    db_path = project_root / "data" / "dividend_recovery.db"
    return create_engine(f"sqlite:///{db_path}", echo=False)


# ============================================================================
# INDICATORI TECNICI
# ============================================================================

def calculate_stochastic(df: pd.DataFrame, k_period=14, d_period=3):
    """
    Calcola Stocastico %K e %D

    %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
    %D = SMA(%K, 3)
    """
    df = df.copy()

    # Lowest low e highest high nel periodo
    df['lowest_low'] = df['low'].rolling(window=k_period).min()
    df['highest_high'] = df['high'].rolling(window=k_period).max()

    # %K
    df['stoch_k'] = 100 * (df['close'] - df['lowest_low']) / (df['highest_high'] - df['lowest_low'])

    # %D (media mobile di %K)
    df['stoch_d'] = df['stoch_k'].rolling(window=d_period).mean()

    return df[['stoch_k', 'stoch_d']]


def calculate_stochastic_rsi(df: pd.DataFrame, rsi_period=14, stoch_period=14, k_period=3, d_period=3):
    """
    Calcola Stocastico RSI

    1. Calcola RSI
    2. Applica stocastico al RSI
    """
    df = df.copy()

    # Calcola RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()

    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # Applica stocastico al RSI
    df['rsi_lowest'] = df['rsi'].rolling(window=stoch_period).min()
    df['rsi_highest'] = df['rsi'].rolling(window=stoch_period).max()

    df['stoch_rsi_k'] = 100 * (df['rsi'] - df['rsi_lowest']) / (df['rsi_highest'] - df['rsi_lowest'])
    df['stoch_rsi_d'] = df['stoch_rsi_k'].rolling(window=d_period).mean()

    return df[['stoch_rsi_k', 'stoch_rsi_d']]


# ============================================================================
# MAIN APP
# ============================================================================

st.title("📊 Analisi Singolo Titolo")

# Crea nuova sessione ogni volta (non cached)
engine = get_database_engine()
Session = sessionmaker(bind=engine)
session = Session()

# ============================================================================
# SELEZIONE TITOLO
# ============================================================================

try:
    stocks = session.query(Stock).all()
except Exception as e:
    st.error(f"Errore nell'accesso al database: {e}")
    st.stop()

stock_options = {f"{s.ticker} - {s.name}": s for s in stocks}

if not stock_options:
    st.warning("⚠️ Nessun titolo nel database")
    st.stop()

selected = st.selectbox("Seleziona Titolo", list(stock_options.keys()))
stock = stock_options[selected]

# ============================================================================
# CARICAMENTO DATI PREZZI E DIVIDENDI
# ============================================================================

try:
    prices = (
        session.query(PriceData)
        .filter_by(stock_id=stock.id)
        .order_by(PriceData.date)
        .all()
    )
    dividends = (
        session.query(Dividend)
        .filter_by(stock_id=stock.id)
        .order_by(Dividend.ex_date)
        .all()
    )
except Exception as e:
    st.error(f"Errore nel caricamento dei dati dal database: {e}")
    session.close()
    st.stop()

# Conversione più efficiente
df_prices = pd.DataFrame([
    (p.date, p.open, p.high, p.low, p.close, p.volume)
    for p in prices
], columns=['date', 'open', 'high', 'low', 'close', 'volume'])

df_divs = pd.DataFrame([
    (d.ex_date, d.amount)
    for d in dividends
], columns=['ex_date', 'amount'])

# Pulizia NaN con controllo post-dropna
if not df_prices.empty:
    df_prices = df_prices.dropna(subset=['date', 'close'])
    if df_prices.empty:
        st.warning("⚠️ Nessun dato valido disponibile")
        session.close()
        st.stop()

if not df_divs.empty:
    df_divs = df_divs.dropna(subset=['ex_date', 'amount'])

# ============================================================================
# METRICHE DI BASE
# ============================================================================

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Ticker", stock.ticker)
with col2:
    st.metric("Mercato", stock.market)
with col3:
    if not df_prices.empty:
        st.metric("Prezzo Attuale", f"€{df_prices.iloc[-1]['close']:.2f}")
with col4:
    st.metric("Dividendi", len(df_divs))

st.markdown("---")

# ============================================================================
# FILTRO TEMPORALE
# ============================================================================

if df_prices.empty:
    st.warning("⚠️ Nessun dato prezzi disponibile per questo titolo")
    session.close()
    st.stop()

min_date = df_prices['date'].min()
max_date = df_prices['date'].max()

st.markdown("### 📅 Filtro Temporale")
date_range = st.slider(
    "Intervallo date",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

df_prices_filtered = df_prices[
    (df_prices['date'] >= date_range[0]) &
    (df_prices['date'] <= date_range[1])
].copy()

df_divs_filtered = df_divs[
    (df_divs['ex_date'] >= date_range[0]) &
    (df_divs['ex_date'] <= date_range[1])
].copy()

if df_prices_filtered.empty:
    st.warning("⚠️ Nessun dato prezzi nel range selezionato")
    session.close()
    st.stop()

# ============================================================================
# CALCOLO RENDIMENTI, VOLATILITÀ, RENDIMENTO CUMULATO
# ============================================================================

df_prices_filtered = df_prices_filtered.sort_values('date').reset_index(drop=True)
df_prices_filtered['return'] = df_prices_filtered['close'].pct_change()

returns = df_prices_filtered['return'].dropna()

avg_return_annual = None
volatility_annual = None
cum_return = None

if not returns.empty:
    avg_return_annual = returns.mean() * 252
    volatility_annual = returns.std() * (252 ** 0.5)
    cum_return = (1 + returns).prod() - 1

# ============================================================================
# CALCOLO RENDIMENTO DIVIDENDI - FIX CRITICO #2: Performance O(n+m)
# ============================================================================

if not df_divs_filtered.empty:
    # Merge invece di apply (molto più veloce!)
    df_divs_filtered = df_divs_filtered.merge(
        df_prices_filtered[['date', 'close']],
        left_on='ex_date',
        right_on='date',
        how='left'
    ).rename(columns={'close': 'price_on_ex'})

    # Calcola yield
    df_divs_filtered['yield'] = df_divs_filtered.apply(
        lambda row: row['amount'] / row['price_on_ex']
        if pd.notnull(row['price_on_ex']) and row['price_on_ex'] != 0
        else None,
        axis=1
    )

    df_divs_filtered['year'] = pd.to_datetime(df_divs_filtered['ex_date']).dt.year
    div_per_year = df_divs_filtered.groupby('year').size().mean()
else:
    div_per_year = 0

# ============================================================================
# CALCOLO INDICATORI TECNICI
# ============================================================================

stoch = calculate_stochastic(df_prices_filtered)
stoch_rsi = calculate_stochastic_rsi(df_prices_filtered)

df_prices_filtered['stoch_k'] = stoch['stoch_k']
df_prices_filtered['stoch_d'] = stoch['stoch_d']
df_prices_filtered['stoch_rsi_k'] = stoch_rsi['stoch_rsi_k']
df_prices_filtered['stoch_rsi_d'] = stoch_rsi['stoch_rsi_d']

# ============================================================================
# SEZIONE STATISTICHE
# ============================================================================

st.markdown("### 📈 Statistiche di Base")

col_s1, col_s2, col_s3, col_s4 = st.columns(4)

with col_s1:
    if avg_return_annual is not None:
        st.metric("Rendimento Medio Annuo", f"{avg_return_annual:.2%}")
    else:
        st.metric("Rendimento Medio Annuo", "N/D")

with col_s2:
    if volatility_annual is not None:
        st.metric("Volatilità Annua", f"{volatility_annual:.2%}")
    else:
        st.metric("Volatilità Annua", "N/D")

with col_s3:
    if cum_return is not None:
        st.metric("Rendimento Cumulato", f"{cum_return:.2%}")
    else:
        st.metric("Rendimento Cumulato", "N/D")

with col_s4:
    st.metric("Dividendi/Anno (media)", f"{div_per_year:.1f}" if div_per_year else "0.0")

st.markdown("---")

# ============================================================================
# LAYOUT GRAFICO + TABELLA
# ============================================================================

col_graph, col_table = st.columns([2, 1])

with col_graph:
    st.markdown("### 📉 Prezzi, Volume e Indicatori")

    # FIX CRITICO #3: Subplot con volume + indicatori
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.15, 0.175, 0.175],
        subplot_titles=(
            f"{stock.ticker} - Prezzi e Dividendi",
            "Volume",
            "Stocastico",
            "Stocastico RSI"
        )
    )

    # ROW 1: Candlestick + Dividendi
    fig.add_trace(
        go.Candlestick(
            x=df_prices_filtered['date'],
            open=df_prices_filtered['open'],
            high=df_prices_filtered['high'],
            low=df_prices_filtered['low'],
            close=df_prices_filtered['close'],
            name='Prezzo',
            increasing_line_color='green',
            decreasing_line_color='red'
        ),
        row=1, col=1
    )

    # Marker dividendi - FIX CRITICO #3: Singolo trace
    if not df_divs_filtered.empty:
        div_dates = []
        div_prices = []
        div_labels = []
        div_colors = []

        for _, div in df_divs_filtered.iterrows():
            price = div['price_on_ex']
            if pd.isnull(price):
                continue

            div_dates.append(div['ex_date'])
            div_prices.append(price * 1.02)

            label = f"€{div['amount']:.3f}"
            if pd.notnull(div['yield']):
                label += f" ({div['yield']:.2%})"
            div_labels.append(label)

            intensity = int(min(div['amount'] * 400, 255)) if pd.notnull(div['amount']) else 100
            div_colors.append(f"rgba(0, {intensity}, 0, 0.9)")

        if div_dates:
            fig.add_trace(
                go.Scatter(
                    x=div_dates,
                    y=div_prices,
                    mode='markers+text',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color=div_colors
                    ),
                    text=div_labels,
                    textposition='top center',
                    name='Dividendi',
                    showlegend=True,
                    hovertemplate='Data: %{x|%Y-%m-%d}<br>%{text}<extra></extra>'
                ),
                row=1, col=1
            )

    # ROW 2: Volume istogramma
    colors = ['green' if row['close'] >= row['open'] else 'red'
              for _, row in df_prices_filtered.iterrows()]

    fig.add_trace(
        go.Bar(
            x=df_prices_filtered['date'],
            y=df_prices_filtered['volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )

    # ROW 3: Stocastico
    fig.add_trace(
        go.Scatter(
            x=df_prices_filtered['date'],
            y=df_prices_filtered['stoch_k'],
            name='Stoch %K',
            line=dict(color='blue', width=1)
        ),
        row=3, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df_prices_filtered['date'],
            y=df_prices_filtered['stoch_d'],
            name='Stoch %D',
            line=dict(color='red', width=1)
        ),
        row=3, col=1
    )

    # Linee di riferimento 20/80
    fig.add_hline(y=80, line_dash="dash", line_color="gray", opacity=0.5, row=3, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="gray", opacity=0.5, row=3, col=1)

    # ROW 4: Stocastico RSI
    fig.add_trace(
        go.Scatter(
            x=df_prices_filtered['date'],
            y=df_prices_filtered['stoch_rsi_k'],
            name='StochRSI %K',
            line=dict(color='purple', width=1)
        ),
        row=4, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df_prices_filtered['date'],
            y=df_prices_filtered['stoch_rsi_d'],
            name='StochRSI %D',
            line=dict(color='orange', width=1)
        ),
        row=4, col=1
    )

    # Linee di riferimento 20/80
    fig.add_hline(y=80, line_dash="dash", line_color="gray", opacity=0.5, row=4, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="gray", opacity=0.5, row=4, col=1)

    # Layout
    fig.update_xaxes(title_text="Data", row=4, col=1)
    fig.update_yaxes(title_text="Prezzo (€)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="%K/%D", row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="%K/%D", row=4, col=1, range=[0, 100])

    fig.update_layout(
        height=900,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("### 💰 Storico Dividendi")

    if not df_divs_filtered.empty:
        df_divs_display = df_divs_filtered[['ex_date', 'amount', 'yield']].copy()
        df_divs_display['yield'] = df_divs_display['yield'].apply(
            lambda x: f"{x:.2%}" if pd.notnull(x) else ""
        )
        df_divs_display.rename(columns={
            'ex_date': 'Data Ex',
            'amount': 'Importo (€)',
            'yield': 'Yield'
        }, inplace=True)

        st.dataframe(
            df_divs_display,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nessun dividendo registrato nel periodo selezionato")

    # Interpretazione indicatori
    st.markdown("---")
    st.markdown("### 📊 Interpretazione Indicatori")

    if not df_prices_filtered.empty:
        last_stoch_k = df_prices_filtered['stoch_k'].iloc[-1]
        last_stoch_rsi_k = df_prices_filtered['stoch_rsi_k'].iloc[-1]

        st.markdown("**Stocastico:**")
        if pd.notnull(last_stoch_k):
            if last_stoch_k > 80:
                st.warning(f"⚠️ Ipercomprato ({last_stoch_k:.1f})")
            elif last_stoch_k < 20:
                st.success(f"✅ Ipervenduto ({last_stoch_k:.1f})")
            else:
                st.info(f"➡️ Neutrale ({last_stoch_k:.1f})")

        st.markdown("**Stocastico RSI:**")
        if pd.notnull(last_stoch_rsi_k):
            if last_stoch_rsi_k > 80:
                st.warning(f"⚠️ Ipercomprato ({last_stoch_rsi_k:.1f})")
            elif last_stoch_rsi_k < 20:
                st.success(f"✅ Ipervenduto ({last_stoch_rsi_k:.1f})")
            else:
                st.info(f"➡️ Neutrale ({last_stoch_rsi_k:.1f})")

# ============================================================================
# FINE - Chiudi sessione correttamente
# ============================================================================

session.close()
