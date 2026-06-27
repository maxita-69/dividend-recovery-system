# 📍 STATO PROGETTO — 2026-06-27 17:32

> Generato automaticamente da `genera_stato.sh`.
> Le sezioni sotto sono LETTE DAL SISTEMA REALE: non modificarle a mano.
> Per cambiare obiettivo / prossimo passo, modifica `INTENTO.md` e rilancia lo script.

## 🎯 Intento corrente (da INTENTO.md)

**Ultima cosa fatta:** servizi API+Streamlit resi persistenti (systemd user), bind corretto a 127.0.0.1, esposizione pubblica esclusa (curl da casa = timeout). Angular in frontend/ confermato VIVO.
**Prossimo passo:** lavorare sull'Angular (frontend/) — verificare proxy.conf.json punti a :8001, poi npm start e accesso via tunnel SSH con -L 4200:localhost:4200
**Domande aperte:** abilitare loginctl enable-linger per avvio al boot? ; API senza auth (ok solo finché localhost) ; accesso remoto = SEMPRE tunnel SSH, MAI esposizione pubblica

## 🌿 Git
```
Branch attivo: main

Ultimi commit:
0320f50 stato: INTENTO.md ripulito (5 righe)
7baad4b stato: pulizia repo completata, API verde
413d476 chore: rimossa dashboard Streamlit morta e downloader duplicati
fbd1509 stato: fetta API verificata e pushata
2f677e2 chore: ignora verifica_api.sh
8024274 feat: scaffolding FastAPI fetta verticale - health + stocks su DB SQLite reale porta 8001
e9bf647 stato: piano API sospeso, prima Fase B
ce9113b Aggiunto sistema di stato/handoff automatico

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
./api
./api/routers
./api/services
./app
./app/pages
./data
./dividendi
./frontend
./frontend/.angular
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
./tests/test_api
```

## 🐍 File Python piu' grossi
```
   278 ./tests/test_recovery_analysis.py
   283 ./src/utils/recovery_analysis.py
   293 ./test_finnhub.py
   299 ./src/database/download_stock_data_hybrid.py
   309 ./config.py
   341 ./tests/test_pattern_analysis.py
   359 ./src/database/download_data_ib.py
   524 ./src/utils/pattern_analysis.py
   540 ./app/pages/1_Single_Stock.py
   601 ./app/pages/7_Database_Dashboard.py
   642 ./app/pages/3_Strategy_Comparison.py
   652 ./app/pages/2_Recovery_Analysis.py
   780 ./app/pages/4_Pattern_Analysis.py
   849 ./app/pages/5_Master_Dashboard.py
 12881 total
```
