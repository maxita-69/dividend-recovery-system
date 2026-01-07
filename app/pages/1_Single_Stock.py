"""
Single Stock Analysis Page
Visualizzazione e analisi singolo titolo
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from database.models import Stock, Dividend, PriceData

st.set_page_config(
    page_title="Single Stock Analysis",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def get_database_session():
    """Get database session (cached)"""
    db_path = Path(__file__).parent.parent.parent / "data" / "dividend_recovery.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Session = sessionmaker(bind=engine)
    return Session()

st.title("📊 Analisi Singolo Titolo")

session = get_database_session()

# Stock selection
stocks = session.query(Stock).all()
stock_options = {f"{s.ticker} - {s.name}": s for s in stocks}

if not stock_options:
    st.warning("⚠️ Nessun titolo nel database")
    st.stop()

selected = st.selectbox("Seleziona Titolo", list(stock_options.keys()))
stock = stock_options[selected]

# Get price data
prices = session.query(PriceData).filter_by(stock_id=stock.id).order_by(PriceData.date).all()
df_prices = pd.DataFrame([{
    'date': p.date,
    'open': p.open,
    'high': p.high,
    'low': p.low,
    'close': p.close,
    'volume': p.volume
} for p in prices])

# Get dividends
dividends = session.query(Dividend).filter_by(stock_id=stock.id).order_by(Dividend.ex_date).all()
df_divs = pd.DataFrame([{
    'ex_date': d.ex_date,
    'amount': d.amount
} for d in dividends])

# Display info
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Ticker", stock.ticker)
with col2:
    st.metric("Mercato", stock.market)
with col3:
    if not df_prices.empty:
        st.metric("Prezzo Attuale", f"€{df_prices.iloc[-1]['close']:.2f}")
with col4:
    st.metric("Dividendi", len(dividends))

st.divider()

# Price chart
if not df_prices.empty:
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df_prices['date'],
        open=df_prices['open'],
        high=df_prices['high'],
        low=df_prices['low'],
        close=df_prices['close'],
        name='Price'
    ))
    
    # Dividend markers
    if not df_divs.empty:
        for _, div in df_divs.iterrows():
            price_on_date = df_prices[df_prices['date'] == div['ex_date']]
            if not price_on_date.empty:
                fig.add_trace(go.Scatter(
                    x=[div['ex_date']],
                    y=[price_on_date.iloc[0]['high'] * 1.02],
                    mode='markers+text',
                    marker=dict(symbol='triangle-down', size=12, color='red'),
                    text=[f"€{div['amount']:.3f}"],
                    textposition='top center',
                    name='Dividend',
                    showlegend=False
                ))
    
    fig.update_layout(
        title=f"{stock.ticker} - Prezzi e Dividendi",
        xaxis_title="Data",
        yaxis_title="Prezzo (€)",
        height=600,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Dividend table
if not df_divs.empty:
    st.subheader("💰 Storico Dividendi")
    st.dataframe(df_divs, use_container_width=True, hide_index=True)
else:
    st.info("Nessun dividendo registrato")
