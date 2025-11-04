import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { ContextBuilderService } from './context-builder.service';
import { RequestConverterService } from './request-converter.service';
import { RequestValidatorService } from './request-validator.service';
import { RequestOptimizerService } from './request-optimizer.service';
import {
  Story,
  Character,
  Rater,
  GenerateChapterRequest,
  GenerateChapterResponse,
  ModifyChapterRequest,
  ModifyChapterResponse,
  FleshOutRequest,
  FleshOutResponse,
  GenerateCharacterDetailsRequest,
  GenerateCharacterDetailsResponse,
  RegenerateBioRequest,
  RegenerateBioResponse,
  PlotOutline,
  PlotOutlineFeedback,
  // Enhanced interfaces with phase support
  EnhancedCharacterFeedbackRequest,
  EnhancedRaterFeedbackRequest,
  EnhancedGenerateChapterRequest,
  EnhancedEditorReviewRequest,
  ApiPhaseContext,
  ChapterComposeState,
  ConversationThread,
  // Legacy request/response types still needed
  CharacterFeedbackRequest,
  CharacterFeedbackResponse,
  RaterFeedbackRequest,
  RaterFeedbackResponse,
  EditorReviewRequest,
  EditorReviewResponse
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
import { StructuredCharacter } from '../models/context-builder.model';
import { transformToStructuredContext, transformToFleshOutStructuredContext } from '../utils/context-transformer';

@Injectable({
  providedIn: 'root'
})
export class GenerationService {
  private apiService = inject(ApiService);
  private contextBuilderService = inject(ContextBuilderService);
  private requestConverterService = inject(RequestConverterService);
  private requestValidatorService = inject(RequestValidatorService);
  private requestOptimizerService = inject(RequestOptimizerService);







  /**
   * Generate chapter using ContextBuilderService
   * This is the new structured approach that replaces manual context building
   */
  generateChapter(story: Story): Observable<GenerateChapterResponse> {
    try {
      // Build structured context using ContextBuilderService
      const contextResult = this.contextBuilderService.buildChapterGenerationContext(
        story,
        story.chapterCreation.plotPoint,
        story.chapterCreation.incorporatedFeedback
      );

      // Check if context building was successful
      if (!contextResult.success || !contextResult.data) {
        throw new Error('Failed to build required context for chapter generation');
      }

      const context = contextResult.data;

      // Build structured request using structured context
      const request: StructuredGenerateChapterRequest = {
        systemPrompts: {
          mainPrefix: context.systemPrompts.mainPrefix,
          mainSuffix: context.systemPrompts.mainSuffix,
          assistantPrompt: this.buildChapterGenerationPrompt(story, context.plotPoint.plotPoint)
        },
        worldbuilding: { content: context.worldbuilding.content },
        storySummary: { summary: context.storySummary.summary },
        plotContext: { plotPoint: context.plotPoint.plotPoint },
        feedbackContext: { incorporatedFeedback: context.feedback.incorporatedFeedback },
        previousChapters: context.previousChapters.chapters.map(ch => ({
          number: ch.number,
          title: ch.title,
          content: ch.content
        })),
        characters: context.characters.characters.map(c => ({
          name: c.name,
          basicBio: c.basicBio,
          sex: c.sex,
          gender: c.gender,
          sexualPreference: c.sexualPreference,
          age: c.age,
          physicalAppearance: c.physicalAppearance,
          usualClothing: c.usualClothing,
          personality: c.personality,
          motivations: c.motivations,
          fears: c.fears,
          relationships: c.relationships
        }))
      };

      return this.apiService.generateChapter(request);
    } catch (error) {
      throw new Error(`Failed to generate chapter with structured context: ${error}`);
    }
  }

  // Modify Chapter
  modifyChapter(
    story: Story,
    currentChapterText: string,
    userRequest: string,
    onProgress?: (phase: string, message: string, progress: number) => void
  ): Observable<ModifyChapterResponse> {
    const request: ModifyChapterRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      previousChapters: story.story.chapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      currentChapter: currentChapterText,
      userRequest: userRequest
    };

    return this.apiService.modifyChapter(request, onProgress);
  }



  // Flesh Out (for plot points or worldbuilding)
  fleshOut(
    story: Story,
    textToFleshOut: string,
    context: string
  ): Observable<FleshOutResponse> {
    // Transform legacy data to structured context
    const legacyData = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      textToFleshOut: textToFleshOut,
      context: context
    };

    const structuredContext = transformToFleshOutStructuredContext(legacyData);

    const request: FleshOutRequest = {
      textToFleshOut: textToFleshOut,
      context: context,
      structured_context: structuredContext
    };

    return this.apiService.fleshOut(request);
  }

  // Generate Character Details
  generateCharacterDetails(
    story: Story,
    basicBio: string,
    existingCharacters: Character[]
  ): Observable<GenerateCharacterDetailsResponse> {
    // Transform legacy data to structured context
    const legacyData = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      basicBio: basicBio,
      existingCharacters: existingCharacters
    };

    const structuredContext = transformToStructuredContext(legacyData);

    const request: GenerateCharacterDetailsRequest = {
      basicBio: basicBio,
      existingCharacters: existingCharacters.map(c => ({
        name: c.name,
        basicBio: c.basicBio,
        relationships: c.relationships
      })),
      structured_context: structuredContext
    };

    return this.apiService.generateCharacterDetails(request);
  }

  // Regenerate Bio from Character Details
  regenerateBio(
    story: Story,
    character: Character
  ): Observable<RegenerateBioResponse> {
    // Transform legacy data to structured context (optional for bio regeneration)
    const legacyData = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      basicBio: character.basicBio,
      existingCharacters: []
    };

    const structuredContext = transformToStructuredContext(legacyData);

    const request: RegenerateBioRequest = {
      name: character.name,
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
      structured_context: structuredContext
    };

    return this.apiService.regenerateBio(request);
  }

  // Regenerate Relationships for a Character
  regenerateRelationships(
    story: Story,
    character: Character,
    otherCharacters: Character[]
  ): Observable<GenerateCharacterDetailsResponse> {
    // Transform legacy data to structured context
    const legacyData = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      basicBio: character.basicBio,
      existingCharacters: [character, ...otherCharacters]
    };

    const structuredContext = transformToStructuredContext(legacyData);

    // Use the same endpoint but we'll only extract the relationships field
    const request: GenerateCharacterDetailsRequest = {
      basicBio: character.basicBio,
      existingCharacters: otherCharacters.map(c => ({
        name: c.name,
        basicBio: c.basicBio,
        relationships: c.relationships
      })),
      structured_context: structuredContext
    };

    return this.apiService.generateCharacterDetails(request);
  }

  // Phase 2 Specific Methods for Chapter Detailer

  // Generate Chapter from Plot Outline
  generateChapterFromOutline(
    story: Story,
    outlineItems: {title: string, description: string}[]
  ): Observable<StructuredGenerateChapterResponse> {
    const plotPoint = outlineItems.map(item => `${item.title}: ${item.description}`).join('\n\n');
    
    const request: StructuredGenerateChapterRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt
      },
      worldbuilding: { content: story.general.worldbuilding },
      storySummary: { summary: story.story.summary },
      plotContext: { plotPoint: plotPoint },
      feedbackContext: { incorporatedFeedback: [] },
      previousChapters: story.story.chapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      characters: Array.from(story.characters.values())
        .filter(c => !c.isHidden)
        .map(c => ({
          name: c.name,
          basicBio: c.basicBio,
          sex: c.sex,
          gender: c.gender,
          sexualPreference: c.sexualPreference,
          age: c.age,
          physicalAppearance: c.physicalAppearance,
          usualClothing: c.usualClothing,
          personality: c.personality,
          motivations: c.motivations,
          fears: c.fears,
          relationships: c.relationships
        }))
    };

    return this.apiService.generateChapter(request);
  }

  // Continue Writing Chapter
  continueChapter(
    story: Story,
    currentChapterContent: string,
    continuationPrompt?: string,
    onProgress?: (phase: string, message: string, progress: number) => void
  ): Observable<ModifyChapterResponse> {
    const defaultPrompt = 'Continue writing this chapter from where it left off, maintaining the same tone, style, and narrative flow.';
    const prompt = continuationPrompt || defaultPrompt;
    
    const request: ModifyChapterRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      previousChapters: story.story.chapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      currentChapter: currentChapterContent,
      userRequest: `${prompt}\n\nCurrent chapter content:\n${currentChapterContent}`
    };

    return this.apiService.modifyChapter(request, onProgress);
  }

  // Regenerate Chapter with Feedback
  regenerateChapterWithFeedback(
    story: Story,
    currentChapterContent: string,
    feedbackItems: {source: string, content: string, type: string}[],
    userInstructions?: string,
    onProgress?: (phase: string, message: string, progress: number) => void
  ): Observable<ModifyChapterResponse> {
    const feedbackText = feedbackItems.map(item => 
      `${item.source} (${item.type}): ${item.content}`
    ).join('\n');
    
    const incorporationPrompt = [
      'Please revise this chapter by incorporating the following feedback:',
      '',
      feedbackText,
      '',
      userInstructions ? `Additional instructions: ${userInstructions}` : '',
      '',
      'Maintain the overall narrative flow while addressing the feedback points.'
    ].filter(line => line !== undefined).join('\n');

    const request: ModifyChapterRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      previousChapters: story.story.chapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      currentChapter: currentChapterContent,
      userRequest: incorporationPrompt
    };

    return this.apiService.modifyChapter(request, onProgress);
  }

  /**
   * Regenerate chapter with feedback using ContextBuilderService
   * This is the new structured approach that replaces manual context building
   */
  regenerateChapterWithFeedbackStructured(
    story: Story,
    currentChapterContent: string,
    feedbackItems: {source: string, content: string, type: string}[],
    userInstructions?: string,
    onProgress?: (phase: string, message: string, progress: number) => void
  ): Observable<ModifyChapterResponse> {
    try {
      // Build structured context using ContextBuilderService
      const systemPromptsResult = this.contextBuilderService.buildSystemPromptsContext(story);
      const worldbuildingResult = this.contextBuilderService.buildWorldbuildingContext(story);
      const storySummaryResult = this.contextBuilderService.buildStorySummaryContext(story);
      const chaptersResult = this.contextBuilderService.buildChaptersContext(story);

      // Check if context building was successful
      if (!systemPromptsResult.success || !worldbuildingResult.success || 
          !storySummaryResult.success || !chaptersResult.success) {
        throw new Error('Failed to build required context for chapter modification');
      }

      // Build feedback text
      const feedbackText = feedbackItems.map(item => 
        `${item.source} (${item.type}): ${item.content}`
      ).join('\n');
      
      const incorporationPrompt = [
        'Please revise this chapter by incorporating the following feedback:',
        '',
        feedbackText,
        '',
        userInstructions ? `Additional instructions: ${userInstructions}` : '',
        '',
        'Maintain the overall narrative flow while addressing the feedback points.'
      ].filter(line => line !== undefined).join('\n');

      // Build request using structured context
      const request: ModifyChapterRequest = {
        systemPrompts: {
          mainPrefix: systemPromptsResult.data!.mainPrefix,
          mainSuffix: systemPromptsResult.data!.mainSuffix,
          assistantPrompt: systemPromptsResult.data!.assistantPrompt
        },
        worldbuilding: worldbuildingResult.data!.content,
        storySummary: storySummaryResult.data!.summary,
        previousChapters: chaptersResult.data!.chapters.map(ch => ({
          number: ch.number,
          title: ch.title,
          content: ch.content
        })),
        currentChapter: currentChapterContent,
        userRequest: incorporationPrompt
      };

      return this.apiService.modifyChapter(request, onProgress);
    } catch (error) {
      throw new Error(`Failed to regenerate chapter with structured context: ${error}`);
    }
  }

  // Generate Chapter Variation
  generateChapterVariation(
    story: Story,
    baseChapterContent: string,
    variationPrompt: string,
    onProgress?: (phase: string, message: string, progress: number) => void
  ): Observable<ModifyChapterResponse> {
    const request: ModifyChapterRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      previousChapters: story.story.chapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      currentChapter: baseChapterContent,
      userRequest: `Create a variation of this chapter with the following changes: ${variationPrompt}\n\nBase chapter:\n${baseChapterContent}`
    };

    return this.apiService.modifyChapter(request, onProgress);
  }

  // Refine Chapter Section
  refineChapterSection(
    story: Story,
    fullChapterContent: string,
    sectionToRefine: string,
    refinementInstructions: string,
    onProgress?: (phase: string, message: string, progress: number) => void
  ): Observable<ModifyChapterResponse> {
    const request: ModifyChapterRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      previousChapters: story.story.chapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      currentChapter: fullChapterContent,
      userRequest: `Please refine this specific section of the chapter: "${sectionToRefine}"\n\nRefinement instructions: ${refinementInstructions}\n\nFull chapter context:\n${fullChapterContent}`
    };

    return this.apiService.modifyChapter(request, onProgress);
  }

  // ============================================================================
  // PHASE-AWARE METHODS FOR THREE-PHASE CHAPTER COMPOSE SYSTEM (WRI-49)
  // ============================================================================

  /**
   * Helper method to build phase context from chapter compose state
   */
  private buildPhaseContext(
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string
  ): ApiPhaseContext | undefined {
    if (!chapterComposeState) {
      return undefined;
    }

    const context: ApiPhaseContext = {};

    // Add previous phase output based on current phase
    const currentPhase = chapterComposeState.currentPhase;
    if (currentPhase === 'chapter_detail' && chapterComposeState.phases.plotOutline.status === 'completed') {
      // Get plot outline as previous phase output
      const outlineItems = Array.from(chapterComposeState.phases.plotOutline.outline.items.values());
      context.previous_phase_output = outlineItems
        .sort((a, b) => a.order - b.order)
        .map(item => `${item.title}: ${item.description}`)
        .join('\n\n');
    } else if (currentPhase === 'final_edit' && chapterComposeState.phases.chapterDetailer.status === 'completed') {
      // Get chapter draft as previous phase output
      context.previous_phase_output = chapterComposeState.phases.chapterDetailer.chapterDraft.content;
    }

    // Add phase-specific instructions
    if (additionalInstructions) {
      context.phase_specific_instructions = additionalInstructions;
    }

    // Add conversation history if available
    if (conversationThread && conversationThread.messages.length > 0) {
      // Get last 5 messages for context
      const recentMessages = conversationThread.messages.slice(-5);
      context.conversation_history = recentMessages.map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: msg.timestamp.toISOString()
      }));
      context.conversation_branch_id = conversationThread.currentBranchId;
    }

    return Object.keys(context).length > 0 ? context : undefined;
  }

  /**
   * Phase-aware character feedback request
   */
  requestCharacterFeedbackWithPhase(
    story: Story,
    character: Character,
    plotPoint: string,
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string
  ): Observable<CharacterFeedbackResponse> {
    const baseRequest: CharacterFeedbackRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      previousChapters: story.story.chapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      character: {
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
        relationships: character.relationships
      },
      plotPoint: plotPoint
    };

    const enhancedRequest: EnhancedCharacterFeedbackRequest = {
      ...baseRequest,
      compose_phase: chapterComposeState?.currentPhase,
      phase_context: this.buildPhaseContext(chapterComposeState, conversationThread, additionalInstructions)
    };

    // Convert to structured request and use new API method
    const structuredRequest: StructuredCharacterFeedbackRequest = {
      worldbuilding: { content: enhancedRequest.worldbuilding },
      storySummary: { summary: enhancedRequest.storySummary },
      plotContext: { plotPoint: enhancedRequest.plotPoint },
      character: enhancedRequest.character,
      previousChapters: enhancedRequest.previousChapters,
      systemPrompts: enhancedRequest.systemPrompts,
      phaseContext: enhancedRequest.phase_context ? {
        currentPhase: enhancedRequest.compose_phase || 'chapter_detail',
        previousPhaseOutput: enhancedRequest.phase_context.previous_phase_output,
        phaseSpecificInstructions: enhancedRequest.phase_context.phase_specific_instructions,
        conversationHistory: enhancedRequest.phase_context.conversation_history,
        conversationBranchId: enhancedRequest.phase_context.conversation_branch_id
      } : undefined
    };
    return this.apiService.requestCharacterFeedback(structuredRequest);
  }

  /**
   * Phase-aware rater feedback request
   */
  requestRaterFeedbackWithPhase(
    story: Story,
    rater: Rater,
    plotPoint: string,
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string
  ): Observable<RaterFeedbackResponse> {
    const baseRequest: RaterFeedbackRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix
      },
      raterPrompt: rater.systemPrompt,
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      previousChapters: story.story.chapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      plotPoint: plotPoint
    };

    const enhancedRequest: EnhancedRaterFeedbackRequest = {
      ...baseRequest,
      compose_phase: chapterComposeState?.currentPhase,
      phase_context: this.buildPhaseContext(chapterComposeState, conversationThread, additionalInstructions)
    };

    // Convert to structured request and use new API method
    const structuredRequest: StructuredRaterFeedbackRequest = {
      worldbuilding: { content: enhancedRequest.worldbuilding },
      storySummary: { summary: enhancedRequest.storySummary },
      plotContext: { plotPoint: enhancedRequest.plotPoint },
      raterPrompt: enhancedRequest.raterPrompt,
      previousChapters: enhancedRequest.previousChapters,
      systemPrompts: enhancedRequest.systemPrompts,
      phaseContext: enhancedRequest.phase_context ? {
        currentPhase: enhancedRequest.compose_phase || 'chapter_detail',
        previousPhaseOutput: enhancedRequest.phase_context.previous_phase_output,
        phaseSpecificInstructions: enhancedRequest.phase_context.phase_specific_instructions,
        conversationHistory: enhancedRequest.phase_context.conversation_history,
        conversationBranchId: enhancedRequest.phase_context.conversation_branch_id
      } : undefined
    };
    return this.apiService.requestRaterFeedback(structuredRequest);
  }

  /**
   * Phase-aware chapter generation
   */
  generateChapterWithPhase(
    story: Story,
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string
  ): Observable<GenerateChapterResponse> {
    const baseRequest: GenerateChapterRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      previousChapters: story.story.chapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      characters: Array.from(story.characters.values())
        .filter(c => !c.isHidden)
        .map(c => ({
          name: c.name,
          basicBio: c.basicBio,
          sex: c.sex,
          gender: c.gender,
          sexualPreference: c.sexualPreference,
          age: c.age,
          physicalAppearance: c.physicalAppearance,
          usualClothing: c.usualClothing,
          personality: c.personality,
          motivations: c.motivations,
          fears: c.fears,
          relationships: c.relationships
        })),
      plotPoint: story.chapterCreation.plotPoint,
      incorporatedFeedback: story.chapterCreation.incorporatedFeedback
    };

    const enhancedRequest: EnhancedGenerateChapterRequest = {
      ...baseRequest,
      compose_phase: chapterComposeState?.currentPhase,
      phase_context: this.buildPhaseContext(chapterComposeState, conversationThread, additionalInstructions)
    };

    // Convert to structured request and use new API method
    const structuredRequest: StructuredGenerateChapterRequest = {
      worldbuilding: { content: enhancedRequest.worldbuilding },
      storySummary: { summary: enhancedRequest.storySummary },
      plotContext: { plotPoint: enhancedRequest.plotPoint },
      feedbackContext: { incorporatedFeedback: enhancedRequest.incorporatedFeedback },
      characters: enhancedRequest.characters,
      previousChapters: enhancedRequest.previousChapters,
      systemPrompts: enhancedRequest.systemPrompts,
      phaseContext: enhancedRequest.phase_context ? {
        currentPhase: enhancedRequest.compose_phase || 'chapter_detail',
        previousPhaseOutput: enhancedRequest.phase_context.previous_phase_output,
        phaseSpecificInstructions: enhancedRequest.phase_context.phase_specific_instructions,
        conversationHistory: enhancedRequest.phase_context.conversation_history,
        conversationBranchId: enhancedRequest.phase_context.conversation_branch_id
      } : undefined
    };
    return this.apiService.generateChapter(structuredRequest);
  }

  /**
   * Phase-aware editor review
   */
  requestEditorReviewWithPhase(
    story: Story,
    chapterText: string,
    chapterComposeState?: ChapterComposeState,
    conversationThread?: ConversationThread,
    additionalInstructions?: string
  ): Observable<EditorReviewResponse> {
    const baseRequest: EditorReviewRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        editorPrompt: story.general.systemPrompts.editorPrompt
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      previousChapters: story.story.chapters.map(ch => ({
        number: ch.number,
        title: ch.title,
        content: ch.content
      })),
      characters: Array.from(story.characters.values())
        .filter(c => !c.isHidden)
        .map(c => ({
          name: c.name,
          basicBio: c.basicBio,
          sex: c.sex,
          gender: c.gender,
          sexualPreference: c.sexualPreference,
          age: c.age,
          physicalAppearance: c.physicalAppearance,
          usualClothing: c.usualClothing,
          personality: c.personality,
          motivations: c.motivations,
          fears: c.fears,
          relationships: c.relationships
        })),
      chapterToReview: chapterText
    };

    const enhancedRequest: EnhancedEditorReviewRequest = {
      ...baseRequest,
      compose_phase: chapterComposeState?.currentPhase,
      phase_context: this.buildPhaseContext(chapterComposeState, conversationThread, additionalInstructions)
    };

    // Convert to structured request and use new API method
    const structuredRequest: StructuredEditorReviewRequest = {
      worldbuilding: { content: enhancedRequest.worldbuilding },
      storySummary: { summary: enhancedRequest.storySummary },
      chapterToReview: enhancedRequest.chapterToReview,
      characters: enhancedRequest.characters,
      previousChapters: enhancedRequest.previousChapters,
      systemPrompts: enhancedRequest.systemPrompts,
      phaseContext: enhancedRequest.phase_context ? {
        currentPhase: enhancedRequest.compose_phase || 'chapter_detail',
        previousPhaseOutput: enhancedRequest.phase_context.previous_phase_output,
        phaseSpecificInstructions: enhancedRequest.phase_context.phase_specific_instructions,
        conversationHistory: enhancedRequest.phase_context.conversation_history,
        conversationBranchId: enhancedRequest.phase_context.conversation_branch_id
      } : undefined
    };
    return this.apiService.requestEditorReview(structuredRequest);
  }

  // ============================================================================
  // PLOT OUTLINE AI CHAT FUNCTIONALITY (WRI-63)
  // ============================================================================

  /**
   * Generate AI response for plot outline chat assistance
   */
  generatePlotOutlineResponse(
    story: Story,
    userMessage: string,
    chatHistory: any[] = []
  ): Observable<string> {
    const request: any = {
      messages: [
        ...chatHistory.slice(-6).map((msg: any) => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        })),
        {
          role: 'user',
          content: userMessage
        }
      ],
      agent_type: 'writer',
      compose_context: {
        current_phase: 'plot_outline',
        story_context: {
          title: story.general.title,
          worldbuilding: story.general.worldbuilding,
          plotOutline: story.plotOutline.content || 'No outline yet.',
          characters: this.formatCharactersForContext(story),
          systemPrompts: story.general.systemPrompts
        }
      },
      system_prompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt
      },
      max_tokens: 500,
      temperature: 0.7
    };

    return new Observable(observer => {
      this.apiService.llmChat(request).subscribe({
        next: (response: any) => {
          observer.next(response.message.content);
          observer.complete();
        },
        error: (error) => {
          console.error('AI chat error:', error);
          observer.error(error);
        }
      });
    });
  }

  /**
   * Format characters for AI context
   */
  private formatCharactersForContext(story: Story): string {
    const characters = Array.from(story.characters.values())
      .filter(c => !c.isHidden)
      .map(c => `- ${c.name}: ${c.basicBio}`)
      .join('\n');
    return characters || 'No characters defined yet.';
  }

  /**
   * Generate AI response for worldbuilding chat assistance
   */
  generateWorldbuildingResponse(
    story: Story,
    userMessage: string,
    chatHistory: any[] = []
  ): Observable<string> {
    const request: any = {
      messages: [
        ...chatHistory.slice(-6).map((msg: any) => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        })),
        {
          role: 'user',
          content: userMessage
        }
      ],
      agent_type: 'writer',
      compose_context: {
        current_phase: 'plot_outline',
        story_context: {
          title: story.general.title,
          worldbuilding: story.general.worldbuilding,
          plotOutline: story.plotOutline?.content || 'No outline yet.',
          characters: this.formatCharactersForContext(story),
          systemPrompts: story.general.systemPrompts
        }
      },
      system_prompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix || 'You are a creative writing assistant helping to develop worldbuilding for a story.',
        mainSuffix: story.general.systemPrompts.mainSuffix,
        assistantPrompt: story.general.systemPrompts.assistantPrompt || 'Help develop rich, consistent worldbuilding by asking questions, providing suggestions, and helping organize worldbuilding information.'
      },
      max_tokens: 500,
      temperature: 0.7
    };

    return new Observable(observer => {
      this.apiService.llmChat(request).subscribe({
        next: (response: any) => {
          observer.next(response.message.content);
          observer.complete();
        },
        error: (error) => {
          console.error('AI chat error:', error);
          observer.error(error);
        }
      });
    });
  }

  // ============================================================================
  // PLOT OUTLINE INTEGRATION FOR CHAPTER GENERATION (WRI-65)
  // ============================================================================

  /**
   * Build chapter generation prompt with plot outline context
   */
  buildChapterGenerationPrompt(story: Story, plotPoint: string): string {
    const prompt = `${story.general.systemPrompts.mainPrefix}

STORY CONTEXT:
Title: ${story.general.title}
Worldbuilding: ${story.general.worldbuilding}

APPROVED PLOT OUTLINE:
${this.getPlotOutlineContext(story)}

CURRENT CHAPTER PLOT POINT:
${plotPoint}

CHARACTERS:
${this.formatCharacters(story)}

RATER FEEDBACK ON PLOT OUTLINE:
${this.formatPlotOutlineFeedback(story)}

Please generate a chapter that follows the approved plot outline while developing the specific plot point provided. Ensure the chapter contributes to the overall story arc and maintains consistency with the established plot structure.

${story.general.systemPrompts.mainSuffix}`;

    return prompt;
  }

  /**
   * Get plot outline context based on status
   */
  private getPlotOutlineContext(story: Story): string {
    if (!story.plotOutline) {
      return 'No plot outline available. Please create and approve a plot outline for better chapter consistency.';
    }

    switch (story.plotOutline.status) {
      case 'approved':
        return `APPROVED PLOT OUTLINE (Approved on ${story.plotOutline.metadata.approvedAt?.toLocaleDateString()}):
${story.plotOutline.content}`;
      
      case 'under_review':
        return `DRAFT PLOT OUTLINE (Under Review - Use with caution):
${story.plotOutline.content}

Note: This plot outline is still under review and may change.`;
      
      case 'draft':
        return `DRAFT PLOT OUTLINE (Not yet reviewed):
${story.plotOutline.content}

Warning: This plot outline has not been reviewed by raters and may need revision.`;
      
      default:
        return `PLOT OUTLINE (Status: ${story.plotOutline.status}):
${story.plotOutline.content}`;
    }
  }

  /**
   * Format plot outline rater feedback for chapter generation
   */
  private formatPlotOutlineFeedback(story: Story): string {
    if (!story.plotOutline || !this.hasRaterFeedback(story.plotOutline)) {
      return 'No rater feedback available on plot outline.';
    }

    const feedbackSummary = this.getRaterFeedbackValues(story.plotOutline)
      .filter(f => f.status === 'complete' && f.userResponse === 'accepted')
      .map(f => `- ${f.raterName}: ${f.feedback.substring(0, 200)}...`)
      .join('\n');

    return feedbackSummary || 'No accepted rater feedback available.';
  }

  /**
   * Safely check if plot outline has rater feedback
   */
  private hasRaterFeedback(plotOutline: PlotOutline): boolean {
    if (!plotOutline.raterFeedback) {
      return false;
    }

    if (plotOutline.raterFeedback instanceof Map) {
      return plotOutline.raterFeedback.size > 0;
    }

    if (typeof plotOutline.raterFeedback === 'object') {
      return Object.keys(plotOutline.raterFeedback).length > 0;
    }

    return false;
  }

  /**
   * Safely get rater feedback values from plot outline
   */
  private getRaterFeedbackValues(plotOutline: PlotOutline): PlotOutlineFeedback[] {
    if (!plotOutline.raterFeedback) {
      return [];
    }

    // Check if it's actually a Map
    if (plotOutline.raterFeedback instanceof Map) {
      return Array.from(plotOutline.raterFeedback.values());
    }

    // If it's a plain object (due to JSON deserialization), convert it
    if (typeof plotOutline.raterFeedback === 'object') {
      // Convert plain object to Map
      const feedbackMap = new Map(Object.entries(plotOutline.raterFeedback as Record<string, PlotOutlineFeedback>));
      plotOutline.raterFeedback = feedbackMap;
      return Array.from(feedbackMap.values());
    }

    return [];
  }

  /**
   * Format characters for chapter generation context
   */
  private formatCharacters(story: Story): string {
    const characters = Array.from(story.characters.values())
      .filter(c => !c.isHidden)
      .map(c => `- ${c.name}: ${c.basicBio}`)
      .join('\n');
    return characters || 'No characters defined yet.';
  }

  // ============================================================================
  // NEW STRUCTURED REQUEST METHODS (WRI-72)
  // ============================================================================

  /**
   * Request character feedback using structured context
   */
  requestCharacterFeedback(
    story: Story,
    character: Character,
    plotPoint: string,
    options: { validate?: boolean; optimize?: boolean } = {}
  ): Observable<StructuredCharacterFeedbackResponse> {
    try {
      // Build structured request using ContextBuilderService
      const systemPromptsResult = this.contextBuilderService.buildSystemPromptsContext(story);
      const worldbuildingResult = this.contextBuilderService.buildWorldbuildingContext(story);
      const storySummaryResult = this.contextBuilderService.buildStorySummaryContext(story);
      const chaptersResult = this.contextBuilderService.buildChaptersContext(story);

      // Check if context building was successful
      if (!systemPromptsResult.success || !worldbuildingResult.success || 
          !storySummaryResult.success || !chaptersResult.success) {
        throw new Error('Failed to build required context for structured character feedback request');
      }

      // Build structured request
      let structuredRequest: StructuredCharacterFeedbackRequest = {
        systemPrompts: {
          mainPrefix: systemPromptsResult.data!.mainPrefix,
          mainSuffix: systemPromptsResult.data!.mainSuffix
        },
        worldbuilding: {
          content: worldbuildingResult.data!.content,
          lastModified: new Date(),
          wordCount: worldbuildingResult.data!.content.split(/\s+/).length
        },
        storySummary: {
          summary: storySummaryResult.data!.summary,
          lastModified: new Date(),
          wordCount: storySummaryResult.data!.summary.split(/\s+/).length
        },
        previousChapters: chaptersResult.data!.chapters.map(ch => ({
          number: ch.number,
          title: ch.title,
          content: ch.content,
          wordCount: ch.content.split(/\s+/).length
        })),
        character: {
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
        },
        plotContext: {
          plotPoint: plotPoint,
          plotOutline: story.plotOutline?.content,
          plotOutlineStatus: story.plotOutline?.status
        },
        requestMetadata: {
          timestamp: new Date(),
          requestSource: 'generation_service_structured'
        }
      };

      // Validate request if requested
      if (options.validate !== false) {
        const validationResult = this.requestValidatorService.validateCharacterFeedbackRequest(structuredRequest);
        if (!validationResult.isValid) {
          throw new Error(`Request validation failed: ${validationResult.errors.map(e => e.message).join(', ')}`);
        }
      }

      // Optimize request if requested
      if (options.optimize !== false) {
        const optimizationResult = this.requestOptimizerService.optimizeCharacterFeedbackRequest(structuredRequest);
        structuredRequest = optimizationResult.optimizedRequest;
      }

      return this.apiService.requestCharacterFeedback(structuredRequest);
    } catch (error) {
      throw new Error(`Failed to request structured character feedback: ${error}`);
    }
  }



  /**
   * Request rater feedback using structured context with streaming support
   */
  requestRaterFeedback(
    story: Story,
    rater: Rater,
    plotPoint: string,
    onProgress?: (progress: { phase: string; message: string; progress: number }) => void,
    _options: { validate?: boolean; optimize?: boolean } = {}
  ): Observable<StructuredRaterFeedbackResponse> {
    try {
      // Build structured request using ContextBuilderService
      const systemPromptsResult = this.contextBuilderService.buildSystemPromptsContext(story);
      const worldbuildingResult = this.contextBuilderService.buildWorldbuildingContext(story);
      const storySummaryResult = this.contextBuilderService.buildStorySummaryContext(story);
      const chaptersResult = this.contextBuilderService.buildChaptersContext(story);
      const charactersResult = this.contextBuilderService.buildCharacterContext(story);

      // Check if context building was successful
      if (!systemPromptsResult.success || !worldbuildingResult.success || 
          !storySummaryResult.success || !chaptersResult.success || !charactersResult.success) {
        throw new Error('Failed to build required context for structured rater feedback request');
      }

      // Build structured request
      const structuredRequest: any = {
        raterPrompt: rater.systemPrompt,
        plotPoint: plotPoint,
        structured_context: {
          systemPrompts: {
            mainPrefix: systemPromptsResult.data!.mainPrefix,
            mainSuffix: systemPromptsResult.data!.mainSuffix,
            assistantPrompt: systemPromptsResult.data!.assistantPrompt
          },
          worldbuilding: {
            content: worldbuildingResult.data!.content,
            lastModified: new Date(),
            wordCount: worldbuildingResult.data!.content.split(/\s+/).length
          },
          storySummary: {
            summary: storySummaryResult.data!.summary,
            lastModified: new Date(),
            wordCount: storySummaryResult.data!.summary.split(/\s+/).length
          },
          previousChapters: chaptersResult.data!.chapters.map(ch => ({
            number: ch.number,
            title: ch.title,
            content: ch.content,
            wordCount: ch.content.split(/\s+/).length
          })),
          characters: charactersResult.data!.characters.map((c: any) => ({
            name: c.name,
            basicBio: c.basicBio,
            sex: c.sex,
            gender: c.gender,
            sexualPreference: c.sexualPreference,
            age: c.age,
            physicalAppearance: c.physicalAppearance,
            usualClothing: c.usualClothing,
            personality: c.personality,
            motivations: c.motivations,
            fears: c.fears,
            relationships: c.relationships,
            isHidden: c.isHidden
          })),
          plotContext: {
            plotPoint: plotPoint,
            plotOutline: story.plotOutline?.content,
            plotOutlineStatus: story.plotOutline?.status
          },
          requestMetadata: {
            timestamp: new Date(),
            requestSource: 'generation_service_streaming'
          }
        }
      };

      // Use streaming API
      return new Observable<StructuredRaterFeedbackResponse>(observer => {
        this.apiService.streamRaterFeedback(structuredRequest).subscribe({
          next: (event) => {
            if (event.type === 'status' && onProgress) {
              onProgress({
                phase: event.phase,
                message: event.message,
                progress: event.progress
              });
            } else if (event.type === 'result') {
              // Transform the result to match expected format
              const response: StructuredRaterFeedbackResponse = {
                raterName: event.data.raterName,
                feedback: event.data.feedback,
                context_metadata: event.data.context_metadata
              };
              observer.next(response);
              observer.complete();
            }
          },
          error: (error) => observer.error(error)
        });
      });
    } catch (error) {
      throw new Error(`Failed to request streaming rater feedback: ${error}`);
    }
  }

  /**
   * Generate chapter using structured context
   */
  generateChapterStructuredNew(
    story: Story,
    options: { validate?: boolean; optimize?: boolean } = {}
  ): Observable<StructuredGenerateChapterResponse> {
    try {
      // Build structured request using ContextBuilderService
      const contextResult = this.contextBuilderService.buildChapterGenerationContext(
        story,
        story.chapterCreation.plotPoint,
        story.chapterCreation.incorporatedFeedback
      );

      // Check if context building was successful
      if (!contextResult.success || !contextResult.data) {
        throw new Error('Failed to build required context for structured chapter generation');
      }

      const context = contextResult.data;

      // Build structured request
      let structuredRequest: StructuredGenerateChapterRequest = {
        systemPrompts: {
          mainPrefix: context.systemPrompts.mainPrefix,
          mainSuffix: context.systemPrompts.mainSuffix,
          assistantPrompt: context.systemPrompts.assistantPrompt
        },
        worldbuilding: {
          content: context.worldbuilding.content,
          lastModified: new Date(),
          wordCount: context.worldbuilding.content.split(/\s+/).length
        },
        storySummary: {
          summary: context.storySummary.summary,
          lastModified: new Date(),
          wordCount: context.storySummary.summary.split(/\s+/).length
        },
        previousChapters: context.previousChapters.chapters.map(ch => ({
          number: ch.number,
          title: ch.title,
          content: ch.content,
          wordCount: ch.content.split(/\s+/).length
        })),
        characters: context.characters.characters.map(c => ({
          name: c.name,
          basicBio: c.basicBio,
          sex: c.sex,
          gender: c.gender,
          sexualPreference: c.sexualPreference,
          age: c.age,
          physicalAppearance: c.physicalAppearance,
          usualClothing: c.usualClothing,
          personality: c.personality,
          motivations: c.motivations,
          fears: c.fears,
          relationships: c.relationships,
          isHidden: c.isHidden
        })),
        plotContext: {
          plotPoint: context.plotPoint.plotPoint,
          plotOutline: story.plotOutline?.content,
          plotOutlineStatus: story.plotOutline?.status
        },
        feedbackContext: {
          incorporatedFeedback: context.feedback.incorporatedFeedback
        },
        requestMetadata: {
          timestamp: new Date(),
          requestSource: 'generation_service_structured'
        }
      };

      // Validate request if requested
      if (options.validate !== false) {
        const validationResult = this.requestValidatorService.validateGenerateChapterRequest(structuredRequest);
        if (!validationResult.isValid) {
          throw new Error(`Request validation failed: ${validationResult.errors.map(e => e.message).join(', ')}`);
        }
      }

      // Optimize request if requested
      if (options.optimize !== false) {
        const optimizationResult = this.requestOptimizerService.optimizeGenerateChapterRequest(structuredRequest);
        structuredRequest = optimizationResult.optimizedRequest;
      }

      return this.apiService.generateChapter(structuredRequest);
    } catch (error) {
      throw new Error(`Failed to generate chapter with structured context: ${error}`);
    }
  }

  /**
   * Request editor review using structured context
   */
  requestEditorReview(
    story: Story,
    chapterText: string,
    options: { validate?: boolean; optimize?: boolean } = {}
  ): Observable<StructuredEditorReviewResponse> {
    try {
      // Build structured request using ContextBuilderService
      const systemPromptsResult = this.contextBuilderService.buildSystemPromptsContext(story);
      const worldbuildingResult = this.contextBuilderService.buildWorldbuildingContext(story);
      const storySummaryResult = this.contextBuilderService.buildStorySummaryContext(story);
      const chaptersResult = this.contextBuilderService.buildChaptersContext(story);
      const charactersResult = this.contextBuilderService.buildCharacterContext(story);

      // Check if context building was successful
      if (!systemPromptsResult.success || !worldbuildingResult.success || 
          !storySummaryResult.success || !chaptersResult.success || !charactersResult.success) {
        throw new Error('Failed to build required context for structured editor review request');
      }

      // Build structured request
      let structuredRequest: StructuredEditorReviewRequest = {
        systemPrompts: {
          mainPrefix: systemPromptsResult.data!.mainPrefix,
          mainSuffix: systemPromptsResult.data!.mainSuffix,
          editorPrompt: systemPromptsResult.data!.assistantPrompt
        },
        worldbuilding: {
          content: worldbuildingResult.data!.content,
          lastModified: new Date(),
          wordCount: worldbuildingResult.data!.content.split(/\s+/).length
        },
        storySummary: {
          summary: storySummaryResult.data!.summary,
          lastModified: new Date(),
          wordCount: storySummaryResult.data!.summary.split(/\s+/).length
        },
        previousChapters: chaptersResult.data!.chapters.map(ch => ({
          number: ch.number,
          title: ch.title,
          content: ch.content,
          wordCount: ch.content.split(/\s+/).length
        })),
        characters: charactersResult.data!.characters.map((c: StructuredCharacter) => ({
          name: c.name,
          basicBio: c.basicBio,
          sex: c.sex,
          gender: c.gender,
          sexualPreference: c.sexualPreference,
          age: c.age,
          physicalAppearance: c.physicalAppearance,
          usualClothing: c.usualClothing,
          personality: c.personality,
          motivations: c.motivations,
          fears: c.fears,
          relationships: c.relationships,
          isHidden: c.isHidden
        })),
        chapterToReview: chapterText,
        requestMetadata: {
          timestamp: new Date(),
          requestSource: 'generation_service_structured'
        }
      };

      // Validate request if requested
      if (options.validate !== false) {
        const validationResult = this.requestValidatorService.validateEditorReviewRequest(structuredRequest);
        if (!validationResult.isValid) {
          throw new Error(`Request validation failed: ${validationResult.errors.map(e => e.message).join(', ')}`);
        }
      }

      // Optimize request if requested
      if (options.optimize !== false) {
        const optimizationResult = this.requestOptimizerService.optimizeEditorReviewRequest(structuredRequest);
        structuredRequest = optimizationResult.optimizedRequest;
      }

      return this.apiService.requestEditorReview(structuredRequest);
    } catch (error) {
      throw new Error(`Failed to request structured editor review: ${error}`);
    }
  }
}
