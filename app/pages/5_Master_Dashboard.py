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

project_root = Path(__file__).parent.parent.parent
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
    # Calcola percorso direttamente nella funzione cached
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
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
# FRAME 2: ANALISI TECNICA ATTORNO AL DIVIDENDO (D-10 → D+45)
# =============================================================================

def render_frame_dividend_focus(stock, df_prices, df_divs):
    """
    Frame 2: Analisi focalizzata su singolo dividendo
    Intervallo: D-10 → D+45
    Grafici incolonnati + linee verticali sincronizzate + metriche chiave
    """
    st.markdown("### 🎯 Analisi Tecnica Attorno al Dividendo (D-10 → D+45)")

    if df_prices.empty or df_divs.empty:
        st.info("Servono prezzi e dividendi per questa analisi.")
        return

    # Selezione dividendo
    df_divs_sorted = df_divs.sort_values('ex_date')
    div_options = {
        f"{row['ex_date'].date()} – €{row['amount']:.3f}": row['ex_date']
        for _, row in df_divs_sorted.iterrows()
    }

    if not div_options:
        st.warning("⚠️ Nessun dividendo disponibile per l'analisi")
        return

    selected_label = st.selectbox("Seleziona Dividendo", list(div_options.keys()), key="frame3_div_select")
    selected_date = div_options[selected_label]

    # Parametri intervallo (opzionale - avanzato)
    with st.expander("⚙️ Configurazione Intervallo Temporale"):
        col_a, col_b = st.columns(2)
        days_before = col_a.number_input("Giorni prima", value=10, min_value=5, max_value=30, key="frame3_days_before")
        days_after = col_b.number_input("Giorni dopo", value=45, min_value=15, max_value=90, key="frame3_days_after")

    # Intervallo D-10 → D+45 (o personalizzato)
    start_date = selected_date - timedelta(days=days_before)
    end_date = selected_date + timedelta(days=days_after)

    dfp = df_prices[
        (df_prices['date'] >= start_date) &
        (df_prices['date'] <= end_date)
    ].copy()

    if dfp.empty:
        st.warning("⚠️ Nessun dato disponibile nell'intervallo selezionato.")
        return

    # Calcolo indicatori
    dfp_ind = calculate_all_indicators(dfp)
    if dfp_ind is None:
        st.error("Errore nel calcolo degli indicatori.")
        return

    # =============================================================================
    # METRICHE CHIAVE POST-DIVIDENDO
    # =============================================================================

    # Trova prezzi chiave
    prices_before = dfp_ind[dfp_ind['date'] < selected_date]
    prices_after = dfp_ind[dfp_ind['date'] > selected_date]
    price_on_ex = dfp_ind[dfp_ind['date'] == selected_date]

    price_before = prices_before['close'].iloc[-1] if len(prices_before) > 0 else None
    price_after = prices_after['close'].iloc[0] if len(prices_after) > 0 else None
    price_current = dfp_ind['close'].iloc[-1] if len(dfp_ind) > 0 else None
    price_ex = price_on_ex['close'].iloc[0] if len(price_on_ex) > 0 else None

    # Importo dividendo
    div_amount = df_divs_sorted[df_divs_sorted['ex_date'] == selected_date]['amount'].iloc[0]

    # Metriche
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if price_before and price_after:
            drop_pct = ((price_after - price_before) / price_before) * 100
            st.metric("Drop Ex-Date", f"{drop_pct:.2f}%", delta=f"{price_after - price_before:.2f}€")
        else:
            st.metric("Drop Ex-Date", "N/D")

    with col2:
        if price_before:
            div_yield = (div_amount / price_before) * 100
            st.metric("Dividend Yield", f"{div_yield:.2f}%", delta=f"€{div_amount:.3f}")
        else:
            st.metric("Dividend Yield", "N/D")

    with col3:
        if price_before and price_current:
            recovery_pct = ((price_current - price_after) / (price_before - price_after)) * 100 if price_after else 0
            st.metric("Recovery %", f"{recovery_pct:.1f}%", delta=f"{price_current - price_after:.2f}€")
        else:
            st.metric("Recovery %", "N/D")

    with col4:
        days_elapsed = (dfp_ind['date'].max() - selected_date).days
        st.metric("Giorni da Ex-Date", f"{days_elapsed}", delta="giorni")

    st.markdown("---")

    # =============================================================================
    # SUBPLOT: Prezzo + Volume + Indicatori
    # =============================================================================

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.50, 0.15, 0.175, 0.175],
        subplot_titles=(
            f"{stock.ticker} – Prezzo (D-{days_before} → D+{days_after})",
            "Volume",
            "Stocastico (%K/%D)",
            "Stocastico RSI (%K/%D)"
        )
    )

    # -------------------------
    # ROW 1: Prezzo
    # -------------------------
    fig.add_trace(go.Candlestick(
        x=dfp_ind['date'],
        open=dfp_ind['open'],
        high=dfp_ind['high'],
        low=dfp_ind['low'],
        close=dfp_ind['close'],
        name='Prezzo',
        increasing_line_color='green',
        decreasing_line_color='red'
    ), row=1, col=1)

    # Marker Ex-Dividend (stella dorata)
    if price_ex:
        fig.add_trace(go.Scatter(
            x=[selected_date],
            y=[price_ex],
            mode='markers',
            marker=dict(size=15, color='gold', symbol='star', line=dict(color='black', width=1)),
            name='Ex-Date',
            showlegend=True,
            hovertemplate=f'Ex-Date: {selected_date.date()}<br>Prezzo: €{price_ex:.2f}<extra></extra>'
        ), row=1, col=1)

    # Linea target recupero (prezzo pre-dividendo)
    if price_before:
        fig.add_hline(
            y=price_before,
            line_dash="dot",
            line_color="green",
            annotation_text=f"Target Recupero (€{price_before:.2f})",
            annotation_position="right",
            row=1, col=1
        )

    # -------------------------
    # ROW 2: Volume
    # -------------------------
    colors = ['green' if row['close'] >= row['open'] else 'red'
              for _, row in dfp_ind.iterrows()]

    fig.add_trace(go.Bar(
        x=dfp_ind['date'],
        y=dfp_ind['volume'],
        marker_color=colors,
        name='Volume',
        showlegend=False
    ), row=2, col=1)

    # -------------------------
    # ROW 3: Stocastico
    # -------------------------
    fig.add_trace(go.Scatter(
        x=dfp_ind['date'],
        y=dfp_ind['stoch_k'],
        name='Stoch %K',
        line=dict(color='blue', width=1)
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=dfp_ind['date'],
        y=dfp_ind['stoch_d'],
        name='Stoch %D',
        line=dict(color='red', width=1)
    ), row=3, col=1)

    fig.add_hline(y=80, line_dash="dash", line_color="gray", opacity=0.5, row=3, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="gray", opacity=0.5, row=3, col=1)

    # -------------------------
    # ROW 4: Stocastico RSI
    # -------------------------
    fig.add_trace(go.Scatter(
        x=dfp_ind['date'],
        y=dfp_ind['stoch_rsi_k'],
        name='StochRSI %K',
        line=dict(color='purple', width=1)
    ), row=4, col=1)

    fig.add_trace(go.Scatter(
        x=dfp_ind['date'],
        y=dfp_ind['stoch_rsi_d'],
        name='StochRSI %D',
        line=dict(color='orange', width=1)
    ), row=4, col=1)

    fig.add_hline(y=80, line_dash="dash", line_color="gray", opacity=0.5, row=4, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="gray", opacity=0.5, row=4, col=1)

    # -------------------------
    # LINEE VERTICALI SINCRONIZZATE
    # -------------------------
    special_dates = {
        f"D-{days_before}": start_date,
        "D-DAY": selected_date,
        f"D+{days_after}": end_date
    }

    for label, d in special_dates.items():
        line_color = "red" if label == "D-DAY" else "black"
        line_width = 2 if label == "D-DAY" else 1.5

        fig.add_vline(
            x=d,
            line_width=line_width,
            line_dash="dash",
            line_color=line_color,
            annotation_text=label,
            annotation_position="top left"
        )

    # Layout generale
    fig.update_xaxes(title_text="Data", row=4, col=1)
    fig.update_yaxes(title_text="Prezzo (€)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="%K/%D", row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="%K/%D", row=4, col=1, range=[0, 100])

    fig.update_layout(
        height=900,
        hovermode='x unified',
        showlegend=True,
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # =============================================================================
    # INTERPRETAZIONE INDICATORI
    # =============================================================================

    st.markdown("#### 📊 Interpretazione Indicatori (Valori Attuali)")

    col_i1, col_i2 = st.columns(2)

    with col_i1:
        st.markdown("**Stocastico:**")
        last_stoch_k = dfp_ind['stoch_k'].iloc[-1]
        if pd.notnull(last_stoch_k):
            if last_stoch_k > 80:
                st.warning(f"⚠️ Ipercomprato ({last_stoch_k:.1f}) - Possibile correzione")
            elif last_stoch_k < 20:
                st.success(f"✅ Ipervenduto ({last_stoch_k:.1f}) - Opportunità acquisto")
            else:
                st.info(f"➡️ Neutrale ({last_stoch_k:.1f})")

    with col_i2:
        st.markdown("**Stocastico RSI:**")
        last_stoch_rsi_k = dfp_ind['stoch_rsi_k'].iloc[-1]
        if pd.notnull(last_stoch_rsi_k):
            if last_stoch_rsi_k > 80:
                st.warning(f"⚠️ Ipercomprato ({last_stoch_rsi_k:.1f}) - Possibile correzione")
            elif last_stoch_rsi_k < 20:
                st.success(f"✅ Ipervenduto ({last_stoch_rsi_k:.1f}) - Opportunità acquisto")
            else:
                st.info(f"➡️ Neutrale ({last_stoch_rsi_k:.1f})")

    # =============================================================================
    # SUGGERIMENTO OPERATIVO
    # =============================================================================

    st.markdown("---")
    st.markdown("#### 💡 Analisi Operativa")

    if price_before and price_current:
        if price_current >= price_before:
            st.success(f"✅ **RECUPERO COMPLETATO**: Il prezzo ha recuperato il dividendo (+{((price_current - price_before) / price_before * 100):.2f}%)")
        else:
            gap = price_before - price_current
            gap_pct = (gap / price_before) * 100
            st.warning(f"⚠️ **RECUPERO PARZIALE**: Mancano €{gap:.2f} ({gap_pct:.2f}%) al target di recupero")


# =============================================================================
# FRAME 3: STATISTICHE & RENDIMENTO CUMULATO
# =============================================================================

def render_frame_stats(stock, df_prices, df_divs):
    """
    Frame 3: Statistiche generali e rendimento
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
    - 🎯 Analisi focalizzata su dividendo specifico (D-10 → D+45)
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

    # FRAME 2: Analisi Tecnica Attorno al Dividendo
    with st.expander("🎯 Analisi Tecnica Attorno al Dividendo (D-10 → D+45)", expanded=False):
        render_frame_dividend_focus(stock, df_prices, df_divs)

    # FRAME 3: Statistiche & Rendimento
    with st.expander("📈 Statistiche & Rendimento Cumulato", expanded=False):
        render_frame_stats(stock, df_prices, df_divs)


if __name__ == "__main__":
    main()
