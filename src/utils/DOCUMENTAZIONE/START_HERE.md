# 🚀 START HERE - Guida Rapida

## 📍 Sei Qui
```
C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
```

---

## ✅ Setup Completo in 5 Passi

### 1️⃣ Verifica Python

Apri **CMD** o **PowerShell** e digita:

```cmd
python --version
```

**Risultato atteso**: `Python 3.11.x` o superiore

❌ Se non funziona → [Installa Python](https://www.python.org/downloads/) (spunta "Add to PATH")

---

### 2️⃣ Crea Virtual Environment

```cmd
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
python -m venv venv
venv\Scripts\activate
```

Dovresti vedere `(venv)` prima del prompt.

---

### 3️⃣ Installa Dipendenze

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

⏱️ Tempo: ~3-5 minuti

---

### 4️⃣ Popola Database (Prima Volta)

**Opzione A - Batch File (Consigliato)**:
```
Doppio click su: update_dividends.bat
```

**Opzione B - Manuale**:
```cmd
python download_stock_data_v2.py
python dividend_calendar.py
```

⏱️ Tempo: ~4-5 ore (lascia girare)

---

### 5️⃣ Avvia Dashboard

**Opzione A - Batch File (Consigliato)**:
```
Doppio click su: start_dashboard.bat
```

**Opzione B - Manuale**:
```cmd
streamlit run dashboard/app.py
```

🌐 Apri browser: **http://localhost:8501**

---

## 🎯 Uso Quotidiano

### Aggiorna Calendario (2-3 min)

```
Doppio click su: update_dividends.bat
```

Oppure:
```cmd
venv\Scripts\activate
python dividend_calendar.py
```

### Visualizza Dashboard

```
Doppio click su: start_dashboard.bat
```

Oppure:
```cmd
venv\Scripts\activate
streamlit run dashboard/app.py
```

---

## 📊 Cosa Troverai

### Nel Dashboard (http://localhost:8501)

1. **Home Page**
   - Statistiche sistema (titoli, dividendi, prezzi)
   - Link a documentazione

2. **📅 Dividend Calendar** ⭐
   - Prossimi dividendi (yield >= 3%)
   - Filtri interattivi (yield, timeframe, mercato)
   - 3 viste: Tabella, Calendario, Analisi
   - Export CSV
   - Aggiornamento con un click

### Da Terminale

```cmd
# Calendario testuale
python dividend_calendar.py

# Output esempio:
# Ticker  Nome                Ex-Date      In   Dividendo  Prezzo  Yield
# T       AT&T Inc.           2026-01-15   4d   $0.28      $22.45  1.24%
# MO      Altria Group        2026-01-18   7d   $1.02      $54.23  1.88%
# ...
```

---

## 🔧 Personalizzazione

### Cambia Yield Minimo

Apri `dividend_calendar.py` (linea 14):
```python
MIN_YIELD_PERCENT = 3.0  # Cambia a 5.0 per solo high-yield
```

### Cambia Timeframe

Apri `dividend_calendar.py` (linea 15):
```python
LOOKFORWARD_DAYS = 90  # Cambia a 30 per solo prossimo mese
```

---

## 📚 Documentazione Completa

| File | Contenuto |
|------|-----------|
| **SETUP_LOCALE.md** | Setup completo Windows + troubleshooting |
| **DIVIDEND_CALENDAR_README.md** | Guida calendario + configurazione avanzata |
| **IB_GATEWAY_SETUP.md** | Setup IB Gateway (per futuro live trading) |

---

## 🆘 Problemi Comuni

### `python: command not found`

**Fix**: Aggiungi Python al PATH o usa:
```cmd
C:\Users\mvuon\AppData\Local\Programs\Python\Python311\python.exe
```

### `ModuleNotFoundError`

**Fix**:
```cmd
venv\Scripts\activate
pip install -r requirements.txt
```

### Dashboard vuota

**Fix**: Popola prima il database:
```cmd
python download_stock_data_v2.py
```

### Errore 403 Yahoo Finance

**Fix**:
- Usa VPN
- Connettiti da casa (non rete aziendale)
- Riprova tra 5-10 minuti (rate limiting)

---

## 🎊 Check Finale

- [x] Python installato
- [x] Virtual environment creato
- [x] Dipendenze installate
- [x] Database popolato (4-5 ore)
- [x] Calendario testato (`python dividend_calendar.py`)
- [x] Dashboard funzionante (http://localhost:8501)

**Tutto OK?** Sei pronto! 🚀

---

## 📞 Quick Commands

```cmd
# Attiva ambiente
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
venv\Scripts\activate

# Update dati + calendario
python download_stock_data_v2.py && python dividend_calendar.py

# Dashboard
streamlit run dashboard/app.py

# O usa i batch files:
# - update_dividends.bat  (doppio click)
# - start_dashboard.bat   (doppio click)
```

---

**Versione**: 1.0
**Data**: 2026-01-11
**Status**: ✅ Pronto per l'uso

**Problemi?** Leggi **SETUP_LOCALE.md** (troubleshooting completo)
