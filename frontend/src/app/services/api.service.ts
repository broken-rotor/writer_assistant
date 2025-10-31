import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  CharacterFeedbackRequest,
  CharacterFeedbackResponse,
  RaterFeedbackRequest,
  RaterFeedbackResponse,
  GenerateChapterRequest,
  GenerateChapterResponse,
  ModifyChapterRequest,
  ModifyChapterResponse,
  EditorReviewRequest,
  EditorReviewResponse,
  FleshOutRequest,
  FleshOutResponse,
  GenerateCharacterDetailsRequest,
  GenerateCharacterDetailsResponse,
  // New enhanced interfaces with phase support
  EnhancedCharacterFeedbackRequest,
  EnhancedRaterFeedbackRequest,
  EnhancedGenerateChapterRequest,
  EnhancedEditorReviewRequest,
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

  // Character Feedback
  requestCharacterFeedback(request: CharacterFeedbackRequest): Observable<CharacterFeedbackResponse> {
    return this.http.post<CharacterFeedbackResponse>(`${this.baseUrl}/character-feedback`, request);
  }

  // Enhanced Character Feedback with Phase Support
  requestCharacterFeedbackWithPhase(request: EnhancedCharacterFeedbackRequest): Observable<CharacterFeedbackResponse> {
    return this.http.post<CharacterFeedbackResponse>(`${this.baseUrl}/character-feedback`, request);
  }

  // Rater Feedback
  requestRaterFeedback(request: RaterFeedbackRequest): Observable<RaterFeedbackResponse> {
    return this.http.post<RaterFeedbackResponse>(`${this.baseUrl}/rater-feedback`, request);
  }

  // Enhanced Rater Feedback with Phase Support
  requestRaterFeedbackWithPhase(request: EnhancedRaterFeedbackRequest): Observable<RaterFeedbackResponse> {
    return this.http.post<RaterFeedbackResponse>(`${this.baseUrl}/rater-feedback`, request);
  }

  // Chapter Generation
  generateChapter(request: GenerateChapterRequest): Observable<GenerateChapterResponse> {
    return this.http.post<GenerateChapterResponse>(`${this.baseUrl}/generate-chapter`, request);
  }

  // Enhanced Chapter Generation with Phase Support
  generateChapterWithPhase(request: EnhancedGenerateChapterRequest): Observable<GenerateChapterResponse> {
    return this.http.post<GenerateChapterResponse>(`${this.baseUrl}/generate-chapter`, request);
  }

  // Chapter Modification
  modifyChapter(request: ModifyChapterRequest): Observable<ModifyChapterResponse> {
    return this.http.post<ModifyChapterResponse>(`${this.baseUrl}/modify-chapter`, request);
  }

  // Editor Review
  requestEditorReview(request: EditorReviewRequest): Observable<EditorReviewResponse> {
    return this.http.post<EditorReviewResponse>(`${this.baseUrl}/editor-review`, request);
  }

  // Enhanced Editor Review with Phase Support
  requestEditorReviewWithPhase(request: EnhancedEditorReviewRequest): Observable<EditorReviewResponse> {
    return this.http.post<EditorReviewResponse>(`${this.baseUrl}/editor-review`, request);
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

  // Structured Character Feedback
  requestCharacterFeedbackStructured(request: StructuredCharacterFeedbackRequest): Observable<StructuredCharacterFeedbackResponse> {
    return this.http.post<StructuredCharacterFeedbackResponse>(`${this.baseUrl}/character-feedback/structured`, request);
  }

  // Structured Rater Feedback
  requestRaterFeedbackStructured(request: StructuredRaterFeedbackRequest): Observable<StructuredRaterFeedbackResponse> {
    return this.http.post<StructuredRaterFeedbackResponse>(`${this.baseUrl}/rater-feedback/structured`, request);
  }

  // Structured Chapter Generation
  generateChapterStructured(request: StructuredGenerateChapterRequest): Observable<StructuredGenerateChapterResponse> {
    return this.http.post<StructuredGenerateChapterResponse>(`${this.baseUrl}/generate-chapter/structured`, request);
  }

  // Structured Editor Review
  requestEditorReviewStructured(request: StructuredEditorReviewRequest): Observable<StructuredEditorReviewResponse> {
    return this.http.post<StructuredEditorReviewResponse>(`${this.baseUrl}/editor-review/structured`, request);
  }
}
