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
  // Chapter Outline Generation interfaces
  ChapterOutlineGenerationRequest,
  ChapterOutlineGenerationResponse,
  // Backend request interfaces
  BackendGenerateChapterRequest,
  BackendEditorReviewRequest,
  BackendEditorReviewResponse
} from '../models/story.model';
import {
  StructuredRaterFeedbackRequest,
  StructuredEditorReviewRequest,
  StructuredCharacterFeedbackResponse,
  StructuredRaterFeedbackResponse,
  StructuredGenerateChapterResponse,
  StructuredEditorReviewResponse
} from '../models/structured-request.model';
import { TokenStrategiesResponse } from '../models/token-limits.model';
import { RequestContext } from '../utils/context-transformer';

// New RequestContext-based request interfaces
export interface CharacterFeedbackRequest {
  character_name: string;
  plotPoint: string;
  request_context: RequestContext;
}

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

  // Flesh Out Plot Point / Worldbuilding - now with SSE streaming
  fleshOut(
    request: FleshOutRequest,
    onProgress?: (update: { phase: string; message: string; progress: number }) => void
  ): Observable<FleshOutResponse> {
    return this.sseStreamingService.createSSEObservable<FleshOutResponse>(
      `${this.baseUrl}/flesh-out`,
      request,
      {
        onProgress: onProgress,
        onError: (error) => {
          console.error('Flesh out streaming error:', error);
        }
      }
    );
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

  // ============================================================================
  // NEW STRUCTURED REQUEST METHODS (WRI-72)
  // ============================================================================

  // Character Feedback - Updated to use RequestContext API
  requestCharacterFeedback(request: CharacterFeedbackRequest): Observable<StructuredCharacterFeedbackResponse> {
    return this.http.post<StructuredCharacterFeedbackResponse>(`${this.baseUrl}/character-feedback`, request);
  }

  // Rater Feedback (now uses streaming internally)
  requestRaterFeedback(request: StructuredRaterFeedbackRequest): Observable<StructuredRaterFeedbackResponse> {
    // Convert structured request to streaming format
    const streamingRequest = {
      raterPrompt: request.raterPrompt,
      plotPoint: request.plotContext?.plotPoint || '',
      structured_context: {
        systemPrompts: request.systemPrompts,
        worldbuilding: request.worldbuilding,
        storySummary: request.storySummary,
        previousChapters: request.previousChapters,
        plotContext: request.plotContext,
        requestMetadata: request.requestMetadata
      }
    };

    // Use streaming API but return only the final result
    return new Observable<StructuredRaterFeedbackResponse>(observer => {
      this.streamRaterFeedback(streamingRequest).subscribe({
        next: (event) => {
          if (event.type === 'result') {
            // Transform the result to match expected format
            const response: StructuredRaterFeedbackResponse = {
              raterName: event.data.raterName,
              feedback: event.data.feedback,
              context_metadata: event.data.context_metadata
            };
            observer.next(response);
            observer.complete();
          }
          // Ignore progress events for this compatibility method
        },
        error: (error) => observer.error(error)
      });
    });
  }

  // Streaming Rater Feedback
  streamRaterFeedback(request: any): Observable<any> {
    return new Observable(observer => {
      fetch(`${this.baseUrl}/rater-feedback`, {
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

  // Chapter Generation (SSE Streaming)
  generateChapter(request: BackendGenerateChapterRequest): Observable<StructuredGenerateChapterResponse> {
    return this.sseStreamingService.createSSEObservable<StructuredGenerateChapterResponse>(
      `${this.baseUrl}/generate-chapter`,
      request
    );
  }

  // Editor Review (Legacy)
  requestEditorReview(request: StructuredEditorReviewRequest): Observable<StructuredEditorReviewResponse> {
    return this.sseStreamingService.createSSEObservable<StructuredEditorReviewResponse>(
      `${this.baseUrl}/editor-review`,
      request
    );
  }

  // Editor Review (New RequestContext API)
  requestEditorReviewWithContext(request: BackendEditorReviewRequest): Observable<BackendEditorReviewResponse> {
    return this.sseStreamingService.createSSEObservable<BackendEditorReviewResponse>(
      `${this.baseUrl}/editor-review`,
      request
    );
  }

  // Chapter Outline Generation (WRI-129)
  generateChapterOutlines(request: ChapterOutlineGenerationRequest): Observable<ChapterOutlineGenerationResponse> {
    return this.http.post<ChapterOutlineGenerationResponse>(`${this.baseUrl}/generate-chapter-outlines`, request);
  }
}
