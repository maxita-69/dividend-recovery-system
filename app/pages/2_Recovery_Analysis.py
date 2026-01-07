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
            'recovered': False,
            'reason': 'no_data'
        }
    
    # Cerca primo giorno con close >= target
    # enumerate parte da 0: giorno 0 = stesso giorno (D0)
    for i, (date, row) in enumerate(future_data.iterrows()):
        if row['close'] >= target_price:
            return {
                'recovery_date': date,
                'recovery_days': i,  # 0 = stesso giorno, 1 = giorno dopo, ecc.
                'recovery_price': row['close'],
                'recovered': True,
                'reason': 'recovered'
            }
    
    # Non ha recuperato entro max_days
    # Restituisci l'ultimo giorno disponibile
    last_date = future_data.index[-1]
    last_price = future_data.iloc[-1]['close']
    actual_days_checked = len(future_data) - 1  # -1 perché giorno 0 è start_date
    
    return {
        'recovery_date': last_date,
        'recovery_days': actual_days_checked,
        'recovery_price': last_price,
        'recovered': False,
        'reason': 'not_recovered' if len(future_data) == max_days else 'insufficient_data'
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
            'recovered': recovery['recovered'],
            'reason': recovery.get('reason', 'unknown')
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

# Recovered con emoji + reason
def format_recovered(row):
    if row['recovered']:
        return f"✅ ({row['recovery_days']}gg)"
    else:
        reason_map = {
            'not_recovered': f"❌ No recovery",
            'insufficient_data': f"⚠️ Dati incompleti"
        }
        return reason_map.get(row['reason'], "❌")

display_df['status'] = display_df.apply(format_recovered, axis=1)

# Seleziona e rinomina colonne
display_df = display_df[[
    'ex_date', 'dividend', 'div_yield', 
    'd_minus_1_close', 'd0_open', 'gap', 'gap_pct',
    'recovery_days', 'recovery_date', 'status'
]]

display_df = display_df.rename(columns={
    'ex_date': 'Ex-Date',
    'dividend': 'Dividendo',
    'div_yield': 'Yield %',
    'd_minus_1_close': 'D-1 Close',
    'd0_open': 'D0 Open',
    'gap': 'Gap €',
    'gap_pct': 'Gap %',
    'recovery_days': 'Recovery Days',
    'recovery_date': 'Recovery Date',
    'status': 'Status'
})

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ============================================================================
# SEZIONE 2: STATISTICHE AGGREGATE - VERSIONE CHIARA
# ============================================================================

st.divider()
st.subheader("📊 Statistiche Recovery - Cosa Significano")

# Filtra solo quelli recuperati VERAMENTE
truly_recovered = analysis_df[
    (analysis_df['recovered'] == True) & 
    (analysis_df['reason'] == 'recovered')
]

# Filtra tutti (inclusi non recuperati per dati insufficienti)
all_events = analysis_df

st.markdown("""
**Come leggere queste statistiche:**
- 🎯 **Win Rate** = Su 100 dividendi, quanti recuperano il prezzo D-1?
- ⏱️ **Recovery Medio** = In media, quanti giorni servono per recuperare?
- 📊 **Recovery Mediano** = Il valore centrale (50% più veloce, 50% più lento)
- ⚠️ **Max giorni** = Il caso peggiore storico
""")

# Row 1: Metriche principali
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_events = len(all_events)
    recovered_count = len(truly_recovered)
    win_rate = (recovered_count / total_events) * 100 if total_events > 0 else 0
    
    st.metric(
        "🎯 Win Rate",
        f"{win_rate:.0f}%",
        delta=f"{recovered_count}/{total_events} eventi",
        help="Percentuale di dividendi che hanno recuperato il prezzo D-1 entro 30 giorni"
    )
    
    if win_rate >= 80:
        st.success("Eccellente! Alta probabilità di recovery")
    elif win_rate >= 60:
        st.info("Buono, recovery probabile")
    else:
        st.warning("Attenzione, recovery incerto")

with col2:
    if not truly_recovered.empty:
        avg_days = truly_recovered['recovery_days'].mean()
        st.metric(
            "⏱️ Recovery Medio",
            f"{avg_days:.1f} giorni",
            help="Media dei giorni necessari per recuperare (solo eventi recuperati)"
        )
        
        if avg_days <= 5:
            st.success("Veloce! Recovery rapido")
        elif avg_days <= 10:
            st.info("Normale, recovery moderato")
        else:
            st.warning("Lento, serve pazienza")
    else:
        st.metric("⏱️ Recovery Medio", "N/A")
        st.error("Nessun recovery completato")

with col3:
    if not truly_recovered.empty:
        median_days = truly_recovered['recovery_days'].median()
        st.metric(
            "📊 Recovery Mediano",
            f"{median_days:.0f} giorni",
            help="Valore centrale: metà recupera più veloce, metà più lento"
        )
        
        st.caption(f"50% recupera in ≤{median_days:.0f}gg")
    else:
        st.metric("📊 Recovery Mediano", "N/A")

with col4:
    if not all_events.empty:
        max_days = all_events['recovery_days'].max()
        st.metric(
            "⚠️ Max Giorni",
            f"{max_days:.0f} giorni",
            help="Caso peggiore: massimo giorni impiegati"
        )
        
        # Identifica se è recuperato o no
        worst_case = all_events[all_events['recovery_days'] == max_days].iloc[0]
        if worst_case['recovered']:
            st.caption("✅ Anche il peggiore ha recuperato")
        else:
            st.caption("❌ Questo caso NON ha recuperato")
    else:
        st.metric("⚠️ Max Giorni", "N/A")

# Row 2: Statistiche dettagliate
st.markdown("---")
st.markdown("**📈 Distribuzione Recovery:**")

col1, col2, col3 = st.columns(3)

with col1:
    if not truly_recovered.empty:
        fast = len(truly_recovered[truly_recovered['recovery_days'] <= 3])
        pct_fast = (fast / len(truly_recovered)) * 100
        st.metric(
            "⚡ Recovery Rapido (≤3gg)",
            f"{fast} eventi ({pct_fast:.0f}%)",
            help="Quanti dividendi hanno recuperato in 3 giorni o meno"
        )

with col2:
    if not truly_recovered.empty:
        medium = len(truly_recovered[
            (truly_recovered['recovery_days'] > 3) & 
            (truly_recovered['recovery_days'] <= 7)
        ])
        pct_medium = (medium / len(truly_recovered)) * 100
        st.metric(
            "🟢 Recovery Normale (4-7gg)",
            f"{medium} eventi ({pct_medium:.0f}%)",
            help="Quanti dividendi hanno recuperato tra 4 e 7 giorni"
        )

with col3:
    if not truly_recovered.empty:
        slow = len(truly_recovered[truly_recovered['recovery_days'] > 7])
        pct_slow = (slow / len(truly_recovered)) * 100
        st.metric(
            "🔴 Recovery Lento (>7gg)",
            f"{slow} eventi ({pct_slow:.0f}%)",
            help="Quanti dividendi hanno impiegato più di 7 giorni"
        )

# Summary box
st.markdown("---")
st.info(f"""
💡 **In sintesi per {stock.ticker}:**
- Su **{total_events} dividendi** storici, **{recovered_count} hanno recuperato** ({win_rate:.0f}%)
- Tempo tipico di recovery: **{median_days:.0f} giorni** (valore mediano)
- Nella maggior parte dei casi ({pct_fast:.0f}%), recupera **entro 3 giorni**
- Caso peggiore: **{max_days:.0f} giorni** {'✅ (recuperato)' if worst_case['recovered'] else '❌ (non recuperato)'}
""")

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
