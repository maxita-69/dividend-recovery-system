"""
Dividend Calendar - Pagina Calendario Dividendi Futuri
Mostra prossimi dividendi con filtri interattivi
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Stock, Dividend, PriceData

# Page config
st.set_page_config(
    page_title="Dividend Calendar",
    page_icon="📅",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .dividend-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .high-yield {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .medium-yield {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .low-yield {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📅 Dividend Calendar")
st.markdown("### Calendario Dividendi Futuri - Prossime Ex-Dividend Dates")

# Sidebar filters
with st.sidebar:
    st.header("🔧 Filtri")

    min_yield = st.slider(
        "Yield Minimo (%)",
        min_value=0.0,
        max_value=15.0,
        value=3.0,
        step=0.5,
        help="Mostra solo dividendi con yield >= questa percentuale"
    )

    lookforward_days = st.selectbox(
        "Finestra Temporale",
        options=[7, 14, 30, 60, 90, 180],
        index=4,  # Default 90
        format_func=lambda x: f"Prossimi {x} giorni",
        help="Mostra dividendi nei prossimi N giorni"
    )

    market_filter = st.multiselect(
        "Filtra per Mercato",
        options=["Tutti", "USA", "Italy"],
        default=["Tutti"],
        help="Filtra titoli per mercato"
    )

    st.markdown("---")

    # Update button
    if st.button("🔄 Aggiorna Calendario", type="primary", use_container_width=True):
        with st.spinner("Aggiornamento calendario in corso..."):
            import subprocess
            import os

            # Get project root
            project_root = Path(__file__).parent.parent.parent

            try:
                # Run dividend_calendar.py
                result = subprocess.run(
                    [sys.executable, str(project_root / "dividend_calendar.py")],
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )

                if result.returncode == 0:
                    st.success("✅ Calendario aggiornato con successo!")
                    st.rerun()
                else:
                    st.error(f"❌ Errore durante aggiornamento:\n{result.stderr}")

            except subprocess.TimeoutExpired:
                st.error("⏱️ Timeout: operazione troppo lunga (>5 min)")
            except Exception as e:
                st.error(f"❌ Errore: {str(e)}")

    st.markdown("---")

    # Link to local script
    st.markdown("""
    ### 🖥️ Script Locale

    **Esegui da terminale**:
    ```bash
    python dividend_calendar.py
    ```

    [📖 Documentazione Completa](../../DIVIDEND_CALENDAR_README.md)
    """)

# Load data from database
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_dividend_calendar(min_yield_pct, days_forward, markets):
    """Load upcoming dividends from database"""

    db_path = Path(__file__).parent.parent.parent / 'data' / 'dividend_recovery.db'

    if not db_path.exists():
        return None

    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Date range
    today = datetime.now().date()
    end_date = today + timedelta(days=days_forward)

    # Query dividends
    query = session.query(
        Stock.ticker,
        Stock.name,
        Stock.market,
        Stock.currency,
        Dividend.ex_date,
        Dividend.amount,
        Dividend.payment_date,
        Dividend.status,
        Dividend.confidence
    ).join(
        Dividend, Stock.id == Dividend.stock_id
    ).filter(
        Dividend.ex_date >= today,
        Dividend.ex_date <= end_date
    )

    # Market filter
    if "Tutti" not in markets and markets:
        query = query.filter(Stock.market.in_(markets))

    results = query.all()

    if not results:
        session.close()
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(results, columns=[
        'ticker', 'name', 'market', 'currency', 'ex_date',
        'amount', 'payment_date', 'status', 'confidence'
    ])

    # Get current prices
    prices = {}
    for ticker in df['ticker'].unique():
        stock = session.query(Stock).filter_by(ticker=ticker).first()
        if stock:
            last_price = (
                session.query(PriceData)
                .filter_by(stock_id=stock.id)
                .order_by(PriceData.date.desc())
                .first()
            )
            if last_price:
                prices[ticker] = last_price.close

    session.close()

    # Add price and yield
    df['price'] = df['ticker'].map(prices)

    # Calculate yield (single dividend)
    df['yield_pct'] = (df['amount'] / df['price'] * 100).fillna(0)

    # Filter by yield
    df = df[df['yield_pct'] >= min_yield_pct]

    # Calculate days until
    df['days_until'] = (pd.to_datetime(df['ex_date']) - pd.Timestamp(today)).dt.days

    # Sort by ex_date
    df = df.sort_values('ex_date')

    return df

# Main content
try:
    df = load_dividend_calendar(min_yield, lookforward_days, market_filter)

    if df is None:
        st.error("❌ Database non trovato!")
        st.info("""
        ### 🚀 Setup Richiesto

        1. Popola il database:
           ```bash
           python download_stock_data_v2.py
           ```

        2. Aggiorna calendario:
           ```bash
           python dividend_calendar.py
           ```

        3. Ricarica questa pagina
        """)

    elif df.empty:
        st.warning(f"""
        ⚠️ Nessun dividendo trovato con:
        - Yield >= {min_yield}%
        - Prossimi {lookforward_days} giorni
        - Mercati: {', '.join(market_filter)}

        **Suggerimenti**:
        - Riduci il yield minimo
        - Aumenta la finestra temporale
        - Verifica che il database sia popolato
        """)

    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📊 Dividendi Trovati", len(df))

        with col2:
            avg_yield = df['yield_pct'].mean()
            st.metric("📈 Yield Medio", f"{avg_yield:.2f}%")

        with col3:
            total_amount = df['amount'].sum()
            st.metric("💰 Tot. Dividendi", f"${total_amount:.2f}")

        with col4:
            next_div_days = df['days_until'].min()
            st.metric("⏱️ Prossimo In", f"{next_div_days} giorni")

        st.markdown("---")

        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Tabella Completa", "📅 Vista Calendario", "📊 Analisi"])

        with tab1:
            # Display full table
            st.subheader("Prossimi Dividendi")

            # Format dataframe for display
            display_df = df[[
                'ticker', 'name', 'ex_date', 'days_until',
                'amount', 'price', 'yield_pct', 'status', 'market'
            ]].copy()

            display_df.columns = [
                'Ticker', 'Nome', 'Ex-Date', 'In (giorni)',
                'Dividendo ($)', 'Prezzo ($)', 'Yield %', 'Status', 'Mercato'
            ]

            # Color code by yield
            def highlight_yield(row):
                yield_val = row['Yield %']
                if yield_val >= 7:
                    return ['background-color: #f5576c; color: white'] * len(row)
                elif yield_val >= 5:
                    return ['background-color: #4facfe; color: white'] * len(row)
                elif yield_val >= 3:
                    return ['background-color: #43e97b; color: black'] * len(row)
                return [''] * len(row)

            styled_df = display_df.style.apply(highlight_yield, axis=1).format({
                'Dividendo ($)': '${:.4f}',
                'Prezzo ($)': '${:.2f}',
                'Yield %': '{:.2f}%'
            })

            st.dataframe(styled_df, use_container_width=True, height=600)

            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"dividend_calendar_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        with tab2:
            # Calendar view - group by week
            st.subheader("Vista Settimanale")

            # Group by week
            df['week'] = pd.to_datetime(df['ex_date']).dt.isocalendar().week
            df['year'] = pd.to_datetime(df['ex_date']).dt.year

            for (year, week), group in df.groupby(['year', 'week']):
                week_start = group['ex_date'].min()
                week_end = group['ex_date'].max()

                st.markdown(f"### Settimana {week} - {year}")
                st.caption(f"{week_start} → {week_end}")

                for _, row in group.iterrows():
                    # Determine yield class
                    if row['yield_pct'] >= 7:
                        yield_class = "high-yield"
                    elif row['yield_pct'] >= 5:
                        yield_class = "medium-yield"
                    else:
                        yield_class = "low-yield"

                    status_icon = "✓" if row['status'] == 'ANNOUNCED' else "⚠️"

                    st.markdown(f"""
                    <div class="dividend-card {yield_class}">
                        <h4>{status_icon} {row['ticker']} - {row['name'][:30]}</h4>
                        <p><strong>Ex-Date:</strong> {row['ex_date']} (in {row['days_until']} giorni)</p>
                        <p><strong>Dividendo:</strong> ${row['amount']:.4f} | <strong>Prezzo:</strong> ${row['price']:.2f} | <strong>Yield:</strong> {row['yield_pct']:.2f}%</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

        with tab3:
            # Analysis view
            st.subheader("Analisi Distribuzione")

            col1, col2 = st.columns(2)

            with col1:
                # Yield distribution
                st.markdown("#### Distribuzione Yield")

                yield_bins = pd.cut(df['yield_pct'], bins=[0, 3, 5, 7, 100], labels=['0-3%', '3-5%', '5-7%', '>7%'])
                yield_counts = yield_bins.value_counts().sort_index()

                st.bar_chart(yield_counts)

            with col2:
                # Market distribution
                st.markdown("#### Distribuzione per Mercato")

                market_counts = df['market'].value_counts()
                st.bar_chart(market_counts)

            # Timeline
            st.markdown("#### Timeline Dividendi")

            timeline_df = df.groupby('ex_date').size().reset_index(name='count')
            timeline_df.columns = ['Data', 'N° Dividendi']
            timeline_df = timeline_df.set_index('Data')

            st.line_chart(timeline_df)

            # Top yielders
            st.markdown("#### 🏆 Top 10 Yield")

            top10 = df.nlargest(10, 'yield_pct')[['ticker', 'name', 'yield_pct', 'ex_date', 'amount']]
            top10.columns = ['Ticker', 'Nome', 'Yield %', 'Ex-Date', 'Dividendo']

            st.dataframe(
                top10.style.format({'Yield %': '{:.2f}%', 'Dividendo': '${:.4f}'}),
                use_container_width=True
            )

except Exception as e:
    st.error(f"❌ Errore nel caricamento dati: {str(e)}")
    st.exception(e)

# Footer with documentation links
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📚 Documentazione

    - [Guida Setup Locale](../../SETUP_LOCALE.md)
    - [Dividend Calendar README](../../DIVIDEND_CALENDAR_README.md)
    """)

with col2:
    st.markdown("""
    ### 🛠️ Script Locali

    ```bash
    # Aggiorna dati
    python download_stock_data_v2.py

    # Aggiorna calendario
    python dividend_calendar.py
    ```
    """)

with col3:
    st.markdown("""
    ### 💡 Tips

    - **Yield >= 7%**: High yield (rosso)
    - **Yield 5-7%**: Medium yield (blu)
    - **Yield 3-5%**: Low yield (verde)
    - **✓**: Dividendo announced
    - **⚠️**: Dividendo predicted
    """)
