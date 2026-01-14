"""
Database Dashboard - Monitoraggio Qualità Database
Pagina per monitorare stato, qualità e consistenza del database
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from database.models import Stock, Dividend, PriceData, DataCollectionLog

# Page config
st.set_page_config(
    page_title="Database Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# AUTHENTICATION - Must be after set_page_config
# ============================================================================
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_authentication

require_authentication()

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .critical-alert {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    .warning-alert {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    .success-alert {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_database_engine():
    """Cache engine, NON la sessione"""
    db_path = Path(__file__).parent.parent.parent / "data" / "dividend_recovery.db"
    if not db_path.exists():
        st.error(f"❌ Database non trovato: {db_path}")
        st.stop()
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session():
    """Crea nuova sessione ogni volta"""
    engine = get_database_engine()
    Session = sessionmaker(bind=engine)
    return Session()


# ============================================================================
# DATA COLLECTION FUNCTIONS
# ============================================================================

def get_kpi_metrics():
    """Ottiene metriche KPI principali"""
    session = get_session()

    total_stocks = session.query(Stock).count()
    total_prices = session.query(PriceData).count()
    total_dividends = session.query(Dividend).count()

    # Ultimo aggiornamento
    latest_stock = session.query(Stock).order_by(Stock.created_at.desc()).first()
    last_added = latest_stock.created_at if latest_stock else None

    # Calcola giorni dall'ultimo aggiornamento
    if last_added:
        days_ago = (datetime.now() - last_added).days
    else:
        days_ago = None

    session.close()

    return {
        'total_stocks': total_stocks,
        'total_prices': total_prices,
        'total_dividends': total_dividends,
        'last_added': last_added,
        'days_ago': days_ago
    }


def get_market_breakdown():
    """Suddivisione titoli per mercato"""
    session = get_session()

    # Query per contare titoli per mercato
    market_counts = session.query(
        Stock.market,
        func.count(Stock.id).label('count')
    ).group_by(Stock.market).all()

    # Query per contare prezzi e dividendi per mercato
    data = []
    for market, stock_count in market_counts:
        # Conta prezzi per questo mercato
        price_count = session.query(PriceData).join(Stock).filter(
            Stock.market == market
        ).count()

        # Conta dividendi per questo mercato
        dividend_count = session.query(Dividend).join(Stock).filter(
            Stock.market == market
        ).count()

        # Calcola copertura media (% di giorni con dati negli ultimi 2 anni)
        stocks_in_market = session.query(Stock).filter(Stock.market == market).all()
        coverage_values = []
        for stock in stocks_in_market:
            prices = session.query(PriceData).filter(PriceData.stock_id == stock.id).count()
            if prices > 0:
                # Stima copertura (assumendo 250 giorni lavorativi/anno * 2 anni)
                expected_days = 500
                coverage = min(100, (prices / expected_days) * 100)
                coverage_values.append(coverage)

        avg_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else 0

        data.append({
            'market': market or 'Non specificato',
            'stocks': stock_count,
            'prices': price_count,
            'dividends': dividend_count,
            'coverage': avg_coverage
        })

    session.close()

    return pd.DataFrame(data)


def analyze_data_consistency():
    """Analizza consistenza e qualità dei dati"""
    session = get_session()

    issues = {
        'critical': [],
        'warning': [],
        'ok': []
    }

    # CRITICI
    # 1. Titoli senza prezzi
    stocks_without_prices = session.query(Stock).outerjoin(PriceData).filter(
        PriceData.id == None
    ).all()

    if stocks_without_prices:
        issues['critical'].append({
            'title': 'Titoli senza prezzi storici',
            'count': len(stocks_without_prices),
            'details': [s.ticker for s in stocks_without_prices[:10]]
        })

    # 2. Prezzi anomali (<=0)
    anomalous_prices = session.query(PriceData).filter(
        (PriceData.close <= 0) | (PriceData.open <= 0)
    ).count()

    if anomalous_prices > 0:
        issues['critical'].append({
            'title': 'Prezzi anomali (≤ 0 o negativi)',
            'count': anomalous_prices,
            'details': []
        })

    # 3. Dividendi senza ex_date
    divs_without_date = session.query(Dividend).filter(Dividend.ex_date == None).count()
    if divs_without_date > 0:
        issues['critical'].append({
            'title': 'Dividendi senza ex_date',
            'count': divs_without_date,
            'details': []
        })

    # WARNING
    # 1. Titoli con gap temporali lunghi (>30 giorni)
    stocks_with_gaps = []
    all_stocks = session.query(Stock).all()

    for stock in all_stocks:
        prices = session.query(PriceData).filter(
            PriceData.stock_id == stock.id
        ).order_by(PriceData.date).all()

        if len(prices) > 1:
            max_gap = 0
            for i in range(1, len(prices)):
                gap = (prices[i].date - prices[i-1].date).days
                if gap > max_gap:
                    max_gap = gap

            if max_gap > 30:
                stocks_with_gaps.append((stock.ticker, max_gap))

    if stocks_with_gaps:
        issues['warning'].append({
            'title': 'Titoli con gap temporali lunghi (>30 giorni)',
            'count': len(stocks_with_gaps),
            'details': [f"{t} ({g}g)" for t, g in stocks_with_gaps[:10]]
        })

    # 2. Incongruenze date dividendi
    incongruent_divs = session.query(Dividend).filter(
        Dividend.payment_date != None,
        Dividend.ex_date > Dividend.payment_date
    ).count()

    if incongruent_divs > 0:
        issues['warning'].append({
            'title': 'Dividendi con date incongruenti (ex_date > payment_date)',
            'count': incongruent_divs,
            'details': []
        })

    # OK
    stocks_with_prices = session.query(Stock).join(PriceData).distinct().count()
    stocks_with_divs = session.query(Stock).join(Dividend).distinct().count()

    issues['ok'].append({
        'title': 'Titoli con dati prezzi',
        'count': stocks_with_prices
    })

    issues['ok'].append({
        'title': 'Titoli con dividendi',
        'count': stocks_with_divs
    })

    session.close()

    return issues


def get_stock_details():
    """Dettagli per ogni singolo ticker"""
    session = get_session()

    stocks = session.query(Stock).all()

    data = []
    for stock in stocks:
        # Prezzi
        prices = session.query(PriceData).filter(PriceData.stock_id == stock.id).all()
        price_count = len(prices)

        if prices:
            first_price_date = min(p.date for p in prices)
            last_price_date = max(p.date for p in prices)

            # Calcola gap
            sorted_prices = sorted(prices, key=lambda x: x.date)
            max_gap = 0
            for i in range(1, len(sorted_prices)):
                gap = (sorted_prices[i].date - sorted_prices[i-1].date).days
                if gap > max_gap:
                    max_gap = gap

            # Anomalie
            anomalies = sum(1 for p in prices if p.close <= 0 or p.open <= 0)
        else:
            first_price_date = None
            last_price_date = None
            max_gap = 0
            anomalies = 0

        # Dividendi
        dividends = session.query(Dividend).filter(Dividend.stock_id == stock.id).all()
        dividend_count = len(dividends)

        if dividends:
            first_div_date = min(d.ex_date for d in dividends if d.ex_date)
            last_div_date = max(d.ex_date for d in dividends if d.ex_date)
            confirmed = sum(1 for d in dividends if d.status == 'CONFIRMED')
            predicted = sum(1 for d in dividends if d.status == 'PREDICTED')

            # Incongruenze
            incongruencies = sum(1 for d in dividends
                               if d.payment_date and d.ex_date and d.ex_date > d.payment_date)
        else:
            first_div_date = None
            last_div_date = None
            confirmed = 0
            predicted = 0
            incongruencies = 0

        # Status globale
        has_issues = (
            price_count == 0 or
            dividend_count == 0 or
            max_gap > 30 or
            anomalies > 0 or
            incongruencies > 0
        )

        data.append({
            'ticker': stock.ticker,
            'name': stock.name,
            'market': stock.market,
            'price_count': price_count,
            'first_price': first_price_date.strftime('%Y-%m-%d') if first_price_date else '-',
            'last_price': last_price_date.strftime('%Y-%m-%d') if last_price_date else '-',
            'max_gap': max_gap,
            'anomalies': anomalies,
            'dividend_count': dividend_count,
            'first_div': first_div_date.strftime('%Y-%m-%d') if first_div_date else '-',
            'last_div': last_div_date.strftime('%Y-%m-%d') if last_div_date else '-',
            'confirmed': confirmed,
            'predicted': predicted,
            'incongruencies': incongruencies,
            'has_issues': '🔴' if has_issues else '✅'
        })

    session.close()

    return pd.DataFrame(data)


def get_recent_logs():
    """Ottiene ultimi log di attività"""
    session = get_session()

    logs = session.query(DataCollectionLog).order_by(
        DataCollectionLog.timestamp.desc()
    ).limit(20).all()

    data = []
    for log in logs:
        data.append({
            'Timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Ticker': log.stock_ticker or '-',
            'Source': log.source,
            'Operation': log.operation,
            'Status': log.status,
            'Records': log.records_processed,
            'Message': (log.message[:60] + '...') if log.message and len(log.message) > 60 else (log.message or '')
        })

    session.close()

    return pd.DataFrame(data)


# ============================================================================
# MAIN PAGE
# ============================================================================

st.title("📊 Database Dashboard")
st.markdown("Monitoraggio qualità e consistenza del database")

# ============================================================================
# 1. KPI METRICS
# ============================================================================

st.header("📈 Metriche Principali")

kpi = get_kpi_metrics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Totale Titoli", f"{kpi['total_stocks']}")

with col2:
    if kpi['days_ago'] is not None:
        delta_text = f"-{kpi['days_ago']} giorni" if kpi['days_ago'] > 0 else "Oggi"
        st.metric("Ultimo Aggiornato", delta_text)
    else:
        st.metric("Ultimo Aggiornato", "N/A")

with col3:
    st.metric("Record Prezzi", f"{kpi['total_prices']:,}")

with col4:
    st.metric("Dividendi Totali", f"{kpi['total_dividends']:,}")

st.markdown("---")

# ============================================================================
# 2. MARKET BREAKDOWN
# ============================================================================

st.header("🌍 Suddivisione per Mercato")

market_df = get_market_breakdown()

if not market_df.empty:
    col1, col2 = st.columns([1, 2])

    with col1:
        # Grafico a torta
        fig_pie = px.pie(
            market_df,
            values='stocks',
            names='market',
            title='Distribuzione Titoli per Mercato'
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Tabella dettagliata
        st.dataframe(
            market_df.rename(columns={
                'market': 'Mercato',
                'stocks': 'Titoli',
                'prices': 'Prezzi',
                'dividends': 'Dividendi',
                'coverage': 'Copertura %'
            }).style.format({
                'Copertura %': '{:.1f}%'
            }),
            use_container_width=True,
            hide_index=True
        )

# Nota su classificazione USA
if any('USA' in str(m).upper() or 'US' in str(m).upper() for m in market_df['market'].values):
    st.info("""
    ℹ️ **Nota sui mercati USA**: La classificazione per indici (NASDAQ, Dow Jones, S&P 500)
    richiede classificazione manuale o tramite API esterne. Attualmente i titoli USA sono
    raggruppati genericamente come "USA".
    """)

st.markdown("---")

# ============================================================================
# 3. DATA CONSISTENCY ANALYSIS
# ============================================================================

st.header("⚠️ Analisi Consistenza Dati")

issues = analyze_data_consistency()

# CRITICAL
if issues['critical']:
    st.markdown('<div class="critical-alert">', unsafe_allow_html=True)
    st.markdown("### 🔴 CRITICI")
    for issue in issues['critical']:
        st.markdown(f"**{issue['title']}**: {issue['count']}")
        if issue['details']:
            with st.expander("Dettagli"):
                st.write(", ".join(issue['details']))
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="success-alert">', unsafe_allow_html=True)
    st.markdown("### ✅ Nessun problema critico rilevato")
    st.markdown('</div>', unsafe_allow_html=True)

# WARNING
if issues['warning']:
    st.markdown('<div class="warning-alert">', unsafe_allow_html=True)
    st.markdown("### 🟡 WARNING")
    for issue in issues['warning']:
        st.markdown(f"**{issue['title']}**: {issue['count']}")
        if issue['details']:
            with st.expander("Dettagli"):
                st.write(", ".join(issue['details']))
    st.markdown('</div>', unsafe_allow_html=True)

# OK
if issues['ok']:
    st.markdown('<div class="success-alert">', unsafe_allow_html=True)
    st.markdown("### ✅ OK")
    for issue in issues['ok']:
        st.markdown(f"**{issue['title']}**: {issue['count']}")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# 4. STOCK DETAILS TABLE
# ============================================================================

st.header("📋 Dettagli per Ticker")

stock_details = get_stock_details()

if not stock_details.empty:
    # Filtri
    col1, col2 = st.columns(2)

    with col1:
        filter_market = st.multiselect(
            "Filtra per mercato:",
            options=stock_details['market'].unique(),
            default=stock_details['market'].unique()
        )

    with col2:
        show_only_issues = st.checkbox("Mostra solo titoli con problemi", value=False)

    # Applica filtri
    filtered_df = stock_details[stock_details['market'].isin(filter_market)]
    if show_only_issues:
        filtered_df = filtered_df[filtered_df['has_issues'] == '🔴']

    # Mostra tabella
    st.dataframe(
        filtered_df.rename(columns={
            'has_issues': 'Status',
            'ticker': 'Ticker',
            'name': 'Nome',
            'market': 'Mercato',
            'price_count': 'N° Prezzi',
            'first_price': 'Primo Prezzo',
            'last_price': 'Ultimo Prezzo',
            'max_gap': 'Gap Max (gg)',
            'anomalies': 'Anomalie',
            'dividend_count': 'N° Dividendi',
            'first_div': 'Primo Div.',
            'last_div': 'Ultimo Div.',
            'confirmed': 'Confermati',
            'predicted': 'Predetti',
            'incongruencies': 'Incongruenze'
        }),
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Statistiche riepilogo
    col1, col2, col3 = st.columns(3)

    with col1:
        ok_count = len(filtered_df[filtered_df['has_issues'] == '✅'])
        st.metric("Titoli OK", ok_count)

    with col2:
        issue_count = len(filtered_df[filtered_df['has_issues'] == '🔴'])
        st.metric("Titoli con Problemi", issue_count)

    with col3:
        if len(filtered_df) > 0:
            pct_ok = (ok_count / len(filtered_df)) * 100
            st.metric("% Qualità", f"{pct_ok:.1f}%")

st.markdown("---")

# ============================================================================
# 5. RECENT ACTIVITY LOGS
# ============================================================================

st.header("📥 Ultimi Log Attività")

logs_df = get_recent_logs()

if not logs_df.empty:
    st.dataframe(
        logs_df,
        use_container_width=True,
        hide_index=True,
        height=300
    )
else:
    st.info("Nessun log disponibile")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("Database Dashboard - Aggiornato in tempo reale")
