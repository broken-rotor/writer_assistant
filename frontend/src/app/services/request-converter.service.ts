/**
 * Request Converter Service
 * 
 * Handles conversion between traditional, enhanced, and structured request formats
 * while maintaining data integrity and backward compatibility.
 */

import { Injectable, inject } from '@angular/core';
import { ContextBuilderService } from './context-builder.service';
import { Story, FeedbackItem } from '../models/story.model';

import {
  CharacterFeedbackRequest,
  RaterFeedbackRequest,
  GenerateChapterRequest,
  EditorReviewRequest,
  EnhancedCharacterFeedbackRequest,
  EnhancedRaterFeedbackRequest,
  EnhancedGenerateChapterRequest,
  EnhancedEditorReviewRequest
} from '../models/story.model';

import {
  StructuredCharacterFeedbackRequest,
  StructuredRaterFeedbackRequest,
  StructuredGenerateChapterRequest,
  StructuredEditorReviewRequest,
  StructuredSystemPrompts,
  StructuredWorldbuilding,
  StructuredStorySummary,
  StructuredCharacterContext,
  StructuredChapterContext,
  StructuredPlotContext,
  StructuredFeedbackContext,
  StructuredPhaseContext,
  RequestConversionOptions,
  RequestConversionResult,
  StructuredRequestValidationError
} from '../models/structured-request.model';

import {
  detectRequestFormat,
  isTraditionalCharacterFeedbackRequest,
  isEnhancedCharacterFeedbackRequest,
  isStructuredCharacterFeedbackRequest,
  isTraditionalRaterFeedbackRequest,
  isEnhancedRaterFeedbackRequest,
  isStructuredRaterFeedbackRequest,
  isTraditionalGenerateChapterRequest,
  isEnhancedGenerateChapterRequest,
  isStructuredGenerateChapterRequest,
  isTraditionalEditorReviewRequest,
  isEnhancedEditorReviewRequest,
  isStructuredEditorReviewRequest
} from '../utils/request-type-guards';

@Injectable({
  providedIn: 'root'
})
export class RequestConverterService {
  private contextBuilderService = inject(ContextBuilderService);

  // ============================================================================
  // PUBLIC API - CONVERSION METHODS
  // ============================================================================

  /**
   * Convert any request format to structured format
   */
  convertToStructured<T>(
    request: any,
    options: RequestConversionOptions = {}
  ): RequestConversionResult<T> {
    const startTime = Date.now();
    const detectionResult = detectRequestFormat(request);
    
    try {
      let convertedRequest: T;
      const errors: StructuredRequestValidationError[] = [];
      const warnings: StructuredRequestValidationError[] = [];

      switch (detectionResult.format) {
        case 'traditional':
          convertedRequest = this.convertTraditionalToStructured(request, options) as T;
          break;
        case 'enhanced':
          convertedRequest = this.convertEnhancedToStructured(request, options) as T;
          break;
        case 'structured':
          convertedRequest = request as T;
          warnings.push({
            field: 'format',
            message: 'Request is already in structured format',
            severity: 'info'
          });
          break;
        default:
          throw new Error(`Unknown request format: ${detectionResult.format}`);
      }

      // Validate after conversion if requested
      if (options.validateAfterConversion) {
        const validationResult = this.validateStructuredRequest(convertedRequest);
        errors.push(...validationResult.errors);
        warnings.push(...validationResult.warnings);
      }

      const conversionTime = Date.now() - startTime;

      return {
        success: true,
        convertedRequest,
        originalFormat: detectionResult.format,
        targetFormat: 'structured',
        errors: errors.length > 0 ? errors : undefined,
        warnings: warnings.length > 0 ? warnings : undefined,
        metadata: {
          conversionTime,
          optimizationsApplied: options.addOptimizationHints ? ['optimization_hints_added'] : undefined
        }
      };
    } catch (error) {
      return {
        success: false,
        originalFormat: detectionResult.format,
        targetFormat: 'structured',
        errors: [{
          field: 'conversion',
          message: `Conversion failed: ${error}`,
          severity: 'error'
        }],
        metadata: {
          conversionTime: Date.now() - startTime
        }
      };
    }
  }

  /**
   * Convert structured request back to traditional format
   */
  convertToTraditional<T>(
    request: any,
    options: RequestConversionOptions = {}
  ): RequestConversionResult<T> {
    const startTime = Date.now();
    
    try {
      let convertedRequest: T;

      if (isStructuredCharacterFeedbackRequest(request)) {
        convertedRequest = this.convertStructuredCharacterFeedbackToTraditional(request) as T;
      } else if (isStructuredRaterFeedbackRequest(request)) {
        convertedRequest = this.convertStructuredRaterFeedbackToTraditional(request) as T;
      } else if (isStructuredGenerateChapterRequest(request)) {
        convertedRequest = this.convertStructuredGenerateChapterToTraditional(request) as T;
      } else if (isStructuredEditorReviewRequest(request)) {
        convertedRequest = this.convertStructuredEditorReviewToTraditional(request) as T;
      } else {
        throw new Error('Unsupported structured request type for conversion to traditional format');
      }

      return {
        success: true,
        convertedRequest,
        originalFormat: 'structured',
        targetFormat: 'traditional',
        metadata: {
          conversionTime: Date.now() - startTime
        }
      };
    } catch (error) {
      return {
        success: false,
        originalFormat: 'structured',
        targetFormat: 'traditional',
        errors: [{
          field: 'conversion',
          message: `Conversion failed: ${error}`,
          severity: 'error'
        }],
        metadata: {
          conversionTime: Date.now() - startTime
        }
      };
    }
  }

  // ============================================================================
  // PRIVATE CONVERSION METHODS - TRADITIONAL TO STRUCTURED
  // ============================================================================

  private convertTraditionalToStructured(request: any, options: RequestConversionOptions): any {
    if (isTraditionalCharacterFeedbackRequest(request)) {
      return this.convertTraditionalCharacterFeedbackToStructured(request, options);
    } else if (isTraditionalRaterFeedbackRequest(request)) {
      return this.convertTraditionalRaterFeedbackToStructured(request, options);
    } else if (isTraditionalGenerateChapterRequest(request)) {
      return this.convertTraditionalGenerateChapterToStructured(request, options);
    } else if (isTraditionalEditorReviewRequest(request)) {
      return this.convertTraditionalEditorReviewToStructured(request, options);
    } else {
      throw new Error('Unsupported traditional request type');
    }
  }

  private convertTraditionalCharacterFeedbackToStructured(
    request: CharacterFeedbackRequest,
    options: RequestConversionOptions
  ): StructuredCharacterFeedbackRequest {
    return {
      systemPrompts: this.convertToStructuredSystemPrompts(request.systemPrompts),
      worldbuilding: this.convertToStructuredWorldbuilding(request.worldbuilding),
      storySummary: this.convertToStructuredStorySummary(request.storySummary),
      previousChapters: this.convertToStructuredChapters(request.previousChapters),
      character: this.convertToStructuredCharacter(request.character),
      plotContext: this.convertToStructuredPlotContext(request.plotPoint),
      requestMetadata: options.preserveMetadata ? {
        timestamp: new Date(),
        requestSource: 'traditional_conversion',
        optimizationHints: options.addOptimizationHints ? ['character_feedback'] : undefined
      } : undefined
    };
  }

  private convertTraditionalRaterFeedbackToStructured(
    request: RaterFeedbackRequest,
    options: RequestConversionOptions
  ): StructuredRaterFeedbackRequest {
    return {
      systemPrompts: this.convertToStructuredSystemPrompts(request.systemPrompts),
      worldbuilding: this.convertToStructuredWorldbuilding(request.worldbuilding),
      storySummary: this.convertToStructuredStorySummary(request.storySummary),
      previousChapters: this.convertToStructuredChapters(request.previousChapters),
      raterPrompt: request.raterPrompt,
      plotContext: this.convertToStructuredPlotContext(request.plotPoint),
      requestMetadata: options.preserveMetadata ? {
        timestamp: new Date(),
        requestSource: 'traditional_conversion',
        optimizationHints: options.addOptimizationHints ? ['rater_feedback'] : undefined
      } : undefined
    };
  }

  private convertTraditionalGenerateChapterToStructured(
    request: GenerateChapterRequest,
    options: RequestConversionOptions
  ): StructuredGenerateChapterRequest {
    return {
      systemPrompts: this.convertToStructuredSystemPrompts(request.systemPrompts),
      worldbuilding: this.convertToStructuredWorldbuilding(request.worldbuilding),
      storySummary: this.convertToStructuredStorySummary(request.storySummary),
      previousChapters: this.convertToStructuredChapters(request.previousChapters),
      characters: request.characters.map(char => this.convertToStructuredCharacter(char)),
      plotContext: this.convertToStructuredPlotContext(request.plotPoint),
      feedbackContext: this.convertToStructuredFeedbackContext(request.incorporatedFeedback),
      requestMetadata: options.preserveMetadata ? {
        timestamp: new Date(),
        requestSource: 'traditional_conversion',
        optimizationHints: options.addOptimizationHints ? ['chapter_generation'] : undefined
      } : undefined
    };
  }

  private convertTraditionalEditorReviewToStructured(
    request: EditorReviewRequest,
    options: RequestConversionOptions
  ): StructuredEditorReviewRequest {
    return {
      systemPrompts: this.convertToStructuredSystemPrompts(request.systemPrompts),
      worldbuilding: this.convertToStructuredWorldbuilding(request.worldbuilding),
      storySummary: this.convertToStructuredStorySummary(request.storySummary),
      previousChapters: this.convertToStructuredChapters(request.previousChapters),
      characters: request.characters.map(char => this.convertToStructuredCharacter(char)),
      chapterToReview: request.chapterToReview,
      requestMetadata: options.preserveMetadata ? {
        timestamp: new Date(),
        requestSource: 'traditional_conversion',
        optimizationHints: options.addOptimizationHints ? ['editor_review'] : undefined
      } : undefined
    };
  }

  // ============================================================================
  // PRIVATE CONVERSION METHODS - ENHANCED TO STRUCTURED
  // ============================================================================

  private convertEnhancedToStructured(request: any, options: RequestConversionOptions): any {
    if (isEnhancedCharacterFeedbackRequest(request)) {
      return this.convertEnhancedCharacterFeedbackToStructured(request, options);
    } else if (isEnhancedRaterFeedbackRequest(request)) {
      return this.convertEnhancedRaterFeedbackToStructured(request, options);
    } else if (isEnhancedGenerateChapterRequest(request)) {
      return this.convertEnhancedGenerateChapterToStructured(request, options);
    } else if (isEnhancedEditorReviewRequest(request)) {
      return this.convertEnhancedEditorReviewToStructured(request, options);
    } else {
      throw new Error('Unsupported enhanced request type');
    }
  }

  private convertEnhancedCharacterFeedbackToStructured(
    request: EnhancedCharacterFeedbackRequest,
    options: RequestConversionOptions
  ): StructuredCharacterFeedbackRequest {
    const structuredRequest = this.convertTraditionalCharacterFeedbackToStructured(request, options);
    
    // Add phase context if available
    if (request.compose_phase || request.phase_context) {
      structuredRequest.phaseContext = this.convertToStructuredPhaseContext(
        request.compose_phase,
        request.phase_context
      );
    }

    return structuredRequest;
  }

  private convertEnhancedRaterFeedbackToStructured(
    request: EnhancedRaterFeedbackRequest,
    options: RequestConversionOptions
  ): StructuredRaterFeedbackRequest {
    const structuredRequest = this.convertTraditionalRaterFeedbackToStructured(request, options);
    
    // Add phase context if available
    if (request.compose_phase || request.phase_context) {
      structuredRequest.phaseContext = this.convertToStructuredPhaseContext(
        request.compose_phase,
        request.phase_context
      );
    }

    return structuredRequest;
  }

  private convertEnhancedGenerateChapterToStructured(
    request: EnhancedGenerateChapterRequest,
    options: RequestConversionOptions
  ): StructuredGenerateChapterRequest {
    const structuredRequest = this.convertTraditionalGenerateChapterToStructured(request, options);
    
    // Add phase context if available
    if (request.compose_phase || request.phase_context) {
      structuredRequest.phaseContext = this.convertToStructuredPhaseContext(
        request.compose_phase,
        request.phase_context
      );
    }

    return structuredRequest;
  }

  private convertEnhancedEditorReviewToStructured(
    request: EnhancedEditorReviewRequest,
    options: RequestConversionOptions
  ): StructuredEditorReviewRequest {
    const structuredRequest = this.convertTraditionalEditorReviewToStructured(request, options);
    
    // Add phase context if available
    if (request.compose_phase || request.phase_context) {
      structuredRequest.phaseContext = this.convertToStructuredPhaseContext(
        request.compose_phase,
        request.phase_context
      );
    }

    return structuredRequest;
  }

  // ============================================================================
  // PRIVATE CONVERSION METHODS - STRUCTURED TO TRADITIONAL
  // ============================================================================

  private convertStructuredCharacterFeedbackToTraditional(
    request: StructuredCharacterFeedbackRequest
  ): CharacterFeedbackRequest {
    return {
      systemPrompts: {
        mainPrefix: request.systemPrompts.mainPrefix,
        mainSuffix: request.systemPrompts.mainSuffix
      },
      worldbuilding: request.worldbuilding.content,
      storySummary: request.storySummary.summary,
      previousChapters: request.previousChapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      character: {
        name: request.character.name,
        basicBio: request.character.basicBio,
        sex: request.character.sex,
        gender: request.character.gender,
        sexualPreference: request.character.sexualPreference,
        age: request.character.age,
        physicalAppearance: request.character.physicalAppearance,
        usualClothing: request.character.usualClothing,
        personality: request.character.personality,
        motivations: request.character.motivations,
        fears: request.character.fears,
        relationships: request.character.relationships
      },
      plotPoint: request.plotContext.plotPoint
    };
  }

  private convertStructuredRaterFeedbackToTraditional(
    request: StructuredRaterFeedbackRequest
  ): RaterFeedbackRequest {
    return {
      systemPrompts: {
        mainPrefix: request.systemPrompts.mainPrefix,
        mainSuffix: request.systemPrompts.mainSuffix
      },
      raterPrompt: request.raterPrompt,
      worldbuilding: request.worldbuilding.content,
      storySummary: request.storySummary.summary,
      previousChapters: request.previousChapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      plotPoint: request.plotContext.plotPoint
    };
  }

  private convertStructuredGenerateChapterToTraditional(
    request: StructuredGenerateChapterRequest
  ): GenerateChapterRequest {
    return {
      systemPrompts: {
        mainPrefix: request.systemPrompts.mainPrefix,
        mainSuffix: request.systemPrompts.mainSuffix,
        assistantPrompt: request.systemPrompts.assistantPrompt || ''
      },
      worldbuilding: request.worldbuilding.content,
      storySummary: request.storySummary.summary,
      previousChapters: request.previousChapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      characters: request.characters.map(char => ({
        name: char.name,
        basicBio: char.basicBio,
        sex: char.sex,
        gender: char.gender,
        sexualPreference: char.sexualPreference,
        age: char.age,
        physicalAppearance: char.physicalAppearance,
        usualClothing: char.usualClothing,
        personality: char.personality,
        motivations: char.motivations,
        fears: char.fears,
        relationships: char.relationships
      })),
      plotPoint: request.plotContext.plotPoint,
      incorporatedFeedback: request.feedbackContext.incorporatedFeedback
    };
  }

  private convertStructuredEditorReviewToTraditional(
    request: StructuredEditorReviewRequest
  ): EditorReviewRequest {
    return {
      systemPrompts: {
        mainPrefix: request.systemPrompts.mainPrefix,
        mainSuffix: request.systemPrompts.mainSuffix,
        editorPrompt: request.systemPrompts.editorPrompt || ''
      },
      worldbuilding: request.worldbuilding.content,
      storySummary: request.storySummary.summary,
      previousChapters: request.previousChapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      characters: request.characters.map(char => ({
        name: char.name,
        basicBio: char.basicBio,
        sex: char.sex,
        gender: char.gender,
        sexualPreference: char.sexualPreference,
        age: char.age,
        physicalAppearance: char.physicalAppearance,
        usualClothing: char.usualClothing,
        personality: char.personality,
        motivations: char.motivations,
        fears: char.fears,
        relationships: char.relationships
      })),
      chapterToReview: request.chapterToReview
    };
  }

  // ============================================================================
  // PRIVATE HELPER METHODS - CONTEXT CONVERSION
  // ============================================================================

  private convertToStructuredSystemPrompts(systemPrompts: any): StructuredSystemPrompts {
    return {
      mainPrefix: systemPrompts.mainPrefix || '',
      mainSuffix: systemPrompts.mainSuffix || '',
      assistantPrompt: systemPrompts.assistantPrompt,
      editorPrompt: systemPrompts.editorPrompt
    };
  }

  private convertToStructuredWorldbuilding(worldbuilding: string): StructuredWorldbuilding {
    return {
      content: worldbuilding,
      lastModified: new Date(),
      wordCount: worldbuilding.split(/\s+/).length
    };
  }

  private convertToStructuredStorySummary(storySummary: string): StructuredStorySummary {
    return {
      summary: storySummary,
      lastModified: new Date(),
      wordCount: storySummary.split(/\s+/).length
    };
  }

  private convertToStructuredCharacter(character: any): StructuredCharacterContext {
    return {
      name: character.name,
      basicBio: character.basicBio,
      sex: character.sex,
      gender: character.gender,
      sexualPreference: character.sexualPreference,
      age: character.age,
      physicalAppearance: character.physicalAppearance,
      usualClothing: character.usualClothing,
      personality: character.personality,
      motivations: character.motivations,
      fears: character.fears,
      relationships: character.relationships,
      isHidden: character.isHidden
    };
  }

  private convertToStructuredChapters(chapters: any[]): StructuredChapterContext[] {
    return chapters.map(ch => ({
      number: ch.number,
      title: ch.title,
      content: ch.content,
      plotPoint: ch.plotPoint,
      wordCount: ch.content ? ch.content.split(/\s+/).length : 0
    }));
  }

  private convertToStructuredPlotContext(plotPoint: string, plotOutline?: string): StructuredPlotContext {
    return {
      plotPoint,
      plotOutline,
      plotOutlineStatus: plotOutline ? 'draft' : undefined
    };
  }

  private convertToStructuredFeedbackContext(incorporatedFeedback: FeedbackItem[]): StructuredFeedbackContext {
    return {
      incorporatedFeedback: incorporatedFeedback.map(feedback => ({
        source: feedback.source,
        type: feedback.type,
        content: feedback.content,
        incorporated: feedback.incorporated
      }))
    };
  }

  private convertToStructuredPhaseContext(
    composePhase?: 'plot_outline' | 'chapter_detail' | 'final_edit',
    phaseContext?: any
  ): StructuredPhaseContext | undefined {
    if (!composePhase && !phaseContext) {
      return undefined;
    }

    return {
      currentPhase: composePhase || 'chapter_detail',
      previousPhaseOutput: phaseContext?.previous_phase_output,
      phaseSpecificInstructions: phaseContext?.phase_specific_instructions,
      conversationHistory: phaseContext?.conversation_history,
      conversationBranchId: phaseContext?.conversation_branch_id
    };
  }

  // ============================================================================
  // PRIVATE VALIDATION METHODS
  // ============================================================================

  private validateStructuredRequest(request: any): { errors: StructuredRequestValidationError[], warnings: StructuredRequestValidationError[] } {
    const errors: StructuredRequestValidationError[] = [];
    const warnings: StructuredRequestValidationError[] = [];

    // Basic validation
    if (!request) {
      errors.push({
        field: 'request',
        message: 'Request is null or undefined',
        severity: 'error'
      });
      return { errors, warnings };
    }

    // Validate system prompts
    if (!request.systemPrompts) {
      errors.push({
        field: 'systemPrompts',
        message: 'System prompts are required',
        severity: 'error'
      });
    } else {
      if (!request.systemPrompts.mainPrefix) {
        warnings.push({
          field: 'systemPrompts.mainPrefix',
          message: 'Main prefix is empty',
          severity: 'warning'
        });
      }
      if (!request.systemPrompts.mainSuffix) {
        warnings.push({
          field: 'systemPrompts.mainSuffix',
          message: 'Main suffix is empty',
          severity: 'warning'
        });
      }
    }

    // Validate worldbuilding
    if (!request.worldbuilding) {
      errors.push({
        field: 'worldbuilding',
        message: 'Worldbuilding context is required',
        severity: 'error'
      });
    } else if (!request.worldbuilding.content) {
      warnings.push({
        field: 'worldbuilding.content',
        message: 'Worldbuilding content is empty',
        severity: 'warning'
      });
    }

    // Validate story summary
    if (!request.storySummary) {
      errors.push({
        field: 'storySummary',
        message: 'Story summary context is required',
        severity: 'error'
      });
    } else if (!request.storySummary.summary) {
      warnings.push({
        field: 'storySummary.summary',
        message: 'Story summary is empty',
        severity: 'warning'
      });
    }

    // Validate previous chapters
    if (!Array.isArray(request.previousChapters)) {
      errors.push({
        field: 'previousChapters',
        message: 'Previous chapters must be an array',
        severity: 'error'
      });
    }

    return { errors, warnings };
  }
}
