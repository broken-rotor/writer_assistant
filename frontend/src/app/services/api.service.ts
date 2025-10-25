import { Injectable } from '@angular/core';
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
  GenerateCharacterDetailsResponse
} from '../models/story.model';
import { TokenStrategiesResponse } from '../models/token-limits.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) {}

  // Character Feedback
  requestCharacterFeedback(request: CharacterFeedbackRequest): Observable<CharacterFeedbackResponse> {
    return this.http.post<CharacterFeedbackResponse>(`${this.baseUrl}/character-feedback`, request);
  }

  // Rater Feedback
  requestRaterFeedback(request: RaterFeedbackRequest): Observable<RaterFeedbackResponse> {
    return this.http.post<RaterFeedbackResponse>(`${this.baseUrl}/rater-feedback`, request);
  }

  // Chapter Generation
  generateChapter(request: GenerateChapterRequest): Observable<GenerateChapterResponse> {
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
}
