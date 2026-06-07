import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dc-card">
      <div class="flex items-center justify-between mb-2">
        <span class="dc-kpi-label">{{ label }}</span>
        <div *ngIf="icon" class="w-8 h-8 rounded-lg bg-dc-accent/10 flex items-center justify-center">
          <span class="text-dc-accent text-sm">{{ icon }}</span>
        </div>
      </div>
      <div class="dc-kpi-value" [class.text-dc-accent]="isPositive" [class.text-dc-text]="!isPositive">
        {{ value }}
      </div>
      <div *ngIf="change !== undefined" class="mt-1">
        <span [class.dc-kpi-change-positive]="(change || 0) >= 0" [class.dc-kpi-change-negative]="(change || 0) < 0">
          {{ (change || 0) >= 0 ? '+' : '' }}{{ change | number:'1.2-2' }}%
        </span>
        <span class="text-dc-text-secondary text-xs ml-1">{{ changeLabel }}</span>
      </div>
      <div *ngIf="subtitle" class="text-dc-text-secondary text-xs mt-1">{{ subtitle }}</div>
    </div>
  `,
  styles: [``]
})
export class KpiCardComponent {
  @Input() label = '';
  @Input() value: string | number = '';
  @Input() change?: number;
  @Input() changeLabel = 'vs prev.';
  @Input() icon = '';
  @Input() isPositive = true;
  @Input() subtitle = '';
}
