/**
 * Request Validator Service
 * 
 * Provides comprehensive validation for structured requests with detailed
 * error reporting and validation rules.
 */

import { Injectable } from '@angular/core';
import {
  StructuredCharacterFeedbackRequest,
  StructuredRaterFeedbackRequest,
  StructuredGenerateChapterRequest,
  StructuredEditorReviewRequest,
  StructuredRequestValidationResult,
  StructuredRequestValidationError
} from '../models/structured-request.model';

@Injectable({
  providedIn: 'root'
})
export class RequestValidatorService {

  // ============================================================================
  // PUBLIC API - VALIDATION METHODS
  // ============================================================================

  /**
   * Validate structured character feedback request
   */
  validateCharacterFeedbackRequest(request: StructuredCharacterFeedbackRequest): StructuredRequestValidationResult {
    const errors: StructuredRequestValidationError[] = [];
    const warnings: StructuredRequestValidationError[] = [];
    const optimizationSuggestions: string[] = [];

    // Validate base request structure
    this.validateBaseRequest(request, errors, warnings);

    // Validate character-specific fields
    this.validateCharacterContext(request.character, errors, warnings);

    // Validate plot context
    this.validatePlotContext(request.plotContext, errors, warnings);

    // Validate phase context if present
    if (request.phaseContext) {
      this.validatePhaseContext(request.phaseContext, errors, warnings);
    }

    // Add optimization suggestions
    this.addCharacterFeedbackOptimizations(request, optimizationSuggestions);

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      optimizationSuggestions: optimizationSuggestions.length > 0 ? optimizationSuggestions : undefined
    };
  }

  /**
   * Validate structured rater feedback request
   */
  validateRaterFeedbackRequest(request: StructuredRaterFeedbackRequest): StructuredRequestValidationResult {
    const errors: StructuredRequestValidationError[] = [];
    const warnings: StructuredRequestValidationError[] = [];
    const optimizationSuggestions: string[] = [];

    // Validate base request structure
    this.validateBaseRequest(request, errors, warnings);

    // Validate rater-specific fields
    if (!request.raterPrompt || request.raterPrompt.trim().length === 0) {
      errors.push({
        field: 'raterPrompt',
        message: 'Rater prompt is required and cannot be empty',
        severity: 'error',
        code: 'RATER_PROMPT_REQUIRED'
      });
    } else if (request.raterPrompt.length < 10) {
      warnings.push({
        field: 'raterPrompt',
        message: 'Rater prompt is very short, consider providing more detailed instructions',
        severity: 'warning',
        code: 'RATER_PROMPT_SHORT'
      });
    }

    // Validate plot context
    this.validatePlotContext(request.plotContext, errors, warnings);

    // Validate phase context if present
    if (request.phaseContext) {
      this.validatePhaseContext(request.phaseContext, errors, warnings);
    }

    // Add optimization suggestions
    this.addRaterFeedbackOptimizations(request, optimizationSuggestions);

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      optimizationSuggestions: optimizationSuggestions.length > 0 ? optimizationSuggestions : undefined
    };
  }

  /**
   * Validate structured chapter generation request
   */
  validateGenerateChapterRequest(request: StructuredGenerateChapterRequest): StructuredRequestValidationResult {
    const errors: StructuredRequestValidationError[] = [];
    const warnings: StructuredRequestValidationError[] = [];
    const optimizationSuggestions: string[] = [];

    // Validate base request structure
    this.validateBaseRequest(request, errors, warnings);

    // Validate characters array
    if (!Array.isArray(request.characters)) {
      errors.push({
        field: 'characters',
        message: 'Characters must be an array',
        severity: 'error',
        code: 'CHARACTERS_ARRAY_REQUIRED'
      });
    } else {
      if (request.characters.length === 0) {
        warnings.push({
          field: 'characters',
          message: 'No characters provided, chapter generation may lack character development',
          severity: 'warning',
          code: 'NO_CHARACTERS'
        });
      } else {
        // Validate each character
        request.characters.forEach((character, index) => {
          this.validateCharacterContext(character, errors, warnings, `characters[${index}]`);
        });
      }
    }

    // Validate plot context
    this.validatePlotContext(request.plotContext, errors, warnings);

    // Validate feedback context
    this.validateFeedbackContext(request.feedbackContext, errors, warnings);

    // Validate phase context if present
    if (request.phaseContext) {
      this.validatePhaseContext(request.phaseContext, errors, warnings);
    }

    // Add optimization suggestions
    this.addChapterGenerationOptimizations(request, optimizationSuggestions);

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      optimizationSuggestions: optimizationSuggestions.length > 0 ? optimizationSuggestions : undefined
    };
  }

  /**
   * Validate structured editor review request
   */
  validateEditorReviewRequest(request: StructuredEditorReviewRequest): StructuredRequestValidationResult {
    const errors: StructuredRequestValidationError[] = [];
    const warnings: StructuredRequestValidationError[] = [];
    const optimizationSuggestions: string[] = [];

    // Validate base request structure
    this.validateBaseRequest(request, errors, warnings);

    // Validate characters array
    if (!Array.isArray(request.characters)) {
      errors.push({
        field: 'characters',
        message: 'Characters must be an array',
        severity: 'error',
        code: 'CHARACTERS_ARRAY_REQUIRED'
      });
    } else {
      request.characters.forEach((character, index) => {
        this.validateCharacterContext(character, errors, warnings, `characters[${index}]`);
      });
    }

    // Validate chapter to review
    if (!request.chapterToReview || request.chapterToReview.trim().length === 0) {
      errors.push({
        field: 'chapterToReview',
        message: 'Chapter to review is required and cannot be empty',
        severity: 'error',
        code: 'CHAPTER_TO_REVIEW_REQUIRED'
      });
    } else if (request.chapterToReview.length < 100) {
      warnings.push({
        field: 'chapterToReview',
        message: 'Chapter to review is very short, review may be limited',
        severity: 'warning',
        code: 'CHAPTER_TO_REVIEW_SHORT'
      });
    }

    // Validate review focus if present
    if (request.reviewFocus && Array.isArray(request.reviewFocus)) {
      if (request.reviewFocus.length === 0) {
        warnings.push({
          field: 'reviewFocus',
          message: 'Review focus array is empty, consider specifying focus areas',
          severity: 'warning',
          code: 'EMPTY_REVIEW_FOCUS'
        });
      }
    }

    // Validate phase context if present
    if (request.phaseContext) {
      this.validatePhaseContext(request.phaseContext, errors, warnings);
    }

    // Add optimization suggestions
    this.addEditorReviewOptimizations(request, optimizationSuggestions);

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      optimizationSuggestions: optimizationSuggestions.length > 0 ? optimizationSuggestions : undefined
    };
  }

  // ============================================================================
  // PRIVATE VALIDATION METHODS
  // ============================================================================

  private validateBaseRequest(
    request: any,
    errors: StructuredRequestValidationError[],
    warnings: StructuredRequestValidationError[]
  ): void {
    // Validate system prompts
    if (!request.systemPrompts) {
      errors.push({
        field: 'systemPrompts',
        message: 'System prompts are required',
        severity: 'error',
        code: 'SYSTEM_PROMPTS_REQUIRED'
      });
    } else {
      if (!request.systemPrompts.mainPrefix || request.systemPrompts.mainPrefix.trim().length === 0) {
        warnings.push({
          field: 'systemPrompts.mainPrefix',
          message: 'Main prefix is empty, consider providing system context',
          severity: 'warning',
          code: 'EMPTY_MAIN_PREFIX'
        });
      }
      if (!request.systemPrompts.mainSuffix || request.systemPrompts.mainSuffix.trim().length === 0) {
        warnings.push({
          field: 'systemPrompts.mainSuffix',
          message: 'Main suffix is empty, consider providing closing instructions',
          severity: 'warning',
          code: 'EMPTY_MAIN_SUFFIX'
        });
      }
    }

    // Validate worldbuilding
    if (!request.worldbuilding) {
      errors.push({
        field: 'worldbuilding',
        message: 'Worldbuilding context is required',
        severity: 'error',
        code: 'WORLDBUILDING_REQUIRED'
      });
    } else {
      if (!request.worldbuilding.content || request.worldbuilding.content.trim().length === 0) {
        warnings.push({
          field: 'worldbuilding.content',
          message: 'Worldbuilding content is empty, story context may be limited',
          severity: 'warning',
          code: 'EMPTY_WORLDBUILDING'
        });
      }
    }

    // Validate story summary
    if (!request.storySummary) {
      errors.push({
        field: 'storySummary',
        message: 'Story summary context is required',
        severity: 'error',
        code: 'STORY_SUMMARY_REQUIRED'
      });
    } else {
      if (!request.storySummary.summary || request.storySummary.summary.trim().length === 0) {
        warnings.push({
          field: 'storySummary.summary',
          message: 'Story summary is empty, narrative context may be limited',
          severity: 'warning',
          code: 'EMPTY_STORY_SUMMARY'
        });
      }
    }

    // Validate previous chapters
    if (!Array.isArray(request.previousChapters)) {
      errors.push({
        field: 'previousChapters',
        message: 'Previous chapters must be an array',
        severity: 'error',
        code: 'PREVIOUS_CHAPTERS_ARRAY_REQUIRED'
      });
    } else {
      request.previousChapters.forEach((chapter: any, index: number) => {
        if (!chapter.title || chapter.title.trim().length === 0) {
          warnings.push({
            field: `previousChapters[${index}].title`,
            message: 'Chapter title is empty',
            severity: 'warning',
            code: 'EMPTY_CHAPTER_TITLE'
          });
        }
        if (!chapter.content || chapter.content.trim().length === 0) {
          warnings.push({
            field: `previousChapters[${index}].content`,
            message: 'Chapter content is empty',
            severity: 'warning',
            code: 'EMPTY_CHAPTER_CONTENT'
          });
        }
        if (typeof chapter.number !== 'number' || chapter.number < 1) {
          errors.push({
            field: `previousChapters[${index}].number`,
            message: 'Chapter number must be a positive integer',
            severity: 'error',
            code: 'INVALID_CHAPTER_NUMBER'
          });
        }
      });
    }
  }

  private validateCharacterContext(
    character: any,
    errors: StructuredRequestValidationError[],
    warnings: StructuredRequestValidationError[],
    fieldPrefix = 'character'
  ): void {
    if (!character) {
      errors.push({
        field: fieldPrefix,
        message: 'Character context is required',
        severity: 'error',
        code: 'CHARACTER_REQUIRED'
      });
      return;
    }

    const requiredFields = ['name', 'basicBio', 'personality'];
    requiredFields.forEach(field => {
      if (!character[field] || character[field].trim().length === 0) {
        errors.push({
          field: `${fieldPrefix}.${field}`,
          message: `Character ${field} is required and cannot be empty`,
          severity: 'error',
          code: `CHARACTER_${field.toUpperCase()}_REQUIRED`
        });
      }
    });

    const recommendedFields = ['motivations', 'fears', 'relationships'];
    recommendedFields.forEach(field => {
      if (!character[field] || character[field].trim().length === 0) {
        warnings.push({
          field: `${fieldPrefix}.${field}`,
          message: `Character ${field} is empty, character development may be limited`,
          severity: 'warning',
          code: `CHARACTER_${field.toUpperCase()}_EMPTY`
        });
      }
    });

    // Validate age
    if (typeof character.age !== 'number' || character.age < 0 || character.age > 200) {
      warnings.push({
        field: `${fieldPrefix}.age`,
        message: 'Character age seems unrealistic',
        severity: 'warning',
        code: 'CHARACTER_AGE_UNREALISTIC'
      });
    }
  }

  private validatePlotContext(
    plotContext: any,
    errors: StructuredRequestValidationError[],
    warnings: StructuredRequestValidationError[]
  ): void {
    if (!plotContext) {
      errors.push({
        field: 'plotContext',
        message: 'Plot context is required',
        severity: 'error',
        code: 'PLOT_CONTEXT_REQUIRED'
      });
      return;
    }

    if (!plotContext.plotPoint || plotContext.plotPoint.trim().length === 0) {
      errors.push({
        field: 'plotContext.plotPoint',
        message: 'Plot point is required and cannot be empty',
        severity: 'error',
        code: 'PLOT_POINT_REQUIRED'
      });
    } else if (plotContext.plotPoint.length < 10) {
      warnings.push({
        field: 'plotContext.plotPoint',
        message: 'Plot point is very short, consider providing more detail',
        severity: 'warning',
        code: 'PLOT_POINT_SHORT'
      });
    }

    if (plotContext.plotOutline && plotContext.plotOutline.trim().length === 0) {
      warnings.push({
        field: 'plotContext.plotOutline',
        message: 'Plot outline is empty',
        severity: 'warning',
        code: 'EMPTY_PLOT_OUTLINE'
      });
    }
  }

  private validateFeedbackContext(
    feedbackContext: any,
    errors: StructuredRequestValidationError[],
    warnings: StructuredRequestValidationError[]
  ): void {
    if (!feedbackContext) {
      errors.push({
        field: 'feedbackContext',
        message: 'Feedback context is required',
        severity: 'error',
        code: 'FEEDBACK_CONTEXT_REQUIRED'
      });
      return;
    }

    if (!Array.isArray(feedbackContext.incorporatedFeedback)) {
      errors.push({
        field: 'feedbackContext.incorporatedFeedback',
        message: 'Incorporated feedback must be an array',
        severity: 'error',
        code: 'INCORPORATED_FEEDBACK_ARRAY_REQUIRED'
      });
    } else {
      feedbackContext.incorporatedFeedback.forEach((feedback: any, index: number) => {
        if (!feedback.source || feedback.source.trim().length === 0) {
          warnings.push({
            field: `feedbackContext.incorporatedFeedback[${index}].source`,
            message: 'Feedback source is empty',
            severity: 'warning',
            code: 'EMPTY_FEEDBACK_SOURCE'
          });
        }
        if (!feedback.content || feedback.content.trim().length === 0) {
          warnings.push({
            field: `feedbackContext.incorporatedFeedback[${index}].content`,
            message: 'Feedback content is empty',
            severity: 'warning',
            code: 'EMPTY_FEEDBACK_CONTENT'
          });
        }
      });
    }
  }

  private validatePhaseContext(
    phaseContext: any,
    errors: StructuredRequestValidationError[],
    warnings: StructuredRequestValidationError[]
  ): void {
    const validPhases = ['plot_outline', 'chapter_detail', 'final_edit'];
    if (!validPhases.includes(phaseContext.currentPhase)) {
      errors.push({
        field: 'phaseContext.currentPhase',
        message: `Invalid phase: ${phaseContext.currentPhase}. Must be one of: ${validPhases.join(', ')}`,
        severity: 'error',
        code: 'INVALID_PHASE'
      });
    }

    if (phaseContext.conversationHistory && !Array.isArray(phaseContext.conversationHistory)) {
      errors.push({
        field: 'phaseContext.conversationHistory',
        message: 'Conversation history must be an array',
        severity: 'error',
        code: 'CONVERSATION_HISTORY_ARRAY_REQUIRED'
      });
    }
  }

  // ============================================================================
  // PRIVATE OPTIMIZATION METHODS
  // ============================================================================

  private addCharacterFeedbackOptimizations(
    request: StructuredCharacterFeedbackRequest,
    suggestions: string[]
  ): void {
    if (request.character.relationships && request.character.relationships.length > 500) {
      suggestions.push('Consider summarizing character relationships to reduce token usage');
    }
    if (request.previousChapters.length > 5) {
      suggestions.push('Consider limiting previous chapters to the most recent 3-5 for better performance');
    }
    if (!request.phaseContext) {
      suggestions.push('Adding phase context can improve response relevance');
    }
  }

  private addRaterFeedbackOptimizations(
    request: StructuredRaterFeedbackRequest,
    suggestions: string[]
  ): void {
    if (request.raterPrompt.length > 1000) {
      suggestions.push('Consider shortening rater prompt to reduce token usage');
    }
    if (request.previousChapters.length > 3) {
      suggestions.push('Consider limiting previous chapters for rater feedback to improve focus');
    }
  }

  private addChapterGenerationOptimizations(
    request: StructuredGenerateChapterRequest,
    suggestions: string[]
  ): void {
    if (request.characters.length > 10) {
      suggestions.push('Consider limiting active characters to improve generation focus');
    }
    if (request.feedbackContext.incorporatedFeedback.length > 20) {
      suggestions.push('Consider summarizing incorporated feedback to reduce complexity');
    }
    const totalChapterContent = request.previousChapters.reduce((total, ch) => total + ch.content.length, 0);
    if (totalChapterContent > 50000) {
      suggestions.push('Consider summarizing previous chapters to reduce token usage');
    }
  }

  private addEditorReviewOptimizations(
    request: StructuredEditorReviewRequest,
    suggestions: string[]
  ): void {
    if (request.chapterToReview.length > 10000) {
      suggestions.push('Consider breaking large chapters into sections for more focused review');
    }
    if (!request.reviewFocus || request.reviewFocus.length === 0) {
      suggestions.push('Specifying review focus areas can improve review quality');
    }
  }
}
