# 📍 STATO PROGETTO — 2026-06-27 16:10

> Generato automaticamente da `genera_stato.sh`.
> Le sezioni sotto sono LETTE DAL SISTEMA REALE: non modificarle a mano.
> Per cambiare obiettivo / prossimo passo, modifica `INTENTO.md` e rilancia lo script.

## 🎯 Intento corrente (da INTENTO.md)

**Fase:** B — Punto della situazione sul codice
**Ultima cosa fatta:** messo in sicurezza il VPS (Fase A completata: SSH, firewall, code-server non-root, key EODHD ruotata)
**Prossimo passo:** analizzare il repo trading con Claude Code in SOLA LETTURA (vedi §15 del manuale)
**Domande aperte:** FMP API key forse leakata (da verificare); auth FastAPI ancora mancante
**Assistente ultima sessione:** Claude (chat)
**Prossimo passo:** Fase B in sola lettura — quale dashboard è viva (app/ vs dashboard/), quale DB reale, core src/ riusabile?
**Domande aperte:** piano API FastAPI di Kimi pronto ma SOSPESO fino a fine Fase B; alla ripresa correggere porta (≠8000, occupata da trading-brain), confermare dashboard e DB

## 🌿 Git
```
Branch attivo: main

Ultimi commit:
ce9113b Aggiunto sistema di stato/handoff automatico
06836d3 docs: aggiunto CONTINUITA.md per sessioni future
3f18727 fix: rimosso import rotto .database da src/utils, corretto pattern_analysis
68836ce docs: aggiunto STATO_CODICE.md con analisi del 20260627
6d4b3ea security: rimossa key EODHD leakata, pulizia repo, aggiornato .gitignore
3983e61 Aggiornamento del progetto al 27 Giugno
a5ff231 docs: flatten to root DOCUMENTAZIONE.md
77d345e docs: unifica 14 file in DOCUMENTAZIONE.md unico

Modifiche NON committate:
 M INTENTO.md
 M STATO.md
```

## ⚙️ Servizi systemd
```
trading-brain    active
code-server      active
nginx            active
tailscaled       active
fail2ban         active
```

## 🐳 Docker (container attivi)
```
NAMES      STATUS      PORTS
postgres   Up 4 days   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
n8n        Up 4 days   0.0.0.0:5678->5678/tcp, [::]:5678->5678/tcp
```

## 📂 Struttura cartelle (max 2 livelli)
```
.
./.claude
./.pytest_cache
./.pytest_cache/v
./.streamlit
./app
./app/pages
./dashboard
./dashboard/pages
./data
./dividendi
./frontend
./frontend/src
./logs
./providers
./script
./scripts
./src
./src/data_providers
./src/database
./src/utils
./tests
```

## 🐍 File Python piu' grossi
```
   299 ./src/database/download_stock_data_hybrid.py
   309 ./config.py
   341 ./tests/test_pattern_analysis.py
   359 ./src/database/download_data_ib.py
   362 ./src/database/download_stock_data_fmp.py
   409 ./src/database/download_stock_data_v2.py
   430 ./dashboard/pages/1_📅_Dividend_Calendar.py
   519 ./src/utils/pattern_analysis.py
   540 ./app/pages/1_Single_Stock.py
   601 ./app/pages/7_Database_Dashboard.py
   642 ./app/pages/3_Strategy_Comparison.py
   652 ./app/pages/2_Recovery_Analysis.py
   780 ./app/pages/4_Pattern_Analysis.py
   849 ./app/pages/5_Master_Dashboard.py
 14264 total
```
