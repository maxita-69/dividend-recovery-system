"""
Strategy Comparison - LONG D-1 vs LONG D0 vs FLIP & RIDE
Confronto strategie con costi REALI Fineco Conto Trading
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from database.models import Stock, Dividend, PriceData

st.set_page_config(
    page_title="Strategy Comparison",
    page_icon="⚙️",
    layout="wide"
)

# COSTI FINECO CONTO TRADING
COMMISSION_RATE = 0.0019  # 0.19%
COMMISSION_MIN = 2.95
COMMISSION_MAX = 19.0
TOBIN_TAX_RATE = 0.001    # 0.1% solo su acquisto
EURIBOR_1M = 0.025
OVERNIGHT_SPREAD = 0.0799
OVERNIGHT_RATE = EURIBOR_1M + OVERNIGHT_SPREAD  # ~10.5%
SHORT_COST_RATE = 0.0695  # 6.95%


def calculate_commission(controvalore):
    """Calcola commissione Fineco: 0.19% (min 2.95, max 19)"""
    comm = controvalore * COMMISSION_RATE
    return max(COMMISSION_MIN, min(comm, COMMISSION_MAX))


@st.cache_resource
def get_database_session():
    """Get database session"""
    db_path = Path(__file__).parent.parent.parent / "data" / "dividend_recovery.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def analyze_long_d1(session, stock_id, ex_date, dividend_amount, leverage, capital):
    """Strategia LONG D-1: Compra giorno PRIMA (con dividendo)"""
    prices = session.query(PriceData).filter_by(stock_id=stock_id).order_by(PriceData.date).all()
    df = pd.DataFrame([{
        'date': p.date,
        'open': p.open,
        'high': p.high,
        'low': p.low,
        'close': p.close,
        'volume': p.volume
    } for p in prices])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    ex_date = pd.Timestamp(ex_date)
    
    if ex_date not in df.index:
        return {'error': 'Ex-date not in data'}
    
    ex_idx = df.index.get_loc(ex_date)
    if ex_idx == 0:
        return {'error': 'No pre-stacco data'}
    
    # BUY D-1 close
    buy_date = df.index[ex_idx - 1]
    buy_price = df.loc[buy_date, 'close']
    shares = (capital * leverage) / buy_price
    exposure = shares * buy_price
    
    # Cerca recovery
    post_ex = df.loc[ex_date:]
    recovery_day = None
    recovery_days = 0
    
    for i, (date, row) in enumerate(post_ex.iterrows()):
        if row['close'] >= buy_price:
            recovery_day = date
            recovery_days = i
            sell_price = row['close']
            break
    
    if recovery_day is None:
        recovery_day = post_ex.index[-1]
        recovery_days = len(post_ex) - 1
        sell_price = post_ex.iloc[-1]['close']
    
    # Calcoli P&L
    price_gain = (sell_price - buy_price) * shares
    dividend_income = dividend_amount * shares
    
    # Costi
    comm_buy = calculate_commission(exposure)
    comm_sell = calculate_commission(shares * sell_price)
    overnight_days = (recovery_day - buy_date).days
    overnight_cost = (exposure * OVERNIGHT_RATE / 365) * overnight_days
    tobin_tax = exposure * TOBIN_TAX_RATE
    
    total_costs = comm_buy + comm_sell + overnight_cost + tobin_tax
    net_profit = price_gain + dividend_income - total_costs
    roi = (net_profit / capital) * 100
    
    return {
        'strategy': 'LONG D-1',
        'buy_date': buy_date,
        'buy_price': buy_price,
        'sell_date': recovery_day,
        'sell_price': sell_price,
        'recovery_days': recovery_days,
        'shares': shares,
        'exposure': exposure,
        'price_gain': price_gain,
        'dividend_income': dividend_income,
        'comm_buy': comm_buy,
        'comm_sell': comm_sell,
        'overnight_cost': overnight_cost,
        'tobin_tax': tobin_tax,
        'total_costs': total_costs,
        'net_profit': net_profit,
        'roi': roi
    }


def analyze_long_d0(session, stock_id, ex_date, dividend_amount, leverage, capital):
    """Strategia LONG D0: Compra giorno stacco (SENZA dividendo)"""
    prices = session.query(PriceData).filter_by(stock_id=stock_id).order_by(PriceData.date).all()
    df = pd.DataFrame([{
        'date': p.date,
        'open': p.open,
        'high': p.high,
        'low': p.low,
        'close': p.close,
        'volume': p.volume
    } for p in prices])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    ex_date = pd.Timestamp(ex_date)
    
    if ex_date not in df.index:
        return {'error': 'Ex-date not in data'}
    
    ex_idx = df.index.get_loc(ex_date)
    if ex_idx == 0:
        return {'error': 'No pre-stacco data'}
    
    # BUY D0 open
    buy_date = ex_date
    buy_price = df.loc[buy_date, 'open']
    shares = (capital * leverage) / buy_price
    exposure = shares * buy_price
    
    # Target = prezzo pre-stacco
    target_price = df.index[ex_idx - 1]
    target_close = df.loc[target_price, 'close']
    
    # Cerca recovery
    post_ex = df.loc[ex_date:]
    recovery_day = None
    recovery_days = 0
    
    for i, (date, row) in enumerate(post_ex.iterrows()):
        if row['close'] >= target_close:
            recovery_day = date
            recovery_days = i
            sell_price = row['close']
            break
    
    if recovery_day is None:
        recovery_day = post_ex.index[-1]
        recovery_days = len(post_ex) - 1
        sell_price = post_ex.iloc[-1]['close']
    
    # Calcoli P&L
    price_gain = (sell_price - buy_price) * shares
    dividend_income = 0  # NO dividendo
    
    # Costi
    comm_buy = calculate_commission(exposure)
    comm_sell = calculate_commission(shares * sell_price)
    overnight_days = (recovery_day - buy_date).days
    overnight_cost = (exposure * OVERNIGHT_RATE / 365) * overnight_days
    tobin_tax = exposure * TOBIN_TAX_RATE
    
    total_costs = comm_buy + comm_sell + overnight_cost + tobin_tax
    net_profit = price_gain + dividend_income - total_costs
    roi = (net_profit / capital) * 100
    
    return {
        'strategy': 'LONG D0',
        'buy_date': buy_date,
        'buy_price': buy_price,
        'sell_date': recovery_day,
        'sell_price': sell_price,
        'recovery_days': recovery_days,
        'shares': shares,
        'exposure': exposure,
        'price_gain': price_gain,
        'dividend_income': dividend_income,
        'comm_buy': comm_buy,
        'comm_sell': comm_sell,
        'overnight_cost': overnight_cost,
        'tobin_tax': tobin_tax,
        'total_costs': total_costs,
        'net_profit': net_profit,
        'roi': roi
    }


def analyze_flip_ride(session, stock_id, ex_date, dividend_amount, leverage, capital):
    """Strategia FLIP & RIDE complessa"""
    prices = session.query(PriceData).filter_by(stock_id=stock_id).order_by(PriceData.date).all()
    df = pd.DataFrame([{
        'date': p.date,
        'open': p.open,
        'high': p.high,
        'low': p.low,
        'close': p.close,
        'volume': p.volume
    } for p in prices])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    ex_date = pd.Timestamp(ex_date)
    
    if ex_date not in df.index:
        return {'error': 'Ex-date not in data'}
    
    ex_idx = df.index.get_loc(ex_date)
    if ex_idx == 0 or ex_idx >= len(df) - 1:
        return {'error': 'Insufficient data'}
    
    # PHASE 1: Long pre-stacco
    buy_date_1 = df.index[ex_idx - 1]
    buy_price_1 = df.loc[buy_date_1, 'close']
    shares_1 = (capital * leverage) / buy_price_1
    exposure_1 = shares_1 * buy_price_1
    
    # PHASE 2: Flip at open D0
    ex_open = df.loc[ex_date, 'open']
    ex_close = df.loc[ex_date, 'close']
    
    sell_price_1 = ex_open
    profit_long = (sell_price_1 - buy_price_1) * shares_1 + (dividend_amount * shares_1)
    
    # Short D0
    short_open = ex_open
    short_close = ex_close
    profit_short = (short_open - short_close) * shares_1
    
    # PHASE 3: Re-buy D+1
    buy_date_2 = df.index[ex_idx + 1]
    buy_price_2 = df.loc[buy_date_2, 'open']
    
    # Recovery
    post_d1 = df.loc[buy_date_2:]
    recovery_day = None
    recovery_days = 0
    
    for i, (date, row) in enumerate(post_d1.iterrows()):
        if row['close'] >= buy_price_1:
            recovery_day = date
            recovery_days = i
            sell_price_2 = row['close']
            break
    
    if recovery_day is None:
        recovery_day = post_d1.index[-1]
        recovery_days = len(post_d1) - 1
        sell_price_2 = post_d1.iloc[-1]['close']
    
    profit_recovery = (sell_price_2 - buy_price_2) * shares_1
    
    # COSTI
    # 6 operazioni totali!
    comm1 = calculate_commission(exposure_1)  # Buy D-1
    comm2 = calculate_commission(shares_1 * sell_price_1)  # Sell D0
    comm3 = calculate_commission(shares_1 * short_open)  # Short D0
    comm4 = calculate_commission(shares_1 * short_close)  # Cover short
    comm5 = calculate_commission(shares_1 * buy_price_2)  # Re-buy D+1
    comm6 = calculate_commission(shares_1 * sell_price_2)  # Final sell
    
    overnight_1 = (exposure_1 * OVERNIGHT_RATE / 365) * 1  # 1 notte
    short_cost = (shares_1 * short_open * SHORT_COST_RATE / 365) * 1
    overnight_2_days = (recovery_day - buy_date_2).days
    overnight_2 = (shares_1 * buy_price_2 * OVERNIGHT_RATE / 365) * overnight_2_days
    
    tobin1 = exposure_1 * TOBIN_TAX_RATE
    tobin2 = shares_1 * buy_price_2 * TOBIN_TAX_RATE
    
    dividend_paid = dividend_amount * shares_1  # Pagato quando short
    
    total_costs = (comm1 + comm2 + comm3 + comm4 + comm5 + comm6 + 
                  overnight_1 + short_cost + overnight_2 + 
                  tobin1 + tobin2 + dividend_paid)
    
    gross_profit = profit_long + profit_short + profit_recovery
    net_profit = gross_profit - total_costs
    roi = (net_profit / capital) * 100
    
    return {
        'strategy': 'FLIP & RIDE',
        'buy_date': buy_date_1,
        'buy_price': buy_price_1,
        'sell_date': recovery_day,
        'sell_price': sell_price_2,
        'recovery_days': (recovery_day - buy_date_1).days,
        'shares': shares_1,
        'exposure': exposure_1,
        'gross_profit': gross_profit,
        'total_costs': total_costs,
        'net_profit': net_profit,
        'roi': roi,
        'detail': f"Long: €{profit_long:.2f}, Short: €{profit_short:.2f}, Recovery: €{profit_recovery:.2f}"
    }


# ======= STREAMLIT UI =======

st.title("⚙️ Confronto Strategie")
st.markdown("Confronta **LONG D-1** vs **LONG D0** vs **FLIP & RIDE** con costi REALI Fineco")

session = get_database_session()

# Stock selection
stocks = session.query(Stock).all()
stock_options = {f"{s.ticker} - {s.name}": s for s in stocks}

if not stock_options:
    st.warning("⚠️ Nessun titolo nel database")
    st.stop()

selected_stock = st.selectbox("Seleziona Titolo", list(stock_options.keys()))
stock = stock_options[selected_stock]

# Dividend selection
dividends = session.query(Dividend).filter_by(stock_id=stock.id).order_by(Dividend.ex_date.desc()).all()

if not dividends:
    st.warning(f"⚠️ Nessun dividendo per {stock.ticker}")
    st.stop()

div_options = {f"{d.ex_date} - €{d.amount:.3f}": d for d in dividends}
selected_div = st.selectbox("Seleziona Dividendo", list(div_options.keys()))
dividend = div_options[selected_div]

# Parameters
st.divider()
col1, col2 = st.columns(2)

with col1:
    leverage = st.slider("Leverage", min_value=1.0, max_value=10.0, value=3.0, step=0.5)

with col2:
    capital = st.slider("Capitale (€)", min_value=300, max_value=10000, value=2000, step=100)

# Calculate
if st.button("🚀 Calcola Strategie", type="primary"):
    with st.spinner("Calcolo in corso..."):
        
        results = []
        
        # LONG D-1
        r1 = analyze_long_d1(session, stock.id, dividend.ex_date, dividend.amount, leverage, capital)
        if 'error' not in r1:
            results.append(r1)
        
        # LONG D0
        r2 = analyze_long_d0(session, stock.id, dividend.ex_date, dividend.amount, leverage, capital)
        if 'error' not in r2:
            results.append(r2)
        
        # FLIP & RIDE
        r3 = analyze_flip_ride(session, stock.id, dividend.ex_date, dividend.amount, leverage, capital)
        if 'error' not in r3:
            results.append(r3)
        
        if results:
            st.success("✅ Calcolo completato!")
            
            # Summary table
            st.subheader("📊 Risultati Comparativi")
            
            comparison = pd.DataFrame([{
                'Strategia': r['strategy'],
                'ROI %': f"{r['roi']:.2f}%",
                'Profit (€)': f"€{r['net_profit']:.2f}",
                'Costi (€)': f"€{r['total_costs']:.2f}",
                'Days': r['recovery_days'],
                'Buy Price': f"€{r['buy_price']:.3f}",
                'Sell Price': f"€{r['sell_price']:.3f}"
            } for r in results])
            
            st.dataframe(comparison, use_container_width=True, hide_index=True)
            
            # Details
            st.divider()
            st.subheader("📋 Dettaglio Strategie")
            
            for r in results:
                with st.expander(f"**{r['strategy']}** - ROI: {r['roi']:.2f}%"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Net Profit", f"€{r['net_profit']:.2f}")
                        st.metric("Exposure", f"€{r['exposure']:.2f}")
                        st.metric("Shares", f"{r['shares']:.2f}")
                    
                    with col2:
                        st.metric("Recovery Days", r['recovery_days'])
                        st.metric("Total Costs", f"€{r['total_costs']:.2f}")
                        if 'dividend_income' in r:
                            st.metric("Dividend Income", f"€{r['dividend_income']:.2f}")
                    
                    if 'detail' in r:
                        st.info(r['detail'])
        else:
            st.error("❌ Errore nel calcolo")

st.divider()
st.caption("Costi Fineco Conto Trading: Comm 0.19% (min €2.95, max €19), Tobin 0.1%, Overnight ~10.5%")
