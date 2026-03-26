# Integrazione Saxo Bank OpenAPI

## Panoramica

Il provider Saxo Bank è stato integrato nel sistema seguendo lo stesso pattern degli altri provider (FMP, Yahoo Finance).

## Funzionalità Supportate

### 1. Chart Service - Dati Storici OHLCV
- **Endpoint**: `/chart/v1/charts/{Uic}/{AssetType}/{Horizon}`
- **Dati**: Prezzi storici giornalieri (OHLCV)
- **Limiti**: Max 1200 punti dati per richiesta (~5 anni di dati giornalieri)
- **Horizon**: D1 (daily) = 1440 minuti

### 2. Corporate Actions - Dividendi
- **Endpoint**: `/ref/v1/corporateactions/`
- **Dati**: Dividendi, split e altre azioni societarie
- **Nota**: Richiede licenze specifiche per alcuni mercati

### 3. Reference Data - Informazioni Strumenti
- **Endpoint**: `/ref/v1/instruments/{AssetType}/{Uic}`
- **Ricerca**: `/ref/v1/instruments/search/{AssetType}`
- **Dati**: Profilo strumenti, UIC, dettagli mercato

## Configurazione

Aggiungi le seguenti variabili d'ambiente al tuo file `.env`:

```bash
# Autenticazione (uno dei due metodi)
SAXO_TOKEN=<tuo_bearer_token>
# OPPURE
SAXO_CLIENT_ID=<tuo_client_id>
SAXO_CLIENT_SECRET=<tuo_client_secret>

# Opzionali
SAXO_BASE_URL=https://api.saxobank.com
SAXO_CUSTOMER_KEY=<tuo_customer_key>
```

## Utilizzo

### Tramite Provider Manager

```python
from providers import get_provider

# Usa SAXO come provider
provider = get_provider('SAXO')

# Scarica prezzi storici
prices = provider.fetch_prices('AAPL', start_date='2020-01-01', end_date='2023-12-31')

# Scarica dividendi
dividends = provider.fetch_dividends('AAPL')

# Prezzo corrente
price = provider.get_price('AAPL')

# Profilo strumento
profile = provider.get_profile('AAPL')

# Ricerca simboli
results = provider.search_symbol('Apple')
```

### Uso Diretto

```python
from providers.saxo_provider import SaxoProvider

provider = SaxoProvider()
prices = provider.fetch_prices('ENEL.MI', asset_type='Stock')
```

## Note Importanti

### 1. UIC (Unique Instrument Code)
Saxo utilizza codici UIC invece dei ticker symbol. Il provider gestisce automaticamente:
- Ricerca del simbolo per ottenere l'UIC
- Cache delle conversioni simbolo -> UIC
- Fallback su UIC numerico se fornito direttamente

### 2. Formati Data
- **Input**: YYYY-MM-DD (es. '2023-01-01')
- **Output**: YYYY-MM-DD nei dizionari restituiti

### 3. Limitazioni API
- Max 1200 candle per richiesta Chart Service
- Per periodi più lunghi, implementare pagination (da sviluppare)
- Corporate Actions richiede licenze di mercato appropriate

### 4. Asset Types Supportati
- `Stock` (default)
- `ETF`
- `Index`
- `Future`
- `Option`
- `Bond`
- Altri supportati da Saxo

## Differenze con Altri Provider

| Funzionalità | FMP | Yahoo | Saxo |
|-------------|-----|-------|------|
| Dati storici | ✅ | ✅ | ✅ (max 1200/sample) |
| Dividendi | ⚠️ (limitato) | ✅ | ✅ (con licenza) |
| Tempo reale | ✅ | ⚠️ | ✅ (con feed) |
| Ricerca simboli | ✅ | ✅ | ✅ |
| Profilo azienda | ✅ | ✅ | ✅ (dati strumentali) |
| Autenticazione | API Key | Nessuna | OAuth2/Bearer |

## Troubleshooting

### Errore: "Impossibile risolvere UIC per simbolo"
- Verifica il formato del simbolo (es. 'ENEL.MI' per Milano)
- Prova a usare direttamente l'UIC numerico se noto
- Controlla che l'asset_type sia corretto

### Errore: "Corporate Actions non disponibile"
- Verifica di avere le licenze di mercato appropriate
- Alcuni mercati richiedono subscription aggiuntive

### Errore: "SAXO_TOKEN non trovato"
- Aggiungi SAXO_TOKEN al file .env
- Oppure usa SAXO_CLIENT_ID + SAXO_CLIENT_SECRET

## Risorse

- [Documentazione Ufficiale Saxo OpenAPI](https://www.developer.saxo/openapi/learn)
- [Chart Service Documentation](https://www.developer.saxo/openapi/endpoints/chart)
- [Corporate Actions Documentation](https://www.developer.saxo/openapi/endpoints/ref)
- [Reference Data Documentation](https://www.developer.saxo/openapi/endpoints/ref)

## Prossimi Miglioramenti

- [ ] Implementare pagination automatica per periodi lunghi
- [ ] Aggiungere supporto streaming real-time
- [ ] Implementare refresh automatico token OAuth2
- [ ] Aggiungere test unitari specifici
- [ ] Supporto per più asset type simultaneamente
