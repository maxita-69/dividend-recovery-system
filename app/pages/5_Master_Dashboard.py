"""
Master Dashboard - Analisi Titoli
Pagina unica con multiple analisi dello stesso titolo
Focus: diverse prospettive analitiche per valutare operabilità
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# =============================================================================
# PATH & IMPORT
# =============================================================================

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'app'))

from database.models import Stock, Dividend, PriceData  # noqa: E402
from auth import require_authentication  # noqa: E402

st.set_page_config(
    page_title="Master Dashboard - Analisi Titoli",
    page_icon="📌",
    layout="wide"
)

require_authentication()

# =============================================================================
# DATABASE
# =============================================================================

@st.cache_resource
def get_database_engine():
    """Cache engine, NON la sessione"""
    db_path = project_root / "data" / "dividend_recovery.db"
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session():
    """Crea nuova sessione ogni volta"""
    engine = get_database_engine()
    Session = sessionmaker(bind=engine)
    return Session()


# =============================================================================
# INDICATORI TECNICI
# =============================================================================

def calculate_stochastic(df: pd.DataFrame, k_period=14, d_period=3):
    """
    Calcola Stocastico %K e %D

    %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
    %D = SMA(%K, 3)
    """
    df = df.copy()
    df['lowest_low'] = df['low'].rolling(window=k_period).min()
    df['highest_high'] = df['high'].rolling(window=k_period).max()
    df['stoch_k'] = 100 * (df['close'] - df['lowest_low']) / (df['highest_high'] - df['lowest_low'])
    df['stoch_d'] = df['stoch_k'].rolling(window=d_period).mean()
    return df[['stoch_k', 'stoch_d']]


def calculate_stochastic_rsi(df: pd.DataFrame, rsi_period=14, stoch_period=14, k_period=3, d_period=3):
    """
    Calcola Stocastico RSI

    1. Calcola RSI
    2. Applica stocastico al RSI
    """
    df = df.copy()

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # Stocastico su RSI
    df['rsi_lowest'] = df['rsi'].rolling(window=stoch_period).min()
    df['rsi_highest'] = df['rsi'].rolling(window=stoch_period).max()
    df['stoch_rsi_k'] = 100 * (df['rsi'] - df['rsi_lowest']) / (df['rsi_highest'] - df['rsi_lowest'])
    df['stoch_rsi_d'] = df['stoch_rsi_k'].rolling(window=d_period).mean()

    return df[['stoch_rsi_k', 'stoch_rsi_d']]


@st.cache_data
def calculate_all_indicators(df_prices: pd.DataFrame):
    """
    Calcola tutti gli indicatori tecnici (con cache)
    Performance: calcolo pesante fatto una volta sola
    """
    if df_prices.empty:
        return None

    df = df_prices.sort_values('date').reset_index(drop=True).copy()

    # Calcola indicatori
    stoch = calculate_stochastic(df)
    stoch_rsi = calculate_stochastic_rsi(df)

    df['stoch_k'] = stoch['stoch_k']
    df['stoch_d'] = stoch['stoch_d']
    df['stoch_rsi_k'] = stoch_rsi['stoch_rsi_k']
    df['stoch_rsi_d'] = stoch_rsi['stoch_rsi_d']

    return df


# =============================================================================
# CARICAMENTO DATI
# =============================================================================

@st.cache_data
def load_stock_data(stock_id: int):
    """
    Carica dati prezzi e dividendi con cache
    """
    session = get_session()

    try:
        prices = (
            session.query(PriceData)
            .filter_by(stock_id=stock_id)
            .order_by(PriceData.date)
            .all()
        )
        dividends = (
            session.query(Dividend)
            .filter_by(stock_id=stock_id)
            .order_by(Dividend.ex_date)
            .all()
        )
    finally:
        session.close()

    df_prices = pd.DataFrame([
        (p.date, p.open, p.high, p.low, p.close, p.volume)
        for p in prices
    ], columns=['date', 'open', 'high', 'low', 'close', 'volume'])

    df_divs = pd.DataFrame([
        (d.ex_date, d.amount)
        for d in dividends
    ], columns=['ex_date', 'amount'])

    # Pulizia con controlli robusti
    if not df_prices.empty:
        df_prices = df_prices.dropna(subset=['date', 'close'])

    if not df_divs.empty:
        df_divs = df_divs.dropna(subset=['ex_date', 'amount'])

    return df_prices, df_divs


def select_stock():
    """Selezione titolo con gestione errori"""
    session = get_session()

    try:
        stocks = session.query(Stock).all()
    except Exception as e:
        session.close()
        st.error(f"Errore nell'accesso al database: {e}")
        st.stop()
    finally:
        session.close()

    if not stocks:
        st.warning("⚠️ Nessun titolo nel database")
        st.stop()

    stock_options = {f"{s.ticker} - {s.name}": s for s in stocks}
    selected = st.selectbox("Seleziona Titolo", list(stock_options.keys()))
    return stock_options[selected]


# =============================================================================
# FRAME 1: PREZZI & DIVIDENDI (Vista Rapida)
# =============================================================================

def render_frame_price_dividends(stock, df_prices, df_divs):
    """
    Frame 1: Vista rapida prezzi e dividendi
    Focus: Overview veloce con filtro temporale
    """
    st.markdown("### 📉 Prezzi & Dividendi - Vista Rapida")

    if df_prices.empty:
        st.warning("⚠️ Nessun dato prezzi disponibile per questo titolo")
        return

    # Metriche base
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ticker", stock.ticker)
    with col2:
        st.metric("Mercato", stock.market)
    with col3:
        st.metric("Prezzo Attuale", f"€{df_prices.iloc[-1]['close']:.2f}")
    with col4:
        st.metric("Dividendi Totali", len(df_divs))

    # Filtro temporale
    min_date = df_prices['date'].min()
    max_date = df_prices['date'].max()

    date_range = st.slider(
        "Intervallo date",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD",
        key="frame1_date_range"
    )

    dfp = df_prices[
        (df_prices['date'] >= date_range[0]) &
        (df_prices['date'] <= date_range[1])
    ].copy()

    dfd = df_divs[
        (df_divs['ex_date'] >= date_range[0]) &
        (df_divs['ex_date'] <= date_range[1])
    ].copy()

    if dfp.empty:
        st.warning("⚠️ Nessun dato nel range selezionato")
        return

    # Grafico semplice
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=dfp['date'],
        open=dfp['open'],
        high=dfp['high'],
        low=dfp['low'],
        close=dfp['close'],
        name='Prezzo',
        increasing_line_color='green',
        decreasing_line_color='red'
    ))

    # Dividendi con colori dinamici
    if not dfd.empty:
        dfd = dfd.merge(
            dfp[['date', 'close']],
            left_on='ex_date',
            right_on='date',
            how='left'
        ).rename(columns={'close': 'price_on_ex'})

        div_dates = []
        div_prices = []
        div_labels = []
        div_colors = []

        for _, div in dfd.iterrows():
            if pd.isnull(div['price_on_ex']):
                continue

            div_dates.append(div['ex_date'])
            div_prices.append(div['price_on_ex'] * 1.02)
            label = f"€{div['amount']:.3f}"
            div_labels.append(label)

            # Colore dinamico basato su importo
            intensity = int(min(div['amount'] * 400, 255)) if pd.notnull(div['amount']) else 100
            div_colors.append(f"rgba(0, {intensity}, 0, 0.9)")

        if div_dates:
            fig.add_trace(go.Scatter(
                x=div_dates,
                y=div_prices,
                mode='markers+text',
                marker=dict(symbol='triangle-down', size=12, color=div_colors),
                text=div_labels,
                textposition='top center',
                name='Dividendi',
                showlegend=True,
                hovertemplate='Data: %{x|%Y-%m-%d}<br>%{text}<extra></extra>'
            ))

    fig.update_layout(
        title=f"{stock.ticker} - Prezzi e Dividendi",
        xaxis_title="Data",
        yaxis_title="Prezzo (€)",
        height=500,
        hovermode='x unified',
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all")
                ]
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabella dividendi compatta
    st.markdown("#### 💰 Storico Dividendi (range selezionato)")
    if not dfd.empty:
        df_divs_display = dfd[['ex_date', 'amount']].copy()
        df_divs_display.rename(columns={
            'ex_date': 'Data Ex',
            'amount': 'Importo (€)'
        }, inplace=True)
        st.dataframe(df_divs_display, use_container_width=False, hide_index=True)
    else:
        st.info("Nessun dividendo nel periodo selezionato")


# =============================================================================
# FRAME 2: INDICATORI TECNICI COMPLETI
# =============================================================================

def render_frame_technical(stock, df_prices, df_divs):
    """
    Frame 2: Analisi tecnica completa
    Focus: Volume, Stocastico, Stocastico RSI
    """
    st.markdown("### 📊 Indicatori Tecnici & Volume")

    if df_prices.empty:
        st.warning("⚠️ Nessun dato prezzi disponibile")
        return

    # Calcola indicatori con cache
    dfp = calculate_all_indicators(df_prices)

    if dfp is None:
        st.error("Errore nel calcolo degli indicatori")
        return

    # Subplot: 4 pannelli
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.15, 0.175, 0.175],
        subplot_titles=(
            f"{stock.ticker} - Prezzi e Dividendi",
            "Volume",
            "Stocastico (%K/%D)",
            "Stocastico RSI (%K/%D)"
        )
    )

    # ROW 1: Prezzi + Dividendi
    fig.add_trace(
        go.Candlestick(
            x=dfp['date'],
            open=dfp['open'],
            high=dfp['high'],
            low=dfp['low'],
            close=dfp['close'],
            name='Prezzo',
            increasing_line_color='green',
            decreasing_line_color='red'
        ),
        row=1, col=1
    )

    # Dividendi
    if not df_divs.empty:
        dfd = df_divs.merge(
            dfp[['date', 'close']],
            left_on='ex_date',
            right_on='date',
            how='left'
        ).rename(columns={'close': 'price_on_ex'})

        div_dates = []
        div_prices = []
        div_labels = []
        div_colors = []

        for _, div in dfd.iterrows():
            if pd.isnull(div['price_on_ex']):
                continue

            div_dates.append(div['ex_date'])
            div_prices.append(div['price_on_ex'] * 1.02)
            label = f"€{div['amount']:.3f}"
            div_labels.append(label)
            intensity = int(min(div['amount'] * 400, 255)) if pd.notnull(div['amount']) else 100
            div_colors.append(f"rgba(0, {intensity}, 0, 0.9)")

        if div_dates:
            fig.add_trace(
                go.Scatter(
                    x=div_dates,
                    y=div_prices,
                    mode='markers+text',
                    marker=dict(symbol='triangle-down', size=12, color=div_colors),
                    text=div_labels,
                    textposition='top center',
                    name='Dividendi',
                    showlegend=True,
                    hovertemplate='Data: %{x|%Y-%m-%d}<br>%{text}<extra></extra>'
                ),
                row=1, col=1
            )

    # ROW 2: Volume
    colors = ['green' if row['close'] >= row['open'] else 'red'
              for _, row in dfp.iterrows()]

    fig.add_trace(
        go.Bar(
            x=dfp['date'],
            y=dfp['volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )

    # ROW 3: Stocastico
    fig.add_trace(
        go.Scatter(
            x=dfp['date'],
            y=dfp['stoch_k'],
            name='Stoch %K',
            line=dict(color='blue', width=1)
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=dfp['date'],
            y=dfp['stoch_d'],
            name='Stoch %D',
            line=dict(color='red', width=1)
        ),
        row=3, col=1
    )
    fig.add_hline(y=80, line_dash="dash", line_color="gray", opacity=0.5, row=3, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="gray", opacity=0.5, row=3, col=1)

    # ROW 4: Stocastico RSI
    fig.add_trace(
        go.Scatter(
            x=dfp['date'],
            y=dfp['stoch_rsi_k'],
            name='StochRSI %K',
            line=dict(color='purple', width=1)
        ),
        row=4, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=dfp['date'],
            y=dfp['stoch_rsi_d'],
            name='StochRSI %D',
            line=dict(color='orange', width=1)
        ),
        row=4, col=1
    )
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

    # Interpretazione indicatori
    st.markdown("#### 📊 Interpretazione Indicatori (Ultimo Valore)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Stocastico:**")
        if not dfp.empty:
            last_stoch_k = dfp['stoch_k'].iloc[-1]
            if pd.notnull(last_stoch_k):
                if last_stoch_k > 80:
                    st.warning(f"⚠️ Ipercomprato ({last_stoch_k:.1f})")
                elif last_stoch_k < 20:
                    st.success(f"✅ Ipervenduto ({last_stoch_k:.1f})")
                else:
                    st.info(f"➡️ Neutrale ({last_stoch_k:.1f})")

    with col2:
        st.markdown("**Stocastico RSI:**")
        if not dfp.empty:
            last_stoch_rsi_k = dfp['stoch_rsi_k'].iloc[-1]
            if pd.notnull(last_stoch_rsi_k):
                if last_stoch_rsi_k > 80:
                    st.warning(f"⚠️ Ipercomprato ({last_stoch_rsi_k:.1f})")
                elif last_stoch_rsi_k < 20:
                    st.success(f"✅ Ipervenduto ({last_stoch_rsi_k:.1f})")
                else:
                    st.info(f"➡️ Neutrale ({last_stoch_rsi_k:.1f})")


# =============================================================================
# FRAME 3: ANALISI PRE/POST DIVIDENDO (Struttura per SAL 5)
# =============================================================================

def render_frame_pre_post_dividend(stock, df_prices, df_divs):
    """
    Frame 3: Analisi eventi Pre/Post dividendo
    Focus: Pattern di comportamento intorno alla data ex-dividend
    STRUTTURA PRONTA per implementazione SAL 5
    """
    st.markdown("### 🔍 Analisi Pre/Post Dividendo")

    if df_prices.empty or df_divs.empty:
        st.info("Servono prezzi e dividendi per questa analisi.")
        return

    st.markdown("""
    Questa sezione sarà il **cuore dell'analisi SAL 5** per identificare pattern operabili.

    **Obiettivo**: Capire se vale la pena operare su un dividendo specifico analizzando:

    #### 📊 Finestre Temporali Pre-Dividendo:
    - **D-10**: Volume, volatilità, trend 10 sedute prima
    - **D-5**: Comportamento 5 sedute prima dello stacco
    - **D-1**: Situazione giorno prima (cruciale per decisione operativa)

    #### 📈 Finestre Temporali Post-Dividendo:
    - **D+5, D+10, D+15, D+20, D+30, D+40, D+45**: Tracking recovery
    - Identificazione **recovery speed** (velocità recupero dividendo)
    - Calcolo **ROI effettivo** per ogni strategia (D1/D0, leva)

    #### 🎯 Pattern da Cercare:
    1. **Volume spike pre-dividend** → Correlazione con recovery veloce?
    2. **Volatilità pre-dividend** → Maggiore volatilità = maggior rischio?
    3. **Trend pre-dividend** → Rialzo pre-stacco influenza post-stacco?
    4. **Yield %** → Dividendi alti recoveryano più lentamente?
    5. **Stagionalità** → Gennaio vs Luglio comportamento diverso?
    6. **Settore** → Banche vs Energia pattern diversi?

    #### 💡 Output Finale:
    - **Score operabilità** per ogni dividendo (1-10)
    - **Probabilità recovery** entro X giorni
    - **Risk/Reward** per D1 vs D0
    - **ML Prediction** (dopo validazione statistica)

    ---

    **Status**: 🚧 Struttura pronta, implementazione in SAL 5 Week 3-4
    """)


# =============================================================================
# FRAME 4: STATISTICHE & RENDIMENTO CUMULATO
# =============================================================================

def render_frame_stats(stock, df_prices, df_divs):
    """
    Frame 4: Statistiche generali e rendimento
    Focus: Metriche di performance del titolo
    """
    st.markdown("### 📈 Statistiche & Rendimento Cumulato")

    if df_prices.empty:
        st.warning("⚠️ Nessun dato prezzi disponibile")
        return

    dfp = df_prices.sort_values('date').reset_index(drop=True).copy()
    dfp['return'] = dfp['close'].pct_change()
    returns = dfp['return'].dropna()

    avg_return_annual = None
    volatility_annual = None
    cum_return = None

    if not returns.empty:
        avg_return_annual = returns.mean() * 252
        volatility_annual = returns.std() * (252 ** 0.5)
        cum_return = (1 + returns).prod() - 1

    # Calcolo dividendi per anno
    if not df_divs.empty:
        df_divs_enriched = df_divs.merge(
            dfp[['date', 'close']],
            left_on='ex_date',
            right_on='date',
            how='left'
        ).rename(columns={'close': 'price_on_ex'})

        df_divs_enriched['yield'] = df_divs_enriched.apply(
            lambda row: row['amount'] / row['price_on_ex']
            if pd.notnull(row['price_on_ex']) and row['price_on_ex'] != 0
            else None,
            axis=1
        )
        df_divs_enriched['year'] = pd.to_datetime(df_divs_enriched['ex_date']).dt.year
        div_per_year = df_divs_enriched.groupby('year').size().mean()
    else:
        div_per_year = 0

    # Metriche
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    with col_s1:
        st.metric(
            "Rendimento Medio Annuo",
            f"{avg_return_annual:.2%}" if avg_return_annual is not None else "N/D"
        )

    with col_s2:
        st.metric(
            "Volatilità Annua",
            f"{volatility_annual:.2%}" if volatility_annual is not None else "N/D"
        )

    with col_s3:
        st.metric(
            "Rendimento Cumulato",
            f"{cum_return:.2%}" if cum_return is not None else "N/D"
        )

    with col_s4:
        st.metric(
            "Dividendi/Anno (media)",
            f"{div_per_year:.1f}" if div_per_year else "0.0"
        )


# =============================================================================
# MAIN
# =============================================================================

def main():
    st.title("📌 Master Dashboard – Analisi Titoli")

    st.markdown("""
    **Obiettivo**: Analisi multi-prospettiva di un singolo titolo per valutare l'operabilità.

    Questa dashboard aggrega diverse analisi per aiutarti a decidere:
    - 📉 Vista rapida prezzi/dividendi
    - 📊 Analisi tecnica approfondita (volume + indicatori)
    - 🔍 Pattern pre/post dividendo (SAL 5)
    - 📈 Statistiche di performance
    """)

    st.markdown("---")

    # Selezione titolo
    stock = select_stock()

    # Caricamento dati con cache
    df_prices, df_divs = load_stock_data(stock.id)

    # FRAME 1: Prezzi & Dividendi (Vista Rapida)
    with st.expander("📉 Prezzi & Dividendi - Vista Rapida", expanded=True):
        render_frame_price_dividends(stock, df_prices, df_divs)

    # FRAME 2: Indicatori Tecnici Completi
    with st.expander("📊 Indicatori Tecnici & Volume", expanded=False):
        render_frame_technical(stock, df_prices, df_divs)

    # FRAME 3: Analisi Pre/Post Dividendo (Struttura SAL 5)
    with st.expander("🔍 Analisi Pre/Post Dividendo (SAL 5)", expanded=False):
        render_frame_pre_post_dividend(stock, df_prices, df_divs)

    # FRAME 4: Statistiche & Rendimento
    with st.expander("📈 Statistiche & Rendimento Cumulato", expanded=False):
        render_frame_stats(stock, df_prices, df_divs)


if __name__ == "__main__":
    main()
