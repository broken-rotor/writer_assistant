import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, timer } from 'rxjs';
import { TOAST_CONFIG, RecoveryAction } from '../constants/token-limits.constants';

/**
 * Toast message types
 */
export enum ToastType {
  SUCCESS = 'success',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

/**
 * Toast message interface
 */
export interface ToastMessage {
  /** Unique identifier for the toast */
  id: string;
  /** Type of toast message */
  type: ToastType;
  /** Main message text */
  message: string;
  /** Optional detailed description */
  description?: string;
  /** Duration in milliseconds (0 for persistent) */
  duration: number;
  /** Whether the toast can be dismissed */
  dismissible: boolean;
  /** Optional action buttons */
  actions?: ToastAction[];
  /** Timestamp when toast was created */
  timestamp: Date;
  /** Whether the toast is currently visible */
  visible: boolean;
}

/**
 * Toast action button interface
 */
export interface ToastAction {
  /** Action identifier */
  id: string;
  /** Button label */
  label: string;
  /** Action type for styling */
  type: 'primary' | 'secondary' | 'danger';
  /** Callback function when action is clicked */
  callback: () => void;
}

/**
 * Service for managing toast notifications
 */
@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private toasts$ = new BehaviorSubject<ToastMessage[]>([]);
  private nextId = 1;

  /**
   * Get observable of current toasts
   */
  getToasts(): Observable<ToastMessage[]> {
    return this.toasts$.asObservable();
  }

  /**
   * Generic show method for backward compatibility
   */
  show(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info'): string {
    switch (type) {
      case 'success':
        return this.showSuccess(message);
      case 'error':
        return this.showError(message);
      case 'warning':
        return this.showWarning(message);
      case 'info':
      default:
        return this.showInfo(message);
    }
  }

  /**
   * Show a success toast
   */
  showSuccess(
    message: string, 
    description?: string, 
    actions?: ToastAction[]
  ): string {
    return this.addToast({
      type: ToastType.SUCCESS,
      message,
      description,
      duration: TOAST_CONFIG.successDuration,
      actions
    });
  }

  /**
   * Show an error toast
   */
  showError(
    message: string, 
    description?: string, 
    actions?: ToastAction[]
  ): string {
    return this.addToast({
      type: ToastType.ERROR,
      message,
      description,
      duration: TOAST_CONFIG.errorDuration,
      actions
    });
  }

  /**
   * Show a warning toast
   */
  showWarning(
    message: string, 
    description?: string, 
    actions?: ToastAction[]
  ): string {
    return this.addToast({
      type: ToastType.WARNING,
      message,
      description,
      duration: TOAST_CONFIG.defaultDuration,
      actions
    });
  }

  /**
   * Show an info toast
   */
  showInfo(
    message: string, 
    description?: string, 
    actions?: ToastAction[]
  ): string {
    return this.addToast({
      type: ToastType.INFO,
      message,
      description,
      duration: TOAST_CONFIG.defaultDuration,
      actions
    });
  }

  /**
   * Show a toast for token limits errors with recovery actions
   */
  showTokenLimitsError(
    message: string,
    recoveryActions: RecoveryAction[],
    onRetry?: () => void,
    onUseFallback?: () => void
  ): string {
    const actions: ToastAction[] = [];

    if (recoveryActions.includes(RecoveryAction.RETRY) && onRetry) {
      actions.push({
        id: 'retry',
        label: 'Retry',
        type: 'primary',
        callback: onRetry
      });
    }

    if (recoveryActions.includes(RecoveryAction.USE_FALLBACK) && onUseFallback) {
      actions.push({
        id: 'use-fallback',
        label: 'Use Defaults',
        type: 'secondary',
        callback: onUseFallback
      });
    }

    return this.showError(message, undefined, actions);
  }

  /**
   * Show a toast for service restoration
   */
  showServiceRestored(serviceName: string): string {
    return this.showSuccess(
      `${serviceName} has been restored`,
      'All features are now available'
    );
  }

  /**
   * Show a toast for fallback mode activation
   */
  showFallbackMode(serviceName: string): string {
    return this.showWarning(
      `${serviceName} unavailable`,
      'Using default settings to keep the app functional'
    );
  }

  /**
   * Dismiss a specific toast
   */
  dismiss(toastId: string): void {
    const currentToasts = this.toasts$.value;
    const updatedToasts = currentToasts.map(toast => 
      toast.id === toastId ? { ...toast, visible: false } : toast
    );
    this.toasts$.next(updatedToasts);

    // Remove the toast after animation
    setTimeout(() => {
      this.remove(toastId);
    }, 300);
  }

  /**
   * Dismiss all toasts
   */
  dismissAll(): void {
    const currentToasts = this.toasts$.value;
    const updatedToasts = currentToasts.map(toast => ({ ...toast, visible: false }));
    this.toasts$.next(updatedToasts);

    // Remove all toasts after animation
    setTimeout(() => {
      this.toasts$.next([]);
    }, 300);
  }

  /**
   * Remove a toast immediately
   */
  remove(toastId: string): void {
    const currentToasts = this.toasts$.value;
    const updatedToasts = currentToasts.filter(toast => toast.id !== toastId);
    this.toasts$.next(updatedToasts);
  }

  /**
   * Add a new toast
   */
  private addToast(config: {
    type: ToastType;
    message: string;
    description?: string;
    duration: number;
    actions?: ToastAction[];
  }): string {
    const id = this.generateId();
    const toast: ToastMessage = {
      id,
      type: config.type,
      message: config.message,
      description: config.description,
      duration: config.duration,
      dismissible: true,
      actions: config.actions,
      timestamp: new Date(),
      visible: true
    };

    const currentToasts = this.toasts$.value;
    
    // Limit the number of toasts
    let updatedToasts = [...currentToasts, toast];
    if (updatedToasts.length > TOAST_CONFIG.maxToasts) {
      // Remove oldest toasts
      updatedToasts = updatedToasts.slice(-TOAST_CONFIG.maxToasts);
    }

    this.toasts$.next(updatedToasts);

    // Auto-dismiss if duration is set
    if (config.duration > 0) {
      timer(config.duration).subscribe(() => {
        this.dismiss(id);
      });
    }

    return id;
  }

  /**
   * Generate unique toast ID
   */
  private generateId(): string {
    return `toast-${this.nextId++}-${Date.now()}`;
  }
}
