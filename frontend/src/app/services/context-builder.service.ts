/**
 * Context Builder Service
 * 
 * Centralizes context building logic for structured data collection.
 * Provides clean, validated context elements to the backend API.
 */

import { Injectable, inject } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { Story, FeedbackItem, ConversationThread, ChapterComposeState } from '../models/story.model';
import {
  SystemPromptsContext,
  WorldbuildingContext,
  StorySummaryContext,
  CharacterContext,
  StructuredCharacter,
  ChaptersContext,
  StructuredChapter,
  PlotContext,
  FeedbackContext,
  ConversationContext,
  StructuredMessage,
  PhaseContext,
  ChapterGenerationContext,
  ContextValidationResult,
  ContextValidationError,
  ContextValidationWarning,
  ContextBuildOptions,
  ContextCacheEntry,
  ContextBuilderResponse
} from '../models/context-builder.model';

import { TokenCountingService } from './token-counting.service';

@Injectable({
  providedIn: 'root'
})
export class ContextBuilderService {
  private tokenCountingService = inject(TokenCountingService);

  // Cache for context elements
  private contextCache = new Map<string, ContextCacheEntry<unknown>>();
  private readonly DEFAULT_CACHE_AGE = 5 * 60 * 1000; // 5 minutes

  // Context update notifications
  private contextUpdated$ = new BehaviorSubject<string>('');

  // ============================================================================
  // PUBLIC API - CORE CONTEXT BUILDERS
  // ============================================================================

  /**
   * Build system prompts context
   */
  buildSystemPromptsContext(
    story: Story,
    options: ContextBuildOptions = {}
  ): ContextBuilderResponse<SystemPromptsContext> {
    try {
      const cacheKey = `system-prompts-${story.id}`;
      
      if (options.useCache !== false) {
        const cached = this.getCachedContext<SystemPromptsContext>(cacheKey, options.maxCacheAge);
        if (cached) {
          return {
            success: true,
            data: cached.data,
            fromCache: true,
            cacheAge: Date.now() - cached.timestamp.getTime()
          };
        }
      }

      const context: SystemPromptsContext = {
        mainPrefix: story.general.systemPrompts.mainPrefix || '',
        mainSuffix: story.general.systemPrompts.mainSuffix || '',
        assistantPrompt: story.general.systemPrompts.assistantPrompt || ''
      };

      const validation = this.validateSystemPromptsContext(context);
      
      if (options.useCache !== false) {
        this.setCachedContext(cacheKey, context, story.id);
      }

      return {
        success: true,
        data: context,
        errors: validation.errors,
        warnings: validation.warnings,
        fromCache: false
      };
    } catch (error) {
      return {
        success: false,
        errors: [{
          field: 'systemPrompts',
          message: `Failed to build system prompts context: ${error}`,
          severity: 'error'
        }]
      };
    }
  }

  /**
   * Build worldbuilding context
   */
  buildWorldbuildingContext(
    story: Story,
    options: ContextBuildOptions = {}
  ): ContextBuilderResponse<WorldbuildingContext> {
    try {
      const cacheKey = `worldbuilding-${story.id}`;
      
      if (options.useCache !== false) {
        const cached = this.getCachedContext<WorldbuildingContext>(cacheKey, options.maxCacheAge);
        if (cached) {
          return {
            success: true,
            data: cached.data,
            fromCache: true,
            cacheAge: Date.now() - cached.timestamp.getTime()
          };
        }
      }

      const worldbuildingContent = story.general.worldbuilding || '';
      const wordCount = this.tokenCountingService.countWords(worldbuildingContent);

      const context: WorldbuildingContext = {
        content: worldbuildingContent,
        isValid: worldbuildingContent.trim().length > 0,
        wordCount: wordCount,
        lastUpdated: new Date()
      };

      const validation = this.validateWorldbuildingContext(context);
      
      if (options.useCache !== false) {
        this.setCachedContext(cacheKey, context, story.id);
      }

      return {
        success: true,
        data: context,
        errors: validation.errors,
        warnings: validation.warnings,
        fromCache: false
      };
    } catch (error) {
      return {
        success: false,
        errors: [{
          field: 'worldbuilding',
          message: `Failed to build worldbuilding context: ${error}`,
          severity: 'error'
        }]
      };
    }
  }

  /**
   * Build story summary context
   */
  buildStorySummaryContext(
    story: Story,
    options: ContextBuildOptions = {}
  ): ContextBuilderResponse<StorySummaryContext> {
    try {
      const cacheKey = `story-summary-${story.id}`;
      
      if (options.useCache !== false) {
        const cached = this.getCachedContext<StorySummaryContext>(cacheKey, options.maxCacheAge);
        if (cached) {
          return {
            success: true,
            data: cached.data,
            fromCache: true,
            cacheAge: Date.now() - cached.timestamp.getTime()
          };
        }
      }

      const summary = story.story.summary || '';
      const wordCount = this.tokenCountingService.countWords(summary);

      const context: StorySummaryContext = {
        summary: summary,
        isValid: summary.trim().length > 0,
        wordCount: wordCount,
        lastUpdated: new Date()
      };

      const validation = this.validateStorySummaryContext(context);
      
      if (options.useCache !== false) {
        this.setCachedContext(cacheKey, context, story.id);
      }

      return {
        success: true,
        data: context,
        errors: validation.errors,
        warnings: validation.warnings,
        fromCache: false
      };
    } catch (error) {
      return {
        success: false,
        errors: [{
          field: 'storySummary',
          message: `Failed to build story summary context: ${error}`,
          severity: 'error'
        }]
      };
    }
  }

  /**
   * Build character context
   */
  buildCharacterContext(
    story: Story,
    options: ContextBuildOptions = {}
  ): ContextBuilderResponse<CharacterContext> {
    try {
      const cacheKey = `characters-${story.id}`;
      
      if (options.useCache !== false) {
        const cached = this.getCachedContext<CharacterContext>(cacheKey, options.maxCacheAge);
        if (cached) {
          return {
            success: true,
            data: cached.data,
            fromCache: true,
            cacheAge: Date.now() - cached.timestamp.getTime()
          };
        }
      }

      const allCharacters = Array.from(story.characters.values());
      const visibleCharacters = allCharacters.filter(c => !c.isHidden);

      const structuredCharacters: StructuredCharacter[] = visibleCharacters.map(character => ({
        name: character.name || '',
        basicBio: character.basicBio || '',
        sex: character.sex || '',
        gender: character.gender || '',
        sexualPreference: character.sexualPreference || '',
        age: character.age || 0,
        physicalAppearance: character.physicalAppearance || '',
        usualClothing: character.usualClothing || '',
        personality: character.personality || '',
        motivations: character.motivations || '',
        fears: character.fears || '',
        relationships: character.relationships || '',
        isHidden: character.isHidden || false
      }));

      const context: CharacterContext = {
        characters: structuredCharacters,
        totalCharacters: allCharacters.length,
        visibleCharacters: visibleCharacters.length,
        lastUpdated: new Date()
      };

      const validation = this.validateCharacterContext(context);
      
      if (options.useCache !== false) {
        this.setCachedContext(cacheKey, context, story.id);
      }

      return {
        success: true,
        data: context,
        errors: validation.errors,
        warnings: validation.warnings,
        fromCache: false
      };
    } catch (error) {
      return {
        success: false,
        errors: [{
          field: 'characters',
          message: `Failed to build character context: ${error}`,
          severity: 'error'
        }]
      };
    }
  }

  /**
   * Build chapters context
   */
  buildChaptersContext(
    story: Story,
    options: ContextBuildOptions = {}
  ): ContextBuilderResponse<ChaptersContext> {
    try {
      const cacheKey = `chapters-${story.id}`;
      
      if (options.useCache !== false) {
        const cached = this.getCachedContext<ChaptersContext>(cacheKey, options.maxCacheAge);
        if (cached) {
          return {
            success: true,
            data: cached.data,
            fromCache: true,
            cacheAge: Date.now() - cached.timestamp.getTime()
          };
        }
      }

      const structuredChapters: StructuredChapter[] = story.story.chapters.map(chapter => ({
        number: chapter.number,
        title: chapter.title || '',
        content: chapter.content || '',
        wordCount: this.tokenCountingService.countWords(chapter.content || ''),
        created: chapter.created || new Date()
      }));

      const totalWordCount = structuredChapters.reduce((sum, chapter) => sum + chapter.wordCount, 0);

      const context: ChaptersContext = {
        chapters: structuredChapters,
        totalChapters: structuredChapters.length,
        totalWordCount: totalWordCount,
        lastUpdated: new Date()
      };

      const validation = this.validateChaptersContext(context);
      
      if (options.useCache !== false) {
        this.setCachedContext(cacheKey, context, story.id);
      }

      return {
        success: true,
        data: context,
        errors: validation.errors,
        warnings: validation.warnings,
        fromCache: false
      };
    } catch (error) {
      return {
        success: false,
        errors: [{
          field: 'chapters',
          message: `Failed to build chapters context: ${error}`,
          severity: 'error'
        }]
      };
    }
  }

  /**
   * Build plot context
   */
  buildPlotContext(
    plotPoint: string,
    _options: ContextBuildOptions = {}
  ): ContextBuilderResponse<PlotContext> {
    try {
      const wordCount = this.tokenCountingService.countWords(plotPoint);

      const context: PlotContext = {
        plotPoint: plotPoint || '',
        isValid: plotPoint.trim().length > 0,
        wordCount: wordCount,
        lastUpdated: new Date()
      };

      const validation = this.validatePlotContext(context);

      return {
        success: true,
        data: context,
        errors: validation.errors,
        warnings: validation.warnings,
        fromCache: false
      };
    } catch (error) {
      return {
        success: false,
        errors: [{
          field: 'plotPoint',
          message: `Failed to build plot context: ${error}`,
          severity: 'error'
        }]
      };
    }
  }

  /**
   * Build feedback context
   */
  buildFeedbackContext(
    incorporatedFeedback: FeedbackItem[] = [],
    selectedFeedback: FeedbackItem[] = [],
    _options: ContextBuildOptions = {}
  ): ContextBuilderResponse<FeedbackContext> {
    try {
      const context: FeedbackContext = {
        incorporatedFeedback: incorporatedFeedback,
        selectedFeedback: selectedFeedback,
        totalFeedbackItems: incorporatedFeedback.length + selectedFeedback.length,
        lastUpdated: new Date()
      };

      const validation = this.validateFeedbackContext(context);

      return {
        success: true,
        data: context,
        errors: validation.errors,
        warnings: validation.warnings,
        fromCache: false
      };
    } catch (error) {
      return {
        success: false,
        errors: [{
          field: 'feedback',
          message: `Failed to build feedback context: ${error}`,
          severity: 'error'
        }]
      };
    }
  }

  /**
   * Build conversation context
   */
  buildConversationContext(
    conversationThread?: ConversationThread,
    maxMessages = 10,
    _options: ContextBuildOptions = {}
  ): ContextBuilderResponse<ConversationContext> {
    try {
      if (!conversationThread) {
        return {
          success: true,
          data: {
            messages: [],
            branchId: '',
            totalMessages: 0,
            recentMessages: [],
            lastUpdated: new Date()
          },
          fromCache: false
        };
      }

      const allMessages: StructuredMessage[] = conversationThread.messages.map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: msg.timestamp.toISOString(),
        messageId: msg.id
      }));

      const recentMessages = allMessages.slice(-maxMessages);

      const context: ConversationContext = {
        messages: allMessages,
        branchId: conversationThread.currentBranchId || '',
        totalMessages: allMessages.length,
        recentMessages: recentMessages,
        lastUpdated: new Date()
      };

      const validation = this.validateConversationContext(context);

      return {
        success: true,
        data: context,
        errors: validation.errors,
        warnings: validation.warnings,
        fromCache: false
      };
    } catch (error) {
      return {
        success: false,
        errors: [{
          field: 'conversation',
          message: `Failed to build conversation context: ${error}`,
          severity: 'error'
        }]
      };
    }
  }

  /**
   * Build phase context
   */
  buildPhaseContext(
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string,
    _options: ContextBuildOptions = {}
  ): ContextBuilderResponse<PhaseContext> {
    try {
      if (!chapterComposeState) {
        return {
          success: true,
          data: {
            currentPhase: '',
            isValid: false
          },
          fromCache: false
        };
      }

      const context: PhaseContext = {
        currentPhase: chapterComposeState.currentPhase,
        isValid: true
      };

      // Add previous phase output based on current phase
      const currentPhase = chapterComposeState.currentPhase;
      if (currentPhase === 'chapter_detail' && chapterComposeState.phases.plotOutline.status === 'completed') {
        const outlineItems = Array.from(chapterComposeState.phases.plotOutline.outline.items.values());
        context.previousPhaseOutput = outlineItems
          .sort((a, b) => a.order - b.order)
          .map(item => `${item.title}: ${item.description}`)
          .join('\n\n');
      } else if (currentPhase === 'final_edit' && chapterComposeState.phases.chapterDetailer.status === 'completed') {
        context.previousPhaseOutput = chapterComposeState.phases.chapterDetailer.chapterDraft.content;
      }

      // Add phase-specific instructions
      if (additionalInstructions) {
        context.phaseSpecificInstructions = additionalInstructions;
      }

      // Add conversation history if available
      if (conversationThread && conversationThread.messages.length > 0) {
        const recentMessages = conversationThread.messages.slice(-5);
        context.conversationHistory = recentMessages.map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content,
          timestamp: msg.timestamp.toISOString()
        }));
        context.conversationBranchId = conversationThread.currentBranchId;
      }

      const validation = this.validatePhaseContext(context);

      return {
        success: true,
        data: context,
        errors: validation.errors,
        warnings: validation.warnings,
        fromCache: false
      };
    } catch (error) {
      return {
        success: false,
        errors: [{
          field: 'phase',
          message: `Failed to build phase context: ${error}`,
          severity: 'error'
        }]
      };
    }
  }

  // ============================================================================
  // PUBLIC API - COMPOSITE CONTEXT BUILDERS
  // ============================================================================

  /**
   * Build complete chapter generation context
   */
  buildChapterGenerationContext(
    story: Story,
    plotPoint: string,
    incorporatedFeedback: FeedbackItem[] = [],
    conversationThread?: ConversationThread,
    chapterComposeState?: ChapterComposeState,
    additionalInstructions?: string,
    options: ContextBuildOptions = {}
  ): ContextBuilderResponse<ChapterGenerationContext> {
    try {
      const systemPromptsResult = this.buildSystemPromptsContext(story, options);
      const worldbuildingResult = this.buildWorldbuildingContext(story, options);
      const storySummaryResult = this.buildStorySummaryContext(story, options);
      const charactersResult = this.buildCharacterContext(story, options);
      const chaptersResult = this.buildChaptersContext(story, options);
      const plotResult = this.buildPlotContext(plotPoint, options);
      const feedbackResult = this.buildFeedbackContext(incorporatedFeedback, [], options);

      const errors: ContextValidationError[] = [];
      const warnings: ContextValidationWarning[] = [];

      // Collect all errors and warnings
      [systemPromptsResult, worldbuildingResult, storySummaryResult, charactersResult, chaptersResult, plotResult, feedbackResult]
        .forEach(result => {
          if (result.errors) errors.push(...result.errors);
          if (result.warnings) warnings.push(...result.warnings);
        });

      // Check if any required context failed
      if (!systemPromptsResult.success || !worldbuildingResult.success || !storySummaryResult.success || 
          !charactersResult.success || !chaptersResult.success || !plotResult.success || !feedbackResult.success) {
        return {
          success: false,
          errors: errors
        };
      }

      const context: ChapterGenerationContext = {
        systemPrompts: systemPromptsResult.data!,
        worldbuilding: worldbuildingResult.data!,
        storySummary: storySummaryResult.data!,
        characters: charactersResult.data!,
        previousChapters: chaptersResult.data!,
        plotPoint: plotResult.data!,
        feedback: feedbackResult.data!
      };

      // Add optional contexts
      if (conversationThread) {
        const conversationResult = this.buildConversationContext(conversationThread, 10, options);
        if (conversationResult.success && conversationResult.data) {
          context.conversation = conversationResult.data;
          if (conversationResult.errors) errors.push(...conversationResult.errors);
          if (conversationResult.warnings) warnings.push(...conversationResult.warnings);
        }
      }

      if (chapterComposeState) {
        const phaseResult = this.buildPhaseContext(chapterComposeState, conversationThread, additionalInstructions, options);
        if (phaseResult.success && phaseResult.data) {
          context.phase = phaseResult.data;
          if (phaseResult.errors) errors.push(...phaseResult.errors);
          if (phaseResult.warnings) warnings.push(...phaseResult.warnings);
        }
      }

      return {
        success: true,
        data: context,
        errors: errors.length > 0 ? errors : undefined,
        warnings: warnings.length > 0 ? warnings : undefined,
        fromCache: false
      };
    } catch (error) {
      return {
        success: false,
        errors: [{
          field: 'chapterGeneration',
          message: `Failed to build chapter generation context: ${error}`,
          severity: 'error'
        }]
      };
    }
  }

  // ============================================================================
  // CACHE MANAGEMENT
  // ============================================================================

  private getCachedContext<T>(key: string, maxAge?: number): ContextCacheEntry<T> | null {
    const entry = this.contextCache.get(key);
    if (!entry) return null;

    const age = Date.now() - entry.timestamp.getTime();
    const maxCacheAge = maxAge || this.DEFAULT_CACHE_AGE;

    if (age > maxCacheAge || !entry.isValid) {
      this.contextCache.delete(key);
      return null;
    }

    return entry;
  }

  private setCachedContext<T>(key: string, data: T, storyVersion: string): void {
    const entry: ContextCacheEntry<T> = {
      data,
      timestamp: new Date(),
      storyVersion,
      isValid: true
    };
    this.contextCache.set(key, entry);
  }

  /**
   * Clear all cached context
   */
  clearCache(): void {
    this.contextCache.clear();
  }

  /**
   * Clear cached context for specific story
   */
  clearStoryCache(storyId: string): void {
    const keysToDelete = Array.from(this.contextCache.keys())
      .filter(key => key.includes(storyId));
    keysToDelete.forEach(key => this.contextCache.delete(key));
  }

  // ============================================================================
  // VALIDATION METHODS
  // ============================================================================

  private validateSystemPromptsContext(context: SystemPromptsContext): ContextValidationResult {
    const errors: ContextValidationError[] = [];
    const warnings: ContextValidationWarning[] = [];

    if (!context.mainPrefix.trim()) {
      warnings.push({
        field: 'mainPrefix',
        message: 'Main prefix is empty',
        suggestion: 'Consider adding a main prefix for better AI guidance'
      });
    }

    if (!context.assistantPrompt.trim()) {
      errors.push({
        field: 'assistantPrompt',
        message: 'Assistant prompt is required',
        severity: 'error'
      });
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  private validateWorldbuildingContext(context: WorldbuildingContext): ContextValidationResult {
    const errors: ContextValidationError[] = [];
    const warnings: ContextValidationWarning[] = [];

    if (!context.isValid) {
      warnings.push({
        field: 'content',
        message: 'Worldbuilding content is empty',
        suggestion: 'Add worldbuilding details to improve story consistency'
      });
    }

    if (context.wordCount > 5000) {
      warnings.push({
        field: 'content',
        message: 'Worldbuilding content is very long',
        suggestion: 'Consider summarizing key points for better performance'
      });
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  private validateStorySummaryContext(context: StorySummaryContext): ContextValidationResult {
    const errors: ContextValidationError[] = [];
    const warnings: ContextValidationWarning[] = [];

    if (!context.isValid) {
      warnings.push({
        field: 'summary',
        message: 'Story summary is empty',
        suggestion: 'Add a story summary to provide context for AI generation'
      });
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  private validateCharacterContext(context: CharacterContext): ContextValidationResult {
    const errors: ContextValidationError[] = [];
    const warnings: ContextValidationWarning[] = [];

    if (context.visibleCharacters === 0) {
      warnings.push({
        field: 'characters',
        message: 'No visible characters found',
        suggestion: 'Add characters to improve story generation'
      });
    }

    context.characters.forEach((character, index) => {
      if (!character.name.trim()) {
        errors.push({
          field: `characters[${index}].name`,
          message: 'Character name is required',
          severity: 'error'
        });
      }
    });

    return { isValid: errors.length === 0, errors, warnings };
  }

  private validateChaptersContext(context: ChaptersContext): ContextValidationResult {
    const errors: ContextValidationError[] = [];
    const warnings: ContextValidationWarning[] = [];

    if (context.totalChapters > 50) {
      warnings.push({
        field: 'chapters',
        message: 'Large number of chapters may impact performance',
        suggestion: 'Consider using chapter summaries for older chapters'
      });
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  private validatePlotContext(context: PlotContext): ContextValidationResult {
    const errors: ContextValidationError[] = [];
    const warnings: ContextValidationWarning[] = [];

    if (!context.isValid) {
      errors.push({
        field: 'plotPoint',
        message: 'Plot point is required for chapter generation',
        severity: 'error'
      });
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  private validateFeedbackContext(context: FeedbackContext): ContextValidationResult {
    const errors: ContextValidationError[] = [];
    const warnings: ContextValidationWarning[] = [];

    if (context.totalFeedbackItems > 20) {
      warnings.push({
        field: 'feedback',
        message: 'Large number of feedback items may impact performance',
        suggestion: 'Consider prioritizing the most relevant feedback'
      });
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  private validateConversationContext(context: ConversationContext): ContextValidationResult {
    const errors: ContextValidationError[] = [];
    const warnings: ContextValidationWarning[] = [];

    if (context.totalMessages > 100) {
      warnings.push({
        field: 'messages',
        message: 'Large conversation history may impact performance',
        suggestion: 'Consider using only recent messages for context'
      });
    }

    return { isValid: errors.length === 0, errors, warnings };
  }

  private validatePhaseContext(context: PhaseContext): ContextValidationResult {
    const errors: ContextValidationError[] = [];
    const warnings: ContextValidationWarning[] = [];

    if (!context.currentPhase) {
      errors.push({
        field: 'currentPhase',
        message: 'Current phase is required',
        severity: 'error'
      });
    }

    return { isValid: errors.length === 0, errors, warnings };
  }
}
