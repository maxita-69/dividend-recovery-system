# 🔧 IB Gateway Setup Guide

## Problema Risolto

**Errore originale**: `ModuleNotFoundError: No module named 'ibapi'`

**Causa**: La libreria `ibapi` nativa di Interactive Brokers aveva problemi di installazione dovuti a incompatibilità con la versione di Python/setuptools.

**Soluzione**: Implementato **ib-insync**, un wrapper moderno e più affidabile per l'API di Interactive Brokers.

---

## ✅ Cosa è stato fatto

### 1. **Installata libreria ib-insync**
```bash
pip install ib-insync
```

### 2. **Creati nuovi script (versione 2.0)**

#### `test_ib_connection_v2.py`
- Test di connessione a IB Gateway
- Messaggi di errore dettagliati e troubleshooting
- Supporto per multiple porte (paper/live trading)

#### `get_dividends_ibkr_v2.py`
- Download dati dividendi da IBKR
- Parsing dati fondamentali
- Gestione errori robusta

### 3. **Aggiornato requirements.txt**
```txt
# Interactive Brokers API
ib-insync>=0.9.86
```

---

## 🚀 Come Usare IB Gateway

### Prerequisiti

1. **Account Interactive Brokers** (anche paper trading gratuito)
2. **IB Gateway installato** o **TWS (Trader Workstation)**

### Download IB Gateway

1. Vai su: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
2. Scarica la versione per il tuo sistema operativo
3. Installa seguendo le istruzioni

### Configurazione IB Gateway

1. **Avvia IB Gateway**
   - Per paper trading: usa le credenziali del tuo account paper
   - Per live trading: usa le credenziali del tuo account reale

2. **Configura API Settings**
   - Vai su: **Configure → Settings → API → Settings**
   - ✅ Abilita "**Enable ActiveX and Socket Clients**"
   - ✅ Aggiungi `127.0.0.1` alla lista "**Trusted IP addresses**"
   - ✅ Verifica la porta:
     - **4002**: IB Gateway paper trading (default)
     - **7497**: TWS paper trading
     - **4001**: IB Gateway live trading
     - **7496**: TWS live trading

3. **Configura Auto-Restart (opzionale)**
   - Abilita "**Auto restart**" per riconnessione automatica

---

## 🧪 Test della Connessione

### 1. Test Base
```bash
cd /home/user/dividend-recovery-system
python test_ib_connection_v2.py
```

**Output atteso (successo)**:
```
🔌 Connessione a IB Gateway in corso...
✅ Connessione a IB Gateway riuscita!
   Server version: 176
   Accounts: ['DU123456']
✅ Test completato con successo!
```

**Output atteso (IB Gateway non in esecuzione)**:
```
❌ Errore di connessione: Connect call failed
🔍 Possibili cause:
   1. IB Gateway non è in esecuzione
   ...
```

### 2. Test Download Dividendi
```bash
python get_dividends_ibkr_v2.py
```

Questo scaricherà dati per AAPL, MSFT, JNJ come test.

---

## 📊 Script Disponibili

### Nuovi Script (v2.0 - ib-insync)

| Script | Descrizione | Stato |
|--------|-------------|-------|
| `test_ib_connection_v2.py` | Test connessione IB Gateway | ✅ Pronto |
| `get_dividends_ibkr_v2.py` | Download dividendi da IBKR | ✅ Pronto |

### Vecchi Script (v1.0 - ibapi nativo)

| Script | Descrizione | Stato |
|--------|-------------|-------|
| `test_ib_connection.py` | Test connessione (vecchio) | ⚠️ Non funziona (manca ibapi) |
| `get_dividends_ibkr.py` | Download dividendi (vecchio) | ⚠️ Non funziona (manca ibapi) |
| `ibkr_dividend_downloader.py` | Downloader (vecchio) | ⚠️ Non funziona (manca ibapi) |
| `update_dividends_ibkr.py` | Update dividendi (vecchio) | ⚠️ Non funziona (manca ibapi) |

**Nota**: Gli script vecchi possono essere aggiornati a ib-insync se necessario.

---

## 🔄 Migrazione da ibapi a ib-insync

### Differenze principali

**Vecchio codice (ibapi)**:
```python
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId):
        print("Connesso!")

app = IBApp()
app.connect("127.0.0.1", 4002, clientId=1)
app.run()
```

**Nuovo codice (ib-insync)**:
```python
from ib_insync import IB, Stock

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)
print(f"Connesso! Accounts: {ib.managedAccounts()}")
ib.disconnect()
```

### Vantaggi di ib-insync

✅ **Installazione semplice**: Nessun problema di compilazione
✅ **API moderna**: Sintassi Pythonic e intuitiva
✅ **Async support**: Supporto nativo per asyncio
✅ **Error handling**: Gestione errori migliorata
✅ **Documentazione**: Documentazione completa e esempi
✅ **Manutenzione attiva**: Progetto attivamente mantenuto

---

## 🐛 Troubleshooting

### Errore: "Connect call failed"

**Causa**: IB Gateway non è in esecuzione o non accetta connessioni.

**Soluzione**:
1. Verifica che IB Gateway sia avviato
2. Controlla che la porta sia corretta (4002 per paper trading)
3. Verifica configurazione API in IB Gateway

### Errore: "Connection refused"

**Causa**: Porta sbagliata o firewall.

**Soluzione**:
1. Prova porte diverse:
   ```python
   ib.connect('127.0.0.1', 7497, clientId=1)  # TWS paper
   ib.connect('127.0.0.1', 4001, clientId=1)  # Gateway live
   ```
2. Verifica firewall:
   ```bash
   sudo ufw allow 4002/tcp
   ```

### Errore: "Already connected"

**Causa**: Client ID già in uso.

**Soluzione**: Cambia il `clientId`:
```python
ib.connect('127.0.0.1', 4002, clientId=2)  # Usa ID diverso
```

### Errore: "Market data not subscribed"

**Causa**: Account non ha sottoscrizione per dati di mercato.

**Soluzione**:
- Per paper trading: attiva "Market Data" nelle impostazioni account
- Per dati fondamentali: non serve sottoscrizione

---

## 📚 Risorse

### Documentazione Ufficiale

- **ib-insync**: https://ib-insync.readthedocs.io/
- **IB API**: https://interactivebrokers.github.io/tws-api/
- **IB Gateway**: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php

### Tutorial

- [ib-insync Quick Start](https://ib-insync.readthedocs.io/quickstart.html)
- [IB API Configuration](https://ibkrguides.com/kb/api-configuration.htm)

---

## 🎯 Next Steps

### Immediato (Oggi)

1. ✅ Problema IB Gateway risolto
2. ✅ Scripts v2.0 creati con ib-insync
3. ✅ Requirements.txt aggiornato

### Prossimi Passi (Se necessario)

1. **Avviare IB Gateway** (quando necessario per live data)
2. **Testare connessione** con `test_ib_connection_v2.py`
3. **Migrare vecchi script** a ib-insync (se servono)
4. **Implementare download automatico** dividendi da IBKR

---

## ⚠️ Note Importanti

### Per Backtesting (SAL 5)

**Non serve IB Gateway!**

Per il backtesting (SAL 5 - priorità massima) useremo **Yahoo Finance**, non IBKR:
- Dati storici gratuiti
- Nessuna connessione API necessaria
- Script già pronto: `download_stock_data_v2.py`

### Quando Serve IB Gateway?

IB Gateway servirà solo per:
- **Live data** (dati real-time)
- **Trading automatico** (se GO decision dopo SAL 5)
- **Dati fondamentali avanzati** (se necessario)

Per ora: **focus su SAL 5 con Yahoo Finance!**

---

**Ultima modifica**: 2026-01-11
**Status**: ✅ IB Gateway issue risolto con ib-insync
