# 🚀 Setup Ambiente Locale - Windows

## 📍 Directory di Lavoro
```
C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
```

---

## ✅ Setup Iniziale (Una Volta Sola)

### 1. Prerequisiti

Verifica di avere installato:
- ✅ **Python 3.11+** → [Download](https://www.python.org/downloads/)
- ✅ **Git** → [Download](https://git-scm.com/download/win)

**Verifica installazione**:
```cmd
python --version
git --version
```

Se manca Python, installalo con "Add Python to PATH" spuntato!

---

### 2. Clona Repository (Se non l'hai già fatto)

```cmd
cd C:\Users\mvuon\Documents\GitHub
git clone https://github.com/maxita-69/dividend-recovery-system.git
cd dividend-recovery-system
```

Se hai già la cartella, aggiorna:
```cmd
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
git pull origin main
```

---

### 3. Crea Virtual Environment (Raccomandato)

```cmd
# Naviga alla directory
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system

# Crea virtual environment
python -m venv venv

# Attiva virtual environment
venv\Scripts\activate

# Dovresti vedere (venv) prima del prompt
```

**Importante**: Ogni volta che apri un nuovo terminale, riattiva:
```cmd
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
venv\Scripts\activate
```

---

### 4. Installa Dipendenze

```cmd
# Assicurati che venv sia attivo (vedi (venv) nel prompt)
pip install --upgrade pip

# Installa tutte le dipendenze
pip install -r requirements.txt

# Se errore con multitasking, ignora (è opzionale)
# Lo script funzionerà lo stesso
```

**Tempo stimato**: 3-5 minuti

---

### 5. Crea Database (Prima Volta)

```cmd
# Crea la directory data se non esiste
mkdir data

# Il database sarà creato automaticamente al primo utilizzo
# (non serve fare altro)
```

---

## 📊 CALENDARIO DIVIDENDI - Primo Utilizzo

### Step 1: Popola Database con i Tuoi Titoli

**Prima volta o per aggiungere nuovi titoli**:

```cmd
# Assicurati che venv sia attivo
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
venv\Scripts\activate

# Scarica dati storici per tutti i 130 titoli
python download_stock_data_v2.py
```

**Output**:
```
=============================================================
DIVIDEND RECOVERY SYSTEM - DATA DOWNLOAD
=============================================================
📊 Analizzando 130 titoli...

🔍 Checking existing data for BMPS.MI...
   No data found, downloading from 2020-01-01

📊 Downloading BMPS.MI...
   Period: 2020-01-01 to 2026-01-11
   ✅ Downloaded 1234 price records
   ✅ Downloaded 15 dividend records
   ✅ Saved 1234 new price records
   ✅ Saved 15 new dividend records
   ✅ All data committed to database

...
(continua per tutti i titoli)
```

**⏱️ Tempo stimato**: 4-5 ore (con throttling anti-Yahoo)

**💡 Suggerimento**: Lancialo e lascialo girare (es. durante la notte).

---

### Step 2: Lancia Calendario Dividendi

**Dopo che il database è popolato**:

```cmd
# Assicurati che venv sia attivo
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
venv\Scripts\activate

# Lancia calendario
python dividend_calendar.py
```

**Output atteso**:
```
================================================================================
📅 DIVIDEND CALENDAR - Prossimi Dividendi
================================================================================
🔍 Filtro: Yield >= 3.0%
📆 Range: Prossimi 90 giorni

📊 Analizzando 130 titoli...
   ... 10/130 processati (3 con yield >= 3.0%)
   ... 20/130 processati (7 con yield >= 3.0%)
   ...

✅ Trovati 47 dividendi con yield >= 3.0%

================================================================================
📅 CALENDARIO DIVIDENDI - Prossimi Eventi
================================================================================

Ticker  Nome                           Ex-Date      In    Dividendo  Prezzo  Yield   Annual %  Status
------  -----------------------------  ----------  ----  ----------  ------  ------  --------  ------
T       AT&T Inc.                      2026-01-15  4d    $0.2775     $22.45  1.24%   4.94%     ✓
MO      Altria Group Inc.              2026-01-18  7d    $1.02       $54.23  1.88%   7.52%     ✓
...

📊 Totale: 47 dividendi
✓ = Announced | ⚠️ = Predicted (basato su pattern storico)

💾 Salvataggio nel database...
   ✅ Salvati 47 nuovi dividendi
   ✅ Aggiornati 0 dividendi esistenti

================================================================================
✅ Aggiornamento calendario completato!
================================================================================
```

**⏱️ Tempo esecuzione**: 2-3 minuti

---

## 🌐 DASHBOARD WEB - Visualizzazione Sito

### Avvia il Sito Streamlit

```cmd
# Assicurati che venv sia attivo
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
venv\Scripts\activate

# Avvia dashboard
streamlit run dashboard/app.py
```

**Output**:
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.10:8501
```

**Apri browser**: http://localhost:8501

---

## ⚙️ Personalizzazione Calendario

### Cambia Filtro Yield

Apri `dividend_calendar.py` con un editor (es. Notepad++, VS Code):

```python
# Linea 14
MIN_YIELD_PERCENT = 3.0   # Cambia qui (es. 5.0 per solo high-yield)
```

### Cambia Finestra Temporale

```python
# Linea 15
LOOKFORWARD_DAYS = 90     # Cambia qui (es. 30 per solo prossimo mese)
```

Salva e rilancia:
```cmd
python dividend_calendar.py
```

---

## 🔄 Aggiornamento Dati (Uso Quotidiano)

### Aggiorna Prezzi e Dividendi Recenti

```cmd
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
venv\Scripts\activate

# Update incrementale (solo nuovi dati)
python download_stock_data_v2.py

# Aggiorna calendario
python dividend_calendar.py
```

**Suggerimento**: Crea un file batch per automazione.

---

## 🤖 Automazione (Opzionale)

### Crea File Batch per Update Automatico

**Crea file**: `update_dividends.bat`

```batch
@echo off
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
call venv\Scripts\activate.bat
python download_stock_data_v2.py
python dividend_calendar.py
pause
```

**Uso**: Doppio click su `update_dividends.bat`

### Schedule con Task Scheduler (Windows)

1. Apri **Task Scheduler** (Utilità di pianificazione)
2. **Crea attività di base**
3. Nome: "Update Dividend Calendar"
4. Trigger: Giornaliero alle 07:00
5. Azione: Avvia programma → `C:\Users\mvuon\Documents\GitHub\dividend-recovery-system\update_dividends.bat`
6. Fine

Ora si aggiorna automaticamente ogni giorno!

---

## 🛠️ Troubleshooting

### Errore: `python: command not found`

**Soluzione**: Python non è nel PATH.
```cmd
# Usa percorso completo
C:\Users\mvuon\AppData\Local\Programs\Python\Python311\python.exe dividend_calendar.py

# O reinstalla Python con "Add to PATH" spuntato
```

### Errore: `ModuleNotFoundError: No module named 'yfinance'`

**Soluzione**: Dipendenze non installate.
```cmd
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
venv\Scripts\activate
pip install -r requirements.txt
```

### Errore: `curl_cffi.requests.exceptions.ProxyError`

**Causa**: Firewall/proxy aziendale blocca Yahoo Finance.

**Soluzioni**:
1. **Usa VPN** (es. Proton VPN gratuito)
2. **Configura proxy**:
   ```cmd
   set HTTP_PROXY=http://proxy.azienda.it:8080
   set HTTPS_PROXY=http://proxy.azienda.it:8080
   python dividend_calendar.py
   ```
3. **Usa da casa** (fuori dalla rete aziendale)

### Database corrotto

**Soluzione**: Ricrea database.
```cmd
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
del data\dividend_recovery.db
python download_stock_data_v2.py
```

### Script lento (>10 min)

**Causa**: Yahoo Finance rate limiting.

**Soluzione**:
- Normale per 130 titoli (2-3 min è OK)
- Se >10 min, controlla connessione internet
- Prova a ridurre numero titoli in `download_stock_data_v2.py`

---

## 📂 Struttura Directory

Dopo setup completo:

```
C:\Users\mvuon\Documents\GitHub\dividend-recovery-system\
│
├── venv\                           # Virtual environment (creato da te)
├── data\                           # Database e dati
│   └── dividend_recovery.db        # Database SQLite
│
├── dashboard\                      # Sito Streamlit
│   ├── app.py                      # Entry point dashboard
│   └── pages\                      # Pagine sito
│       ├── 1_📊_Dividend_Calendar.py  # Nuova pagina calendario
│       └── ...
│
├── src\                            # Codice sorgente
│   └── database\
│       └── models.py               # Modelli database
│
├── dividend_calendar.py            # 🎯 SCRIPT CALENDARIO
├── download_stock_data_v2.py       # Script download dati
├── requirements.txt                # Dipendenze Python
├── DIVIDEND_CALENDAR_README.md     # Documentazione calendario
└── SETUP_LOCALE.md                 # 📖 Questa guida
```

---

## 🎯 Quick Reference - Comandi Principali

```cmd
# === SETUP INIZIALE (una volta) ===
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# === PRIMO DOWNLOAD DATI (4-5 ore) ===
python download_stock_data_v2.py

# === USO QUOTIDIANO ===
# 1. Attiva ambiente
venv\Scripts\activate

# 2. Aggiorna calendario (2-3 min)
python dividend_calendar.py

# 3. Avvia sito (opzionale)
streamlit run dashboard/app.py

# === UPDATE DATI (settimanale/mensile) ===
python download_stock_data_v2.py  # Solo nuovi dati
python dividend_calendar.py       # Refresh calendario
```

---

## 📞 Supporto

### Errori Comuni

| Errore | Soluzione |
|--------|-----------|
| `python not found` | Aggiungi Python al PATH o usa percorso completo |
| `No module named X` | `pip install -r requirements.txt` |
| `Database locked` | Chiudi altri script/dashboard prima |
| `403/Proxy error` | Usa VPN o connessione casa (non aziendale) |
| Calendario vuoto | Popola prima il DB: `python download_stock_data_v2.py` |

### Logs

Se serve debug:
```cmd
python dividend_calendar.py > logs\calendar.log 2>&1
type logs\calendar.log
```

---

## ✅ Checklist Setup Completo

- [ ] Python 3.11+ installato
- [ ] Virtual environment creato (`venv\`)
- [ ] Dipendenze installate (`pip install -r requirements.txt`)
- [ ] Database popolato (`python download_stock_data_v2.py`)
- [ ] Calendario testato (`python dividend_calendar.py`)
- [ ] Dashboard funzionante (`streamlit run dashboard/app.py`)
- [ ] (Opzionale) Batch file per automazione creato
- [ ] (Opzionale) Task Scheduler configurato

---

**Ultima modifica**: 2026-01-11
**Versione**: 1.0
**Target OS**: Windows 10/11
**Python version**: 3.11+
