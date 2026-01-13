# 🧪 TEST FINNHUB API - Istruzioni

## 📋 Scopo

Questo script testa l'API di Finnhub per verificare se supporta correttamente i **titoli italiani** e quali dati fornisce.

## ⚙️ Prerequisiti

```bash
pip install requests
```

## 🚀 Come Eseguire il Test

### 1. Scarica o fai pull del branch

```bash
git checkout claude/sync-main-branch-Y0MDv
git pull origin claude/sync-main-branch-Y0MDv
```

### 2. Esegui lo script SUL TUO PC (non in sandbox)

```bash
python test_finnhub.py
```

### 3. Analizza i risultati

Lo script testerà per ogni ticker:
- ✅ **Profilo azienda** (nome, exchange, paese, valuta)
- ✅ **Quote corrente** (prezzo realtime)
- ✅ **Prezzi storici** (OHLCV - Open, High, Low, Close, Volume)
- ✅ **Dividendi storici** (dal 2023 a oggi)

## 📊 Output Atteso

Al termine vedrai un **RIEPILOGO FINALE** come questo:

```
======================================================================
                         RIEPILOGO FINALE
======================================================================

📊 VALUTAZIONE FINNHUB PER TITOLI ITALIANI:

✅ = Dati disponibili e funzionanti
❌ = Dati non disponibili o errori

----------------------------------------------------------------------

ENI.MI:
  • Profilo azienda : ✅
  • Quote corrente  : ✅
  • Prezzi storici  : ✅
  • Dividendi       : ✅

ENEL.MI:
  • Profilo azienda : ✅
  • Quote corrente  : ✅
  • Prezzi storici  : ✅
  • Dividendi       : ❌  <-- Esempio se non ci sono dividendi
```

## 🎯 Personalizzazione

Puoi modificare la lista dei ticker da testare aprendo `test_finnhub.py` e modificando:

```python
TEST_TICKERS = [
    "ENI.MI",      # Eni SpA
    "ENEL.MI",     # Enel SpA
    "UCG.MI",      # UniCredit
    "ISP.MI",      # Intesa Sanpaolo
    # Aggiungi i tuoi ticker qui
]
```

## 📝 Decisioni da Prendere

Dopo aver eseguito il test:

### ✅ SE TUTTI I DATI SONO DISPONIBILI
→ **Procedi con l'integrazione di Finnhub** nel sistema

### ⚠️ SE MANCANO ALCUNI DATI (es. dividendi)
→ **Considera strategia ibrida**:
   - Yahoo Finance per dividendi
   - Finnhub per prezzi

### ❌ SE NON FUNZIONA O DATI INCOMPLETI
→ **Mantieni sistema attuale** (Yahoo Finance per titoli italiani)

## 🔍 Cosa Verificare

1. **Dividendi**: Finnhub restituisce l'array completo?
2. **Prezzi**: I dati storici sono completi e corretti?
3. **Rate limiting**: Con piano gratuito hai 60 chiamate/minuto - è sufficiente?
4. **Qualità dati**: I valori corrispondono a quelli ufficiali?

## 💬 Prossimi Passi

Una volta completato il test:
1. Condividi i risultati
2. Decideremo insieme se:
   - ✅ Integrare Finnhub come provider principale
   - ✅ Usarlo come fallback
   - ✅ Combinarlo in strategia multi-provider
   - ❌ Non usarlo

---

**NOTA**: Questo test NON modifica il database né il sistema esistente. È solo un test isolato.
