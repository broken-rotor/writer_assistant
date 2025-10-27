import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  Story,
  Character,
  Rater,
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

@Injectable({
  providedIn: 'root'
})
export class GenerationService {
  constructor(private apiService: ApiService) {}

  // Character Feedback
  requestCharacterFeedback(
    story: Story,
    character: Character,
    plotPoint: string
  ): Observable<CharacterFeedbackResponse> {
    const request: CharacterFeedbackRequest = {
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

    return this.apiService.requestCharacterFeedback(request);
  }

  // Rater Feedback
  requestRaterFeedback(
    story: Story,
    rater: Rater,
    plotPoint: string
  ): Observable<RaterFeedbackResponse> {
    const request: RaterFeedbackRequest = {
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

    return this.apiService.requestRaterFeedback(request);
  }

  // Generate Chapter
  generateChapter(story: Story): Observable<GenerateChapterResponse> {
    const request: GenerateChapterRequest = {
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

    return this.apiService.generateChapter(request);
  }

  // Modify Chapter
  modifyChapter(
    story: Story,
    currentChapterText: string,
    userRequest: string
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

    return this.apiService.modifyChapter(request);
  }

  // Editor Review
  requestEditorReview(
    story: Story,
    chapterText: string
  ): Observable<EditorReviewResponse> {
    const request: EditorReviewRequest = {
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

    return this.apiService.requestEditorReview(request);
  }

  // Flesh Out (for plot points or worldbuilding)
  fleshOut(
    story: Story,
    textToFleshOut: string,
    context: string
  ): Observable<FleshOutResponse> {
    const request: FleshOutRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      textToFleshOut: textToFleshOut,
      context: context
    };

    return this.apiService.fleshOut(request);
  }

  // Generate Character Details
  generateCharacterDetails(
    story: Story,
    basicBio: string,
    existingCharacters: Character[]
  ): Observable<GenerateCharacterDetailsResponse> {
    const request: GenerateCharacterDetailsRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      basicBio: basicBio,
      existingCharacters: existingCharacters.map(c => ({
        name: c.name,
        basicBio: c.basicBio,
        relationships: c.relationships
      }))
    };

    return this.apiService.generateCharacterDetails(request);
  }

  // Regenerate Relationships for a Character
  regenerateRelationships(
    story: Story,
    character: Character,
    otherCharacters: Character[]
  ): Observable<GenerateCharacterDetailsResponse> {
    // Use the same endpoint but we'll only extract the relationships field
    const request: GenerateCharacterDetailsRequest = {
      systemPrompts: {
        mainPrefix: story.general.systemPrompts.mainPrefix,
        mainSuffix: story.general.systemPrompts.mainSuffix
      },
      worldbuilding: story.general.worldbuilding,
      storySummary: story.story.summary,
      basicBio: character.basicBio,
      existingCharacters: otherCharacters.map(c => ({
        name: c.name,
        basicBio: c.basicBio,
        relationships: c.relationships
      }))
    };

    return this.apiService.generateCharacterDetails(request);
  }

  // Phase 2 Specific Methods for Chapter Detailer

  // Generate Chapter from Plot Outline
  generateChapterFromOutline(
    story: Story,
    outlineItems: Array<{title: string, description: string}>,
    chapterNumber: number
  ): Observable<GenerateChapterResponse> {
    const plotPoint = outlineItems.map(item => `${item.title}: ${item.description}`).join('\n\n');
    
    const request: GenerateChapterRequest = {
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
      plotPoint: plotPoint,
      incorporatedFeedback: []
    };

    return this.apiService.generateChapter(request);
  }

  // Continue Writing Chapter
  continueChapter(
    story: Story,
    currentChapterContent: string,
    continuationPrompt?: string
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

    return this.apiService.modifyChapter(request);
  }

  // Regenerate Chapter with Feedback
  regenerateChapterWithFeedback(
    story: Story,
    currentChapterContent: string,
    feedbackItems: Array<{source: string, content: string, type: string}>,
    userInstructions?: string
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

    return this.apiService.modifyChapter(request);
  }

  // Generate Chapter Variation
  generateChapterVariation(
    story: Story,
    baseChapterContent: string,
    variationPrompt: string
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

    return this.apiService.modifyChapter(request);
  }

  // Refine Chapter Section
  refineChapterSection(
    story: Story,
    fullChapterContent: string,
    sectionToRefine: string,
    refinementInstructions: string
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

    return this.apiService.modifyChapter(request);
  }
}
