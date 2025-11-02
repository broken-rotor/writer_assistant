import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  operation?: string;
}

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  private loadingSubject = new BehaviorSubject<LoadingState>({
    isLoading: false
  });

  public loading$: Observable<LoadingState> = this.loadingSubject.asObservable();

  /**
   * Show loading indicator with optional message
   * @param message Optional message to display (e.g., "Generating chapter...")
   * @param operation Optional operation identifier for tracking
   */
  show(message?: string, operation?: string): void {
    this.loadingSubject.next({
      isLoading: true,
      message,
      operation
    });
  }

  /**
   * Update loading message while keeping loading state active
   * @param message New message to display
   * @param operation Optional operation identifier for tracking
   */
  updateMessage(message: string, operation?: string): void {
    const currentState = this.loadingSubject.value;
    if (currentState.isLoading) {
      this.loadingSubject.next({
        isLoading: true,
        message,
        operation: operation || currentState.operation
      });
    }
  }

  /**
   * Hide loading indicator
   */
  hide(): void {
    this.loadingSubject.next({
      isLoading: false
    });
  }

  /**
   * Get current loading state
   */
  get isLoading(): boolean {
    return this.loadingSubject.value.isLoading;
  }
}
