import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { SSEStreamingService } from './sse-streaming.service';
import {
  ModifyChapterRequest,
  ModifyChapterResponse,
  FleshOutRequest,
  FleshOutResponse,
  GenerateCharacterDetailsRequest,
  GenerateCharacterDetailsResponse,
  RegenerateBioRequest,
  RegenerateBioResponse,
  // New LLM Chat interfaces
  LLMChatRequest,
  LLMChatResponse,
  LLMChatStreamMessage,
  // New Phase Validation interfaces
  PhaseTransitionRequest,
  PhaseTransitionResponse
} from '../models/story.model';
import {
  StructuredCharacterFeedbackRequest,
  StructuredRaterFeedbackRequest,
  StructuredGenerateChapterRequest,
  StructuredEditorReviewRequest,
  StructuredCharacterFeedbackResponse,
  StructuredRaterFeedbackResponse,
  StructuredGenerateChapterResponse,
  StructuredEditorReviewResponse
} from '../models/structured-request.model';
import { TokenStrategiesResponse } from '../models/token-limits.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000/api/v1';

  private http = inject(HttpClient);
  private sseStreamingService = inject(SSEStreamingService);

  // Chapter Modification - now with SSE streaming
  modifyChapter(
    request: ModifyChapterRequest,
    onProgress?: (phase: string, message: string, progress: number) => void
  ): Observable<ModifyChapterResponse> {
    return this.sseStreamingService.createSSEObservable<ModifyChapterResponse>(
      `${this.baseUrl}/modify-chapter`,
      request,
      {
        onProgress: onProgress ? (update) => onProgress(update.phase, update.message, update.progress) : undefined,
        onError: (error) => {
          console.error('Chapter modification streaming error:', error);
        }
      }
    );
  }

  // Flesh Out Plot Point / Worldbuilding
  fleshOut(request: FleshOutRequest): Observable<FleshOutResponse> {
    return this.http.post<FleshOutResponse>(`${this.baseUrl}/flesh-out`, request);
  }

  // Generate Character Details - now with SSE streaming
  generateCharacterDetails(
    request: GenerateCharacterDetailsRequest,
    onProgress?: (update: { phase: string; message: string; progress: number }) => void
  ): Observable<GenerateCharacterDetailsResponse> {
    return this.sseStreamingService.createSSEObservable<GenerateCharacterDetailsResponse>(
      `${this.baseUrl}/generate-character-details`,
      request,
      {
        onProgress: onProgress,
        onError: (error) => {
          console.error('Character details generation streaming error:', error);
        }
      }
    );
  }

  // Regenerate Bio - with SSE streaming
  regenerateBio(
    request: RegenerateBioRequest,
    onProgress?: (update: { phase: string; message: string; progress: number }) => void
  ): Observable<RegenerateBioResponse> {
    return this.sseStreamingService.createSSEObservable<RegenerateBioResponse>(
      `${this.baseUrl}/regenerate-bio`,
      request,
      {
        onProgress: onProgress,
        onError: (error) => {
          console.error('Bio regeneration streaming error:', error);
        }
      }
    );
  }

  // Token Strategies
  getTokenStrategies(): Observable<TokenStrategiesResponse> {
    return this.http.get<TokenStrategiesResponse>(`${this.baseUrl}/tokens/strategies`);
  }

  // ============================================================================
  // NEW ENDPOINTS FOR THREE-PHASE CHAPTER COMPOSE SYSTEM (WRI-49)
  // ============================================================================

  // LLM Chat (separate from RAG) - now with SSE streaming
  llmChat(request: LLMChatRequest): Observable<LLMChatResponse> {
    return new Observable<LLMChatResponse>(observer => {
      fetch(`${this.baseUrl}/chat/llm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        
        if (!reader) {
          throw new Error('No response body');
        }
        
        const processStream = async () => {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              
              const chunk = decoder.decode(value);
              const lines = chunk.split('\n');
              
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data: LLMChatStreamMessage = JSON.parse(line.slice(6));
                    
                    if (data.type === 'result') {
                      observer.next(data.data);
                      observer.complete();
                      return;
                    } else if (data.type === 'error') {
                      observer.error(new Error(data.message));
                      return;
                    }
                    // Status updates are handled but not emitted to maintain compatibility
                  } catch (parseError) {
                    console.warn('Failed to parse SSE message:', line, parseError);
                  }
                }
              }
            }
          } catch (error) {
            observer.error(error);
          }
        };
        
        processStream();
      })
      .catch(error => {
        observer.error(error);
      });
    });
  }

  // LLM Chat with progress updates - for components that want to show progress
  llmChatWithUpdates(request: LLMChatRequest): Observable<LLMChatStreamMessage> {
    return new Observable<LLMChatStreamMessage>(observer => {
      fetch(`${this.baseUrl}/chat/llm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        
        if (!reader) {
          throw new Error('No response body');
        }
        
        const processStream = async () => {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              
              const chunk = decoder.decode(value);
              const lines = chunk.split('\n');
              
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data: LLMChatStreamMessage = JSON.parse(line.slice(6));
                    observer.next(data);
                    
                    if (data.type === 'result' || data.type === 'error') {
                      observer.complete();
                      return;
                    }
                  } catch (parseError) {
                    console.warn('Failed to parse SSE message:', line, parseError);
                  }
                }
              }
            }
          } catch (error) {
            observer.error(error);
          }
        };
        
        processStream();
      })
      .catch(error => {
        observer.error(error);
      });
    });
  }

  // Phase Transition Validation
  validatePhaseTransition(request: PhaseTransitionRequest): Observable<PhaseTransitionResponse> {
    return this.http.post<PhaseTransitionResponse>(`${this.baseUrl}/validate/phase-transition`, request);
  }

  // ============================================================================
  // NEW STRUCTURED REQUEST METHODS (WRI-72)
  // ============================================================================

  // Character Feedback - now with SSE streaming
  requestCharacterFeedback(
    request: StructuredCharacterFeedbackRequest,
    onProgress?: (update: { phase: string; message: string; progress: number }) => void
  ): Observable<StructuredCharacterFeedbackResponse> {
    return this.sseStreamingService.createSSEObservable<StructuredCharacterFeedbackResponse>(
      `${this.baseUrl}/character-feedback`,
      request,
      {
        onProgress: onProgress,
        onError: (error) => {
          console.error('Character feedback streaming error:', error);
        }
      }
    );
  }

  // Rater Feedback
  requestRaterFeedback(request: StructuredRaterFeedbackRequest): Observable<StructuredRaterFeedbackResponse> {
    return this.http.post<StructuredRaterFeedbackResponse>(`${this.baseUrl}/rater-feedback/structured`, request);
  }

  // Streaming Rater Feedback
  streamRaterFeedback(request: any): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.baseUrl}/rater-feedback/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request)
      }).then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        
        if (!reader) {
          throw new Error('No response body');
        }
        
        const readStream = async () => {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              
              const chunk = decoder.decode(value);
              const lines = chunk.split('\n');
              
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const eventData = JSON.parse(line.slice(6));
                    observer.next(eventData);
                    
                    if (eventData.type === 'result') {
                      observer.complete();
                      return;
                    } else if (eventData.type === 'error') {
                      observer.error(new Error(eventData.message || 'Streaming error'));
                      return;
                    }
                  } catch (parseError) {
                    console.warn('Failed to parse SSE event:', line, parseError);
                  }
                }
              }
            }
          } catch (error) {
            observer.error(error);
          }
        };
        
        readStream();
      }).catch(error => {
        observer.error(error);
      });
      
      return () => {
        // Cleanup if needed
      };
    });
  }

  // Chapter Generation
  generateChapter(request: StructuredGenerateChapterRequest): Observable<StructuredGenerateChapterResponse> {
    return this.http.post<StructuredGenerateChapterResponse>(`${this.baseUrl}/generate-chapter/structured`, request);
  }

  // Editor Review
  requestEditorReview(request: StructuredEditorReviewRequest): Observable<StructuredEditorReviewResponse> {
    return this.sseStreamingService.createSSEObservable<StructuredEditorReviewResponse>(
      `${this.baseUrl}/editor-review`,
      request
    );
  }
}
