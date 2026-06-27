# Istruzioni per Claude Code — dividend-recovery-system

## All'avvio di OGNI sessione, fai SEMPRE questo PER PRIMO
1. Esegui: `./genera_stato.sh`
2. Leggi il file `STATO.md` appena generato.
3. Riassumimi in massimo 5 righe dove siamo, poi aspetta istruzioni.
STATO.md e' la fonte di verita': non serve rispiegare il progetto.

## Cos'e' questo progetto
Sistema di dividend capture: entrare 2-3 giorni prima dell'ex-dividend date,
target margine netto 2-3%, mercati USA/UK/Italia. Gira su VPS Contabo (Ubuntu 24.04).

## Stack
- Backend: Python + FastAPI ; Frontend: Angular 17+ ; Dashboard: Streamlit
- DB: PostgreSQL + SQLAlchemy ; Data: yfinance, EODHD, FMP, IBKR

## Regole
- MAI committare chiavi/API key (stanno in .env, gitignored).
- Prima di modifiche estese: git add -A && git commit (cosi' si torna indietro).
- All'inizio chiedi conferma prima di modificare file o lanciare comandi.

## A fine sessione
Aggiorna INTENTO.md, rilancia ./genera_stato.sh, poi git commit -am "stato: $(date +%F)".
