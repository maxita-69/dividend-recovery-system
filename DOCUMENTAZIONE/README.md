# 📊 Dividend Recovery Trading System

Sistema quantitativo per analizzare e tradare il recovery post-dividend su titoli con fondamentali solidi.

**🌐 DEPLOY SU STREAMLIT CLOUD - READY TO GO!**

## 🎯 Obiettivo

Verificare empiricamente se titoli con **fondamentali forti** (validati da Dividend Aristocrats, SCHD holdings, ecc.) tendono a recuperare il prezzo dopo lo stacco dividendo in un timeframe di 5-30 giorni, permettendo strategie di trading con leverage su piattaforme come Fineco.

## 🧠 Filosofia del Progetto

**Approccio ibrido quantitativo + fondamentale:**

1. **Filtro qualitativo**: Usa analisi fondamentali di investitori long-term (Dividend Growth Investors, ETF holdings) come pre-screening
2. **Analisi quantitativa**: Applica backtesting statistico rigoroso sul pattern di recovery post-dividend
3. **Decisione data-driven**: Opera solo su titoli che passano ENTRAMBI i filtri

**Perché funziona:**
- Titoli di qualità hanno maggiore probabilità di recovery
- Inefficienza temporanea del mercato post-dividend
- Leverage amplifica guadagni su movimenti piccoli ma probabili

## 📁 Struttura Progetto

```
dividend-recovery-system/
├── src/
│   ├── database/           # Gestione SQLite DB (models)
│   └── utils/             # Utilities condivise ⭐ NEW
│       ├── recovery_analysis.py  # Logica recovery condivisa
│       ├── database.py           # Session management
│       ├── validation.py         # Data quality checks
│       └── logging_config.py     # Structured logging
├── app/
│   ├── Home.py            # Dashboard principale
│   └── pages/             # Pagine Streamlit
│       ├── 1_Single_Stock.py
│       ├── 2_Recovery_Analysis.py
│       ├── 3_Strategy_Comparison.py
│       └── 4_Pattern_Analysis.py  # ⭐ NEW Analisi predittiva
├── tests/                 # Test automatizzati ⭐ NEW (51 tests)
├── scripts/               # Script download dati
├── data/                  # Database SQLite
├── logs/                  # Application logs ⭐ NEW
├── config.py              # Configurazione centralizzata ⭐ NEW
└── IMPROVEMENTS.md        # Changelog miglioramenti ⭐ NEW
```

## 🚀 Quick Start

### Prerequisiti

- Python 3.10+
- Git

### Installazione

```bash
# 1. Clone repository
git clone https://github.com/TUO_USERNAME/dividend-recovery-system.git
cd dividend-recovery-system

# 2. Crea virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate     # Windows

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Setup database
python scripts/setup_db.py
```

### Primo Utilizzo

```bash
# Analizza JPMorgan Chase (esempio)
python src/analyzer/analyze_stock.py --ticker JPM

# Oppure lancia dashboard interattiva
streamlit run src/dashboard/app.py
```

## 🔬 Metodologia

### 1. Selezione Titoli (Filtro Qualitativo)

**Fonti per pre-screening:**
- ✅ Dividend Aristocrats (25+ anni dividend growth)
- ✅ Dividend Kings (50+ anni dividend growth)
- ✅ SCHD Holdings (Schwab US Dividend Equity ETF)
- ✅ VIG Holdings (Vanguard Dividend Appreciation ETF)
- ✅ NOBL Holdings (ProShares S&P 500 Dividend Aristocrats ETF)

**Criteri di inclusione:**
- Market cap > $10B (liquidità per leverage)
- Dividend yield 2-5% (sweet spot)
- Payout ratio < 70% (sostenibilità)
- Presenza in almeno 2 fonti

### 2. Analisi Quantitativa

**Metriche calcolate per ogni titolo:**
- Drop % nel giorno ex-dividend (teorico vs effettivo)
- Recovery days (tempo medio per tornare al prezzo pre-ex)
- Win rate (% eventi con recovery completo in 30gg)
- Expected value con leverage 3-5x
- Risk metrics (max drawdown, sharpe ratio)

**Backtesting:**
- Periodo: ultimi 5-10 anni
- Eventi minimi: 20 stacchi dividendo
- Out-of-sample validation

### 3. Decision Support

**Score 0-100 per ogni opportunità:**
- 80-100 🟢 HIGH: Alta probabilità, trade consigliato
- 60-79 🟡 MEDIUM: Possibile, valuta risk/reward
- 0-59 🔴 LOW: Skip, rischio troppo alto

## 💰 Costi di Trading (Fineco)

Il sistema include TUTTI i costi reali:
- **Commissioni**: 0.19% per operazione
- **Tobin Tax**: 0.1% (solo titoli italiani)
- **Overnight costs**: Euribor + 7.99% annualizzato
- **Tasse**: Capital gain 26% (Italia)

## ⚠️ Disclaimer

Questo è un **sistema di analisi**, NON un sistema di trading automatico.

- ✅ Fornisce scoring e raccomandazioni
- ✅ Calcola P&L attesi includendo costi
- ❌ NON esegue trade automaticamente
- ❌ NON è consulenza finanziaria

**Tutte le decisioni di trading sono responsabilità dell'utilizzatore.**

## 📊 Esempio Output

```
Ticker: JPM (JPMorgan Chase)
Ex-Dividend Date: 2026-01-15
Dividend: $1.50 (yield 1.75%)

📈 ANALISI STORICA (ultimi 20 eventi):
- Recovery medio: 8 giorni
- Win rate (30gg): 85%
- Drop medio: -1.2% vs teorico -1.75%
- Max drawdown: -2.1%

💰 SIMULAZIONE TRADE (leverage 5x, capitale €2,000):
- Entry: €85.50 (D-1 close)
- Exit atteso: €86.80 (D+8)
- P&L lordo: €76.20
- Costi totali: €22.40
- P&L netto: €53.80 (+2.69%)

🎯 SCORE: 88/100 🟢 HIGH
RACCOMANDAZIONE: TRADE
```

## 🛠️ Sviluppo

### Setup Ambiente di Sviluppo

```bash
# Installa dipendenze dev
pip install -r requirements.txt

# Run tests
pytest tests/

# Run con coverage
pytest --cov=src tests/
```

### Contribuire

1. Fork il repository
2. Crea branch feature (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri Pull Request

## 📚 Documentazione

- [Architettura Sistema](docs/ARCHITECTURE.md)
- [Strategia Trading](docs/STRATEGY.md)
- [Guida Setup](docs/SETUP.md)
- [API Reference](docs/API.md)

## 📜 License

MIT License - vedi [LICENSE](LICENSE) file

## 👤 Autore

**Max**
- Esperienza: Trading quantitativo
- Focus: Dividend capture strategies con leverage
- Piattaforma: Fineco

---

**⚠️ IMPORTANTE**: Questo progetto è per scopi educativi e di ricerca. Il trading comporta rischi significativi. Opera solo con capitale che puoi permetterti di perdere.
