"""
Dividend Recovery System - Home Page
Dashboard principale con status sistema e overview
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.models import Stock, Dividend, PriceData, DataCollectionLog

# Page config
st.set_page_config(
    page_title="Dividend Recovery System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# AUTHENTICATION - Must be after set_page_config
# ============================================================================
sys.path.insert(0, str(Path(__file__).parent))
from auth import require_authentication

require_authentication()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-ok {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_database_session():
    """Get database session (cached)"""
    db_path = Path(__file__).parent.parent / "data" / "dividend_recovery.db"
    
    if not db_path.exists():
        st.error(f"❌ Database not found at: {db_path}")
        st.info("💡 Run `python download_stock_data.py` first to create the database")
        st.stop()
    
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def get_system_status():
    """Get system status and statistics"""
    session = get_database_session()
    
    # Count records
    n_stocks = session.query(Stock).count()
    n_dividends = session.query(Dividend).count()
    n_prices = session.query(PriceData).count()
    
    # Latest update
    latest_price = session.query(PriceData).order_by(PriceData.date.desc()).first()
    last_update = latest_price.date if latest_price else None
    
    # Latest collection log
    latest_log = session.query(DataCollectionLog).order_by(
        DataCollectionLog.timestamp.desc()
    ).first()
    
    return {
        'n_stocks': n_stocks,
        'n_dividends': n_dividends,
        'n_prices': n_prices,
        'last_update': last_update,
        'latest_log': latest_log
    }


def get_stocks_overview():
    """Get overview of all supervised stocks"""
    session = get_database_session()
    
    stocks = session.query(Stock).all()
    
    data = []
    for stock in stocks:
        # Get dividend count
        n_dividends = session.query(Dividend).filter_by(stock_id=stock.id).count()
        
        # Get price range
        prices = session.query(PriceData).filter_by(stock_id=stock.id).order_by(PriceData.date).all()
        
        if prices:
            first_date = prices[0].date
            last_date = prices[-1].date
            current_price = prices[-1].close
        else:
            first_date = None
            last_date = None
            current_price = None
        
        # Get last dividend
        last_div = session.query(Dividend).filter_by(stock_id=stock.id).order_by(
            Dividend.ex_date.desc()
        ).first()
        
        data.append({
            'Ticker': stock.ticker,
            'Nome': stock.name,
            'Mercato': stock.market,
            'Dividendi': n_dividends,
            'Primo Dato': first_date.strftime('%Y-%m-%d') if first_date else '-',
            'Ultimo Dato': last_date.strftime('%Y-%m-%d') if last_date else '-',
            'Prezzo Attuale': f"€{current_price:.3f}" if current_price else '-',
            'Ultimo Dividendo': last_div.ex_date.strftime('%Y-%m-%d') if last_div else '-'
        })
    
    return pd.DataFrame(data)


# Main page
st.markdown('<p class="main-header">📊 Dividend Recovery System</p>', unsafe_allow_html=True)

st.markdown("""
Sistema quantitativo per analisi e trading dividend recovery su titoli italiani.

**Strategia**: Analisi pattern di recupero prezzo post-stacco dividendo con leverage su Fineco.
""")

st.divider()

# System Status
st.subheader("🔧 System Status")

try:
    status = get_system_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Titoli Supervisionati", status['n_stocks'])
    
    with col2:
        st.metric("Record Prezzi", f"{status['n_prices']:,}")
    
    with col3:
        st.metric("Dividendi Storici", status['n_dividends'])
    
    with col4:
        if status['last_update']:
            days_ago = (datetime.now().date() - status['last_update']).days
            st.metric("Ultimo Aggiornamento", f"{days_ago} giorni fa")
        else:
            st.metric("Ultimo Aggiornamento", "N/A")
    
    # Status indicator
    if status['last_update']:
        days_ago = (datetime.now().date() - status['last_update']).days
        if days_ago == 0:
            st.success("✅ Sistema aggiornato")
        elif days_ago <= 7:
            st.info(f"ℹ️ Ultimo aggiornamento: {days_ago} giorni fa")
        else:
            st.warning(f"⚠️ Dati non aggiornati da {days_ago} giorni")
    
    st.divider()
    
    # Stocks Overview
    st.subheader("📋 Titoli Supervisionati")
    
    df = get_stocks_overview()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Nessun titolo nel database")
        st.info("💡 Esegui `python download_stock_data.py` per popolare il database")
    
    st.divider()
    
    # Quick Navigation
    st.subheader("🧭 Navigazione Rapida")

    col1, col2 = st.columns(2)

    with col1:
        st.page_link("pages/1_Single_Stock.py", label="📊 Analisi Singolo Titolo", icon="📊")
        st.page_link("pages/2_Recovery_Analysis.py", label="📈 Recovery Analysis", icon="📈")

    with col2:
        st.page_link("pages/3_Strategy_Comparison.py", label="⚙️ Confronto Strategie", icon="⚙️")
        st.page_link("pages/4_Pattern_Analysis.py", label="🔍 Pattern Analysis", icon="🔍")

except Exception as e:
    st.error(f"❌ Errore durante il caricamento: {str(e)}")
    st.info("💡 Assicurati che il database sia stato creato con `python download_stock_data.py`")

# Footer
st.divider()
st.caption("Dividend Recovery System v0.1 - Sistema quantitativo per dividend capture trading")
