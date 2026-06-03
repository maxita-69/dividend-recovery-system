import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-recommendation-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span class="dc-badge" [ngClass]="badgeClass">
      {{ recommendation }}
    </span>
  `,
  styles: [``]
})
export class RecommendationBadgeComponent {
  @Input() recommendation: string = 'HOLD';

  get badgeClass(): string {
    switch (this.recommendation) {
      case 'STRONG_BUY': return 'dc-badge-strong-buy';
      case 'BUY': return 'dc-badge-buy';
      case 'HOLD': return 'dc-badge-hold';
      case 'SELL': return 'dc-badge-sell';
      case 'AVOID': return 'dc-badge-avoid';
      default: return 'dc-badge-hold';
    }
  }
}
