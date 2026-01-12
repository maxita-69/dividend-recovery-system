# 📅 Dividend Calendar - Calendario Dividendi Futuri

## 🎯 Scopo

Strumento per **monitorare i prossimi dividendi** del tuo portfolio:
- ✅ Mostra prossime ex-dividend dates (30-90 giorni)
- ✅ Filtra per yield >= 3% (configurabile)
- ✅ Aggiorna il database automaticamente
- ✅ Output tabella chiara e leggibile

## 🚀 Utilizzo

### Comando Base

```bash
python dividend_calendar.py
```

Questo:
1. Legge tutti i 130 titoli dal database
2. Per ognuno recupera info sul prossimo dividendo da Yahoo Finance
3. Filtra per yield >= 3%
4. Mostra tabella ordinata per data
5. Salva nel database per tracking

### Output Esempio

```
================================================================================
📅 DIVIDEND CALENDAR - Prossimi Eventi
================================================================================

Ticker  Nome                           Ex-Date      In    Dividendo  Prezzo  Yield   Annual %  Status
------  -----------------------------  ----------  ----  ----------  ------  ------  --------  ------
T       AT&T Inc.                      2026-01-15  4d    $0.2775     $22.45  1.24%   4.94%     ✓
MO      Altria Group Inc.              2026-01-18  7d    $1.02       $54.23  1.88%   7.52%     ✓
ABBV    AbbVie Inc.                    2026-02-14  34d   $1.55       $175.30 0.88%   3.53%     ✓
...

📊 Totale: 47 dividendi
✓ = Announced | ⚠️ = Predicted (basato su pattern storico)
```

### Legenda Colonne

| Colonna | Descrizione |
|---------|-------------|
| **Ticker** | Symbol del titolo |
| **Nome** | Nome azienda (troncato a 30 caratteri) |
| **Ex-Date** | Data stacco dividendo (ultimo giorno per comprare e ricevere) |
| **In** | Giorni mancanti |
| **Dividendo** | Importo singolo dividendo in USD |
| **Prezzo** | Prezzo corrente del titolo |
| **Yield** | Yield del singolo dividendo (%) |
| **Annual %** | Yield annuale stimato (%) |
| **Status** | ✓ Announced (ufficiale) / ⚠️ Predicted (basato su storico) |

---

## ⚙️ Configurazione

Modifica le costanti all'inizio del file `dividend_calendar.py`:

```python
MIN_YIELD_PERCENT = 3.0   # Yield minimo per essere incluso
LOOKFORWARD_DAYS = 90     # Quanti giorni nel futuro guardare
DB_PATH = 'data/dividend_recovery.db'  # Path database
```

### Esempi Configurazione

**Solo high-yield (>= 5%)**:
```python
MIN_YIELD_PERCENT = 5.0
```

**Prossimi 30 giorni solo**:
```python
LOOKFORWARD_DAYS = 30
```

**Include anche yield bassi (>= 1%)**:
```python
MIN_YIELD_PERCENT = 1.0
```

---

## 📊 Come Funziona

### 1. **Metodo Primario** - Yahoo Finance Info

Per ogni ticker:
- Recupera `dividendRate` (annuale)
- Recupera `exDividendDate` (prossima)
- Recupera `currentPrice`
- Calcola yield singolo dividendo

**Pro**: Dati ufficiali, precisi
**Contro**: Se Yahoo non ha ex-date futura, skippa

### 2. **Metodo Alternativo** - Pattern Prediction

Se metodo primario fallisce:
- Analizza ultimi 5 dividendi storici
- Calcola intervallo medio (es. 90 giorni)
- Predice prossima ex-date: `ultima_data + intervallo_medio`
- Usa ultimo importo come stima

**Pro**: Copre anche titoli senza ex-date ufficiale
**Contro**: Basato su pattern (confidence ~70%)

---

## 🗄️ Database

I dividendi futuri vengono salvati nella tabella `dividends` con:

```sql
ex_date          - Data stacco dividendo
amount           - Importo in USD/EUR
payment_date     - Data pagamento (se disponibile)
status           - 'ANNOUNCED' o 'PREDICTED'
confidence       - 0.95 (announced) o 0.70 (predicted)
prediction_source - 'YAHOO_FINANCE'
```

### Query Manuale

```bash
sqlite3 data/dividend_recovery.db

-- Vedi prossimi dividendi
SELECT s.ticker, d.ex_date, d.amount, d.status
FROM dividends d
JOIN stocks s ON d.stock_id = s.id
WHERE d.ex_date >= date('now')
ORDER BY d.ex_date;
```

---

## 🔄 Aggiornamento Regolare

### Manuale (ogni volta che serve)

```bash
python dividend_calendar.py
```

### Automatico (cron job)

Aggiungi a crontab per aggiornamento giornaliero:

```bash
# Edit crontab
crontab -e

# Aggiungi (ogni giorno alle 7:00 AM)
0 7 * * * cd /path/to/dividend-recovery-system && python dividend_calendar.py >> logs/calendar_updates.log 2>&1
```

---

## 📚 Fonti Alternative (se Yahoo fallisce)

Se Yahoo Finance ha problemi, puoi implementare scraping da:

### Dukascopy Dividend Calendar
- URL: https://www.dukascopy.com/swiss/english/marketwatch/stocks/dividend-calendar/
- Fornisce: Ticker, Ex-Date, Amount, Payment Date

### DivvyDiary
- URL: https://divvydiary.com/calendar
- Fornisce: Calendario mensile globale, filtri per paese

### Investing.com
- URL: https://it.investing.com/dividends-calendar/
- Fornisce: Calendario Italia + USA, filtrabile per regione

### Nasdaq Dividend Calendar
- URL: https://www.nasdaq.com/market-activity/dividends
- API/Scraping per titoli USA

---

## ❓ FAQ

### Q: Perché alcuni titoli non compaiono?

**A**: Motivi possibili:
1. Yield < 3% (il filtro li esclude)
2. Prossimo dividendo oltre 90 giorni
3. Titolo non paga dividendi
4. Yahoo Finance non ha dati aggiornati

**Soluzione**: Riduci `MIN_YIELD_PERCENT` o aumenta `LOOKFORWARD_DAYS`

### Q: Cosa significa "Status: ⚠️"?

**A**: Il dividendo è **predetto** basandosi su pattern storico (ultima ex-date + intervallo medio).
Confidence ~70%. Verifica su sito ufficiale azienda prima di fare affidamento.

### Q: Come aggiungo nuovi titoli?

**A**: I titoli vengono letti automaticamente dal database `stocks`.
Per aggiungere:
1. Aggiungi ticker a `download_stock_data_v2.py`
2. Esegui `python download_stock_data_v2.py` per popolare DB
3. Esegui `python dividend_calendar.py` per vedere dividendi

### Q: Posso filtrare solo titoli USA?

**A**: Modifica lo script aggiungendo filtro market:

```python
# In build_dividend_calendar()
stocks = session.query(Stock).filter(Stock.market == 'USA').all()
```

### Q: Yahoo Finance dà errore 403/timeout

**A**:
1. Verifica connessione internet
2. Potrebbe essere rate limiting (aspetta 1-2 minuti)
3. Usa VPN se bloccato nella tua regione
4. Implementa scraping alternativo da Dukascopy/Investing.com

---

## 🛠️ Troubleshooting

### Errore: `ModuleNotFoundError: No module named 'yfinance'`

```bash
pip install yfinance pandas beautifulsoup4 lxml tabulate
```

### Errore: `ModuleNotFoundError: No module named 'multitasking'`

Workaround (crea mock module):
```bash
mkdir -p multitasking
cat > multitasking/__init__.py << 'EOF'
import threading
from functools import wraps

def task(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

def wait_for_tasks():
    for thread in threading.enumerate():
        if thread != threading.current_thread():
            thread.join()
__version__ = '0.0.12.mock'
EOF
```

### Nessun dividendo trovato

1. Verifica che database ha titoli:
   ```bash
   sqlite3 data/dividend_recovery.db "SELECT COUNT(*) FROM stocks;"
   ```

2. Se 0, popola prima:
   ```bash
   python download_stock_data_v2.py
   ```

3. Riduci filtro yield:
   ```python
   MIN_YIELD_PERCENT = 1.0  # O anche 0.0 per vedere tutti
   ```

---

## 📈 Integrazioni Future

### Dashboard Web (Streamlit)

```python
# dividend_calendar_dashboard.py
import streamlit as st
from dividend_calendar import build_dividend_calendar, get_session

st.title("📅 Dividend Calendar")
session = get_session()
calendar = build_dividend_calendar(session, min_yield=3.0)

st.dataframe(calendar)
```

### Export CSV

```python
import pandas as pd

calendar = build_dividend_calendar(session)
df = pd.DataFrame(calendar)
df.to_csv('dividend_calendar.csv', index=False)
```

### Email Alerts

```python
# Invia email con dividendi prossimi 7 giorni
upcoming = [d for d in calendar if d['days_until'] <= 7]
send_email("Dividendi questa settimana", format_html(upcoming))
```

---

## 📄 Licenza

Parte del **Dividend Recovery System**
© 2026 - Uso personale

---

**Ultima modifica**: 2026-01-11
**Versione**: 1.0
**Status**: ✅ Pronto per l'uso
