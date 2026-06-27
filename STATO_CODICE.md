# STATO DEL CODICE — dividend-recovery-system
**Data analisi:** 27 Giugno 2026, 14:54
**Analizzato da:** Kimi 2.6 (analisi preliminare da struttura file + git history)
**Metodo:** Opzione A — fotografia manuale (Passo B.1 Piano Test v1.3)
**Repo:** `~/dividend-recovery-system` (branch `main`, commit `3983e61`)

---

## 1. MAPPA DEI MODULI

| Modulo | Path | Righe | Stato | Note |
|--------|------|-------|-------|------|
| **Config centrale** | `config.py` | 309 | 🟡 Da verificare | Variabili globali, provider, credenziali |
| **Database** | `src/database/` | ~1.500 | 🔴 Duplicazione massiva | 5 file di download diversi |
| **Utils** | `src/utils/` | ~1.050 | 🟡 Da verificare | pattern, recovery, validation, logging |
| **Dashboard Streamlit (primaria)** | `app/` | ~5.100 | 🟢 Più completa | 7 pagine, Master Dashboard 849 righe |
| **Dashboard Streamlit (secondaria)** | `dashboard/` | ~608 | 🔴 Probabilmente morta | Merge residuo? |
| **Frontend Angular** | `frontend/src/` | — | ⚪ Da verificare | Build funzionante? |
| **Provider FMP** | `providers/fmp_provider.py` | 157 | 🟡 Da verificare | Implementazione FMP |
| **Data Providers (src)** | `src/data_providers/` | — | ⚪ Da verificare | Cartella esiste |
| **Dividend Calendar** | `dividendi/` | 392 | 🟡 Da verificare | dividend_calendar.py, debug_all |
| **Predictor** | `src/dividend_predictor.py` | 252 | 🟡 Da verificare | Modello ML? |
| **Ingest** | `src/ingest_endpoint.py` | 193 | 🟡 Da verificare | Endpoint FastAPI? |
| **Test** | `tests/` | 859 | 🟡 Copertura bassa | 3 file |
| **Script vari** | `script/`, `scripts/` | 378 | 🔴 Duplicazione | Due cartelle simili |
| **Standalone test** | `test_*.py` (root) | 1.089 | 🔴 Probabilmente morti | File sparsi in root |

**Totale:** 14.269 righe Python in ~40 file

---

## 2. STATO DI COMPLETAMENTO

### 🟢 Completato / Funzionante
- Config centralizzata (`config.py`)
- Dashboard Streamlit principale (`app/` con 7 pagine)
- Database module (`src/database/database.py`)
- Pattern Analysis + test
- Recovery Analysis + test
- Validation + test
- Dividend Calendar
- Provider FMP

### 🟡 Abbozzato / Da verificare
- Frontend Angular (esiste ma stato incognito)
- FastAPI backend (`ingest_endpoint.py` unico riferimento?)
- ML Predictor (modello addestrato?)
- Streamlit config

### 🔴 Duplicato / Morto / Da rimuovere
- **5 file download_stock_data*** → unificare
- **Dashboard secondaria** (`dashboard/`) → verificare se usata
- **Script vs scripts** → unificare
- **Test standalone in root** → spostare o rimuovere

---

## 3. INCONGRUENZE RILEVATE

### 3.1 Merge di 3 branch
Commit `edbe632`: "Unified Angular frontend from dividend-capture-trading + dividend-recovery-angular + kimi-agent-progetto-trading-ml"

**Conseguenze:**
- Due dashboard Streamlit
- 5 file di download dati
- File di test sparsi
- Documentazione frammentata (6 file `.md`)

### 3.2 Doppia struttura dashboard
- `app/` → 7 pagine, 5.100 righe (struttura completa)
- `dashboard/` → 1 pagina + app.py, 608 righe (probabilmente residuo)

### 3.3 Molteplici strategie download
| File | Righe |
|------|-------|
| `download_stock_data.py` | 210 |
| `download_stock_data_hybrid.py` | 299 |
| `download_stock_data_v2.py` | 409 |
| `download_stock_data_fmp.py` | 362 |
| `download_data_ib.py` | 359 |

**Nessuno è chiaramente "il principale".**

### 3.4 Manca `CLAUDE.md`
- `.claude/` esiste ma vuota
- `CLAUDE.md` non esiste
- Da creare se si usa Claude Code intensivamente

### 3.5 Frontend Angular — stato incognito
- Esiste `frontend/src/` ma non verificato:
  - `npm install` funziona?
  - `ng build` valido?
  - Collegato al backend?

### 3.6 Backend FastAPI — esiste davvero?
- Manuale dichiara FastAPI
- `src/ingest_endpoint.py` (193 righe) unico riferimento
- Manca `main.py` strutturato?

---

## 4. STATO GIT

| Parametro | Valore |
|-----------|--------|
| Branch | `main` ✅ |
| Stato | `nothing to commit, working tree clean` ✅ |
| Commit recente | `3983e61` — pulizia repo 27/06 |
| Merge 3 branch | `edbe632` |

---

## 5. ALLINEAMENTO STACK DICHIARATO

| Stack dichiarato | Stato repo | Esito |
|------------------|------------|-------|
| Angular 17+ | `frontend/src/` esiste | 🟡 Da verificare build |
| FastAPI | `ingest_endpoint.py` (193 righe) | 🟡 Incompleto? |
| Streamlit | `app/` (7 pagine) + `dashboard/` | 🟢 Presente ma duplicato |
| PostgreSQL | `src/database/database.py` | 🟢 Presente |
| SQLAlchemy | Probabilmente in `database.py` | 🟡 Da verificare |
| yfinance | Riferimenti presenti | 🟢 |
| FMP | `providers/fmp_provider.py` | 🟢 |
| EODHD | `config.py` | 🟢 Key ruotata |
| IBKR | `download_data_ib.py` | 🟡 Implementato |
| scikit-learn | `dividend_predictor.py` | 🟡 Stato incognito |
| Finnhub | `test_finnhub.py` | 🟡 Testato |

---

## 6. PRIORITÀ DI INTERVENTO

### 🔴 URGENTE
| # | Azione |
|---|--------|
| 1 | Unificare i 5 file di download dati |
| 2 | Verificare se `dashboard/` è usata o morta |
| 3 | Verificare se esiste un `main.py` FastAPI |

### 🟡 IMPORTANTE
| # | Azione |
|---|--------|
| 4 | Spostare/rimuovere test standalone dalla root |
| 5 | Unificare `script/` e `scripts/` |
| 6 | Verificare build Angular |
| 7 | Creare `CLAUDE.md` |
| 8 | Rivedere documentazione (6 file `.md`) |

### 🟢 FUTURO
| # | Azione |
|---|--------|
| 9 | Aumentare copertura test |
| 10 | Verificare stato ML model |
| 11 | Valutare rimozione `dashboard/` |

---

## 7. DOMANDE APERTE PER CLAUDE CODE

1. Quale dei 5 file `download_stock_data*.py` è quello "buono"?
2. Esiste un `main.py` FastAPI strutturato?
3. `dashboard/` è usata da qualcuno?
4. Il frontend Angular builda?
5. `src/data_providers/` è vuota o piena?
6. `dividend_predictor.py` è modello addestrato o abbozzo?
7. I file `test_*.py` in root sono test veri o script di debug?

---

## 8. RIEPILOGO IN UNA FRASE

> Il repo è un **merge di 3 branch** con un progetto funzionante ma **duplicazioni significative** (5 file download, 2 dashboard, 2 cartelle script) e **componenti incogniti** (Angular build, FastAPI strutturato, ML model). Priorità: unificare download, verificare doppia dashboard, capire se il backend FastAPI esiste.

---

*Analisi prodotta da Kimi 2.6 il 27 Giugno 2026, 14:54.*
