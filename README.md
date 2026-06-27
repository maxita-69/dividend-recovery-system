# Dividend Recovery System — Unified Frontend

A unified Angular frontend application that merges components from three distinct development branches into a single, cohesive trading dashboard for Borsa Italiana dividend capture and recovery analysis strategies.

---

## Overview

This project consolidates frontend code from three source branches:

| Branch | Description | Components Merged |
|--------|-------------|-------------------|
| `dividend-capture-trading` (B1) | Dividend capture trading dashboard with simulator, calendar, and ML predictions | 10 components + 4 services |
| `dividend-recovery-angular` (B2) | Recovery analysis tools with strategy comparison and pattern analysis | 6 page components + 1 service |
| `kimi-agent-progetto-trading-ml` (B3) | ML trading agent project (backend-focused; frontend was absorbed into B1/B2) | — |

The merged frontend provides a complete trading system UI covering dividend capture simulation, calendar tracking, ML-powered predictions, portfolio management, recovery analysis, strategy comparison, pattern detection, and database dashboards — all accessible from a unified sidebar navigation.

---

## Component Origin Mapping

| Component | Source Branch | Route |
|-----------|--------------|-------|
| `DashboardComponent` | dividend-capture-trading | `/dashboard` |
| `DividendCalendarComponent` | dividend-capture-trading | `/calendar`, `/stocks` |
| `PortfolioComponent` | dividend-capture-trading | `/portfolio` |
| `PredictionsComponent` | dividend-capture-trading | `/predictions` |
| `SimulatorComponent` | dividend-capture-trading | `/simulator` |
| `StockDetailComponent` | dividend-capture-trading | `/stocks/:ticker` |
| `CostBreakdownComponent` | dividend-capture-trading | (shared) |
| `KpiCardComponent` | dividend-capture-trading | (shared) |
| `RecommendationBadgeComponent` | dividend-capture-trading | (shared) |
| `YieldBarComponent` | dividend-capture-trading | (shared) |
| `HomeComponent` | dividend-recovery-angular | `/recovery` (redirected) |
| `RecoverySingleStockComponent` | dividend-recovery-angular | `/recovery-stock/:id` |
| `RecoveryAnalysisComponent` | dividend-recovery-angular | `/recovery` |
| `StrategyComparisonComponent` | dividend-recovery-angular | `/strategy` |
| `PatternAnalysisComponent` | dividend-recovery-angular | `/pattern` |
| `MasterDashboardComponent` | dividend-recovery-angular | `/master-dashboard` |
| `DatabaseDashboardComponent` | dividend-recovery-angular | `/database` |

### Shared Components (B1 — Reusable UI)

The following shared components from `dividend-capture-trading` are used across multiple pages:

- **`CostBreakdownComponent`** — Visual breakdown of commissions, Tobin tax, and withholding tax
- **`KpiCardComponent`** — Metric display card with value, label, and trend indicator
- **`RecommendationBadgeComponent`** — Styled badge for STRONG_BUY / BUY / HOLD / SELL / AVOID ratings
- **`YieldBarComponent`** — Horizontal bar chart for yield visualization with gross/net comparison

---

## Services

| Service | Source | Purpose |
|---------|--------|---------|
| `ApiService` | B1 (dividend-capture-trading) | HTTP client for dividend capture APIs — stocks, dividends, predictions, simulator, calendar, opportunities. Includes comprehensive mock data generators for offline development. |
| `ChartService` | B1 (dividend-capture-trading) | Chart.js configuration factory — provides themed chart configs (line, bar, doughnut, horizontal bar) with dark-theme color palette matching the B1 design system. |
| `DataService` | B1 (dividend-capture-trading) | Reactive state management using RxJS `BehaviorSubject`s — maintains stocks, dividends, predictions, opportunities, and portfolio positions with computed observables. |
| `DividendService` | B2 (dividend-recovery-angular) | HTTP client for recovery analysis APIs — stock lookup, dividend history, price data, strategy comparison, and dashboard summary. Uses `inject()` pattern (Angular 17+). |

---

## Prerequisites

- **Node.js** `18+`
- **npm** `9+`

---

## Setup Instructions

```bash
# Clone the repository
git clone <repo-url>
cd dividend-recovery-system
git checkout main-merged

# === Backend (FastAPI) ===
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
# API runs on http://localhost:8001
# Swagger UI: http://localhost:8001/docs

# === Frontend (new terminal) ===
cd frontend
npm install
npm run start
# Frontend runs on http://localhost:4200
```

The frontend is configured with a proxy (`proxy.conf.json`) that forwards `/api` requests to the backend at `http://localhost:8000` during development.

---

## Additional Dependencies

Angular Material was added from branch B2 (`dividend-recovery-angular`) to support Material Design components used in recovery analysis pages.

### Added Packages

| Package | Version |
|---------|---------|
| `@angular/material` | `^17.3.0` |
| `@angular/cdk` | `^17.3.0` |

### Configuration Changes

- **Prebuilt theme** added to `angular.json`:
  ```json
  "styles": [
    "node_modules/@angular/material/prebuilt-themes/indigo-pink.css",
    "src/styles.css"
  ]
  ```
- **Roboto font** and **Material Icons** added to `index.html`:
  ```html
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
  ```

These additions enable Angular Material components (cards, tables, buttons, datepickers, etc.) in B2 pages without breaking the existing B1 Tailwind-based styling.

---

## Available Routes

All routes are **lazy-loaded** for optimal code splitting.

| # | Route | Component | Description |
|---|-------|-----------|-------------|
| 1 | `/` → `/dashboard` | redirect | Default landing page |
| 2 | `/dashboard` | `DashboardComponent` | Main KPIs, opportunity feed, dividend calendar overview |
| 3 | `/stocks` | `DividendCalendarComponent` | Stock listing with dividend calendar view |
| 4 | `/stocks/:ticker` | `StockDetailComponent` | Individual stock detail with price charts and indicators |
| 5 | `/simulator` | `SimulatorComponent` | Dividend capture trade simulator with P&L calculation |
| 6 | `/predictions` | `PredictionsComponent` | ML model predictions for dividend events |
| 7 | `/calendar` | `DividendCalendarComponent` | Full dividend calendar by month |
| 8 | `/portfolio` | `PortfolioComponent` | Active and closed trade positions tracker |
| 9 | `/recovery` | `RecoveryAnalysisComponent` | Dividend recovery pattern analysis (B2) |
| 10 | `/strategy` | `StrategyComparisonComponent` | Side-by-side strategy comparison (B2) |
| 11 | `/pattern` | `PatternAnalysisComponent` | Historical recovery pattern detection (B2) |
| 12 | `/master-dashboard` | `MasterDashboardComponent` | Unified master control dashboard (B2) |
| 13 | `/database` | `DatabaseDashboardComponent` | Database status and management (B2) |
| 14 | `/recovery-stock/:id` | `RecoverySingleStockComponent` | Single-stock recovery deep-dive (B2) |
| — | `**` | → `/dashboard` | Wildcard redirect to dashboard |

---

## Architecture Notes

### Standalone Components

All components use Angular's **standalone component** pattern (no `NgModules`). Each component declares its own imports:

```typescript
@Component({
  standalone: true,
  imports: [CommonModule, RouterLink, ...],
  // ...
})
```

### Lazy-Loaded Routes

Every route in `app.routes.ts` uses `loadComponent` for automatic code splitting:

```typescript
{
  path: 'dashboard',
  loadComponent: () =>
    import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent),
}
```

### Dual Styling System

The merged frontend supports **two coexisting styling approaches**:

| Approach | Used By | Details |
|----------|---------|---------|
| **Tailwind CSS + Custom Dark Theme** | B1 components | Dark-themed utility classes (`bg-dc-bg`, `text-dc-text`, `dc-card`, etc.) defined in `styles.css` using `@layer components` |
| **Angular Material + SCSS** | B2 components | Material Design components with `indigo-pink` prebuilt theme; component-level `.scss` files |

Both systems work side-by-side without conflicts. B1 components use Tailwind utility classes; B2 components use Angular Material directives and SCSS styles.

### Application Configuration

The app uses `bootstrapApplication` with a centralized `ApplicationConfig`:

```typescript
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptorsFromDi()),
    provideAnimationsAsync(),        // Required for Angular Material
    provideCharts(withDefaultRegisterables()), // Chart.js via ng2-charts
  ],
};
```

### Unified Navigation

The `AppComponent` provides a single sidebar that includes navigation links for **both B1 and B2** routes, organized into two sections:

- **Dividend Capture** (B1): Dashboard, Simulator, ML Predictions, Dividend Calendar, Portfolio, Stock Detail
- **Recovery Analysis** (B2): Home, Master Dashboard, Recovery Analysis, Strategy Comparison, Pattern Analysis, Database, Single Stock

### Model Files

| File | Source | Purpose |
|------|--------|---------|
| `models/stock.model.ts` | B1 | Dividend capture models: `Stock`, `DividendEvent`, `MLPrediction`, `SimulationResult`, `Opportunity`, `PortfolioPosition`, plus mock data |
| `models/recovery-models.ts` | B2 | Recovery analysis models: `Stock`, `Dividend`, `PriceData`, `StrategyComparison`, `DashboardSummary` |
| `models/index.ts` | B2 | Barrel export for recovery models |

---

## Branch Merge Rules

> **Important:** Backend files were **NOT modified** during this merge.

The merge process only affected the `frontend/` directory. All backend code, database models, Python scripts, Streamlit dashboards, and configuration files in the repository root remain untouched from their original branches.

### What Was Merged

- All TypeScript components from B1 and B2
- All services and model files
- `app.routes.ts` — combined routes from both branches
- `app.component.ts` — unified sidebar with navigation for both sections
- `app.config.ts` — providers for routing, HTTP client, animations, and charts
- `package.json` — merged dependencies (Angular Material + CDK added from B2)
- `angular.json` — added Material prebuilt theme to styles array
- `index.html` — added Roboto font and Material Icons links
- `styles.css` — kept Tailwind base + B1 design system classes

### What Was Preserved

- Backend Python code (`backend/`, `src/`, `app/`)
- Streamlit dashboards (`dashboard/`, `app/Home.py`, `app/pages/`)
- Database layer (`src/database/`)
- Documentation (`DOCUMENTAZIONE/`)
- Configuration files (`.env`, `.gitignore`, etc.)

---

## Project Structure

```
dividend-recovery-system/
├── frontend/                          # Angular frontend (merged)
│   ├── src/
│   │   ├── app/
│   │   │   ├── app.component.ts       # Root layout with sidebar
│   │   │   ├── app.config.ts          # App-level providers
│   │   │   ├── app.routes.ts          # All 13+ routes (lazy-loaded)
│   │   │   ├── components/            # B1 components
│   │   │   │   ├── dashboard/
│   │   │   │   ├── dividend-calendar/
│   │   │   │   ├── portfolio/
│   │   │   │   ├── predictions/
│   │   │   │   ├── simulator/
│   │   │   │   ├── stock-detail/
│   │   │   │   └── shared/            # Reusable B1 components
│   │   │   │       ├── cost-breakdown/
│   │   │   │       ├── kpi-card/
│   │   │   │       ├── recommendation-badge/
│   │   │   │       └── yield-bar/
│   │   │   ├── pages/                 # B2 components
│   │   │   │   ├── home/
│   │   │   │   ├── recovery-analysis/
│   │   │   │   ├── single-stock/
│   │   │   │   ├── strategy-comparison/
│   │   │   │   ├── pattern-analysis/
│   │   │   │   ├── master-dashboard/
│   │   │   │   └── database-dashboard/
│   │   │   ├── services/
│   │   │   │   ├── api.service.ts     # B1 HTTP client + mocks
│   │   │   │   ├── chart.service.ts   # B1 Chart.js configs
│   │   │   │   ├── data.service.ts    # B1 state management
│   │   │   │   └── dividend.service.ts # B2 HTTP client
│   │   │   └── models/
│   │   │       ├── stock.model.ts     # B1 data models + mocks
│   │   │       ├── recovery-models.ts # B2 data models
│   │   │       └── index.ts           # B2 barrel export
│   │   ├── index.html                 # Fonts + Material Icons
│   │   ├── main.ts                    # Bootstrap entry point
│   │   └── styles.css                 # Tailwind + B1 design system
│   ├── angular.json                   # CLI config (Material theme added)
│   ├── package.json                   # Merged dependencies
│   ├── proxy.conf.json                # Dev proxy to localhost:8000
│   └── tailwind.config.js             # Tailwind CSS configuration
├── backend/                           # Python backend (unchanged)
├── src/                               # Python source modules (unchanged)
├── app/                               # Streamlit app (unchanged)
├── dashboard/                         # Streamlit dashboard (unchanged)
├── DOCUMENTAZIONE/                    # Project docs (unchanged)
└── README.md                          # This file
```

---

## Development Notes

- **Mock Mode**: `ApiService` has `useMocks = true` for frontend-only development. Set to `false` when the backend is running.
- **Proxy**: The development server proxies `/api` calls to `http://localhost:8000` via `proxy.conf.json`.
- **Charts**: Uses `ng2-charts` (Chart.js Angular wrapper) for all chart components.
- **Animations**: `provideAnimationsAsync()` enables Angular Material animations and is loaded asynchronously for better startup performance.
- **Currency**: All monetary values are in **EUR** (Borsa Italiana).
- **Language**: UI labels are primarily in **Italian**.

---

## License

Private — Internal Trading System
