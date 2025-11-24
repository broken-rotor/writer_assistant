import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface AgenticData {
  content?: string;
  iteration?: number;
  evaluation_feedback?: string;
  passed_evaluation?: boolean;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  operation?: string;
  progress?: number;
  phase?: string;
  data?: AgenticData;
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
   * @param progress Optional progress percentage (0-100)
   * @param phase Optional phase description
   * @param data Optional agentic data for rich display
   */
  show(message?: string, operation?: string, progress?: number, phase?: string, data?: AgenticData): void {
    this.loadingSubject.next({
      isLoading: true,
      message,
      operation,
      progress,
      phase,
      data
    });
  }

  /**
   * Update loading message while keeping loading state active
   * @param message New message to display
   * @param operation Optional operation identifier for tracking
   * @param progress Optional progress percentage (0-100)
   * @param phase Optional phase description
   * @param data Optional agentic data for rich display
   */
  updateMessage(message: string, operation?: string, progress?: number, phase?: string, data?: AgenticData): void {
    const currentState = this.loadingSubject.value;
    if (currentState.isLoading) {
      this.loadingSubject.next({
        isLoading: true,
        message,
        operation: operation || currentState.operation,
        progress: progress !== undefined ? progress : currentState.progress,
        phase: phase !== undefined ? phase : currentState.phase,
        data: data !== undefined ? data : currentState.data
      });
    }
  }

  /**
   * Update progress while keeping loading state active
   * @param progress Progress percentage (0-100)
   * @param message Optional message to display
   * @param phase Optional phase description
   * @param data Optional agentic data for rich display
   */
  updateProgress(progress: number, message?: string, phase?: string, data?: AgenticData): void {
    const currentState = this.loadingSubject.value;
    if (currentState.isLoading) {
      this.loadingSubject.next({
        isLoading: true,
        message: message || currentState.message,
        operation: currentState.operation,
        progress,
        phase: phase || currentState.phase,
        data: data !== undefined ? data : currentState.data
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
