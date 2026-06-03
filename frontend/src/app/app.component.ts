import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="min-h-screen bg-dc-bg text-dc-text flex">
      <!-- Sidebar -->
      <aside
        class="fixed inset-y-0 left-0 z-40 w-64 bg-dc-card border-r border-dc-border transform transition-transform duration-300 lg:translate-x-0 lg:static"
        [class.-translate-x-full]="!sidebarOpen"
        [class.translate-x-0]="sidebarOpen"
      >
        <div class="h-full flex flex-col">
          <!-- Logo -->
          <div class="px-6 py-5 border-b border-dc-border">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-xl bg-dc-accent/15 flex items-center justify-center">
                <svg class="w-5 h-5 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                </svg>
              </div>
              <div>
                <h1 class="font-bold text-sm tracking-tight">Dividend Capture</h1>
                <p class="text-[10px] text-dc-text-secondary -mt-0.5">Trading System</p>
              </div>
            </div>
          </div>

          <!-- Nav -->
          <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            <!-- B1 Section: Dividend Capture -->
            <div class="dc-section-title">Dividend Capture</div>

            <a routerLink="/dashboard" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
              </svg>
              Dashboard
            </a>
            <a routerLink="/simulator" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
              </svg>
              Simulatore
            </a>
            <a routerLink="/predictions" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
              Predizioni ML
            </a>
            <a routerLink="/calendar" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
              Calendario Dividendi
            </a>
            <a routerLink="/portfolio" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
              </svg>
              Portafoglio
            </a>
            <a routerLink="/stocks/AAPL" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
              Dettaglio Stock
            </a>

            <!-- Divider -->
            <div class="my-3 border-t border-dc-border"></div>

            <!-- B2 Section: Recovery Analysis -->
            <div class="dc-section-title">Recovery Analysis</div>

            <a routerLink="/recovery" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              Home
            </a>
            <a routerLink="/master-dashboard" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
              </svg>
              Master Dashboard
            </a>
            <a routerLink="/recovery" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
              </svg>
              Analisi Recovery
            </a>
            <a routerLink="/strategy" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
              Confronto Strategie
            </a>
            <a routerLink="/pattern" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"/>
              </svg>
              Pattern Analysis
            </a>
            <a routerLink="/database" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/>
              </svg>
              Database
            </a>
            <a routerLink="/recovery-stock/AAPL" routerLinkActive="active" class="dc-nav-link" (click)="closeSidebar()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
              Recovery Single Stock
            </a>
          </nav>

          <!-- Footer -->
          <div class="px-4 py-3 border-t border-dc-border">
            <div class="text-[10px] text-dc-text-secondary text-center">
              Borsa Italiana Dividend Capture v2.0
            </div>
          </div>
        </div>
      </aside>

      <!-- Mobile overlay -->
      <div
        *ngIf="sidebarOpen"
        class="fixed inset-0 bg-black/50 z-30 lg:hidden"
        (click)="sidebarOpen = false"
      ></div>

      <!-- Main Content -->
      <div class="flex-1 flex flex-col min-w-0">
        <!-- Topbar -->
        <header class="sticky top-0 z-20 bg-dc-card/80 backdrop-blur-md border-b border-dc-border">
          <div class="flex items-center justify-between px-4 lg:px-8 py-3">
            <div class="flex items-center gap-3">
              <button
                (click)="sidebarOpen = !sidebarOpen"
                class="lg:hidden p-2 rounded-lg hover:bg-dc-border/50 text-dc-text-secondary"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                </svg>
              </button>
              <div class="flex items-center gap-2 text-dc-text-secondary text-sm">
                <span>Borsa Italiana</span>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
                <span class="text-dc-text font-medium">{{ pageTitle }}</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dc-bg border border-dc-border">
                <div class="w-2 h-2 rounded-full bg-dc-accent animate-pulse"></div>
                <span class="text-xs text-dc-text-secondary">Mercato Aperto</span>
              </div>
              <div class="w-8 h-8 rounded-full bg-dc-primary/30 flex items-center justify-center border border-dc-accent/30">
                <svg class="w-4 h-4 text-dc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
              </div>
            </div>
          </div>
        </header>

        <!-- Page Content -->
        <main class="flex-1 p-4 lg:p-8 overflow-y-auto">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
  `]
})
export class AppComponent {
  sidebarOpen = false;
  pageTitle = 'Dashboard';

  closeSidebar(): void {
    this.sidebarOpen = false;
  }
}
