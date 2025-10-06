import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';

export interface OutlineGenerationRequest {
  title: string;
  genre: string;
  description: string;
  user_guidance: string;
  configuration?: Record<string, any>;
}

export interface ChapterGenerationRequest {
  session_id: string;
  chapter_number: number;
  user_guidance: string;
  story_context: Record<string, any>;
  configuration?: Record<string, any>;
}

export interface FeedbackRequest {
  phase: string;
  feedback_type: string;
  feedback: Record<string, any>;
}

export interface GenerationResponse {
  success: boolean;
  data: any;
  metadata: {
    timestamp: string;
    request_id: string;
    version: string;
  };
}

export interface SessionStatus {
  session_id: string;
  current_phase: string;
  current_step: string;
  status: string;
  progress: number;
  active_agents: string[];
  estimated_completion: string;
}

export interface AgentStatus {
  writer_agent?: {
    status: string;
    current_task: string;
    progress: number;
    estimated_completion: string;
    memory_state: string;
  };
  character_agents?: Record<string, any>;
  rater_agents?: Record<string, any>;
}

@Injectable({
  providedIn: 'root'
})
export class GenerationService {
  private readonly apiUrl = `${environment.apiUrl}/generate`;

  private currentSessionSubject = new BehaviorSubject<string | null>(null);
  private sessionStatusSubject = new BehaviorSubject<SessionStatus | null>(null);
  private agentStatusSubject = new BehaviorSubject<AgentStatus | null>(null);

  public currentSession$ = this.currentSessionSubject.asObservable();
  public sessionStatus$ = this.sessionStatusSubject.asObservable();
  public agentStatus$ = this.agentStatusSubject.asObservable();

  constructor(private http: HttpClient) {}

  // Outline Generation
  generateOutline(request: OutlineGenerationRequest): Observable<GenerationResponse> {
    return this.http.post<GenerationResponse>(`${this.apiUrl}/outline`, request);
  }

  // Chapter Generation
  generateChapter(request: ChapterGenerationRequest): Observable<GenerationResponse> {
    return this.http.post<GenerationResponse>(`${this.apiUrl}/chapter`, request);
  }

  // Session Management
  getSessionStatus(sessionId: string): Observable<GenerationResponse> {
    return this.http.get<GenerationResponse>(`${this.apiUrl}/session/${sessionId}/status`);
  }

  submitFeedback(sessionId: string, feedback: FeedbackRequest): Observable<GenerationResponse> {
    return this.http.post<GenerationResponse>(`${this.apiUrl}/session/${sessionId}/feedback`, feedback);
  }

  // Agent Management
  getAgentStatus(sessionId: string): Observable<GenerationResponse> {
    return this.http.get<GenerationResponse>(`${this.apiUrl}/session/${sessionId}/agents/status`);
  }

  cancelAgentTask(sessionId: string, agentId: string): Observable<GenerationResponse> {
    return this.http.post<GenerationResponse>(`${this.apiUrl}/session/${sessionId}/agents/${agentId}/cancel`, {});
  }

  restartFailedAgent(sessionId: string, agentId: string): Observable<GenerationResponse> {
    return this.http.post<GenerationResponse>(`${this.apiUrl}/session/${sessionId}/agents/${agentId}/restart`, {});
  }

  // Session State Management
  setCurrentSession(sessionId: string | null): void {
    this.currentSessionSubject.next(sessionId);
  }

  getCurrentSession(): string | null {
    return this.currentSessionSubject.value;
  }

  updateSessionStatus(status: SessionStatus): void {
    this.sessionStatusSubject.next(status);
  }

  updateAgentStatus(status: AgentStatus): void {
    this.agentStatusSubject.next(status);
  }

  // Polling for updates
  startSessionPolling(sessionId: string, interval: number = 5000): void {
    if (this.getCurrentSession() === sessionId) {
      this.pollSessionStatus(sessionId, interval);
      this.pollAgentStatus(sessionId, interval);
    }
  }

  stopSessionPolling(): void {
    this.setCurrentSession(null);
    this.sessionStatusSubject.next(null);
    this.agentStatusSubject.next(null);
  }

  private pollSessionStatus(sessionId: string, interval: number): void {
    const poll = () => {
      if (this.getCurrentSession() === sessionId) {
        this.getSessionStatus(sessionId).subscribe({
          next: (response) => {
            if (response.success) {
              this.updateSessionStatus(response.data);
            }
            setTimeout(poll, interval);
          },
          error: (error) => {
            console.error('Error polling session status:', error);
            setTimeout(poll, interval * 2); // Back off on error
          }
        });
      }
    };
    poll();
  }

  private pollAgentStatus(sessionId: string, interval: number): void {
    const poll = () => {
      if (this.getCurrentSession() === sessionId) {
        this.getAgentStatus(sessionId).subscribe({
          next: (response) => {
            if (response.success) {
              this.updateAgentStatus(response.data);
            }
            setTimeout(poll, interval);
          },
          error: (error) => {
            console.error('Error polling agent status:', error);
            setTimeout(poll, interval * 2); // Back off on error
          }
        });
      }
    };
    poll();
  }

  // WebSocket support (for future implementation)
  connectWebSocket(sessionId: string): void {
    // TODO: Implement WebSocket connection for real-time updates
    // const wsUrl = `${environment.wsUrl}/session/${sessionId}/ws`;
    console.log('WebSocket connection not yet implemented');
  }

  disconnectWebSocket(): void {
    // TODO: Implement WebSocket disconnection
    console.log('WebSocket disconnection not yet implemented');
  }
}