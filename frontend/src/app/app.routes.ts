import { Routes } from '@angular/router';

export const routes: Routes = [
  // B1 Routes (dividend-capture-trading)
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./components/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'stocks',
    loadComponent: () =>
      import('./components/dividend-calendar/dividend-calendar.component').then((m) => m.DividendCalendarComponent),
  },
  {
    path: 'stocks/:ticker',
    loadComponent: () =>
      import('./components/stock-detail/stock-detail.component').then((m) => m.StockDetailComponent),
  },
  {
    path: 'simulator',
    loadComponent: () =>
      import('./components/simulator/simulator.component').then((m) => m.SimulatorComponent),
  },
  {
    path: 'predictions',
    loadComponent: () =>
      import('./components/predictions/predictions.component').then((m) => m.PredictionsComponent),
  },
  {
    path: 'calendar',
    loadComponent: () =>
      import('./components/dividend-calendar/dividend-calendar.component').then((m) => m.DividendCalendarComponent),
  },
  {
    path: 'portfolio',
    loadComponent: () =>
      import('./components/portfolio/portfolio.component').then((m) => m.PortfolioComponent),
  },
  // B2 Routes (dividend-recovery-angular)
  {
    path: 'recovery',
    loadComponent: () =>
      import('./pages/recovery-analysis/recovery-analysis.component').then((m) => m.RecoveryAnalysisComponent),
  },
  {
    path: 'strategy',
    loadComponent: () =>
      import('./pages/strategy-comparison/strategy-comparison.component').then((m) => m.StrategyComparisonComponent),
  },
  {
    path: 'pattern',
    loadComponent: () =>
      import('./pages/pattern-analysis/pattern-analysis.component').then((m) => m.PatternAnalysisComponent),
  },
  {
    path: 'master-dashboard',
    loadComponent: () =>
      import('./pages/master-dashboard/master-dashboard.component').then((m) => m.MasterDashboardComponent),
  },
  {
    path: 'database',
    loadComponent: () =>
      import('./pages/database-dashboard/database-dashboard.component').then((m) => m.DatabaseDashboardComponent),
  },
  {
    path: 'recovery-stock/:id',
    loadComponent: () =>
      import('./pages/single-stock/recovery-single-stock.component').then((m) => m.RecoverySingleStockComponent),
  },
  { path: '**', redirectTo: '/dashboard' },
];
