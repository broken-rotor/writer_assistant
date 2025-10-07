import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { StoryInput, StoryDraft, Character, FeedbackData } from '../../shared/models';

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  metadata?: {
    timestamp: string;
    requestId: string;
    processingTime: number;
  };
  errors?: any;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json'
    });
  }

  // Story Generation APIs
  generateDraft(storyInput: StoryInput, storyContext: any = {}): Observable<ApiResponse<StoryDraft>> {
    const payload = {
      user_input: {
        type: 'theme_topic_outline',
        content: storyInput.theme,
        expansion_request: 'develop this into a detailed story outline'
      },
      user_preferences: {
        style_profile: storyInput.style,
        length_preference: storyInput.length,
        focus_areas: storyInput.focusAreas
      },
      story_context: {
        existing_content: null,
        characters: [],
        previous_drafts: [],
        user_feedback_history: [],
        ...storyContext
      }
    };

    return this.http.post<ApiResponse<StoryDraft>>(
      `${this.baseUrl}/generate/draft`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  reviseDraft(originalDraft: StoryDraft, userFeedback: string, specificChanges: string[]): Observable<ApiResponse<StoryDraft>> {
    const payload = {
      original_draft: {
        title: originalDraft.title,
        outline: originalDraft.outline,
        characters: originalDraft.characters,
        themes: originalDraft.themes
      },
      user_feedback: userFeedback,
      specific_changes: specificChanges,
      revision_context: {
        previous_revisions: [],
        user_preferences: {}
      }
    };

    return this.http.post<ApiResponse<StoryDraft>>(
      `${this.baseUrl}/generate/revise-draft`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  // Character Dialog APIs
  generateCharacterDialog(character: Character, userMessage: string, conversationContext: any): Observable<ApiResponse<any>> {
    const payload = {
      character_definition: {
        character_id: character.id,
        name: character.name,
        personality: character.personality,
        background: character.background,
        current_knowledge: character.currentState.currentKnowledge,
        emotional_state: character.currentState.emotionalState
      },
      conversation_context: conversationContext,
      user_message: userMessage
    };

    return this.http.post<ApiResponse<any>>(
      `${this.baseUrl}/character/dialog`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  generateCharacterReactions(storyDraft: StoryDraft, selectedCharacters: string[], reactionPrompt: string): Observable<ApiResponse<any>> {
    const payload = {
      story_draft: {
        title: storyDraft.title,
        outline: storyDraft.outline,
        characters: storyDraft.characters
      },
      selected_characters: selectedCharacters,
      reaction_prompt: reactionPrompt,
      story_context: 'Character reaction to proposed story events'
    };

    return this.http.post<ApiResponse<any>>(
      `${this.baseUrl}/character/generate-reactions`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  // Detailed Content Generation
  generateDetailedContent(storyDraft: StoryDraft, selectedResponses: any[], userGuidance: string): Observable<ApiResponse<any>> {
    const payload = {
      story_draft: {
        title: storyDraft.title,
        outline: storyDraft.outline,
        characters: storyDraft.characters,
        themes: storyDraft.themes
      },
      selected_character_responses: selectedResponses,
      user_guidance: userGuidance,
      generation_preferences: {
        target_length: 2500,
        mood: 'investigative_tension',
        style: 'literary_mystery'
      }
    };

    return this.http.post<ApiResponse<any>>(
      `${this.baseUrl}/generate/detailed-content`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  // Feedback APIs
  generateFeedback(content: any, storyContext: any, feedbackAgents: any[]): Observable<ApiResponse<FeedbackData[]>> {
    const payload = {
      content_to_review: content,
      story_context: storyContext,
      feedback_agents: feedbackAgents
    };

    return this.http.post<ApiResponse<FeedbackData[]>>(
      `${this.baseUrl}/feedback/generate`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  applySelectedFeedback(originalContent: any, storyContext: any, selectedFeedback: any[], ignoredFeedback: any[]): Observable<ApiResponse<any>> {
    const payload = {
      original_content: originalContent,
      story_context: storyContext,
      selected_feedback: selectedFeedback,
      ignored_feedback: ignoredFeedback
    };

    return this.http.post<ApiResponse<any>>(
      `${this.baseUrl}/generate/apply-feedback`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  // Utility APIs
  validateStoryStructure(storyContent: any, validationRules: any): Observable<ApiResponse<any>> {
    const payload = {
      story_content: storyContent,
      validation_rules: validationRules
    };

    return this.http.post<ApiResponse<any>>(
      `${this.baseUrl}/validate/story-structure`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  getAgentTypes(): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(
      `${this.baseUrl}/agents/types`,
      { headers: this.getHeaders() }
    );
  }

  getCharacterTemplates(): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(
      `${this.baseUrl}/templates/characters`,
      { headers: this.getHeaders() }
    );
  }

  checkApiHealth(): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(
      `${this.baseUrl}/health`,
      { headers: this.getHeaders() }
    );
  }

  // Character Expansion API
  generateCharacterExpansion(expansionRequest: any): Observable<ApiResponse<any>> {
    const payload = {
      character: expansionRequest.character,
      section: expansionRequest.section,
      user_prompt: expansionRequest.userPrompt,
      expansion_context: {
        current_content: expansionRequest.character.currentContent,
        story_context: {}
      }
    };

    return this.http.post<ApiResponse<any>>(
      `${this.baseUrl}/character/expand`,
      payload,
      { headers: this.getHeaders() }
    );
  }
}