"""
Strategy Comparison - VERSIONE CORRETTA
Confronto LONG D-1 vs LONG D0 vs SHORT+LONG con dati REALI e recovery detection
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import timedelta
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

# ============================================================================
# AUTHENTICATION - Must be after set_page_config
# ============================================================================
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_authentication

require_authentication()

# ============================================================================
# COSTI FINECO CONTO TRADING
# ============================================================================
COMMISSION_RATE = 0.0019      # 0.19%
COMMISSION_MIN = 2.95         # €
COMMISSION_MAX = 19.0         # €
TOBIN_TAX_RATE = 0.001        # 0.1% solo su acquisto
EURIBOR_1M = 0.025            # 2.5% (aggiornare periodicamente)
OVERNIGHT_SPREAD = 0.0799     # 7.99%
OVERNIGHT_RATE = EURIBOR_1M + OVERNIGHT_SPREAD  # ~10.5% annuo
SHORT_COST_RATE = 0.0695      # 6.95% annuo


def calculate_commission(controvalore):
    """Calcola commissione Fineco: 0.19% (min €2.95, max €19)"""
    comm = controvalore * COMMISSION_RATE
    return max(COMMISSION_MIN, min(comm, COMMISSION_MAX))


# ============================================================================
# FUNZIONI CORE - RECOVERY DETECTION
# ============================================================================

def get_price_dataframe(session, stock_id):
    """Ottieni DataFrame prezzi ordinato per data"""
    prices = session.query(PriceData).filter_by(
        stock_id=stock_id
    ).order_by(PriceData.date).all()
    
    if not prices:
        return None
    
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
    
    return df


def find_recovery(df, start_date, target_price, max_days=30):
    """
    Cerca il PRIMO giorno in cui il prezzo close >= target_price
    
    Args:
        df: DataFrame con prezzi (index = date)
        start_date: Data da cui iniziare (D0)
        target_price: Prezzo da recuperare (D-1 close)
        max_days: Giorni massimi di ricerca
    
    Returns:
        dict con recovery_date, recovery_days, recovery_price, recovered
    """
    start_date = pd.Timestamp(start_date)
    
    # Filtra dati >= start_date e prendi max_days
    future_data = df[df.index >= start_date].head(max_days)
    
    if future_data.empty:
        return {
            'recovery_date': None,
            'recovery_days': None,
            'recovery_price': None,
            'recovered': False
        }
    
    # Cerca primo giorno con close >= target
    # enumerate parte da 0: giorno 0 = stesso giorno (D0)
    for i, (date, row) in enumerate(future_data.iterrows()):
        if row['close'] >= target_price:
            return {
                'recovery_date': date,
                'recovery_days': i,  # 0 = stesso giorno, 1 = giorno dopo, ecc.
                'recovery_price': row['close'],
                'recovered': True
            }
    
    # Non ha recuperato entro max_days
    # Restituisci l'ultimo giorno disponibile
    last_date = future_data.index[-1]
    last_price = future_data.iloc[-1]['close']
    
    # Calcola giorni trascorsi da start_date all'ultimo giorno disponibile
    days_passed = (last_date - start_date).days
    
    return {
        'recovery_date': last_date,
        'recovery_days': days_passed,  # Giorni REALI trascorsi
        'recovery_price': last_price,
        'recovered': False
    }


# ============================================================================
# STRATEGIA A: LONG CON DIVIDENDO
# ============================================================================

def strategy_long_with_dividend(df, ex_date, dividend_amount, leverage, capital):
    """
    STRATEGIA A: Compra D-1 close, incassa dividendo, vende al recovery
    
    Entry: D-1 alle 17:25 (approssimato con close)
    Exit: Primo giorno con close >= D-1 close
    """
    ex_date = pd.Timestamp(ex_date)
    
    # Trova D-1
    dates_before = df[df.index < ex_date]
    if dates_before.empty:
        return {'error': 'Nessun dato prima dello stacco'}
    
    d_minus_1 = dates_before.index[-1]
    buy_price = df.loc[d_minus_1, 'close']
    
    # Calcola posizione
    shares = (capital * leverage) / buy_price
    exposure = shares * buy_price
    
    # Cerca recovery (da D0 in poi)
    recovery = find_recovery(df, ex_date, target_price=buy_price, max_days=30)
    
    if not recovery['recovered']:
        # Non ha recuperato: vendi comunque all'ultimo giorno
        sell_date = recovery['recovery_date']
        sell_price = recovery['recovery_price']
        recovered = False
    else:
        sell_date = recovery['recovery_date']
        sell_price = recovery['recovery_price']
        recovered = True
    
    # P&L
    price_gain = (sell_price - buy_price) * shares
    dividend_income = dividend_amount * shares
    gross_profit = price_gain + dividend_income
    
    # COSTI
    # 1. Commissioni: buy + sell
    comm_buy = calculate_commission(exposure)
    comm_sell = calculate_commission(shares * sell_price)
    
    # 2. Tobin tax: solo su acquisto
    tobin = exposure * TOBIN_TAX_RATE
    
    # 3. Overnight: da D-1 a sell_date
    overnight_days = (sell_date - d_minus_1).days
    overnight_cost = (exposure * OVERNIGHT_RATE / 365) * overnight_days
    
    total_costs = comm_buy + comm_sell + tobin + overnight_cost
    net_profit = gross_profit - total_costs
    roi = (net_profit / capital) * 100
    
    return {
        'strategy': 'LONG D-1 (con dividendo)',
        'buy_date': d_minus_1,
        'buy_price': buy_price,
        'sell_date': sell_date,
        'sell_price': sell_price,
        'shares': shares,
        'exposure': exposure,
        'leverage': leverage,
        'recovery_days': recovery['recovery_days'],
        'recovered': recovered,
        'price_gain': price_gain,
        'dividend_income': dividend_income,
        'gross_profit': gross_profit,
        'comm_buy': comm_buy,
        'comm_sell': comm_sell,
        'tobin_tax': tobin,
        'overnight_cost': overnight_cost,
        'total_costs': total_costs,
        'net_profit': net_profit,
        'roi': roi
    }


# ============================================================================
# STRATEGIA B: LONG SENZA DIVIDENDO
# ============================================================================

def strategy_long_without_dividend(df, ex_date, dividend_amount, leverage, capital):
    """
    STRATEGIA B: Compra D0 open, NO dividendo, vende al recovery
    
    Entry: D0 alle 09:05 (approssimato con open)
    Exit: Primo giorno con close >= D-1 close (stesso target di A!)
    """
    ex_date = pd.Timestamp(ex_date)
    
    # Trova D-1 close (target recovery)
    dates_before = df[df.index < ex_date]
    if dates_before.empty:
        return {'error': 'Nessun dato prima dello stacco'}
    
    d_minus_1 = dates_before.index[-1]
    target_price = df.loc[d_minus_1, 'close']
    
    # Entry: D0 open
    if ex_date not in df.index:
        return {'error': 'Ex-date non presente nei dati'}
    
    buy_price = df.loc[ex_date, 'open']
    
    # Calcola posizione
    shares = (capital * leverage) / buy_price
    exposure = shares * buy_price
    
    # Cerca recovery (da D0 in poi, stesso target di A)
    recovery = find_recovery(df, ex_date, target_price=target_price, max_days=30)
    
    if not recovery['recovered']:
        sell_date = recovery['recovery_date']
        sell_price = recovery['recovery_price']
        recovered = False
    else:
        sell_date = recovery['recovery_date']
        sell_price = recovery['recovery_price']
        recovered = True
    
    # P&L
    price_gain = (sell_price - buy_price) * shares
    dividend_income = 0.0  # NO dividendo
    gross_profit = price_gain
    
    # COSTI
    comm_buy = calculate_commission(exposure)
    comm_sell = calculate_commission(shares * sell_price)
    tobin = exposure * TOBIN_TAX_RATE
    
    # Overnight: da D0 a sell_date
    overnight_days = (sell_date - ex_date).days
    overnight_cost = (exposure * OVERNIGHT_RATE / 365) * overnight_days
    
    total_costs = comm_buy + comm_sell + tobin + overnight_cost
    net_profit = gross_profit - total_costs
    roi = (net_profit / capital) * 100
    
    return {
        'strategy': 'LONG D0 (senza dividendo)',
        'buy_date': ex_date,
        'buy_price': buy_price,
        'sell_date': sell_date,
        'sell_price': sell_price,
        'shares': shares,
        'exposure': exposure,
        'leverage': leverage,
        'recovery_days': recovery['recovery_days'],
        'recovered': recovered,
        'target_price': target_price,
        'price_gain': price_gain,
        'dividend_income': dividend_income,
        'gross_profit': gross_profit,
        'comm_buy': comm_buy,
        'comm_sell': comm_sell,
        'tobin_tax': tobin,
        'overnight_cost': overnight_cost,
        'total_costs': total_costs,
        'net_profit': net_profit,
        'roi': roi
    }


# ============================================================================
# STREAMLIT UI
# ============================================================================

@st.cache_resource
def get_database_session():
    """Get database session"""
    db_path = Path(__file__).parent.parent.parent / "data" / "dividend_recovery.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


st.title("⚙️ Confronto Strategie A vs B")
st.markdown("""
Confronto **2 strategie** con **dati storici REALI** e **recovery detection automatico**:
- **Strategia A**: LONG D-1 (con dividendo) - Compra giorno prima, incassa dividendo
- **Strategia B**: LONG D0 (senza dividendo) - Compra giorno stacco, prezzo già scontato

🎯 **Obiettivo**: Verificare quale strategia rende di più al netto dei costi Fineco
""")

session = get_database_session()

# Stock selection
stocks = session.query(Stock).all()
if not stocks:
    st.warning("⚠️ Nessun titolo nel database")
    st.stop()

stock_options = {f"{s.ticker} - {s.name}": s for s in stocks}
selected = st.selectbox("Seleziona Titolo", list(stock_options.keys()))
stock = stock_options[selected]

# Get price data
df = get_price_dataframe(session, stock.id)
if df is None:
    st.error("❌ Nessun dato prezzi per questo titolo")
    st.stop()

# Dividend selection
dividends = session.query(Dividend).filter_by(stock_id=stock.id).order_by(
    Dividend.ex_date.desc()
).all()

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
if st.button("🚀 Calcola con Dati REALI", type="primary"):
    with st.spinner("Analisi dati storici in corso..."):
        try:
            results = []
            
            # Strategia A
            r_a = strategy_long_with_dividend(df, dividend.ex_date, dividend.amount, leverage, capital)
            if 'error' not in r_a:
                results.append(r_a)
            else:
                st.error(f"Strategia A: {r_a['error']}")
            
            # Strategia B
            r_b = strategy_long_without_dividend(df, dividend.ex_date, dividend.amount, leverage, capital)
            if 'error' not in r_b:
                results.append(r_b)
            else:
                st.error(f"Strategia B: {r_b['error']}")
            
            if not results:
                st.error("❌ Nessuna strategia calcolabile")
                st.stop()
            
            st.success("✅ Analisi completata con dati storici REALI!")
            
            # Tabella comparativa
            st.subheader("📊 Risultati Comparativi")
            
            comparison = pd.DataFrame([{
                'Strategia': r['strategy'],
                'ROI %': f"{r['roi']:.2f}%",
                'Net Profit': f"€{r['net_profit']:.2f}",
                'Gross Profit': f"€{r['gross_profit']:.2f}",
                'Costi Totali': f"€{r['total_costs']:.2f}",
                'Recovery Days': r['recovery_days'] if r['recovered'] else f"{r['recovery_days']}*",
                'Recovered': '✅' if r['recovered'] else '❌'
            } for r in results])
            
            st.dataframe(comparison, use_container_width=True, hide_index=True)
            
            if not all(r['recovered'] for r in results):
                st.warning("⚠️ * = Non ha recuperato entro 30 giorni (vendita forzata)")
            
            # Dettaglio per strategia
            st.divider()
            st.subheader("📋 Dettaglio Strategie")
            
            for r in results:
                with st.expander(f"**{r['strategy']}** - ROI: {r['roi']:.2f}% | Net: €{r['net_profit']:.2f}"):
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Buy Date", r['buy_date'].strftime('%Y-%m-%d'))
                        if 'buy_price' in r:
                            st.metric("Buy Price", f"€{r['buy_price']:.3f}")
                        st.metric("Shares", f"{r['shares']:.2f}")
                        
                    with col2:
                        st.metric("Sell Date", r['sell_date'].strftime('%Y-%m-%d'))
                        if 'sell_price' in r:
                            st.metric("Sell Price", f"€{r['sell_price']:.3f}")
                        st.metric("Recovery Days", r['recovery_days'])
                        
                    with col3:
                        st.metric("Gross Profit", f"€{r['gross_profit']:.2f}")
                        st.metric("Total Costs", f"€{r['total_costs']:.2f}")
                        st.metric("Net Profit", f"€{r['net_profit']:.2f}")
                    
                    # Breakdown costi
                    st.markdown("**Breakdown Costi:**")
                    if 'comm_buy' in r:
                        st.write(f"- Commissione buy: €{r['comm_buy']:.2f}")
                        st.write(f"- Commissione sell: €{r['comm_sell']:.2f}")
                        st.write(f"- Tobin tax: €{r['tobin_tax']:.2f}")
                        st.write(f"- Overnight cost: €{r['overnight_cost']:.2f}")
                    
                    # Dividend income
                    if 'dividend_income' in r and r['dividend_income'] > 0:
                        st.success(f"💰 Dividend income: €{r['dividend_income']:.2f}")
        
        except Exception as e:
            st.error(f"❌ Errore: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

st.divider()
st.caption("💡 Recovery detection automatico su dati storici REALI | Costi Fineco: Comm 0.19%, Tobin 0.1%, Overnight ~10.5%")
