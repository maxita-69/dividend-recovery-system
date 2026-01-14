# 🤝 PROTOCOLLO OPERATIVO - Interazione Claude & User

**Data creazione**: 2026-01-14
**Versione**: 1.0
**Scopo**: Definire le regole ferree di come Claude deve lavorare su questo progetto

---

## ⚠️ REGOLE FONDAMENTALI

Queste regole sono **VINCOLANTI** e devono essere rispettate **SEMPRE**, senza eccezioni.

---

## 📋 FASE 1: ESPLORAZIONE (OBBLIGATORIA)

### Prima di fare QUALSIASI modifica, Claude DEVE:

1. ✅ **Esplorare COMPLETAMENTE la struttura dell'applicazione**
   - Non limitarsi a un singolo file o cartella
   - Verificare TUTTA la codebase rilevante
   - Identificare dipendenze e relazioni tra componenti

2. ✅ **Leggere TUTTI i file rilevanti**
   - Non assumere il contenuto di un file
   - Non fare modifiche "al buio"
   - Leggere file di configurazione, modelli, routing, etc.

3. ✅ **Capire COME funziona attualmente**
   - Comprendere il flusso applicativo
   - Identificare pattern esistenti
   - Capire convenzioni e standard utilizzati

4. ✅ **Mostrare un ELENCO COMPLETO di cosa ha trovato**
   - Report strutturato della situazione attuale
   - Lista file rilevanti con path completi
   - Architettura e organizzazione del codice
   - Numero di pagine/componenti esistenti

5. ✅ **Aspettare conferma ESPLICITA prima di modificare**
   - Non procedere senza approvazione dell'utente
   - Presentare il piano d'azione
   - Attendere "OK" o "procedi" esplicito

---

## 🔍 STRUMENTI DI ESPLORAZIONE

### Uso del Task Agent (OBBLIGATORIO per esplorazioni complesse)

Quando l'utente richiede modifiche a sistemi complessi (app Streamlit, routing, architettura multi-file), Claude DEVE usare:

```
Task agent con subagent_type=Explore per mappare TUTTA la struttura:
- Dove sono definite le pagine
- Come funziona il routing
- Quali file sono coinvolti
- Configurazioni e dipendenze
- Report completo e strutturato
```

**Livello di thoroughness**:
- `quick`: Solo per task semplici e isolati
- `medium`: Per modifiche standard
- `very thorough`: Per modifiche a sistemi complessi o architetturali (SEMPRE usare per app Streamlit)

---

## ✅ FASE 2: VERIFICA (OBBLIGATORIA)

### Prima di dichiarare "completato", Claude DEVE:

1. ✅ **Verificare visivamente con screenshot/documentazione**
   - Se l'utente fornisce screenshot, confrontare con la propria analisi
   - Se ci sono discrepanze, **FERMARSI IMMEDIATAMENTE**
   - Segnalare le differenze trovate
   - Non procedere finché non è chiarito

2. ✅ **Cross-check con documentazione esistente**
   - Leggere SAL_PROGRESS.md per contesto generale
   - Verificare REGISTRO_PROGETTO.md per attività recenti
   - Consultare README e guide tecniche rilevanti

3. ✅ **Validare le assunzioni**
   - Se si assume qualcosa ("probabilmente funziona così"), VERIFICARE
   - Non dare per scontato nulla
   - Meglio chiedere che sbagliare

---

## 🚦 FASE 3: CHECKPOINT (OBBLIGATORIO)

### Ogni volta che completa un task, Claude DEVE:

1. ✅ **FERMARSI e mostrare:**
   - ✓ **Cosa ha fatto** (descrizione sintetica)
   - ✓ **Cosa ha modificato** (lista file con diff/summary)
   - ✓ **Eventuali problemi incontrati**
   - ✓ **Prossimi passi previsti**

2. ✅ **Aspettare conferma per procedere**
   - Non concatenare task senza approvazione
   - Permettere all'utente di revisionare
   - Accettare feedback e correzioni

3. ✅ **Aggiornare REGISTRO_PROGETTO.md**
   - Tracciare l'attività completata
   - Aggiornare "PUNTO ATTUALE"
   - Documentare decisioni prese

---

## 🚫 COSA NON FARE MAI

### Errori comuni da evitare assolutamente:

❌ **NON procedere con modifiche senza esplorazione completa**
- Esempio: "Vedo 1 file, quindi ci sono solo 1 pagina" ❌
- Corretto: "Esploro TUTTA la struttura, trovo 7 pagine" ✅

❌ **NON fare assunzioni sulla struttura del codice**
- Esempio: "Probabilmente è organizzato così..." ❌
- Corretto: "Ho letto i file, è organizzato così:" ✅

❌ **NON sovrascrivere configurazioni esistenti**
- Prima: Capire come funziona ora
- Poi: Estendere/integrare, non sostituire

❌ **NON concatenare task senza checkpoint**
- Esempio: Modifico A → Modifico B → Modifico C (tutto insieme) ❌
- Corretto: Modifico A → CHECKPOINT → Utente approva → Modifico B ✅

❌ **NON ignorare discrepanze tra analisi e screenshot**
- Se screenshot mostra 7 pagine ma trovo 2 file → **FERMARSI** ✅

---

## 📝 TEMPLATE DI COMUNICAZIONE

### Prima di iniziare un task:

```
Ho capito la richiesta. Prima di procedere, devo:

1. Esplorare completamente la struttura [specificare cosa]
2. Leggere i file rilevanti: [lista]
3. Verificare [cosa va verificato]

Userò il Task agent con Explore mode per mappare tutto.
Ti fornirò un report completo prima di toccare qualsiasi file.

Procedo con l'esplorazione?
```

### Dopo l'esplorazione:

```
✅ ESPLORAZIONE COMPLETATA

Ho trovato:
- [Lista completa di cosa esiste]
- [Struttura attuale]
- [File rilevanti]

Report completo:
[Report strutturato]

Piano d'azione:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Posso procedere con le modifiche?
```

### Dopo ogni task:

```
✅ TASK COMPLETATO: [Nome task]

Cosa ho fatto:
- [Azione 1]
- [Azione 2]

File modificati:
- path/to/file1.py (aggiunto X, modificato Y)
- path/to/file2.md (creato nuovo file)

Prossimi passi:
- [Step successivo]

Posso procedere?
```

---

## 🎯 GESTIONE TODO LIST

Claude DEVE usare TodoWrite per:

1. **Pianificare task complessi** (3+ step)
2. **Tracciare progresso** in tempo reale
3. **Un solo task in_progress** alla volta
4. **Completare immediatamente** dopo ogni step (no batch)
5. **Aggiornare prima di procedere** al prossimo

---

## 📚 DOCUMENTAZIONE DA CONSULTARE SEMPRE

Prima di iniziare qualsiasi task, Claude dovrebbe leggere:

1. **REGISTRO_PROGETTO.md** → Dove siamo, ultima attività, direzione
2. **SAL_PROGRESS.md** → Stato generale, filosofia progetto, obiettivi
3. **README.md** o file specifici per il task in questione

---

## 🔄 COMMIT E VERSIONING

### Quando fare commit:

- ✅ Solo quando l'utente lo richiede esplicitamente
- ✅ Dopo che l'utente ha approvato le modifiche
- ✅ Con messaggi chiari e descrittivi

### Branch di lavoro:

- ✅ Lavorare SEMPRE sul branch specificato dall'utente
- ✅ Non pushare mai su `main` senza permesso esplicito
- ✅ Verificare il branch attuale prima di ogni commit

---

## 💡 PRINCIPIO GUIDA

> **"Meglio chiedere 10 volte che sbagliare 1 volta"**

Il tempo speso in esplorazione e verifica è SEMPRE ben investito.
Distruggere lavoro esistente per fretta è INACCETTABILE.

---

## ✅ CHECKLIST PRE-MODIFICA

Prima di modificare QUALSIASI file, verificare:

- [ ] Ho esplorato la struttura completa?
- [ ] Ho letto tutti i file rilevanti?
- [ ] Ho capito come funziona attualmente?
- [ ] Ho verificato con screenshot/documentazione?
- [ ] Ho presentato un report completo all'utente?
- [ ] Ho ricevuto conferma esplicita per procedere?
- [ ] Ho pianificato i task con TodoWrite?
- [ ] So esattamente cosa modificare e perché?

**Se anche UNA SOLA risposta è NO → NON PROCEDERE**

---

## 📞 IN CASO DI DUBBIO

**SEMPRE:**
1. 🛑 Fermarsi
2. 🔍 Investigare meglio
3. 💬 Chiedere chiarimenti all'utente
4. ✅ Attendere conferma

**MAI:**
1. ❌ Assumere
2. ❌ Indovinare
3. ❌ Procedere "alla cieca"

---

**Questo protocollo è VINCOLANTE e deve essere rispettato in OGNI sessione di lavoro.**

---

*Versione 1.0 - Creato il 2026-01-14 dopo analisi errori ricorrenti*
