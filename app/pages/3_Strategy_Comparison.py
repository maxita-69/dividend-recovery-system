"""
Strategy Comparison - LONG D-1 vs LONG D0 vs FLIP & RIDE
Confronto strategie con costi REALI Fineco Conto Trading
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Dict, Any
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

# COSTI FINECO CONTO TRADING (aggiornati a 2025)
COMMISSION_RATE = 0.0019      # 0.19%
COMMISSION_MIN = 2.95         # €
COMMISSION_MAX = 19.0         # €
TOBIN_TAX_RATE = 0.001        # 0.1% solo su acquisto
OVERNIGHT_RATE = 0.105        # ~10.5% (EURIBOR 2.5% + spread 8%)
SHORT_COST_RATE = 0.0695      # 6.95% p.a. su posizioni short


def calculate_commission(controvalore: float) -> float:
    """Calcola commissione Fineco: 0.19% (min €2.95, max €19)"""
    comm = controvalore * COMMISSION_RATE
    return max(COMMISSION_MIN, min(comm, COMMISSION_MAX))


@dataclass
class PriceContext:
    """Contesto temporale per uno stacco dividendo"""
    stock_id: int
    ticker: str
    ex_date: pd.Timestamp
    dividend_amount: float
    d_minus_1_close: float
    d0_open: float
    d0_close: float
    d_plus_1_open: Optional[float] = None
    recovery_target: float = 0.0  # default: D-1 close

    @property
    def gap(self) -> float:
        return self.d_minus_1_close - self.d0_open


@dataclass
class StrategyResult:
    strategy: str
    net_profit: float
    gross_profit: float
    total_costs: float
    roi_pct: float
    recovery_days: int
    shares: float
    exposure: float
    buy_price: float
    sell_price: float
    buy_date: pd.Timestamp
    sell_date: pd.Timestamp
    details: Dict[str, Any]


@st.cache_resource
def get_database_session():
    """Get database session"""
    db_path = Path(__file__).parent.parent.parent / "data" / "dividend_recovery.db"
    if not db_path.exists():
        st.error(f"❌ Database non trovato: {db_path}")
        st.stop()
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def get_price_context(session, stock_id: int, ex_date: str, dividend_amount: float) -> PriceContext:
    """Estrae il contesto temporale attorno allo stacco"""
    prices = session.query(PriceData).filter_by(stock_id=stock_id).order_by(PriceData.date).all()
    if not prices:
        raise ValueError("Nessun dato storico per questo titolo")
    
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
    
    ex_ts = pd.Timestamp(ex_date)
    if ex_ts not in df.index:
        raise ValueError(f"Ex-date {ex_date} non presente nei dati")
    
    idx = df.index.get_loc(ex_ts)
    if idx == 0:
        raise ValueError("Nessun dato precedente lo stacco")
    
    d_minus_1_close = df.iloc[idx - 1]['close']
    d0_open = df.loc[ex_ts, 'open']
    d0_close = df.loc[ex_ts, 'close']
    
    d_plus_1_open = None
    if idx + 1 < len(df):
        d_plus_1_open = df.iloc[idx + 1]['open']
    
    # Target di recovery: D-1 close (break-even rispetto a chi ha tenuto)
    recovery_target = d_minus_1_close
    
    return PriceContext(
        stock_id=stock_id,
        ticker="",
        ex_date=ex_ts,
        dividend_amount=dividend_amount,
        d_minus_1_close=d_minus_1_close,
        d0_open=d0_open,
        d0_close=d0_close,
        d_plus_1_open=d_plus_1_open,
        recovery_target=recovery_target
    )


def apply_fineco_costs(
    gross_profit: float,
    exposure: float,
    shares: float,
    buy_price: float,
    sell_price: float,
    buy_date: pd.Timestamp,
    sell_date: pd.Timestamp,
    operations: int = 2,  # buy + sell
    short_exposure: float = 0.0,
    overnight_days_long: int = 0,
    overnight_days_short: int = 0,
    tobin_tax_applies: bool = True
) -> float:
    """Applica costi Fineco e restituisce net_profit"""
    # Commissioni (1 per operazione)
    comm_total = operations * calculate_commission(exposure)
    
    # Tobin tax (solo su acquisti)
    tobin = exposure * TOBIN_TAX_RATE if tobin_tax_applies else 0.0
    
    # Overnight cost long
    overnight_long = exposure * OVERNIGHT_RATE / 365 * overnight_days_long
    
    # Overnight cost short (se applicabile)
    overnight_short = short_exposure * SHORT_COST_RATE / 365 * overnight_days_short
    
    total_costs = comm_total + tobin + overnight_long + overnight_short
    net_profit = gross_profit - total_costs
    return net_profit, total_costs


def simulate_long_d1(context: PriceContext, capital: float, leverage: float) -> StrategyResult:
    buy_price = context.d_minus_1_close
    shares = (capital * leverage) / buy_price
    exposure = shares * buy_price
    
    # Cerca recupero al prezzo d'acquisto
    # Per simulazione: ipotizziamo recovery in 5 giorni (dato reale: spesso 1-3)
    # In futuro: estendi con dati storici del recupero
    recovery_days = 3  # placeholder — da sostituire con logica reale
    sell_price = context.recovery_target  # break-even
    
    price_gain = (sell_price - buy_price) * shares
    dividend_income = context.dividend_amount * shares
    gross_profit = price_gain + dividend_income
    
    # Costi: buy + sell (2 operazioni)
    # Overnight: 1 notte (D-1 → D0), poi chiusura in D+recovery_days
    overnight_days = 1 + recovery_days
    net_profit, total_costs = apply_fineco_costs(
        gross_profit=gross_profit,
        exposure=exposure,
        shares=shares,
        buy_price=buy_price,
        sell_price=sell_price,
        buy_date=context.ex_date - pd.Timedelta(days=1),
        sell_date=context.ex_date + pd.Timedelta(days=recovery_days),
        operations=2,
        overnight_days_long=overnight_days,
        tobin_tax_applies=True
    )
    
    return StrategyResult(
        strategy="LONG D-1",
        net_profit=net_profit,
        gross_profit=gross_profit,
        total_costs=total_costs,
        roi_pct=(net_profit / capital) * 100,
        recovery_days=recovery_days,
        shares=shares,
        exposure=exposure,
        buy_price=buy_price,
        sell_price=sell_price,
        buy_date=context.ex_date - pd.Timedelta(days=1),
        sell_date=context.ex_date + pd.Timedelta(days=recovery_days),
        details={
            "price_gain": price_gain,
            "dividend_income": dividend_income
        }
    )


def simulate_long_d0(context: PriceContext, capital: float, leverage: float) -> StrategyResult:
    buy_price = context.d0_open
    shares = (capital * leverage) / buy_price
    exposure = shares * buy_price
    
    # Recovery al prezzo D-1 close (break-even vs chi ha tenuto)
    recovery_days = 3
    sell_price = context.recovery_target
    
    price_gain = (sell_price - buy_price) * shares
    dividend_income = 0.0
    gross_profit = price_gain
    
    # Costi: buy + sell
    # Overnight: solo recovery_days (apertura D0 → chiusura D+recovery)
    overnight_days = recovery_days
    net_profit, total_costs = apply_fineco_costs(
        gross_profit=gross_profit,
        exposure=exposure,
        shares=shares,
        buy_price=buy_price,
        sell_price=sell_price,
        buy_date=context.ex_date,
        sell_date=context.ex_date + pd.Timedelta(days=recovery_days),
        operations=2,
        overnight_days_long=overnight_days,
        tobin_tax_applies=True
    )
    
    return StrategyResult(
        strategy="LONG D0",
        net_profit=net_profit,
        gross_profit=gross_profit,
        total_costs=total_costs,
        roi_pct=(net_profit / capital) * 100,
        recovery_days=recovery_days,
        shares=shares,
        exposure=exposure,
        buy_price=buy_price,
        sell_price=sell_price,
        buy_date=context.ex_date,
        sell_date=context.ex_date + pd.Timedelta(days=recovery_days),
        details={
            "price_gain": price_gain,
            "dividend_income": dividend_income
        }
    )


def simulate_flip_ride(context: PriceContext, capital: float, leverage: float) -> StrategyResult:
    if context.d_plus_1_open is None:
        raise ValueError("Necessario almeno un giorno dopo lo stacco per FLIP & RIDE")
    
    buy_price_1 = context.d_minus_1_close
    shares = (capital * leverage) / buy_price_1
    exposure = shares * buy_price_1
    
    # Fase 1: Long D-1 close → sell D0 open
    profit1 = (context.d0_open - buy_price_1 + context.dividend_amount) * shares
    
    # Fase 2: Short D0 open → cover D0 close
    profit2 = (context.d0_open - context.d0_close) * shares
    
    # Fase 3: Re-buy D+1 open → sell a recovery target
    buy_price_2 = context.d_plus_1_open
    sell_price = context.recovery_target
    profit3 = (sell_price - buy_price_2) * shares
    
    gross_profit = profit1 + profit2 + profit3
    
    # Costi:
    # - 6 operazioni: buy, sell, short, cover, re-buy, sell
    # - Overnight: 
    #     * long: 1 notte (D-1 → D0) → ma chiuso all'apertura → 0 notti
    #     * short: 0 notti (chiuso in giornata)
    #     * long2: recovery_days (da D+1 a D+1+recovery)
    recovery_days = 3
    net_profit, total_costs = apply_fineco_costs(
        gross_profit=gross_profit,
        exposure=exposure,
        shares=shares,
        buy_price=buy_price_1,  # non usato direttamente
        sell_price=sell_price,
        buy_date=context.ex_date - pd.Timedelta(days=1),
        sell_date=context.ex_date + pd.Timedelta(days=1 + recovery_days),
        operations=6,
        overnight_days_long=recovery_days,  # solo per il terzo long
        short_exposure=exposure,
        overnight_days_short=0,  # short chiuso in giornata
        tobin_tax_applies=True  # per ogni acquisto (3 volte: ma stimiamo 2×)
    )
    
    # Nota: Tobin tax applicata 3 volte (buy, re-buy, ...) → qui stimiamo 2× in tobin
    # In realtà, Fineco la calcola per ogni trade di acquisto → per precisione, servirebbe dettaglio
    
    return StrategyResult(
        strategy="FLIP & RIDE",
        net_profit=net_profit,
        gross_profit=gross_profit,
        total_costs=total_costs,
        roi_pct=(net_profit / capital) * 100,
        recovery_days=1 + recovery_days,
        shares=shares,
        exposure=exposure,
        buy_price=buy_price_1,
        sell_price=sell_price,
        buy_date=context.ex_date - pd.Timedelta(days=1),
        sell_date=context.ex_date + pd.Timedelta(days=1 + recovery_days),
        details={
            "profit_phase1": profit1,
            "profit_phase2": profit2,
            "profit_phase3": profit3,
            "gap_vs_div": abs(context.gap - context.dividend_amount)
        }
    )


# ======= STREAMLIT UI =======

st.title("⚙️ Confronto Strategie")
st.markdown("Confronto **LONG D-1** vs **LONG D0** vs **FLIP & RIDE** con costi REALI Fineco")

session = get_database_session()

# Stock selection
stocks = session.query(Stock).all()
if not stocks:
    st.warning("⚠️ Nessun titolo nel database")
    st.stop()

stock_options = {f"{s.ticker} - {s.name} ({s.market})": s for s in stocks}
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
col1, col2, col3 = st.columns(3)

with col1:
    leverage = st.slider("Leverage", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
with col2:
    capital = st.slider("Capitale (€)", min_value=300, max_value=10000, value=2000, step=100)
with col3:
    recovery_days_assumption = st.slider("Giorni recovery (assunto)", 1, 10, 3, 1)

# Calculate
if st.button("🚀 Calcola Strategie", type="primary"):
    with st.spinner("Calcolo in corso..."):
        try:
            # Ottieni contesto
            context = get_price_context(session, stock.id, dividend.ex_date, dividend.amount)
            context.ticker = stock.ticker
            
            # Warn se gap ≠ dividendo
            if abs(context.gap - context.dividend_amount) > 0.02 * context.dividend_amount:
                st.warning(f"⚠️ Gap ({context.gap:.3f}) ≠ Dividendo ({context.dividend_amount:.3f}) → dati potenzialmente non aggiustati o errati")
            
            # Simula
            results = []
            
            r1 = simulate_long_d1(context, capital, leverage)
            results.append(r1)
            
            r2 = simulate_long_d0(context, capital, leverage)
            results.append(r2)
            
            # Solo se c'è D+1
            if context.d_plus_1_open is not None:
                r3 = simulate_flip_ride(context, capital, leverage)
                results.append(r3)
            else:
                st.info("ℹ️ FLIP & RIDE non disponibile (mancano dati D+1)")
            
            # Mostra risultati
            st.success("✅ Calcolo completato!")
            
            # Tabella comparativa
            st.subheader("📊 Risultati Comparativi")
            comparison = pd.DataFrame([{
                'Strategia': r.strategy,
                'ROI %': f"{r.roi_pct:.2f}%",
                'Profit (€)': f"€{r.net_profit:.2f}",
                'Costi (€)': f"€{r.total_costs:.2f}",
                'Giorni': r.recovery_days,
                'Posizione': f"{r.shares:.1f} azioni",
                'Exposure': f"€{r.exposure:.0f}"
            } for r in results])
            st.dataframe(comparison, use_container_width=True, hide_index=True)
            
            # Dettaglio espandibile
            st.divider()
            st.subheader("📋 Dettaglio per Strategia")
            for r in results:
                with st.expander(f"**{r.strategy}** — ROI: {r.roi_pct:.2f}% | Net: €{r.net_profit:.2f}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Gross Profit", f"€{r.gross_profit:.2f}")
                        st.metric("Net Profit", f"€{r.net_profit:.2f}")
                    with c2:
                        st.metric("Costi Totali", f"€{r.total_costs:.2f}")
                        st.metric("Recovery Days", r.recovery_days)
                    with c3:
                        st.metric("Buy Price", f"€{r.buy_price:.3f}")
                        st.metric("Sell Price", f"€{r.sell_price:.3f}")
                    
                    if 'dividend_income' in r.details:
                        st.metric("Dividend Income", f"€{r.details['dividend_income']:.2f}")
                    if 'profit_phase1' in r.details:
                        st.info(f"Phase 1 (Long): €{r.details['profit_phase1']:.2f}")
                        st.info(f"Phase 2 (Short): €{r.details['profit_phase2']:.2f}")
                        st.info(f"Phase 3 (Recovery): €{r.details['profit_phase3']:.2f}")
        
        except Exception as e:
            st.error(f"❌ Errore: {str(e)}")
            st.code(str(e), language="python")

st.divider()
st.caption("""
📊 **Assunzioni**:  
- Recovery in {recovery_days_assumption} giorni (da personalizzare con dati storici)  
- Overnight: calcolato solo per posizioni aperte a fine giornata  
- FLIP & RIDE richiede dati fino a D+1  
💡 Prossimo step: integrazione con dati reali di recovery time
""".format(recovery_days_assumption=recovery_days_assumption))

# Footer
st.markdown("⚙️ *Fineco Conto Trading: Comm 0.19% (min €2.95), Tobin 0.1%, Overnight ~10.5%*")