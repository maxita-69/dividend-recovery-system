Dividend Recovery System — Documentazione Unica
Stato: Working — Architettura context-broker in costruzione Ultimo aggiornamento: 14 Giugno 2026 Versione documento: 1.0 (merge unificato di 14 file originali)

1. Visione & Filosofia
1.1 Cosa stiamo costruendo
Sistema quantitativo per analizzare e tradare strategie di Dividend Recovery su titoli italiani e americani con fondamentali forti.

Strategia core:

Buy: D-1 o D0 (prima/giorno dello stacco dividendo)
Sell: Quando il prezzo recupera completamente (entro 5-30 giorni)
Leverage: Fineco (3-5x)
Target universe: Dividend Aristocrats, SCHD holdings, payout ratio < 70%
1.2 Filosofia (le 5 regole non negoziabili)
1.
Non si automatizza un sistema che perde soldi — prima validare, poi automatizzare.
2.
SAL 5 (Backtesting) è il cuore — se fallisce, STOP.
3.
Approccio ibrido: filtro qualitativo (Dividend Aristocrats) + analisi quantitativa.
4.
Decisione data-driven: GO/NO-GO su metriche oggettive definite PRIMA di vedere i risultati.
5.
Validation first, infrastructure later.
1.3 Disclaimer
Sistema di analisi, NON consulenza finanziaria, NON trading automatico. Tutte le decisioni operative sono responsabilità dell'utente.

2. Architettura Attuale
2.1 Stack
Componente	Tecnologia	Dove
Database	PostgreSQL 15 in Docker	VPS, porta 5432, db trading_db
Broker API	FastAPI (trading-brain)	VPS, porta 8000, systemd
Workflow	n8n	Tailscale Funnel, vmi3343226.tail26239d.ts.net
Dashboard	Streamlit (5-8 pagine)	VPS
Repo	~/dividend-recovery-system	GitHub: maxita-69
Dati	yfinance (gratis) → IBKR ($5.60/mese)	Provider
2.2 Il context broker (in costruzione)
L'idea: il FastAPI broker diventa il punto di incontro asincrono tra più LLM (Kimi, Claude, MiniMax) che lavorano sul progetto in sessioni separate.

Componenti previsti:

POST /llm-handoff — briefing in uscita (esiste già)
POST /ingest — ricevere blocchi handoff strutturati (da aggiungere)
CLI brief — generatore di briefing leggibile
CLI ingest — ingestore di handoff JSON
DB PostgreSQL — unica fonte di verità
Vedi § 6 per il protocollo operativo completo.

2.3 Schema del database (5 tabelle — da verificare live)
I vecchi doc (epoca SQLite) nominano 3 modelli: Stock, Dividend, PriceData. Le 5 attuali del PostgreSQL vanno estratte live:

bash

Copy
docker exec -i $(docker ps -qf "ancestor=postgres:15-alpine") psql -U trading -d trading_db -c "\dt"
Risultato atteso: 5 tabelle. I nomi e i campi vanno aggiunti a questa sezione dopo l'estrazione.

2.4 Tailscale & accesso
Accesso SSH: solo via Tailscale (ssh massimiliano@vmi3343226), NON via IP pubblico
Porta 22 pubblica: chiusa (default Contabo)
n8n pubblico: via Tailscale Funnel
FastAPI: solo localhost (per ora), niente esposizione esterna
3. Stato del Lavoro
3.1 Cosa funziona oggi (snapshot 14 Giu 2026)
✅ PostgreSQL 15 in Docker attivo (porta 5432)
✅ FastAPI broker attivo (porta 8000, systemd trading-brain)
✅ n8n accessibile via Tailscale
✅ Repo dividend-recovery-system su GitHub
✅ ~5-8 pagine Streamlit funzionanti (Single Stock, Recovery Analysis, Strategy Comparison, Pattern Analysis, Master Dashboard, + varianti)
✅ ~51 test unitari
✅ Provider architecture multi-source (Yahoo, FMP, IBKR)
3.2 Cosa è fermo / bloccato
#	Blocker	Impatto	Soluzione
1	Chiave EODHD leakata in cronologia chat	Account/provider compromesso	Ruotare su eodhd.com ADESSO
2	Auth PostgreSQL esposta	Rischio accesso non autorizzato	Aggiungere X-API-Key, IP allowlist
3	SAL 5 Backtesting non completato	Strategia non validata empiricamente	Implementare engine in src/backtesting/engine.py
4	Titoli USA non scaricati	Sample insufficiente (276 eventi vs target 500)	Eseguire download_stock_data_v2.py
5	POST /ingest non esiste	Protocollo handoff è solo teorico	Implementare (vedi § 6)
6	Documentazione frammentata in 14 file	Confusione, tempo perso a cercare	Questo file unico
3.3 Cronologia SAL (Stati Avanzamento Lavori)
SAL	Cosa	Status	Note
1	Stock Universe Screener	🟡 60%	41 IT, 0 USA, target 60+
2	Dividend Calendar	✅ 100%	Funzionante, con prediction
3	News & Sentiment	⏸️ 0%	Rimandato a dopo SAL 5
4	Portfolio Management	⏸️ 0%	Dopo SAL 5 GO
5	Backtesting	🟡 25%	Infrastruttura pronta, engine mancante
6	Daily Automation	⏸️ 0%	Dopo SAL 5 GO
3.4 Criteri GO/NO-GO per SAL 5 (da definire PRIMA del run)
Win rate > 60%
Expected value > 0 (dopo TUTTI i costi)
Sharpe ratio > 1.0
Max drawdown < 15%
Almeno 30% di eventi con recovery < 10 giorni
4. Stack tecnico & costi di trading
4.1 Costi Fineco (da config.py)
Voce	Valore
Commissioni	0.19% per operazione
Tobin Tax	0.10% (solo IT)
Overnight	Euribor 1M + 7.99% annuo
Capital gain	26%
4.2 Universo titoli target (pre-screening)
Dividend Aristocrats (25+ anni di crescita dividendo)
Dividend Kings (50+ anni)
SCHD holdings
VIG / NOBL holdings
Market cap > $10B
Yield 2-5%
Payout ratio < 70%
Presenti in almeno 2 fonti
4.3 Score 0-100 (decision support)
80-100 🟢 HIGH — trade consigliato
60-79 🟡 MEDIUM — valutare risk/reward
0-59 🔴 LOW — skip
5. Comandi Rapidi
5.1 Accesso VPS
bash

Copy
# SSH via Tailscale (SOLO questo, non IP pubblico)

ssh massimiliano@vmi3343226


# Stato servizi

sudo systemctl status trading-brain

sudo systemctl status tailscale-funnel
5.2 Database
bash

Copy
# Container info

docker ps


# Accesso psql

docker exec -it $(docker ps -qf "ancestor=postgres:15-alpine") psql -U trading -d trading_db


# Lista tabelle

docker exec -i $(docker ps -qf "ancestor=postgres:15-alpine") psql -U trading -d trading_db -c "\dt"
5.3 FastAPI
bash

Copy
# Health check

curl http://localhost:8000/


# Briefing LLM

curl http://localhost:8000/llm-handoff


# Logs

sudo journalctl -u trading-brain -f
5.4 Lavoro sul repo
bash

Copy
cd ~/dividend-recovery-system

source venv/bin/activate

python download_stock_data_v2.py  # ~3h per 20 titoli USA

python dividend_calendar.py

streamlit run app/Home.py
6. Protocollo Operativo (regole ferree per gli LLM)
6.1 Fase 1 — Esplorazione (obbligatoria prima di ogni modifica)
L'LLM DEVE:

1.
✅ Esplorare l'intera struttura (non un singolo file)
2.
✅ Leggere tutti i file rilevanti, non assumere
3.
✅ Capire come funziona attualmente
4.
✅ Mostrare report completo di cosa ha trovato
5.
✅ Mostrare preview delle modifiche (mockup, snippet, schema)
6.
✅ Aspettare conferma esplicita prima di modificare
6.2 Fase 2 — Verifica (prima di dichiarare "fatto")
✅ Verificare con screenshot/log se l'utente li fornisce
✅ Cross-check con questo documento
✅ Validare le assunzioni (non indovinare)
6.3 Fase 3 — Checkpoint (dopo ogni task)
✅ Fermarsi, mostrare: cosa fatto, cosa modificato, problemi, prossimi step
✅ NON concatenare task senza approvazione
✅ Aggiornare questo documento
6.4 Comunicazione
L'LLM deve aprire un task con:

text

Copy
Ho capito. Prima di procedere:

1. [cosa esplorerò]

2. [cosa leggerò]

3. [cosa verificherò]

Procedo?
E chiudere con:

text

Copy
✅ TASK COMPLETATO: [nome]

Cosa ho fatto: [...]

File modificati: [...]

Prossimi step: [...]

Posso procedere?
6.5 Principio guida
"Meglio chiedere 10 volte che sbagliare 1 volta"

6.6 Cosa NON fare MAI
❌ Modificare senza esplorazione completa
❌ Assumere la struttura del codice
❌ Sovrascrivere configurazioni esistenti
❌ Concatenare task senza checkpoint
❌ Ignorare discrepanze tra analisi e realtà
❌ Committare su main senza permesso
6.7 Handoff protocol (context broker)
A fine sessione, l'LLM DEVE emettere un blocco strutturato:

json

Copy
// ```handoff

{

  "session_meta": {

    "llm": "claude|kimi|minimax",

    "date": "YYYY-MM-DD",

    "branch": "..."

  },

  "decisions": [...],

  "files_touched": [...],

  "next_task": "...",

  "open_problems": [...]

}

// ```
L'utente lo incolla in POST /ingest (o via CLI ingest) e il DB viene aggiornato. Schema formale handoff.v1 da definire (todo breve termine).

7. Decisioni chiave
7.1 Architetturali (assunte)
✅ PostgreSQL 15 in Docker (NON SQLite)
✅ Streamlit per dashboard
✅ yfinance per dati storici (gratis)
✅ IBKR per future live data
✅ Provider abstraction (Yahoo, FMP, IBKR)
✅ Modular structure
7.2 Strategiche (assunte)
✅ Filtro qualitativo PRIMA (Dividend Aristocrats)
✅ Backtesting su ~500 events
✅ Multi-strategy comparison (D-1 vs D0, leverage vs no)
✅ Tutti i costi inclusi
✅ GO/NO-GO basato su metriche predefinite
7.3 Da rivedere / decidere
⚠️ Provider dati definitivo (Yahoo, FMP o Finnhub per USA?)
⚠️ Tolleranza gap dati (giorni mancanti accettabili?)
⚠️ Gestione anomalie (esclusione titoli con dati cattivi?)
⚠️ Leverage preferito: 3x o 5x?
⚠️ Entry point preferito: D-1 close o D0 open?
⚠️ Max holding period: fisso 30gg o dinamico?
⚠️ Metriche esatte di successo backtesting
⚠️ Schema formale handoff.v1 JSON Schema
8. Roadmap prossima
8.1 Urgente (oggi)
 Ruotare chiave EODHD su eodhd.com
 Sostituire i 14 file DOCUMENTAZIONE/ con questo file unico
 Installare Tailscale sul PC Windows (per accesso SSH)
8.2 Breve termine (questa settimana)
 Implementare POST /ingest su FastAPI
 Definire handoff.v1 JSON Schema
 Creare CLI brief e ingest
 Aggiungere X-API-Key + auth minima al broker
 Validare le 5 tabelle del DB (estrarre schema live, aggiornare §2.3)
8.3 Medio termine (questo mese)
 Implementare backtesting engine (src/backtesting/engine.py)
 Scaricare 20 titoli USA (~3h, sblocca SAL 5)
 Run backtest completo su ~500 events
 GO/NO-GO decision su SAL 5
8.4 Lungo termine (se GO)
 Pattern analysis (correlazioni pre→post recovery)
 ML model (Random Forest / XGBoost)
 Out-of-sample validation
 Daily automation (SAL 6)
 Live trading integration (IBKR)
9. Note operative
9.1 Convenzioni
Maiuscole per costanti, snake_case per variabili
Path: ~/dividend-recovery-system/
Branch: main (no push diretti, sempre feature branch)
Commit: solo dopo approvazione utente
9.2 File & cartelle chiave
text

Copy
~/dividend-recovery-system/

├── app/                        # Dashboard Streamlit

│   ├── Home.py

│   └── pages/                  # 5-8 pagine

├── src/

│   ├── database/

│   │   ├── models.py           # ⭐ I modelli DB (5 tabelle, da validare)

│   │   ├── download_*.py

│   │   └── test_*.py

│   ├── utils/                  # ⭐ Utilities condivise

│   │   ├── recovery_analysis.py

│   │   ├── pattern_analysis.py

│   │   ├── validation.py

│   │   └── logging_config.py

│   └── backtesting/            # 🔜 Da creare

│       └── engine.py

├── providers/                  # Yahoo, FMP, IBKR abstraction

├── dividendi/                  # Script IBKR dedicati

├── dashboard/                  # Dashboard calendario (separata)

├── config.py                   # ⭐ Configurazione centralizzata

├── tests/                      # 51+ unit test

└── DOCUMENTAZIONE.md           # ⭐ QUESTO FILE (unico, canonico)
9.3 Sicurezza
Item	Stato	Azione
Chiave EODHD	🔴 Leaked in chat	Ruotare ADESSO su eodhd.com
FastAPI auth	🔴 Assente	Aggiungere X-API-Key + IP allowlist
PostgreSQL password	🟡 In Bitwarden	OK, ruotare periodicamente
n8n via Tailscale Funnel	🟡 Esposto	Verificare auth
Streamlit auth	✅ Presente	bcrypt + cookie
secrets.toml	✅ Non in git	OK
Repo GitHub	✅ Privato	OK
Porta 22 pubblica	✅ Chiusa	OK (solo Tailscale SSH)
9.4 Comandi del context broker (post-implementazione, reference)
bash

Copy
# Genera briefing leggibile (1× per sessione LLM)

brief


# Ingest handoff JSON a fine sessione

ingest < handoff.json
Entrambi wrap di curl verso FastAPI. Da implementare.

10. Contatti & Riferimenti
Developer: Massimiliano (Max) Esperienza: Trading quantitativo Piattaforma: Fineco Approccio: "RIGORE e pazienza" Repo: https://github.com/maxita-69/dividend-recovery-system VPS: Contabo (vmi3343226), Ubuntu

Appendice A — Setup locale Windows (ridotto al minimo)
Setup usato finora sul PC di sviluppo, ancora valido:

cmd

Copy
cd C:\Users\mvuon\Documents\GitHub\dividend-recovery-system

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt
Nota: ora lo sviluppo attivo è sul VPS. Il PC Windows serve solo per review e accesso SSH via Tailscale.

Appendice B — Troubleshooting rapido
Errore	Causa probabile	Fix
python: command not found	Python non in PATH	Reinstalla con "Add to PATH"
ModuleNotFoundError: yfinance	Dipendenze non installate	pip install -r requirements.txt
curl_cffi ProxyError	Firewall aziendale	VPN o rete casa
Yahoo Finance 403	Rate limiting	Aspetta 5-10 min o VPN
Database locked	Altri script aperti	Chiudi dashboard/Streamlit
FastAPI non risponde	Servizio giù	sudo systemctl restart trading-brain
SSH port 22 timeout	IP pubblico chiuso	Usa Tailscale: ssh massimiliano@vmi3343226
psql: connection refused	Container down	docker ps, restart container
Versione documento: 1.0 — Merge unificato di 14 file originali (DEPLOY_GUIDE, DIVIDEND_CALENDAR_README, IB_GATEWAY_SETUP, IMPROVEMENTS, PROTOCOLLO_OPERATIVO, README, REGISTRO_PROGETTO, SAL_PROGRESS, SETUP_LOCALE, START_HERE, STEP_1_COMPLETED, STREAMLIT_SECRETS_SETUP, UPLOAD_TO_GITHUB, STATO_ATTUALE)

File originali da archiviare/cancellare dopo approvazione del merge.
