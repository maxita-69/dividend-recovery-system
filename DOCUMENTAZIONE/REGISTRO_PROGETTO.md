# 📖 REGISTRO PROGETTO - Diario Sviluppo

**Progetto**: Dividend Recovery System
**Repository**: maxita-69/dividend-recovery-system
**Ultimo aggiornamento**: 2026-01-14

---

## 🎯 OBIETTIVO GENERALE DEL PROGETTO

Creare un sistema quantitativo per analizzare e tradare strategie di **Dividend Recovery** su titoli italiani e americani con fondamentali forti.

### Strategia Core:
- **Buy**: D-1 o D0 (prima/giorno dello stacco dividendo)
- **Sell**: Quando prezzo recupera completamente (entro 5-30 giorni)
- **Leverage**: Fineco (leva 5x su FinecoBank)
- **Target**: Titoli solidi (Dividend Aristocrats, SCHD holdings)

### Filosofia:
> **"Non si automatizza un sistema che perde soldi"**

Prima **VALIDARE empiricamente** (SAL 5 - Backtesting), poi automatizzare.

---

## 🧭 DIREZIONE ATTUALE

**FASE**: Data Quality & Database Reliability (Pre-SAL 5)

**Focus**: Garantire affidabilità dati storici prima di iniziare backtesting serio

**Perché**:
- Backtesting richiede dati prezzi/dividendi accurati
- Provider diversi danno risultati diversi
- Serve validazione sistematica delle fonti dati

---

## 📍 PUNTO ATTUALE (2026-01-14 - Aggiornato)

### Dove siamo:
- ✅ App Streamlit completa con **8 PAGINE** (Home, Single Stock, Recovery Analysis, Strategy Comparison, Pattern Analysis, Master Dashboard, Download Data, **Database Dashboard**)
- ✅ Database SQLite con 127 titoli, ~190k record prezzi, 2291 dividendi
- ✅ Ultimo aggiornamento DB: 5 giorni fa
- ✅ **COMPLETATO**: Dashboard Database per monitoraggio qualità dati
- ⚠️ **IN CORSO**: Validazione affidabilità dati scaricati da provider esterni

### Cosa abbiamo completato oggi:
- ✅ Creato PROTOCOLLO_OPERATIVO.md con regole ferree di lavoro (+ regola preview)
- ✅ Creato REGISTRO_PROGETTO.md per tracciatura continua
- ✅ Implementata pagina Database Dashboard (7_Database_Dashboard.py)

### Prossimi passi:
1. ~~Creare Dashboard Database (monitoring qualità dati)~~ ✅ **COMPLETATO**
2. Testare Dashboard Database e verificare funzionamento
3. Completare validazione provider
4. Popolare DB con titoli USA (SCHD holdings)
5. Iniziare SAL 5 (Backtesting) con dati validati

---

## 📅 CRONOLOGIA ATTIVITÀ

### **2026-01-14 (Pomeriggio)** - Implementazione Database Dashboard

**Attività**:
- Implementata nuova pagina `7_Database_Dashboard.py` (608 righe)
- Monitoraggio completo qualità database

**Funzionalità implementate**:
1. ✅ **KPI Metrics**: Totale titoli, ultimo aggiornamento, prezzi, dividendi
2. ✅ **Suddivisione Mercati**: Tabella + grafico a torta
3. ✅ **Analisi Consistenza**:
   - Alert critici (titoli senza prezzi, prezzi anomali, dividendi incompleti)
   - Warning (gap temporali, incongruenze date)
   - Status OK per dati validi
4. ✅ **Dettagli per Ticker**: Tabella completa con filtri per mercato e problemi
5. ✅ **Log Attività**: Ultimi 20 download/operazioni

**Pattern seguiti**:
- Autenticazione con `require_authentication()`
- Database session pattern (cached engine, nuove sessioni)
- CSS custom per alert (critical/warning/success)
- Layout responsive con colonne Streamlit
- Grafici Plotly (pie chart per mercati)

**Note tecniche**:
- Classificazione indici USA (NASDAQ/DJ/SP500) segnalata come non automatica
- Info box per avvisare che serve classificazione manuale
- Campo `index_membership` preparato per future implementazioni

**Risultato**:
- ✅ App passa da 7 a 8 pagine
- ✅ Completa visibilità su qualità database
- ✅ Identificazione automatica problemi dati

---

### **2026-01-14 (Mattina)** - Creazione Protocollo Operativo

**Attività**:
- Creato `PROTOCOLLO_OPERATIVO.md` con regole ferree di lavoro
- Creato `REGISTRO_PROGETTO.md` (questo file) per tracciatura continua

**Motivazione**:
- Errori ricorrenti: modifiche senza esplorazione completa
- Necessità di memoria persistente tra sessioni
- Migliorare efficienza collaborazione Claude-User

**Errore rilevato**:
- Claude ha analizzato solo 1 file in `dashboard/pages/` concludendo erroneamente "2 pagine totali"
- Screenshot utente mostrava chiaramente 7 pagine nel menu
- Rischio: sovrascrivere configurazione esistente con nuova parziale
- **Lezione**: SEMPRE usare Task agent Explore per mappare strutture complesse

**Risultato**:
- ✅ Protocollo operativo vincolante definito
- ✅ Sistema di tracciatura attività implementato
- ✅ Esplorazione completa app: trovate 7 pagine in `app/` (non `dashboard/`)

---

### **2026-01-13** - Test Download Dati (Sessione Serale)

**Commit**:
- `b3c61d9` - Aggiunto ticker AEXAY (titolo americano) alla lista test
- `db0d803` - Aggiunto script test Yahoo Finance per validazione dati
- `dc47d42` - Aggiunto script analisi database titoli e dividendi
- `d1bdf46` - Test Finnhub: aggiunti ticker USA per confronto

**Attività**:
1. ✅ Creato `test_yahoo_download.py` (267 righe)
   - Test sistematico download da Yahoo Finance
   - Analisi qualità: prezzi + dividendi
   - Ticker testati: FBK.MI, ENI.MI, ENEL.MI, AEXAY
   - Statistiche dettagliate, anomalie, valori mancanti

2. ✅ Creato `analizza_db.py` (168 righe)
   - Analisi contenuto database attuale
   - Statistiche titoli, prezzi, dividendi
   - Distribuzione per mercato
   - Log ultimi download

3. ✅ Test comparativi provider
   - Yahoo Finance: Testato su titoli italiani + USA
   - Finnhub: Aggiunti ticker USA per confronto
   - FMP: Test precedenti

**Scoperte**:
- Yahoo Finance: Dati affidabili per titoli .MI (italiani)
- Dividendi: Alcuni provider hanno gap o date inconsistenti
- Database attuale: 19 MB, ben popolato ma solo titoli italiani

**Obiettivo sessione**:
> "Rendere affidabile la mia base dati"

**Stato**: ⚠️ Test in corso, validazione non completata

---

### **2026-01-12** - Aggiornamento SAL Progress

**Commit**:
- Aggiornato `SAL_PROGRESS.md` con filosofia progetto e stato DB

**Focus**:
- Definizione chiara principi guida
- Mapping stato database (41 titoli Italia, 0 USA)
- Identificazione criticità: mancano titoli USA

---

### **2026-01-11 e precedenti** - Sviluppo App Streamlit

**Attività principali**:
- ✅ Implementate 7 pagine applicazione
- ✅ Autenticazione utenti (streamlit-authenticator)
- ✅ Grafici interattivi Plotly (candlestick, indicatori tecnici)
- ✅ Analisi recovery storica
- ✅ Confronto strategie con costi broker
- ✅ Pattern analysis
- ✅ Master dashboard multi-prospettiva

**Tecnologie**:
- Streamlit multi-page app
- SQLAlchemy ORM
- Plotly per grafici
- SQLite database

---

## 🔄 EVOLUZIONI PROGETTO

### Da Idea a Sistema Strutturato

**Fase 1** - Concezione (Dicembre 2025?):
- Idea: Tradare recovery post-dividendo con leverage Fineco
- Target: FinecoBank (FBK.MI) come caso studio

**Fase 2** - Prototipo:
- Download dati base
- Prime analisi recovery
- Prove manuali

**Fase 3** - Strutturazione (Gennaio 2026):
- ✅ Database strutturato (SQLite + SQLAlchemy)
- ✅ App Streamlit completa
- ✅ Multi-provider data collection
- ✅ Analisi avanzate (pattern, strategie, backtesting preparatorio)

**Fase 4** - Data Quality (IN CORSO):
- ⚠️ Validazione sistematica provider
- ⚠️ Test affidabilità dati storici
- ⚠️ Identificazione gap e anomalie

**Fase 5** - Backtesting (PROSSIMA):
- 🔮 Validazione empirica strategie
- 🔮 Metriche performance (win rate, expected value, Sharpe)
- 🔮 Decisione GO/NO-GO sul trading reale

---

## ❌ ERRORI COMMESSI E LEZIONI APPRESE

### **2026-01-14** - Analisi incompleta struttura app

**Errore**:
- Analizzato solo `dashboard/pages/` → trovato 1 file
- Concluso erroneamente: "solo 2 pagine totali"
- Screenshot mostrava chiaramente 7 pagine
- Non usato Task agent Explore

**Impatto potenziale**:
- Rischio sovrascrittura configurazione esistente
- Perdita pagine funzionanti
- Regressione applicazione

**Lezione**:
1. **MAI assumere** struttura senza esplorazione completa
2. **SEMPRE usare** Task agent Explore per sistemi complessi
3. **SEMPRE confrontare** analisi con screenshot/documentazione
4. **FERMARSI** se ci sono discrepanze

**Soluzione implementata**:
- Creato PROTOCOLLO_OPERATIVO.md vincolante
- Definite regole ferree pre-modifica
- Sistema checkpoint obbligatori

---

### **Data sconosciuta** - Provider diversi, dati diversi

**Problema**:
- Yahoo Finance, Finnhub, FMP danno risultati leggermente diversi
- Dividendi: Date inconsistenti tra provider
- Prezzi: Piccole differenze su adjusted close

**Lezione**:
- Serve validazione sistematica
- Documentare quale provider usare per quale mercato
- Cross-check dati critici

**Soluzione in corso**:
- Script test sistematici (`test_yahoo_download.py`, etc.)
- Analisi comparativa provider
- Dashboard monitoring qualità dati (TODO)

---

## 🎯 TASK IN SOSPESO

### Priorità ALTA (Blocca SAL 5)

1. **Dashboard Database Monitoring**
   - Totale titoli, suddivisione mercati
   - Data ultimo aggiornamento
   - Analisi consistenza dati (gap, anomalie, valori mancanti)
   - Alert visivi problemi

2. **Completare validazione provider**
   - Decidere provider ufficiale per IT/USA
   - Documentare scelte
   - Script download validato

3. **Popolare titoli USA**
   - SCHD holdings (25 titoli)
   - S&P 500 Dividend Aristocrats
   - Download dati storici 5+ anni

### Priorità MEDIA

4. **Classificazione indici USA**
   - Campo `index_membership` in DB (NASDAQ, DJ, SP500)
   - Script popolamento automatico (API?)
   - Fallback: Classificazione manuale

5. **Migliorare logging download**
   - Tracciare ogni operazione
   - Timestamp, source, status, errori

### Priorità BASSA (Post-validazione)

6. **Ottimizzazioni performance**
7. **Deploy produzione**
8. **Documentazione utente finale**

---

## 💡 DECISIONI CHIAVE DA PRENDERE

### Immediate:

- [ ] **Provider dati definitivo**: Yahoo Finance, Finnhub o FMP per USA?
- [ ] **Tolleranza gap dati**: Quanti giorni mancanti sono accettabili?
- [ ] **Gestione anomalie**: Escludere titoli con dati problematici?

### Future (Pre-SAL 5):

- [ ] **Metriche successo backtesting**: Win rate >60%? Expected value soglia?
- [ ] **Periodo test**: Quanti anni di dati storici serve testare?
- [ ] **Costi broker**: Fineco vs IB, quale usare per calcoli?
- [ ] **Leverage**: Confermare 5x su Fineco o testare anche senza leva?

---

## 📚 FILE CHIAVE DA CONSULTARE

### Documentazione Progetto:
- `DOCUMENTAZIONE/SAL_PROGRESS.md` - Stato avanzamento lavori, filosofia
- `DOCUMENTAZIONE/PROTOCOLLO_OPERATIVO.md` - Regole lavoro (QUESTO)
- `DOCUMENTAZIONE/REGISTRO_PROGETTO.md` - Diario (QUESTO FILE)
- `DOCUMENTAZIONE/START_HERE.md` - Guida rapida setup
- `DOCUMENTAZIONE/README.md` - Overview generale

### Tecnica:
- `app/Home.py` - Entry point applicazione
- `src/database/models.py` - Modelli dati (Stock, Dividend, PriceData)
- `test_yahoo_download.py` - Test validazione dati Yahoo
- `analizza_db.py` - Analisi database attuale

### Configurazione:
- `.streamlit/config.toml` - Config Streamlit
- `.streamlit/secrets.toml` - Credenziali (non in repo)

---

## 🔮 VISIONE FUTURA

### Cosa vogliamo costruire:

**Sistema Completo Dividend Recovery** che:
1. ✅ Monitora titoli con fondamentali forti
2. ✅ Identifica opportunità dividend recovery
3. 🔮 Backtesta strategie empiricamente
4. 🔮 Genera alert operativi (se backtesting positivo)
5. 🔮 Traccia performance reale
6. 🔮 Adatta strategia in base a risultati

**Metrica successo finale**:
> Sistema che genera expected value positivo costante dopo TUTTI i costi (spread, commissioni, leverage)

**Principio guida**:
> Se backtesting mostra perdite → STOP. Non si automatizza un sistema che perde soldi.

---

## 📝 NOTE OPERATIVE

### Come usare questo file:

**All'inizio di ogni sessione**:
1. Leggere sezione "PUNTO ATTUALE"
2. Vedere "CRONOLOGIA ATTIVITÀ" (ultimi 2-3 giorni)
3. Capire contesto e direzione

**Durante la sessione**:
1. Aggiornare cronologia con task completati
2. Documentare decisioni prese
3. Tracciare errori/problemi incontrati

**Fine sessione**:
1. Aggiornare "PUNTO ATTUALE"
2. Commit di questo file
3. Preparare prossimi passi

---

## 🤝 COLLABORAZIONE

**User (Max)**:
- Definisce strategia e obiettivi
- Valida risultati e analisi
- Decide GO/NO-GO su implementazioni

**Claude**:
- Implementa codice seguendo PROTOCOLLO_OPERATIVO.md
- Analizza dati e genera insight
- Propone soluzioni tecniche
- **SEMPRE**: Esplora → Report → Attende conferma → Esegue

---

**Questo registro è VIVO e deve essere aggiornato costantemente.**

Ogni sessione deve lasciare traccia qui per garantire continuità.

---

*Ultima modifica: 2026-01-14 - Creazione iniziale*
