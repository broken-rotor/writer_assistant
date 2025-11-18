import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-collapsible-section',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule],
  templateUrl: './collapsible-section.component.html',
  styleUrl: './collapsible-section.component.scss'
})
export class CollapsibleSectionComponent {
  @Input() title = '';
  @Input() subtitle = '';
  @Input() icon = '';
  @Input() isExpanded = true;
  @Input() isCollapsible = true;
  @Input() showExpandedSummary = false;
  @Input() expandedSummary = '';
  @Input() disabled = false;
  
  @Output() toggleExpanded = new EventEmitter<boolean>();

  onToggle(): void {
    if (!this.isCollapsible || this.disabled) return;
    
    this.isExpanded = !this.isExpanded;
    this.toggleExpanded.emit(this.isExpanded);
  }
}
