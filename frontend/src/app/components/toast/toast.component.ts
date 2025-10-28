import { Component, OnInit, OnDestroy, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable, Subject } from 'rxjs';
import { ToastService, ToastMessage, ToastType } from '../../services/toast.service';

/**
 * Toast notification component
 */
@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './toast.component.html',
  styleUrl: './toast.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ToastComponent implements OnInit, OnDestroy {
  toasts$: Observable<ToastMessage[]>;
  private destroy$ = new Subject<void>();

  // Expose enum to template
  readonly ToastType = ToastType;

  constructor(private toastService: ToastService) {
    this.toasts$ = this.toastService.getToasts();
  }

  ngOnInit(): void {
    // Initialize toast component
    this.toasts$ = this.toastService.getToasts();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Dismiss a toast
   */
  dismissToast(toastId: string): void {
    this.toastService.dismiss(toastId);
  }

  /**
   * Execute a toast action
   */
  executeAction(action: any): void {
    if (action && typeof action.callback === 'function') {
      action.callback();
    }
  }

  /**
   * Get CSS classes for toast
   */
  getToastClasses(toast: ToastMessage): string[] {
    const classes = ['toast', `toast--${toast.type}`];
    
    if (!toast.visible) {
      classes.push('toast--hidden');
    }
    
    if (toast.actions && toast.actions.length > 0) {
      classes.push('toast--with-actions');
    }
    
    return classes;
  }

  /**
   * Get icon for toast type
   */
  getToastIcon(type: ToastType): string {
    switch (type) {
      case ToastType.SUCCESS:
        return '✅';
      case ToastType.ERROR:
        return '❌';
      case ToastType.WARNING:
        return '⚠️';
      case ToastType.INFO:
        return 'ℹ️';
      default:
        return 'ℹ️';
    }
  }

  /**
   * Get action button classes
   */
  getActionClasses(actionType: string): string[] {
    const classes = ['toast__action'];
    
    switch (actionType) {
      case 'primary':
        classes.push('toast__action--primary');
        break;
      case 'secondary':
        classes.push('toast__action--secondary');
        break;
      case 'danger':
        classes.push('toast__action--danger');
        break;
      default:
        classes.push('toast__action--default');
    }
    
    return classes;
  }

  /**
   * Track by function for toast list
   */
  trackByToastId(index: number, toast: ToastMessage): string {
    return toast.id;
  }
}
