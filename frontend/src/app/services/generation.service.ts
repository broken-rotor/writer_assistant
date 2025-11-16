import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService, CharacterFeedbackRequest } from './api.service';
import { ContextBuilderService } from './context-builder.service';
import { RequestConverterService } from './request-converter.service';
import { RequestValidatorService } from './request-validator.service';
import { RequestOptimizerService } from './request-optimizer.service';
import { PlotOutlineContextService } from './plot-outline-context.service';
import { transformToRequestContext } from '../utils/context-transformer';
import {
  Story,
  Character,
  CharacterInfo,
  Rater,
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
  FeedbackItem,
  // Chapter Outline Generation interfaces
  ChapterOutlineGenerationRequest,
  ChapterOutlineGenerationResponse,
  CharacterContext,
  // Backend request interfaces
  BackendGenerateChapterRequest
} from '../models/story.model';
import {
  StructuredCharacterFeedbackResponse,
  StructuredRaterFeedbackResponse,
  StructuredGenerateChapterResponse,
  StructuredEditorReviewResponse
} from '../models/structured-request.model';
import { StructuredCharacter } from '../models/context-builder.model';
import { BackendEditorReviewRequest, BackendEditorReviewResponse } from '../models/story.model';

@Injectable({
  providedIn: 'root'
})
export class GenerationService {
  private apiService = inject(ApiService);
  private contextBuilderService = inject(ContextBuilderService);
  private requestConverterService = inject(RequestConverterService);
  private requestValidatorService = inject(RequestValidatorService);
  private requestOptimizerService = inject(RequestOptimizerService);
  private plotOutlineContextService = inject(PlotOutlineContextService);







  /**
   * Generate chapter using ContextBuilderService
   * This is the new structured approach that replaces manual context building
   */
  generateChapter(story: Story, plotPoint: string, incorporatedFeedback: FeedbackItem[] = []): Observable<GenerateChapterResponse> {
    try {
      // Convert to backend-compatible format using the same approach as generateChapterFromOutline
      const backendRequest = this.convertToBackendGenerateChapterRequestGeneral(
        story, 
        plotPoint, 
        incorporatedFeedback
      );

      return this.apiService.generateChapter(backendRequest);
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
    // Determine chapter number by finding the chapter that matches the current text
    const chapterNumber = this.findChapterNumberByContent(story, currentChapterText);
    
    const request: ModifyChapterRequest = {
      chapter_number: chapterNumber,
      userRequest: userRequest,
      request_context: transformToRequestContext(story)
    };

    return this.apiService.modifyChapter(request, onProgress);
  }

  /**
   * Find the chapter number by matching the current chapter text with existing chapters
   */
  private findChapterNumberByContent(story: Story, currentChapterText: string): number {
    if (!story.story?.chapters || story.story.chapters.length === 0) {
      return 1; // Default to chapter 1 if no chapters exist
    }

    // Try to find exact match first
    const exactMatch = story.story.chapters.find(ch => ch.content === currentChapterText);
    if (exactMatch) {
      return exactMatch.number;
    }

    // If no exact match, try to find by partial content match (first 500 characters)
    const textStart = currentChapterText.substring(0, 500);
    const partialMatch = story.story.chapters.find(ch => 
      ch.content.substring(0, 500) === textStart
    );
    if (partialMatch) {
      return partialMatch.number;
    }

    // If still no match, return the next chapter number
    const maxChapterNumber = Math.max(...story.story.chapters.map(ch => ch.number));
    return maxChapterNumber + 1;
  }



  // Flesh Out (for plot points or worldbuilding)
  fleshOut(
    story: Story,
    textToFleshOut: string,
    context: string
  ): Observable<FleshOutResponse> {
    // Use the new RequestContext transformation
    const requestContext = transformToRequestContext(story);

    const request: FleshOutRequest = {
      textToFleshOut: textToFleshOut,
      context: context,
      request_context: requestContext
    };

    return this.apiService.fleshOut(request);
  }

  // Generate Character Details
  generateCharacterDetails(
    story: Story,
    basicBio: string,
    existingCharacters: Character[],
    onProgress?: (update: { phase: string; message: string; progress: number }) => void
  ): Observable<GenerateCharacterDetailsResponse> {
    // Use the new RequestContext transformation
    const requestContext = transformToRequestContext(story);

    const request: GenerateCharacterDetailsRequest = {
      basicBio: basicBio,
      existingCharacters: existingCharacters.map(c => ({
        name: c.name,
        basicBio: c.basicBio,
        relationships: c.relationships
      })),
      request_context: requestContext
    };

    return this.apiService.generateCharacterDetails(request, onProgress);
  }

  // Regenerate Bio from Character Details
  regenerateBio(
    story: Story,
    character: Character,
    onProgress?: (update: { phase: string; message: string; progress: number }) => void
  ): Observable<RegenerateBioResponse> {
    // Use the new RequestContext transformation
    const requestContext = transformToRequestContext(story);

    // Create CharacterInfo from Character
    const characterInfo: CharacterInfo = {
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
    };

    const request: RegenerateBioRequest = {
      character_info: characterInfo,
      request_context: requestContext
    };

    return this.apiService.regenerateBio(request, onProgress);
  }

  // Regenerate Relationships for a Character
  regenerateRelationships(
    story: Story,
    character: Character,
    otherCharacters: Character[]
  ): Observable<GenerateCharacterDetailsResponse> {
    // Use the new RequestContext transformation
    const requestContext = transformToRequestContext(story);

    // Use the same endpoint but we'll only extract the relationships field
    const request: GenerateCharacterDetailsRequest = {
      basicBio: character.basicBio,
      existingCharacters: otherCharacters.map(c => ({
        name: c.name,
        basicBio: c.basicBio,
        relationships: c.relationships
      })),
      request_context: requestContext
    };

    return this.apiService.generateCharacterDetails(request);
  }

  // Phase 2 Specific Methods for Chapter Detailer

  // Generate Chapter from Plot Outline
  generateChapterFromOutline(
    story: Story,
    outlineItems: {title: string, description: string, key_plot_items?: string[]}[],
    chapterNumber = 1
  ): Observable<StructuredGenerateChapterResponse> {
    // Use key plot items if available, otherwise fall back to description
    const plotPoint = outlineItems.map(item => {
      if (item.key_plot_items && item.key_plot_items.length > 0) {
        return `${item.title}:\n${item.key_plot_items.map(plotItem => `- ${plotItem}`).join('\n')}`;
      } else {
        return `${item.title}: ${item.description}`;
      }
    }).join('\n\n');
    
    // Convert to backend-compatible format
    const backendRequest = this.convertToBackendGenerateChapterRequest(
      story, 
      plotPoint, 
      outlineItems, 
      chapterNumber
    );

    return this.apiService.generateChapter(backendRequest);
  }

  private convertToBackendGenerateChapterRequest(
    story: Story,
    plotPoint: string,
    outlineItems: {title: string, description: string, key_plot_items?: string[]}[],
    chapterNumber: number
  ): any {
    // Use the new RequestContext transformation
    const requestContext = transformToRequestContext(story);

    // Create context processing config with plot outline data
    const contextProcessingConfig = {
      plot_outline_content: story.plotOutline?.content,
      draft_outline_items: outlineItems.map((item, index) => ({
        id: `outline_item_${index}`,
        title: item.title,
        description: item.description,
        order: index,
        type: 'chapter_outline'
      })),
      chapter_number: chapterNumber,
      story_context: {
        title: story.general.title,
        worldbuilding: story.general.worldbuilding,
        summary: story.story.summary,
        previous_chapters: story.story.chapters.map(ch => ({
          number: ch.number,
          title: ch.title,
          content: ch.content
        }))
      }
    };

    // Create backend-compatible request
    return {
      plotPoint: plotPoint,
      compose_phase: 'chapter_detail',
      request_context: requestContext,
      context_processing_config: contextProcessingConfig
    };
  }

  /**
   * Convert story and plot point to backend-compatible request format for general chapter generation
   */
  private convertToBackendGenerateChapterRequestGeneral(
    story: Story,
    plotPoint: string,
    _incorporatedFeedback: FeedbackItem[] = []
  ): BackendGenerateChapterRequest {
    // Use the new RequestContext transformation
    const requestContext = transformToRequestContext(story);

    // Create context processing config
    const contextProcessingConfig = {
      story_context: {
        title: story.general.title,
        worldbuilding: story.general.worldbuilding,
        summary: story.story.summary,
        previous_chapters: story.story.chapters.map(ch => ({
          number: ch.number,
          title: ch.title,
          content: ch.content
        }))
      }
    };

    // Create backend-compatible request
    return {
      plotPoint: plotPoint,
      request_context: requestContext,
      context_processing_config: contextProcessingConfig
    };
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
    
    // Determine chapter number by finding the chapter that matches the current text
    const chapterNumber = this.findChapterNumberByContent(story, currentChapterContent);
    
    const request: ModifyChapterRequest = {
      chapter_number: chapterNumber,
      userRequest: `${prompt}\n\nCurrent chapter content:\n${currentChapterContent}`,
      request_context: transformToRequestContext(story)
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

    // Determine chapter number by finding the chapter that matches the current text
    const chapterNumber = this.findChapterNumberByContent(story, currentChapterContent);
    
    const request: ModifyChapterRequest = {
      chapter_number: chapterNumber,
      userRequest: incorporationPrompt,
      request_context: transformToRequestContext(story)
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

      // Determine chapter number by finding the chapter that matches the current text
      const chapterNumber = this.findChapterNumberByContent(story, currentChapterContent);
      
      // Build request using structured context
      const request: ModifyChapterRequest = {
        chapter_number: chapterNumber,
        userRequest: incorporationPrompt,
        request_context: transformToRequestContext(story)
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
    // Determine chapter number by finding the chapter that matches the current text
    const chapterNumber = this.findChapterNumberByContent(story, baseChapterContent);
    
    const request: ModifyChapterRequest = {
      chapter_number: chapterNumber,
      userRequest: `Create a variation of this chapter with the following changes: ${variationPrompt}\n\nBase chapter:\n${baseChapterContent}`,
      request_context: transformToRequestContext(story)
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
    // Determine chapter number by finding the chapter that matches the current text
    const chapterNumber = this.findChapterNumberByContent(story, fullChapterContent);
    
    const request: ModifyChapterRequest = {
      chapter_number: chapterNumber,
      userRequest: `Please refine this specific section of the chapter: "${sectionToRefine}"\n\nRefinement instructions: ${refinementInstructions}\n\nFull chapter context:\n${fullChapterContent}`,
      request_context: transformToRequestContext(story)
    };

    return this.apiService.modifyChapter(request, onProgress);
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
   * Request character feedback using RequestContext API
   */
  requestCharacterFeedback(
    story: Story,
    character: Character,
    plotPoint: string,
    options: { validate?: boolean; optimize?: boolean } = {}
  ): Observable<StructuredCharacterFeedbackResponse> {
    try {
      // Use transformToRequestContext utility to generate context
      const request_context = transformToRequestContext(story);

      // Build new request format
      const request: CharacterFeedbackRequest = {
        character_name: character.name,
        plotPoint: plotPoint,
        request_context: request_context
      };

      // Note: Validation and optimization options are maintained for backward compatibility
      // but are currently not implemented for the new RequestContext format
      if (options.validate !== false) {
        // TODO: Implement validation for RequestContext format if needed
        console.log('Validation option noted but not implemented for RequestContext format');
      }

      if (options.optimize !== false) {
        // TODO: Implement optimization for RequestContext format if needed
        console.log('Optimization option noted but not implemented for RequestContext format');
      }

      return this.apiService.requestCharacterFeedback(request);
    } catch (error) {
      throw new Error(`Failed to request character feedback: ${error}`);
    }
  }



  /**
   * Request rater feedback using RequestContext API with streaming support
   */
  requestRaterFeedback(
    story: Story,
    rater: Rater,
    plotPoint: string,
    onProgress?: (progress: { phase: string; message: string; progress: number }) => void,
    _options: { validate?: boolean; optimize?: boolean } = {}
  ): Observable<StructuredRaterFeedbackResponse> {
    try {
      // Use transformToRequestContext utility to generate context
      const request_context = transformToRequestContext(story);

      // Build request in the format expected by backend
      const request = {
        raterName: rater.name,
        plotPoint: plotPoint,
        request_context: request_context
      };

      // Use streaming API
      return new Observable<StructuredRaterFeedbackResponse>(observer => {
        this.apiService.streamRaterFeedback(request).subscribe({
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
    plotPoint: string,
    incorporatedFeedback: FeedbackItem[] = [],
    _options: { validate?: boolean; optimize?: boolean } = {}
  ): Observable<StructuredGenerateChapterResponse> {
    try {
      // Convert to backend-compatible format using the same approach as generateChapter
      const backendRequest = this.convertToBackendGenerateChapterRequestGeneral(
        story, 
        plotPoint, 
        incorporatedFeedback
      );

      // Note: Validation and optimization are skipped for backend requests as they use a different format
      // The backend handles validation internally

      return this.apiService.generateChapter(backendRequest);
    } catch (error) {
      throw new Error(`Failed to generate chapter with structured context: ${error}`);
    }
  }

  /**
   * Request editor review using RequestContext API
   */
  requestEditorReview(
    story: Story,
    chapterText: string,
    options: { validate?: boolean; optimize?: boolean } = {}
  ): Observable<StructuredEditorReviewResponse> {
    try {
      // Use transformToRequestContext utility to generate context
      const requestContext = transformToRequestContext(story);

      // Determine chapter number by matching chapterText with story chapters
      let chapterNumber = 1; // Default to 1 if not found
      if (story.story?.chapters) {
        const matchingChapter = story.story.chapters.find(chapter => 
          chapter.content.trim() === chapterText.trim()
        );
        if (matchingChapter) {
          chapterNumber = matchingChapter.number;
        } else {
          // If exact match not found, try to find by partial content match
          const partialMatch = story.story.chapters.find(chapter => 
            chapter.content.includes(chapterText.substring(0, Math.min(100, chapterText.length)))
          );
          if (partialMatch) {
            chapterNumber = partialMatch.number;
          }
        }
      }

      // Create new request format
      const request: BackendEditorReviewRequest = {
        chapter_number: chapterNumber,
        request_context: requestContext
      };

      // Note: Validation and optimization options are maintained for backward compatibility
      // but are not currently implemented for the new RequestContext format
      if (options.validate !== false) {
        // TODO: Implement validation for RequestContext format if needed
        console.warn('Validation not yet implemented for RequestContext format');
      }

      if (options.optimize !== false) {
        // TODO: Implement optimization for RequestContext format if needed
        console.warn('Optimization not yet implemented for RequestContext format');
      }

      // Call new API method and transform response to maintain compatibility
      return this.apiService.requestEditorReviewWithContext(request).pipe(
        map((backendResponse: BackendEditorReviewResponse): StructuredEditorReviewResponse => ({
          overallAssessment: `Editor review for chapter ${chapterNumber}`, // Provide default assessment
          suggestions: backendResponse.suggestions.map(suggestion => ({
            issue: suggestion.issue,
            suggestion: suggestion.suggestion,
            priority: suggestion.priority as 'high' | 'medium' | 'low',
            selected: false // Default to not selected
          })),
          metadata: {
            requestId: `editor_review_${chapterNumber}_${Date.now()}`,
            processingTime: 0,
            optimizationsApplied: []
          }
        }))
      );
    } catch (error) {
      throw new Error(`Failed to request editor review: ${error}`);
    }
  }

  // ============================================================================
  // CHAPTER OUTLINE GENERATION (WRI-129)
  // ============================================================================

  /**
   * Generate chapter outline from story outline
   */
  generateChapterOutlinesFromStoryOutline(
    story: Story,
    storyOutline: string
  ): Observable<ChapterOutlineGenerationResponse> {
    try {
      // Validate input
      if (!storyOutline || !storyOutline.trim()) {
        throw new Error('Story outline is required for chapter outline generation');
      }

      // Prepare the request
      const request: ChapterOutlineGenerationRequest = {
        story_outline: storyOutline,
        story_context: {
          title: story.general.title,
          worldbuilding: story.general.worldbuilding,
          characters: Array.from(story.characters.values()).map(char => ({
            name: char.name,
            basicBio: char.basicBio
          }))
        },
        character_contexts: this.convertCharactersToCharacterContexts(story.characters),
        generation_preferences: {
          // Add any generation preferences here
        },
        system_prompts: story.general.systemPrompts
      };

      return this.apiService.generateChapterOutlines(request);
    } catch (error) {
      throw new Error(`Failed to generate chapter outline: ${error}`);
    }
  }

  /**
   * Convert Character objects to CharacterContext objects for enhanced AI processing
   */
  private convertCharactersToCharacterContexts(characters: Map<string, Character>): CharacterContext[] {
    return Array.from(characters.values())
      .filter(char => !char.isHidden) // Only include visible characters
      .map(char => ({
        character_id: char.id,
        character_name: char.name,
        current_state: {
          // Extract current state from character properties
          physicalAppearance: char.physicalAppearance,
          age: char.age,
          sex: char.sex,
          gender: char.gender
        },
        recent_actions: [], // Could be populated from story events in the future
        relationships: this.parseRelationshipsFromText(char.relationships),
        goals: this.parseGoalsFromText(char.motivations),
        memories: [], // Could be populated from story events in the future
        personality_traits: this.parsePersonalityTraits(char.personality)
      }));
  }

  /**
   * Parse relationships text into structured format
   */
  private parseRelationshipsFromText(relationshipsText: string): Record<string, string> {
    if (!relationshipsText || !relationshipsText.trim()) {
      return {};
    }
    
    // Simple parsing - could be enhanced with more sophisticated NLP
    const relationships: Record<string, string> = {};
    const lines = relationshipsText.split('\n').filter(line => line.trim());
    
    lines.forEach(line => {
      // Look for patterns like "Character Name: relationship description"
      const match = line.match(/^([^:]+):\s*(.+)$/);
      if (match) {
        relationships[match[1].trim()] = match[2].trim();
      }
    });
    
    return relationships;
  }

  /**
   * Parse goals/motivations text into array format
   */
  private parseGoalsFromText(motivationsText: string): string[] {
    if (!motivationsText || !motivationsText.trim()) {
      return [];
    }
    
    // Split by common delimiters and clean up
    return motivationsText
      .split(/[,;.\n]/)
      .map(goal => goal.trim())
      .filter(goal => goal.length > 0)
      .slice(0, 5); // Limit to top 5 goals
  }

  /**
   * Parse personality text into traits array
   */
  private parsePersonalityTraits(personalityText: string): string[] {
    if (!personalityText || !personalityText.trim()) {
      return [];
    }
    
    // Split by common delimiters and clean up
    return personalityText
      .split(/[,;.\n]/)
      .map(trait => trait.trim())
      .filter(trait => trait.length > 0)
      .slice(0, 8); // Limit to top 8 traits
  }
}
