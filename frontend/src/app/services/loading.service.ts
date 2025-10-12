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
