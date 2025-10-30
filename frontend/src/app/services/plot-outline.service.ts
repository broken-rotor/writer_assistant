import { Injectable, inject } from '@angular/core';
import { Observable, from, throwError } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { GenerationService } from './generation.service';
import { StoryService } from './story.service';
import { Story, PlotOutlineFeedback, Rater } from '../models/story.model';

@Injectable({
  providedIn: 'root'
})
export class PlotOutlineService {
  private generationService = inject(GenerationService);
  private storyService = inject(StoryService);

  requestPlotOutlineFeedback(
    storyId: string, 
    raterId: string, 
    plotOutline: string
  ): Observable<PlotOutlineFeedback> {
    const story = this.storyService.getStory(storyId);
    if (!story) {
      return throwError('Story not found');
    }

    const rater = story.raters.get(raterId);
    if (!rater || !rater.enabled) {
      return throwError('Rater not found or disabled');
    }

    const prompt = this.buildRaterPrompt(story, rater, plotOutline);
    
    return this.generationService.generatePlotOutlineResponse(
      story,
      prompt,
      [] // No chat history for rater feedback
    ).pipe(
      map(response => {
        const feedback: PlotOutlineFeedback = {
          raterId: raterId,
          raterName: rater.name,
          feedback: response,
          status: 'complete',
          timestamp: new Date()
        };
        return feedback;
      }),
      catchError(() => {
        const errorFeedback: PlotOutlineFeedback = {
          raterId: raterId,
          raterName: rater.name,
          feedback: '',
          status: 'error',
          timestamp: new Date()
        };
        return throwError(errorFeedback);
      })
    );
  }

  private buildRaterPrompt(story: Story, rater: Rater, plotOutline: string): string {
    const context = `
STORY CONTEXT:
Title: ${story.general.title}
Worldbuilding: ${story.general.worldbuilding}

CHARACTERS:
${this.formatCharacters(story)}

PLOT OUTLINE TO REVIEW:
${plotOutline}

TASK: As a ${rater.name}, please provide detailed feedback on this plot outline. Focus on your area of expertise and provide specific, actionable suggestions for improvement.

Consider:
- Story structure and narrative flow
- Character development opportunities
- Genre conventions and reader expectations
- Plot consistency and logic
- Pacing and tension
- Areas that need more development

Provide constructive feedback that will help improve the story.`;

    return `${story.general.systemPrompts.mainPrefix}
${context}
${rater.systemPrompt}
${story.general.systemPrompts.mainSuffix}`;
  }

  private formatCharacters(story: Story): string {
    const characters = Array.from(story.characters.values())
      .filter(c => !c.isHidden)
      .map(c => `- ${c.name}: ${c.basicBio}`)
      .join('\n');
    return characters || 'No characters defined yet.';
  }

  requestAllRaterFeedback(storyId: string): Observable<PlotOutlineFeedback[]> {
    const story = this.storyService.getStory(storyId);
    if (!story) {
      return throwError('Story not found');
    }

    const enabledRaters = Array.from(story.raters.values())
      .filter(rater => rater.enabled);

    if (enabledRaters.length === 0) {
      return throwError('No enabled raters found');
    }

    const feedbackRequests = enabledRaters.map(rater => 
      this.requestPlotOutlineFeedback(storyId, rater.id, story.plotOutline.content).toPromise()
    );

    return from(Promise.allSettled(feedbackRequests)).pipe(
      map(results => {
        const feedback: PlotOutlineFeedback[] = [];
        results.forEach((result, index) => {
          if (result.status === 'fulfilled' && result.value) {
            feedback.push(result.value);
          } else {
            // Create error feedback for failed requests
            const rater = enabledRaters[index];
            feedback.push({
              raterId: rater.id,
              raterName: rater.name,
              feedback: '',
              status: 'error',
              timestamp: new Date()
            });
          }
        });
        return feedback;
      })
    );
  }
}
