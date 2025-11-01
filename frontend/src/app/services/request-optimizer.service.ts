/**
 * Request Optimizer Service
 * 
 * Implements optimization strategies for different context types to improve
 * performance and reduce token usage while maintaining request quality.
 */

import { Injectable, inject } from '@angular/core';
import { TokenCountingService } from './token-counting.service';
import {
  StructuredCharacterFeedbackRequest,
  StructuredRaterFeedbackRequest,
  StructuredGenerateChapterRequest,
  StructuredEditorReviewRequest,
  StructuredChapterContext,
  StructuredCharacterContext
} from '../models/structured-request.model';

export interface OptimizationResult<T> {
  optimizedRequest: T;
  optimizationsApplied: string[];
  tokensSaved: number;
  originalTokenCount: number;
  optimizedTokenCount: number;
}

export interface OptimizationOptions {
  maxTokens?: number;
  prioritizeRecent?: boolean;
  summarizeContent?: boolean;
  limitCharacters?: number;
  limitChapters?: number;
  preserveQuality?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class RequestOptimizerService {
  private tokenCountingService = inject(TokenCountingService);

  // Default optimization settings
  private readonly DEFAULT_MAX_TOKENS = 8000;
  private readonly DEFAULT_MAX_CHARACTERS = 8;
  private readonly DEFAULT_MAX_CHAPTERS = 5;

  // ============================================================================
  // PUBLIC API - OPTIMIZATION METHODS
  // ============================================================================

  /**
   * Optimize character feedback request
   */
  optimizeCharacterFeedbackRequest(
    request: StructuredCharacterFeedbackRequest,
    options: OptimizationOptions = {}
  ): OptimizationResult<StructuredCharacterFeedbackRequest> {
    const originalTokenCount = this.estimateTokenCount(request);
    const optimizationsApplied: string[] = [];
    let optimizedRequest = { ...request };

    const maxTokens = options.maxTokens || this.DEFAULT_MAX_TOKENS;

    // Optimize previous chapters
    if (optimizedRequest.previousChapters.length > (options.limitChapters || 3)) {
      optimizedRequest.previousChapters = this.optimizeChapters(
        optimizedRequest.previousChapters,
        options.limitChapters || 3,
        options.prioritizeRecent !== false
      );
      optimizationsApplied.push('limited_previous_chapters');
    }

    // Optimize character relationships if too long
    if (optimizedRequest.character.relationships && optimizedRequest.character.relationships.length > 500) {
      optimizedRequest.character = {
        ...optimizedRequest.character,
        relationships: this.summarizeText(optimizedRequest.character.relationships, 300)
      };
      optimizationsApplied.push('summarized_character_relationships');
    }

    // Optimize worldbuilding if too long
    if (optimizedRequest.worldbuilding.content.length > 2000) {
      optimizedRequest.worldbuilding = {
        ...optimizedRequest.worldbuilding,
        content: this.summarizeText(optimizedRequest.worldbuilding.content, 1500)
      };
      optimizationsApplied.push('summarized_worldbuilding');
    }

    // Check if we're still over token limit and apply more aggressive optimizations
    const currentTokenCount = this.estimateTokenCount(optimizedRequest);
    if (currentTokenCount > maxTokens) {
      optimizedRequest = this.applyAggressiveOptimizations(optimizedRequest, optimizationsApplied);
    }

    const finalTokenCount = this.estimateTokenCount(optimizedRequest);

    return {
      optimizedRequest,
      optimizationsApplied,
      tokensSaved: originalTokenCount - finalTokenCount,
      originalTokenCount,
      optimizedTokenCount: finalTokenCount
    };
  }

  /**
   * Optimize rater feedback request
   */
  optimizeRaterFeedbackRequest(
    request: StructuredRaterFeedbackRequest,
    options: OptimizationOptions = {}
  ): OptimizationResult<StructuredRaterFeedbackRequest> {
    const originalTokenCount = this.estimateTokenCount(request);
    const optimizationsApplied: string[] = [];
    const optimizedRequest = { ...request };

    // Optimize rater prompt if too long
    if (optimizedRequest.raterPrompt.length > 800) {
      optimizedRequest.raterPrompt = this.summarizeText(optimizedRequest.raterPrompt, 600);
      optimizationsApplied.push('summarized_rater_prompt');
    }

    // Optimize previous chapters (rater feedback typically needs fewer chapters)
    if (optimizedRequest.previousChapters.length > (options.limitChapters || 2)) {
      optimizedRequest.previousChapters = this.optimizeChapters(
        optimizedRequest.previousChapters,
        options.limitChapters || 2,
        options.prioritizeRecent !== false
      );
      optimizationsApplied.push('limited_previous_chapters');
    }

    // Optimize worldbuilding
    if (optimizedRequest.worldbuilding.content.length > 1500) {
      optimizedRequest.worldbuilding = {
        ...optimizedRequest.worldbuilding,
        content: this.summarizeText(optimizedRequest.worldbuilding.content, 1000)
      };
      optimizationsApplied.push('summarized_worldbuilding');
    }

    const finalTokenCount = this.estimateTokenCount(optimizedRequest);

    return {
      optimizedRequest,
      optimizationsApplied,
      tokensSaved: originalTokenCount - finalTokenCount,
      originalTokenCount,
      optimizedTokenCount: finalTokenCount
    };
  }

  /**
   * Optimize chapter generation request
   */
  optimizeGenerateChapterRequest(
    request: StructuredGenerateChapterRequest,
    options: OptimizationOptions = {}
  ): OptimizationResult<StructuredGenerateChapterRequest> {
    const originalTokenCount = this.estimateTokenCount(request);
    const optimizationsApplied: string[] = [];
    const optimizedRequest = { ...request };

    // Optimize characters (limit to most relevant)
    if (optimizedRequest.characters.length > (options.limitCharacters || this.DEFAULT_MAX_CHARACTERS)) {
      optimizedRequest.characters = this.optimizeCharacters(
        optimizedRequest.characters,
        options.limitCharacters || this.DEFAULT_MAX_CHARACTERS
      );
      optimizationsApplied.push('limited_characters');
    }

    // Optimize previous chapters
    if (optimizedRequest.previousChapters.length > (options.limitChapters || this.DEFAULT_MAX_CHAPTERS)) {
      optimizedRequest.previousChapters = this.optimizeChapters(
        optimizedRequest.previousChapters,
        options.limitChapters || this.DEFAULT_MAX_CHAPTERS,
        options.prioritizeRecent !== false
      );
      optimizationsApplied.push('limited_previous_chapters');
    }

    // Optimize incorporated feedback
    if (optimizedRequest.feedbackContext.incorporatedFeedback.length > 15) {
      optimizedRequest.feedbackContext = {
        ...optimizedRequest.feedbackContext,
        incorporatedFeedback: optimizedRequest.feedbackContext.incorporatedFeedback.slice(-15)
      };
      optimizationsApplied.push('limited_incorporated_feedback');
    }

    // Optimize character details
    optimizedRequest.characters = optimizedRequest.characters.map(char => 
      this.optimizeCharacterDetails(char)
    );
    if (optimizedRequest.characters.some((char, index) => 
      char !== request.characters[index])) {
      optimizationsApplied.push('optimized_character_details');
    }

    const finalTokenCount = this.estimateTokenCount(optimizedRequest);

    return {
      optimizedRequest,
      optimizationsApplied,
      tokensSaved: originalTokenCount - finalTokenCount,
      originalTokenCount,
      optimizedTokenCount: finalTokenCount
    };
  }

  /**
   * Optimize editor review request
   */
  optimizeEditorReviewRequest(
    request: StructuredEditorReviewRequest,
    options: OptimizationOptions = {}
  ): OptimizationResult<StructuredEditorReviewRequest> {
    const originalTokenCount = this.estimateTokenCount(request);
    const optimizationsApplied: string[] = [];
    const optimizedRequest = { ...request };

    // For editor review, we typically need fewer previous chapters
    if (optimizedRequest.previousChapters.length > (options.limitChapters || 2)) {
      optimizedRequest.previousChapters = this.optimizeChapters(
        optimizedRequest.previousChapters,
        options.limitChapters || 2,
        options.prioritizeRecent !== false
      );
      optimizationsApplied.push('limited_previous_chapters');
    }

    // Optimize characters (editor review typically needs fewer character details)
    if (optimizedRequest.characters.length > (options.limitCharacters || 6)) {
      optimizedRequest.characters = this.optimizeCharacters(
        optimizedRequest.characters,
        options.limitCharacters || 6
      );
      optimizationsApplied.push('limited_characters');
    }

    // Optimize character details for editor review (less detail needed)
    optimizedRequest.characters = optimizedRequest.characters.map(char => 
      this.optimizeCharacterForReview(char)
    );
    optimizationsApplied.push('optimized_characters_for_review');

    // If chapter to review is very long, consider chunking suggestion
    if (optimizedRequest.chapterToReview.length > 8000) {
      // Don't actually chunk here, but add optimization suggestion
      optimizationsApplied.push('large_chapter_detected');
    }

    const finalTokenCount = this.estimateTokenCount(optimizedRequest);

    return {
      optimizedRequest,
      optimizationsApplied,
      tokensSaved: originalTokenCount - finalTokenCount,
      originalTokenCount,
      optimizedTokenCount: finalTokenCount
    };
  }

  // ============================================================================
  // PRIVATE OPTIMIZATION METHODS
  // ============================================================================

  private optimizeChapters(
    chapters: StructuredChapterContext[],
    maxChapters: number,
    prioritizeRecent = true
  ): StructuredChapterContext[] {
    if (chapters.length <= maxChapters) {
      return chapters;
    }

    if (prioritizeRecent) {
      // Take the most recent chapters
      return chapters.slice(-maxChapters);
    } else {
      // Take evenly distributed chapters
      const step = Math.floor(chapters.length / maxChapters);
      return chapters.filter((_, index) => index % step === 0).slice(0, maxChapters);
    }
  }

  private optimizeCharacters(
    characters: StructuredCharacterContext[],
    maxCharacters: number
  ): StructuredCharacterContext[] {
    if (characters.length <= maxCharacters) {
      return characters;
    }

    // Prioritize non-hidden characters and those with more detailed information
    const sortedCharacters = [...characters].sort((a, b) => {
      // Hidden characters get lower priority
      if (a.isHidden && !b.isHidden) return 1;
      if (!a.isHidden && b.isHidden) return -1;

      // Characters with more complete information get higher priority
      const aCompleteness = this.calculateCharacterCompleteness(a);
      const bCompleteness = this.calculateCharacterCompleteness(b);
      return bCompleteness - aCompleteness;
    });

    return sortedCharacters.slice(0, maxCharacters);
  }

  private optimizeCharacterDetails(character: StructuredCharacterContext): StructuredCharacterContext {
    const optimized = { ...character };

    // Summarize long fields
    if (optimized.relationships && optimized.relationships.length > 400) {
      optimized.relationships = this.summarizeText(optimized.relationships, 300);
    }
    if (optimized.personality && optimized.personality.length > 300) {
      optimized.personality = this.summarizeText(optimized.personality, 200);
    }
    if (optimized.motivations && optimized.motivations.length > 200) {
      optimized.motivations = this.summarizeText(optimized.motivations, 150);
    }
    if (optimized.fears && optimized.fears.length > 200) {
      optimized.fears = this.summarizeText(optimized.fears, 150);
    }

    return optimized;
  }

  private optimizeCharacterForReview(character: StructuredCharacterContext): StructuredCharacterContext {
    // For editor review, we need less character detail
    return {
      ...character,
      name: character.name,
      basicBio: character.basicBio,
      personality: character.personality ? this.summarizeText(character.personality, 100) : character.personality,
      // Keep other essential fields but summarize them more aggressively
      sex: character.sex,
      gender: character.gender,
      age: character.age,
      physicalAppearance: character.physicalAppearance ? this.summarizeText(character.physicalAppearance, 50) : character.physicalAppearance,
      usualClothing: character.usualClothing ? this.summarizeText(character.usualClothing, 30) : character.usualClothing,
      sexualPreference: character.sexualPreference,
      motivations: character.motivations ? this.summarizeText(character.motivations, 80) : character.motivations,
      fears: character.fears ? this.summarizeText(character.fears, 80) : character.fears,
      relationships: character.relationships ? this.summarizeText(character.relationships, 150) : character.relationships,
      isHidden: character.isHidden
    };
  }

  private applyAggressiveOptimizations<T>(request: T, optimizationsApplied: string[]): T {
    // This would apply more aggressive optimizations if needed
    // For now, just return the request as-is
    optimizationsApplied.push('aggressive_optimization_attempted');
    return request;
  }

  private calculateCharacterCompleteness(character: StructuredCharacterContext): number {
    let completeness = 0;
    const fields = ['name', 'basicBio', 'personality', 'motivations', 'fears', 'relationships', 'physicalAppearance'];
    
    fields.forEach(field => {
      if (character[field as keyof StructuredCharacterContext] && 
          String(character[field as keyof StructuredCharacterContext]).trim().length > 0) {
        completeness++;
      }
    });

    return completeness;
  }

  private summarizeText(text: string, maxLength: number): string {
    if (text.length <= maxLength) {
      return text;
    }

    // Simple summarization: take first part and add ellipsis
    // In a real implementation, this could use more sophisticated summarization
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    let summary = '';
    
    for (const sentence of sentences) {
      if (summary.length + sentence.length + 1 <= maxLength - 3) {
        summary += (summary ? '. ' : '') + sentence.trim();
      } else {
        break;
      }
    }

    return summary + (summary.length < text.length ? '...' : '');
  }

  private estimateTokenCount(request: any): number {
    // Simple token estimation - in a real implementation, this would use
    // the actual token counting service
    const jsonString = JSON.stringify(request);
    return Math.ceil(jsonString.length / 4); // Rough approximation: 4 chars per token
  }
}
