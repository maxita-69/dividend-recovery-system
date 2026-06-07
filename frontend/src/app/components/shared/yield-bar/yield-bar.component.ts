import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-yield-bar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="w-full">
      <div class="flex justify-between text-xs mb-1">
        <span class="text-dc-text-secondary">Lordo: <span class="text-dc-accent font-medium">{{ gross | number:'1.2-2' }}%</span></span>
        <span class="text-dc-text-secondary">Netto: <span class="text-dc-secondary font-medium">{{ net | number:'1.2-2' }}%</span></span>
      </div>
      <div class="dc-progress-bar">
        <div class="dc-progress-bar-fill bg-dc-accent" [style.width.%]="grossWidth"></div>
      </div>
      <div class="dc-progress-bar mt-1">
        <div class="dc-progress-bar-fill bg-dc-secondary" [style.width.%]="netWidth"></div>
      </div>
    </div>
  `,
  styles: [``]
})
export class YieldBarComponent {
  @Input() gross = 0;
  @Input() net = 0;
  @Input() maxScale = 8;

  get grossWidth(): number {
    return Math.min(100, (this.gross / this.maxScale) * 100);
  }

  get netWidth(): number {
    return Math.min(100, (this.net / this.maxScale) * 100);
  }
}
