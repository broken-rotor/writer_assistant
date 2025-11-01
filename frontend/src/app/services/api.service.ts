import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ModifyChapterRequest,
  ModifyChapterResponse,
  FleshOutRequest,
  FleshOutResponse,
  GenerateCharacterDetailsRequest,
  GenerateCharacterDetailsResponse,
  // New LLM Chat interfaces
  LLMChatRequest,
  LLMChatResponse,
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

  // Chapter Modification
  modifyChapter(request: ModifyChapterRequest): Observable<ModifyChapterResponse> {
    return this.http.post<ModifyChapterResponse>(`${this.baseUrl}/modify-chapter`, request);
  }

  // Flesh Out Plot Point / Worldbuilding
  fleshOut(request: FleshOutRequest): Observable<FleshOutResponse> {
    return this.http.post<FleshOutResponse>(`${this.baseUrl}/flesh-out`, request);
  }

  // Generate Character Details
  generateCharacterDetails(request: GenerateCharacterDetailsRequest): Observable<GenerateCharacterDetailsResponse> {
    return this.http.post<GenerateCharacterDetailsResponse>(`${this.baseUrl}/generate-character-details`, request);
  }

  // Token Strategies
  getTokenStrategies(): Observable<TokenStrategiesResponse> {
    return this.http.get<TokenStrategiesResponse>(`${this.baseUrl}/tokens/strategies`);
  }

  // ============================================================================
  // NEW ENDPOINTS FOR THREE-PHASE CHAPTER COMPOSE SYSTEM (WRI-49)
  // ============================================================================

  // LLM Chat (separate from RAG)
  llmChat(request: LLMChatRequest): Observable<LLMChatResponse> {
    return this.http.post<LLMChatResponse>(`${this.baseUrl}/chat/llm`, request);
  }

  // Phase Transition Validation
  validatePhaseTransition(request: PhaseTransitionRequest): Observable<PhaseTransitionResponse> {
    return this.http.post<PhaseTransitionResponse>(`${this.baseUrl}/validate/phase-transition`, request);
  }

  // ============================================================================
  // NEW STRUCTURED REQUEST METHODS (WRI-72)
  // ============================================================================

  // Character Feedback
  requestCharacterFeedback(request: StructuredCharacterFeedbackRequest): Observable<StructuredCharacterFeedbackResponse> {
    return this.http.post<StructuredCharacterFeedbackResponse>(`${this.baseUrl}/character-feedback/structured`, request);
  }

  // Rater Feedback
  requestRaterFeedback(request: StructuredRaterFeedbackRequest): Observable<StructuredRaterFeedbackResponse> {
    return this.http.post<StructuredRaterFeedbackResponse>(`${this.baseUrl}/rater-feedback/structured`, request);
  }

  // Chapter Generation
  generateChapter(request: StructuredGenerateChapterRequest): Observable<StructuredGenerateChapterResponse> {
    return this.http.post<StructuredGenerateChapterResponse>(`${this.baseUrl}/generate-chapter/structured`, request);
  }

  // Editor Review
  requestEditorReview(request: StructuredEditorReviewRequest): Observable<StructuredEditorReviewResponse> {
    return this.http.post<StructuredEditorReviewResponse>(`${this.baseUrl}/editor-review/structured`, request);
  }
}
