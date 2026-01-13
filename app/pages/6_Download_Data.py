"""
Data Download Page - Scarica dati storici da FMP Provider
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.download_stock_data_hybrid import download_tickers, create_database


# Page config
st.set_page_config(page_title="Download Data", page_icon="📥", layout="wide")

st.title("📥 Download Stock Data")
st.markdown("Scarica dati storici usando **provider ibridi** (FMP per USA, Yahoo per Italia).")

# ---------------------------------------------------------
# SIDEBAR - CONFIGURAZIONE
# ---------------------------------------------------------

st.sidebar.header("⚙️ Configurazione")

# Lista ticker predefinita
ALL_TICKERS = [
    # TITOLI ITALIANI
    "ENEL.MI", "ENI.MI", "ISP.MI", "UCG.MI", "G.MI",
    "TRN.MI", "SRG.MI", "TEN.MI", "NEXI.MI", "STM.MI",
    "BMPS.MI", "MB.MI", "BAMI.MI", "INW.MI", "BPSO.MI",
    "SPM.MI", "BPE.MI", "PST.MI", "BMED.MI", "UNI.MI",
    "AZM.MI", "A2A.MI", "IG.MI", "HER.MI", "FBK.MI",
    "REC.MI", "STLAM.MI", "MONC.MI", "IVG.MI", "AMP.MI",
    "TIT.MI", "LTMC.MI", "DIA.MI", "BZU.MI", "CPR.MI",
    "BC.MI", "PRY.MI", "RACE.MI", "LDO.MI", "IP.MI",

    # TITOLI USA
    "AAPL", "MSFT", "JNJ", "PG", "KO", "PEP", "MCD",
    "XOM", "CVX", "T", "VZ", "JPM", "BAC",
    "WMT", "HD", "UPS", "LMT", "IBM", "CSCO"
]

# Opzione selezione ticker
selection_mode = st.sidebar.radio(
    "Modalità selezione ticker:",
    ["📋 Tutti i ticker", "✏️ Custom list", "🇮🇹 Solo Italia", "🇺🇸 Solo USA"]
)

if selection_mode == "📋 Tutti i ticker":
    selected_tickers = ALL_TICKERS
elif selection_mode == "🇮🇹 Solo Italia":
    selected_tickers = [t for t in ALL_TICKERS if t.endswith('.MI')]
elif selection_mode == "🇺🇸 Solo USA":
    selected_tickers = [t for t in ALL_TICKERS if not t.endswith('.MI')]
else:  # Custom
    custom_input = st.sidebar.text_area(
        "Inserisci ticker (uno per riga):",
        value="AAPL\nMSFT\nENEL.MI",
        height=150
    )
    selected_tickers = [t.strip() for t in custom_input.split('\n') if t.strip()]

st.sidebar.markdown(f"**Ticker selezionati**: {len(selected_tickers)}")

# ---------------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------------

# Info Providers
st.info("""
ℹ️ **Configurazione Provider**:
- 🇺🇸 **Titoli USA** (AAPL, MSFT, ecc.) → **FMP** (250 chiamate/giorno)
- 🇮🇹 **Titoli Italiani** (.MI) → **Yahoo Finance** (gratuito, illimitato)
- Download incrementale: scarica solo dati mancanti
- Ticker già aggiornati vengono skippati automaticamente
""")

# Database status
try:
    session = create_database()
    from src.database.models import Stock, PriceData, Dividend

    n_stocks = session.query(Stock).count()
    n_prices = session.query(PriceData).count()
    n_dividends = session.query(Dividend).count()
    session.close()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Stocks in DB", n_stocks)
    with col2:
        st.metric("📈 Price Records", f"{n_prices:,}")
    with col3:
        st.metric("💰 Dividend Records", f"{n_dividends:,}")

except Exception as e:
    st.error(f"❌ Errore connessione database: {e}")

st.markdown("---")

# ---------------------------------------------------------
# DOWNLOAD SECTION
# ---------------------------------------------------------

st.subheader("🚀 Avvia Download")

col_btn, col_info = st.columns([1, 3])

with col_btn:
    start_download = st.button(
        "▶️ Start Download",
        type="primary",
        disabled=len(selected_tickers) == 0
    )

with col_info:
    if len(selected_tickers) > 0:
        st.info(f"Pronto per scaricare **{len(selected_tickers)} ticker**")
    else:
        st.warning("Nessun ticker selezionato")

# ---------------------------------------------------------
# EXECUTE DOWNLOAD
# ---------------------------------------------------------

if start_download:
    st.markdown("---")
    st.subheader("📥 Download in corso...")

    # Progress containers
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()

    # Statistiche
    stats = {'success': 0, 'errors': 0, 'skipped': 0}

    def progress_callback(ticker, idx, total, status, message):
        """Callback per aggiornare UI durante download"""
        progress = idx / total
        progress_bar.progress(progress)

        status_icons = {
            'checking': '🔍',
            'downloading': '⬇️',
            'success': '✅',
            'error': '❌',
            'skipped': '⏭️'
        }

        icon = status_icons.get(status, '📊')
        status_text.text(f"{icon} [{idx}/{total}] {message}")

        # Log nel container
        if status == 'success':
            log_container.success(f"✅ {ticker}: Download completato")
        elif status == 'error':
            log_container.error(f"❌ {ticker}: {message}")
        elif status == 'skipped':
            log_container.info(f"⏭️ {ticker}: {message}")

    try:
        # Esegui download
        session = create_database()
        stats = download_tickers(
            selected_tickers,
            session=session,
            progress_callback=progress_callback
        )
        session.close()

        # Completion message
        progress_bar.progress(1.0)
        status_text.empty()

        st.balloons()
        st.success("🎉 Download completato!")

        # Final stats
        st.markdown("### 📊 Risultati Download")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Successi", stats['success'])
        with col2:
            st.metric("❌ Errori", stats['errors'])
        with col3:
            st.metric("⏭️ Skipped", stats['skipped'])

        # Updated DB stats
        session = create_database()
        n_stocks = session.query(Stock).count()
        n_prices = session.query(PriceData).count()
        n_dividends = session.query(Dividend).count()
        session.close()

        st.markdown("### 💾 Database Status Aggiornato")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Stocks", n_stocks)
        with col2:
            st.metric("Price Records", f"{n_prices:,}")
        with col3:
            st.metric("Dividends", f"{n_dividends:,}")

    except Exception as e:
        st.error(f"❌ Errore durante download: {e}")
        import traceback
        st.code(traceback.format_exc())

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <strong>Hybrid Providers</strong> |
    🇺🇸 FMP (250 calls/day) + 🇮🇹 Yahoo Finance (unlimited) |
    <a href="https://site.financialmodelingprep.com/developer/docs" target="_blank">FMP Docs</a> |
    <a href="https://pypi.org/project/yfinance/" target="_blank">yfinance Docs</a>
</div>
""", unsafe_allow_html=True)
