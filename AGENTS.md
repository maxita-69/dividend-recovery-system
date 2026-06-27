# AGENTS.md — Dividend Recovery Trading System

> This file is intended for AI coding agents. It describes the project architecture, build process, conventions, and critical context needed to work effectively in this codebase.

---

## Project Overview

The **Dividend Recovery Trading System** is a quantitative analysis platform for studying post-dividend price recovery patterns on Borsa Italiana (and other markets). It helps identify whether high-quality dividend stocks tend to recover their price after the ex-dividend date within a 5–30 day window, enabling data-driven trading strategies.

The project has **three concurrent frontend/runtime layers**:
1. **Python backend + Streamlit dashboards** — primary analysis engine and UI
2. **Angular frontend** — unified trading dashboard (merged from three branches: dividend-capture-trading/B1, dividend-recovery-angular/B2, with ML-agent backend assets from kimi-agent-progetto-trading-ml/B3)
3. **SQLite database** — local data store for prices, dividends, and audit logs

Key business concepts:
- **Dividend capture / recovery** — analyzing price behavior around ex-dates
- **Trading cost modeling** — Fineco-specific commissions, Tobin tax, overnight financing
- **Pattern analysis** — correlating pre-dividend price/volume behavior with post-dividend recovery using cosine similarity
- **Dividend prediction** — forecasting next dividends from historical interval patterns

---

## Technology Stack

### Backend / Data Layer (Python)
- **Python** 3.10+
- **pandas**, **numpy** — data manipulation
- **yfinance**, **requests**, **beautifulsoup4** — financial data acquisition
- **SQLAlchemy** 2.0+ — ORM and database access (SQLite)
- **plotly**, **matplotlib** — visualization
- **Streamlit** 1.28+ — interactive dashboards
- **streamlit-authenticator** 0.4.1 — login system for Streamlit apps
- **pytest**, **pytest-cov** — testing
- **pydantic** — data validation
- **scikit-learn**, **statsmodels** — ML and statistical analysis
- **ib-insync** — Interactive Brokers API integration
- **schedule** — task scheduling for automated data updates
- **python-json-logger**, **python-dateutil**, **typing-extensions** — logging and date/type utilities
- **tabulate** — table formatting for calendar displays
- **eodhd** — EOD Historical Data API client
- **python-dotenv**, **pyyaml** — configuration management

### Frontend (Angular)
- **Angular** 17.3+ with standalone components (no NgModules)
- **Angular Material** 17.3 — Material Design components for B2 pages
- **Tailwind CSS** 3.4 — utility-first styling for B1 pages
- **Chart.js** 4.4+ with **ng2-charts** — charts
- **RxJS** — reactive state management
- **TypeScript** 5.3+

### Data Providers
- **Financial Modeling Prep (FMP)** — primary provider for prices and dividends
- **Yahoo Finance** — fallback provider via `yfinance`
- **Interactive Brokers (IBKR)** — direct broker data feed
- **EOD Historical Data** — supplemental provider

### Database
- **SQLite** (`data/dividend_recovery.db`, `data/dividend_recovery_ib.db`)
- SQLAlchemy ORM with declarative base models

---

## Project Structure

```
dividend-recovery-system/
├── app/                              # Streamlit multi-page app (primary UI)
│   ├── Home.py                       # Main dashboard entry point
│   ├── auth.py                       # streamlit-authenticator login/logout
│   └── pages/
│       ├── 1_Single_Stock.py         # Single stock charts
│       ├── 2_Recovery_Analysis.py    # Recovery statistics
│       ├── 3_Strategy_Comparison.py  # Strategy backtesting
│       ├── 4_Pattern_Analysis.py     # Predictive pattern analysis
│       ├── 5_Master_Dashboard.py     # Unified control dashboard
│       ├── 6_Download_Data.py        # Data download UI
│       └── 7_Database_Dashboard.py   # DB management UI
│
├── api/                              # FastAPI backend
│   ├── main.py
│   ├── routers/
│   └── services/
│
├── frontend/                         # Angular unified frontend
│   ├── src/app/
│   │   ├── app.component.ts          # Root layout with sidebar
│   │   ├── app.config.ts             # Application providers
│   │   ├── app.routes.ts             # Lazy-loaded routes (13+ routes)
│   │   ├── components/               # B1 components (dividend-capture)
│   │   │   ├── dashboard/
│   │   │   ├── simulator/
│   │   │   ├── predictions/
│   │   │   ├── portfolio/
│   │   │   ├── dividend-calendar/
│   │   │   ├── stock-detail/
│   │   │   └── shared/               # Reusable UI
│   │   │       ├── cost-breakdown/
│   │   │       ├── kpi-card/
│   │   │       ├── recommendation-badge/
│   │   │       └── yield-bar/
│   │   ├── pages/                    # B2 components (recovery-analysis)
│   │   │   ├── home/                 # B2 landing page (redirected)
│   │   │   ├── recovery-analysis/
│   │   │   ├── strategy-comparison/
│   │   │   ├── pattern-analysis/
│   │   │   ├── master-dashboard/
│   │   │   ├── database-dashboard/
│   │   │   └── single-stock/
│   │   ├── services/                 # HTTP clients and state
│   │   │   ├── api.service.ts        # B1 API + comprehensive mocks
│   │   │   ├── chart.service.ts      # Chart.js config factory
│   │   │   ├── data.service.ts       # RxJS BehaviorSubject state
│   │   │   └── dividend.service.ts   # B2 recovery analysis API
│   │   └── models/
│   │       ├── stock.model.ts        # B1 models + mock data
│   │       └── recovery-models.ts    # B2 models
│   ├── angular.json
│   ├── package.json
│   ├── proxy.conf.json               # Dev proxy → localhost:8000
│   └── tailwind.config.js
│
├── src/                              # Core Python library
│   ├── database/
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   ├── database.py               # Session management, helpers
│   │   ├── download_stock_data_hybrid.py # Active hybrid downloader (Yahoo + FMP)
│   │   ├── download_data_ib.py       # Interactive Brokers downloader
│   │   ├── diagnose_ib_connection.py # IB connection diagnostics
│   │   └── test_*.py                 # Connection/test scripts (IB, USA, gateway)
│   ├── utils/
│   │   ├── recovery_analysis.py      # Core recovery detection algorithm
│   │   ├── pattern_analysis.py       # Pre/post dividend correlation
│   │   ├── validation.py             # Data quality checks
│   │   └── logging_config.py         # Structured JSON logging
│   ├── dividend_predictor.py         # Dividend prediction from history
│   ├── fetch_dividends.py            # Simple dividend fetcher
│   └── fetch_prices.py               # Simple price fetcher
│
├── providers/                        # Pluggable data provider pattern
│   ├── base_provider.py              # Abstract base class
│   ├── fmp_provider.py               # FMP implementation
│   ├── yahoo_provider.py             # Yahoo Finance implementation
│   └── provider_manager.py           # Provider switching
│
├── dividendi/                        # IBKR dividend-specific scripts
│   ├── dividend_calendar.py
│   ├── debug_all.py
│   ├── debug_dividend.py
│   ├── get_dividends_ibkr.py
│   ├── get_dividends_ibkr_v2.py
│   ├── ibkr_dividend_downloader.py
│   └── ibkr_dividend_parser.py
│
├── scripts/
│   ├── setup_db.py                   # Initialize SQLite schema
│   └── download_mib30.py             # Download FTSE MIB 30 constituents
│
├── tests/                            # pytest test suite
│   ├── test_recovery_analysis.py
│   ├── test_validation.py
│   └── test_pattern_analysis.py
│
├── data/                             # SQLite databases (commit to git for Streamlit Cloud)
│   ├── dividend_recovery.db
│   └── dividend_recovery_ib.db
│
├── logs/                             # Runtime logs (gitignored)
│
├── config.py                         # Centralized singleton configuration
├── requirements.txt                  # Python dependencies
└── .streamlit/config.toml            # Streamlit server/UI config
```

---

## Build and Run Commands

### Python Backend / Streamlit

```bash
# Setup virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/setup_db.py

# Run primary Streamlit app (analysis dashboard)
streamlit run app/Home.py
# Runs on http://localhost:8501

# Run FastAPI backend (porta 8001)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

# Run tests
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

### Angular Frontend

```bash
cd frontend

# Install dependencies
npm install

# Development server (proxies /api to localhost:8000)
npm run start
# Runs on http://localhost:4200

# Production build
npm run build

# Run Angular unit tests (Karma + Jasmine)
npm run test
```

> **Note:** There is no committed backend API server at `localhost:8000` in this repository. The Angular frontend's `ApiService` defaults to `useMocks = true` for frontend-only development. When a backend is running, set `useMocks = false` in `api.service.ts`.

---

## Code Style Guidelines

### Python
- **Docstrings in Italian** — the project originated with Italian documentation; maintain consistency.
- Use `snake_case` for functions and variables, `PascalCase` for classes.
- Prefer type hints for function signatures.
- Use `pathlib.Path` for filesystem paths.
- Import order: stdlib → third-party → local (`sys.path.insert` is used for local imports in Streamlit scripts).
- Do not hardcode values — use `config.py` singleton (`Config` class) for all parameters.
- Logging: use `logging_config.get_logger(__name__)` for structured JSON logging.

### Angular / TypeScript
- **Standalone components only** — no `NgModules`. Each component declares its own `imports`.
- Use lazy-loaded routes with `loadComponent` for code splitting.
- Two styling systems coexist:
  - **B1 components** (dividend-capture): Tailwind CSS utility classes (`bg-dc-bg`, `dc-card`, etc.)
  - **B2 components** (recovery-analysis): Angular Material directives + SCSS
- Do not mix Tailwind and Material in the same component without care.
- Services use standard DI; `DividendService` uses `inject()` pattern (Angular 17+).

---

## Testing Instructions

### Python Tests (pytest)

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_recovery_analysis.py -v

# Specific test class/method
pytest tests/test_recovery_analysis.py::TestFindRecovery::test_immediate_recovery -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

Test structure:
- `test_recovery_analysis.py` — recovery detection algorithm, statistics, historical analysis
- `test_validation.py` — price data, dividend data, and input validation
- `test_pattern_analysis.py` — feature extraction, correlation, similarity

Current coverage: ~50 tests covering recovery detection, edge cases, statistics, validation, and error handling.

### Angular Tests
- Standard Angular CLI Karma + Jasmine setup.
- Run with `npm run test` inside `frontend/`.
- No custom test utilities; use Angular testing utilities directly.

---

## Data Architecture

### Database Schema (SQLite)

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `stocks` | `ticker` (unique), `name`, `market`, `sector`, `currency`, `created_at`, `updated_at` | Instrument master data |
| `dividends` | `stock_id` (FK), `ex_date`, `amount`, `payment_date`, `record_date`, `currency`, `dividend_type`, `status`, `confidence`, `prediction_source`, `created_at` | Dividend events (historical + predicted) |
| `price_data` | `stock_id` (FK), `date`, `open`, `high`, `low`, `close`, `volume`, `adjusted_close` | OHLCV time series |
| `data_collection_logs` | `timestamp`, `source`, `operation`, `stock_ticker`, `status`, `records_processed`, `message` | Audit trail for data operations |

### Configuration (`config.py`)

The `Config` singleton manages all tunable parameters:
- `TradingCosts` — Fineco commission (0.19%, min €2.95, max €19), Tobin tax (0.1%), overnight financing (Euribor + 7.99%)
- `AnalysisConfig` — max_recovery_days (30), recovery_threshold (1.0), evolution windows
- `PatternAnalysisConfig` — lookback_days (40), recovery_days (15), similarity_threshold (0.8)
- `DataCollectionConfig` — download delays, retries, validation flags
- `StreamlitConfig` — UI defaults, chart settings, caching TTL

Environment variables can override most values (see `_load_from_environment`).

### Data Providers

The `providers/` package implements a simple pluggable pattern:
- `BaseProvider` defines `fetch_prices(symbol)` and `fetch_dividends(symbol)`
- `FMPProvider` uses Financial Modeling Prep API (`FMP_API_KEY` from `.env`)
- `YahooProvider` uses `yfinance`
- `ProviderManager` switches between them based on `DATA_PROVIDER` env var

The `src/database/` directory contains multiple download scripts that use these providers or direct APIs. The hybrid downloader (`download_stock_data_hybrid.py`) falls back between providers.

---

## Security Considerations

- **API keys** are stored in `.env` (sensitive file — not readable by agents). Required keys: `FMP_API_KEY`.
- **Authentication** for Streamlit apps uses `streamlit-authenticator` with bcrypt-hashed passwords stored in Streamlit secrets (`.streamlit/secrets.toml` locally, or Streamlit Cloud Secrets in production).
- **No automatic trading execution** — this is an analysis system only. It provides scoring and recommendations but does not place orders.
- **Database files** in `data/` are committed to Git so Streamlit Cloud can access them. Do not commit real trading account credentials or personal data.
- The `.env` file and `.streamlit/secrets.toml` are excluded by `.gitignore`.

---

## Deployment Notes

### Streamlit Cloud (Primary Deployment)
- Entry point: `app/Home.py`
- Repository must include `data/dividend_recovery.db` (ensure `.gitignore` does not exclude `*.db`)
- Configure secrets in Streamlit Cloud dashboard (see `DOCUMENTAZIONE/STREAMLIT_SECRETS_SETUP.md`)
- Pushes to the connected branch trigger automatic redeployment

### Angular Frontend
- The merged frontend is designed for local development or static hosting.
- Development proxy (`proxy.conf.json`) forwards `/api` to `http://localhost:8000`.
- No production backend API is included in this repository.

### Database Migration
- Use `scripts/setup_db.py` to create schema on a fresh environment.
- Use `migrate_dividend_prediction.py` to migrate existing databases when the schema changes.

---

## Development Conventions

### Streamlit Page Naming
Pages in `app/pages/` use numbered prefixes to control sidebar order:
```
1_Single_Stock.py
2_Recovery_Analysis.py
3_Strategy_Comparison.py
...
```

### Currency and Localization
- **Currency**: EUR for Borsa Italiana instruments.
- **UI Labels**: Primarily Italian in Streamlit apps and Python docstrings.
- **Code Comments**: Italian in Python, English in Angular.

### Mock Mode
The Angular `ApiService` has a `useMocks` flag. Set to `true` for frontend-only development (default). Set to `false` when a backend is running at `localhost:8000`.

### Logging
Use the project's structured logger:
```python
from utils.logging_config import get_logger
logger = get_logger(__name__)
logger.info("message", extra={"ticker": "ENEL.MI"})
```

### Adding New Tests
1. Create `tests/test_<module>.py`
2. Add `sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))` at the top
3. Write test classes/methods with descriptive names starting with `test_`
4. Run `pytest tests/test_<module>.py -v` to verify

---

## Known Issues / Reality Check

A few things to keep in mind when navigating this codebase:

- **`frontend/README.md` references a `backend/` folder** that does not exist in the repository root. The Python backend logic is distributed across `api/`, `src/`, `app/`, `providers/`, `dividendi/`, `script/`, and the root-level Python scripts.

- **FastAPI backend runs on `localhost:8001`** (port 8000 is used by `trading-brain`). The Angular dev proxy still points to `localhost:8000`; update `frontend/proxy.conf.json` when connecting to the real backend.

- **`src/data_providers/` exists but is not the active provider package.** It currently contains only a `.env` file. The pluggable provider implementation lives in `providers/` (`base_provider.py`, `fmp_provider.py`, `yahoo_provider.py`, `provider_manager.py`).

- **Several root-level scripts are development/verification tools**, not part of the main runtime: `quick_test_fmp.py`, `test_fmp_complete.py`, `test_yahoo_download.py`, `standalone_fmp_test.py`, `analizza_db.py`, `create_sample_data.py`, etc. Check their contents before assuming they are production pipelines.

- **Database files in `data/` are tracked by Git** (`.gitignore` does not exclude `*.db`) so that Streamlit Cloud can access them. Avoid committing large or sensitive data exports.

---

## Important Files for Agents

| File | Why it matters |
|------|----------------|
| `config.py` | All tunable parameters, trading costs, DB path |
| `src/database/models.py` | SQLAlchemy schema — reference before any DB change |
| `src/utils/recovery_analysis.py` | Core recovery algorithm used across the system |
| `src/utils/validation.py` | Data quality rules — changes affect all ingest pipelines |
| `app/auth.py` | Authentication logic for all Streamlit pages |
| `requirements.txt` | Python deps — keep in sync with any new package usage |
| `frontend/src/app/app.routes.ts` | Angular routing — add new routes here |
| `frontend/src/app/services/api.service.ts` | Backend contract + mocks |

---

*Last updated: 2026-06-14*
