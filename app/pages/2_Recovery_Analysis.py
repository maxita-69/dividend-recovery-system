"""
Recovery Analysis - Analisi Storica Dividend Recovery
Analizza TUTTI i dividendi storici per capire pattern di recovery
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from database.models import Stock, Dividend, PriceData

st.set_page_config(
    page_title="Recovery Analysis",
    page_icon="📈",
    layout="wide"
)


# ============================================================================
# FUNZIONI CORE
# ============================================================================

@st.cache_resource
def get_database_session():
    """Get database session"""
    db_path = Path(__file__).parent.parent.parent / "data" / "dividend_recovery.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


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
    
    Returns:
        dict con recovery_date, recovery_days, recovery_price, recovered
    """
    start_date = pd.Timestamp(start_date)
    
    # Filtra dati >= start_date
    future_data = df[df.index >= start_date].head(max_days)
    
    if future_data.empty:
        return {
            'recovery_date': None,
            'recovery_days': None,
            'recovery_price': None,
            'recovered': False
        }
    
    # Cerca primo giorno con close >= target
    for i, (date, row) in enumerate(future_data.iterrows()):
        if row['close'] >= target_price:
            return {
                'recovery_date': date,
                'recovery_days': i,
                'recovery_price': row['close'],
                'recovered': True
            }
    
    # Non ha recuperato entro max_days
    last_date = future_data.index[-1]
    last_price = future_data.iloc[-1]['close']
    
    return {
        'recovery_date': last_date,
        'recovery_days': len(future_data) - 1,
        'recovery_price': last_price,
        'recovered': False
    }


def analyze_all_dividends(df, dividends):
    """
    Analizza TUTTI i dividendi storici e calcola recovery per ognuno
    
    Returns:
        DataFrame con analisi completa
    """
    results = []
    
    for div in dividends:
        ex_date = pd.Timestamp(div.ex_date)
        
        # Trova D-1 close (target recovery)
        dates_before = df[df.index < ex_date]
        if dates_before.empty:
            continue
        
        d_minus_1 = dates_before.index[-1]
        target_price = df.loc[d_minus_1, 'close']
        
        # Prezzi D0
        if ex_date not in df.index:
            continue
        
        d0_open = df.loc[ex_date, 'open']
        d0_close = df.loc[ex_date, 'close']
        
        # Gap
        gap = target_price - d0_open
        gap_pct = (gap / target_price) * 100
        
        # Recovery da D0
        recovery = find_recovery(df, ex_date, target_price, max_days=30)
        
        # Calcola dividend yield
        div_yield = (div.amount / target_price) * 100
        
        results.append({
            'ex_date': div.ex_date,
            'dividend': div.amount,
            'div_yield': div_yield,
            'd_minus_1_close': target_price,
            'd0_open': d0_open,
            'd0_close': d0_close,
            'gap': gap,
            'gap_pct': gap_pct,
            'recovery_days': recovery['recovery_days'],
            'recovery_date': recovery['recovery_date'],
            'recovery_price': recovery['recovery_price'],
            'recovered': recovery['recovered']
        })
    
    return pd.DataFrame(results)


# ============================================================================
# STREAMLIT UI
# ============================================================================

st.title("📈 Recovery Analysis - Analisi Storica")
st.markdown("""
Analisi **TUTTI i dividendi storici** per capire:
- Quanto tempo impiega il titolo a recuperare?
- Quale è la probabilità di recovery?
- Ci sono pattern ricorrenti?
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

# Get data
df = get_price_dataframe(session, stock.id)
if df is None:
    st.error("❌ Nessun dato prezzi per questo titolo")
    st.stop()

dividends = session.query(Dividend).filter_by(stock_id=stock.id).order_by(
    Dividend.ex_date
).all()

if not dividends:
    st.warning(f"⚠️ Nessun dividendo per {stock.ticker}")
    st.stop()

# Analyze all dividends
with st.spinner("Analisi di tutti i dividendi storici..."):
    analysis_df = analyze_all_dividends(df, dividends)

if analysis_df.empty:
    st.error("❌ Impossibile analizzare i dividendi (dati insufficienti)")
    st.stop()

st.success(f"✅ Analizzati {len(analysis_df)} dividendi storici!")

# ============================================================================
# SEZIONE 1: TABELLA COMPLETA
# ============================================================================

st.divider()
st.subheader("📋 Tabella Completa Dividendi")

# Formatta tabella per display
display_df = analysis_df.copy()
display_df['ex_date'] = pd.to_datetime(display_df['ex_date']).dt.strftime('%Y-%m-%d')
display_df['recovery_date'] = pd.to_datetime(display_df['recovery_date']).dt.strftime('%Y-%m-%d')
display_df['dividend'] = display_df['dividend'].apply(lambda x: f"€{x:.3f}")
display_df['div_yield'] = display_df['div_yield'].apply(lambda x: f"{x:.2f}%")
display_df['d_minus_1_close'] = display_df['d_minus_1_close'].apply(lambda x: f"€{x:.3f}")
display_df['d0_open'] = display_df['d0_open'].apply(lambda x: f"€{x:.3f}")
display_df['gap'] = display_df['gap'].apply(lambda x: f"€{x:.3f}")
display_df['gap_pct'] = display_df['gap_pct'].apply(lambda x: f"{x:.2f}%")
display_df['recovered'] = display_df['recovered'].apply(lambda x: '✅' if x else '❌')

# Rinomina colonne
display_df = display_df.rename(columns={
    'ex_date': 'Ex-Date',
    'dividend': 'Dividendo',
    'div_yield': 'Yield %',
    'd_minus_1_close': 'D-1 Close',
    'd0_open': 'D0 Open',
    'gap': 'Gap',
    'gap_pct': 'Gap %',
    'recovery_days': 'Recovery Days',
    'recovery_date': 'Recovery Date',
    'recovery_price': 'Recovery Price',
    'recovered': 'Recovered'
})

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ============================================================================
# SEZIONE 2: STATISTICHE AGGREGATE
# ============================================================================

st.divider()
st.subheader("📊 Statistiche Aggregate")

# Calcola statistiche
recovered_only = analysis_df[analysis_df['recovered'] == True]
all_recovery_days = analysis_df['recovery_days'].dropna()

col1, col2, col3, col4 = st.columns(4)

with col1:
    win_rate = (len(recovered_only) / len(analysis_df)) * 100
    st.metric("Win Rate", f"{win_rate:.1f}%", 
              help="% dividendi che hanno recuperato entro 30 giorni")

with col2:
    if not recovered_only.empty:
        avg_recovery = recovered_only['recovery_days'].mean()
        st.metric("Recovery Medio", f"{avg_recovery:.1f} giorni",
                 help="Media giorni per recovery (solo quelli recuperati)")
    else:
        st.metric("Recovery Medio", "N/A")

with col3:
    if not recovered_only.empty:
        median_recovery = recovered_only['recovery_days'].median()
        st.metric("Recovery Mediano", f"{median_recovery:.0f} giorni",
                 help="Mediana giorni per recovery (50° percentile)")
    else:
        st.metric("Recovery Mediano", "N/A")

with col4:
    if not all_recovery_days.empty:
        max_recovery = all_recovery_days.max()
        st.metric("Recovery Max", f"{max_recovery:.0f} giorni",
                 help="Massimo giorni impiegati (anche non recuperati)")
    else:
        st.metric("Recovery Max", "N/A")

# Statistiche aggiuntive
col1, col2, col3 = st.columns(3)

with col1:
    if not recovered_only.empty:
        min_recovery = recovered_only['recovery_days'].min()
        st.metric("Recovery Min", f"{min_recovery:.0f} giorni")

with col2:
    avg_div_yield = analysis_df['div_yield'].mean()
    st.metric("Dividend Yield Medio", f"{avg_div_yield:.2f}%")

with col3:
    avg_gap = analysis_df['gap_pct'].mean()
    st.metric("Gap Medio", f"{avg_gap:.2f}%")

# ============================================================================
# SEZIONE 3: DISTRIBUZIONE RECOVERY DAYS
# ============================================================================

st.divider()
st.subheader("📊 Distribuzione Recovery Days")

if not recovered_only.empty:
    # Histogram
    fig_hist = px.histogram(
        recovered_only,
        x='recovery_days',
        nbins=15,
        title="Distribuzione Giorni per Recovery",
        labels={'recovery_days': 'Recovery Days', 'count': 'Frequenza'},
        color_discrete_sequence=['#1f77b4']
    )
    fig_hist.update_layout(
        xaxis_title="Giorni",
        yaxis_title="Numero Eventi",
        showlegend=False
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Box plot
    fig_box = px.box(
        recovered_only,
        y='recovery_days',
        title="Box Plot Recovery Days",
        labels={'recovery_days': 'Giorni'},
        color_discrete_sequence=['#2ca02c']
    )
    st.plotly_chart(fig_box, use_container_width=True)
else:
    st.warning("⚠️ Nessun recovery completato per creare grafici")

# ============================================================================
# SEZIONE 4: CORRELAZIONI
# ============================================================================

st.divider()
st.subheader("🔍 Correlazioni")

if not recovered_only.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        # Recovery vs Dividend Yield
        fig_yield = px.scatter(
            recovered_only,
            x='div_yield',
            y='recovery_days',
            title="Recovery Days vs Dividend Yield",
            labels={'div_yield': 'Dividend Yield %', 'recovery_days': 'Recovery Days'},
            trendline="ols",
            color_discrete_sequence=['#ff7f0e']
        )
        st.plotly_chart(fig_yield, use_container_width=True)
    
    with col2:
        # Recovery vs Gap
        fig_gap = px.scatter(
            recovered_only,
            x='gap_pct',
            y='recovery_days',
            title="Recovery Days vs Gap %",
            labels={'gap_pct': 'Gap %', 'recovery_days': 'Recovery Days'},
            trendline="ols",
            color_discrete_sequence=['#d62728']
        )
        st.plotly_chart(fig_gap, use_container_width=True)
    
    # Correlation matrix
    corr_data = recovered_only[['div_yield', 'gap_pct', 'recovery_days']].corr()
    
    st.markdown("**Matrice di Correlazione:**")
    st.dataframe(corr_data.style.background_gradient(cmap='RdYlGn', vmin=-1, vmax=1), use_container_width=True)

# ============================================================================
# SEZIONE 5: INSIGHTS
# ============================================================================

st.divider()
st.subheader("💡 Insights")

if not recovered_only.empty:
    # Best/Worst cases
    best_idx = recovered_only['recovery_days'].idxmin()
    worst_idx = all_recovery_days.idxmax()
    
    best_event = analysis_df.loc[best_idx]
    worst_event = analysis_df.loc[worst_idx]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success(f"""
        **🏆 Recovery Più Veloce:**
        - Data: {best_event['ex_date'].strftime('%Y-%m-%d')}
        - Recovery: {best_event['recovery_days']} giorni
        - Dividend: €{best_event['dividend']:.3f} ({best_event['div_yield']:.2f}%)
        """)
    
    with col2:
        st.error(f"""
        **🐌 Recovery Più Lento:**
        - Data: {worst_event['ex_date'].strftime('%Y-%m-%d')}
        - Recovery: {worst_event['recovery_days']} giorni
        - Dividend: €{worst_event['dividend']:.3f} ({worst_event['div_yield']:.2f}%)
        - Recovered: {'✅' if worst_event['recovered'] else '❌'}
        """)

# Footer
st.divider()
st.caption("""
💡 **Come interpretare:**
- **Win Rate alto (>80%)** = Recovery molto probabile
- **Mediana bassa (<5gg)** = Recovery veloce nella maggior parte dei casi
- **Correlazione div_yield vs recovery** = Yield più alti richiedono più tempo?
""")
