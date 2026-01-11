"""
Dividend Recovery System - Dashboard Web
Main entry point for Streamlit multi-page app
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Page config
st.set_page_config(
    page_title="Dividend Recovery System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Main page
st.markdown('<div class="main-header">💰 Dividend Recovery System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Sistema di Analisi e Monitoraggio Dividendi</div>', unsafe_allow_html=True)

# Introduction
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-box">
        <h3>📅 Calendario Dividendi</h3>
        <p>Monitora i prossimi dividendi del tuo portfolio con filtri personalizzabili per yield e timeframe.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-box">
        <h3>📊 Analisi Storica</h3>
        <p>Analizza pattern storici e performance dei dividendi per ottimizzare le strategie di trading.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-box">
        <h3>🎯 Backtest Strategie</h3>
        <p>Testa strategie di Dividend Recovery su dati storici per validare la redditività.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Quick stats
st.header("📈 Statistiche Sistema")

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import Stock, Dividend, PriceData

    # Connect to database
    db_path = Path(__file__).parent.parent / 'data' / 'dividend_recovery.db'

    if db_path.exists():
        engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Get stats
        total_stocks = session.query(Stock).count()
        total_dividends = session.query(Dividend).count()
        total_prices = session.query(PriceData).count()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Titoli Monitorati", f"{total_stocks}")

        with col2:
            st.metric("Eventi Dividendo", f"{total_dividends:,}")

        with col3:
            st.metric("Dati Prezzi", f"{total_prices:,}")

        with col4:
            # Calculate average dividend yield
            from datetime import datetime
            future_divs = session.query(Dividend).filter(
                Dividend.ex_date >= datetime.now().date()
            ).count()
            st.metric("Dividendi Futuri", f"{future_divs}")

        session.close()
    else:
        st.warning("⚠️ Database non trovato. Esegui prima `python download_stock_data_v2.py`")

except Exception as e:
    st.info("💡 Database non ancora popolato. Segui le istruzioni nella barra laterale.")

# Sidebar
with st.sidebar:
    st.header("🚀 Quick Start")

    st.markdown("""
    ### Setup Iniziale

    1. **Popola Database**
       ```bash
       python download_stock_data_v2.py
       ```

    2. **Aggiorna Calendario**
       ```bash
       python dividend_calendar.py
       ```

    3. **Visualizza Dashboard**
       Usa le pagine nel menu laterale!
    """)

    st.markdown("---")

    st.markdown("""
    ### 📚 Documentazione

    - [Setup Locale](../SETUP_LOCALE.md)
    - [Dividend Calendar Guide](../DIVIDEND_CALENDAR_README.md)
    - [IB Gateway Setup](../IB_GATEWAY_SETUP.md)
    """)

    st.markdown("---")

    st.info("""
    💡 **Tip**: Usa la pagina **Dividend Calendar**
    per vedere i prossimi dividendi con yield >= 3%!
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>Dividend Recovery System v1.0</p>
    <p>Developed by Claude & User | 2026</p>
</div>
""", unsafe_allow_html=True)
