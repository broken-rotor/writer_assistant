import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Story, FeedbackData, FeedbackAgent, FeedbackItem } from '../../shared/models';
import { ApiService } from '../../core/services/api.service';
import { LocalStorageService } from '../../core/services/local-storage.service';

@Component({
  selector: 'app-refinement',
  templateUrl: './refinement.component.html',
  styleUrls: ['./refinement.component.scss']
})
export class RefinementComponent implements OnInit {
  story: Story | null = null;
  feedbackAgents: FeedbackAgent[] = [];
  selectedAgents: Set<string> = new Set();
  feedbackData: FeedbackData[] = [];
  selectedFeedback: FeedbackItem[] = [];
  ignoredFeedback: FeedbackItem[] = [];

  isGeneratingFeedback = false;
  isApplyingFeedback = false;
  showFeedbackResults = false;

  agentSelectionForm: FormGroup;

  availableAgents = [
    {
      id: 'character_consistency',
      name: 'Character Consistency Rater',
      type: 'rater',
      specialties: ['character_development', 'consistency'],
      focusAreas: ['Character voice', 'Personality consistency', 'Character motivations'],
      description: 'Evaluates character consistency and development throughout the story'
    },
    {
      id: 'narrative_flow',
      name: 'Narrative Flow Rater',
      type: 'rater',
      specialties: ['pacing', 'structure'],
      focusAreas: ['Story pacing', 'Scene transitions', 'Narrative structure'],
      description: 'Analyzes story flow, pacing, and structural elements'
    },
    {
      id: 'literary_quality',
      name: 'Literary Quality Rater',
      type: 'rater',
      specialties: ['prose', 'style'],
      focusAreas: ['Writing quality', 'Language use', 'Literary devices'],
      description: 'Evaluates prose quality, style, and literary merit'
    },
    {
      id: 'genre_specialist',
      name: 'Genre Specialist',
      type: 'specialist',
      specialties: ['genre_conventions'],
      focusAreas: ['Genre elements', 'Trope usage', 'Reader expectations'],
      description: 'Provides genre-specific feedback and analysis'
    },
    {
      id: 'editor',
      name: 'Editorial Agent',
      type: 'editor',
      specialties: ['editing', 'refinement'],
      focusAreas: ['Overall coherence', 'Final polish', 'Publication readiness'],
      description: 'Provides comprehensive editorial feedback and suggestions'
    }
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private fb: FormBuilder,
    private apiService: ApiService,
    private localStorageService: LocalStorageService,
    private snackBar: MatSnackBar
  ) {
    this.agentSelectionForm = this.fb.group({
      selectedAgents: [[]]
    });
  }

  ngOnInit(): void {
    const storyId = this.route.snapshot.paramMap.get('id');
    if (storyId) {
      this.loadStory(storyId);
    } else {
      this.router.navigate(['/stories']);
    }

    // Check if feedback was requested from content generation
    const requestFeedback = this.route.snapshot.queryParamMap.get('requestFeedback');
    if (requestFeedback === 'true') {
      this.autoSelectDefaultAgents();
    }
  }

  private loadStory(storyId: string): void {
    this.story = this.localStorageService.getStory(storyId);
    if (!this.story) {
      this.snackBar.open('Story not found', 'Close', { duration: 3000 });
      this.router.navigate(['/stories']);
      return;
    }

    if (!this.story.finalContent) {
      this.snackBar.open('No content available for refinement', 'Close', { duration: 3000 });
      this.router.navigate(['/content-generation', storyId]);
      return;
    }

    // Load existing feedback if available
    if (this.story.refinementHistory && this.story.refinementHistory.length > 0) {
      const latestRefinement = this.story.refinementHistory[this.story.refinementHistory.length - 1];
      if (latestRefinement.feedbackData) {
        this.feedbackData = latestRefinement.feedbackData;
        this.showFeedbackResults = true;
      }
    }
  }

  private autoSelectDefaultAgents(): void {
    // Auto-select commonly used agents
    const defaultAgents = ['character_consistency', 'narrative_flow', 'literary_quality'];
    defaultAgents.forEach(agentId => this.selectedAgents.add(agentId));
    this.agentSelectionForm.patchValue({
      selectedAgents: Array.from(this.selectedAgents)
    });
  }

  onAgentSelectionChange(agentId: string, selected: boolean): void {
    if (selected) {
      this.selectedAgents.add(agentId);
    } else {
      this.selectedAgents.delete(agentId);
    }

    this.agentSelectionForm.patchValue({
      selectedAgents: Array.from(this.selectedAgents)
    });
  }

  onGenerateFeedback(): void {
    if (this.selectedAgents.size === 0 || !this.story || this.isGeneratingFeedback) {
      return;
    }

    this.isGeneratingFeedback = true;
    this.feedbackData = [];
    this.selectedFeedback = [];
    this.ignoredFeedback = [];

    const selectedAgentData = this.availableAgents.filter(agent =>
      this.selectedAgents.has(agent.id)
    );

    const storyContext = {
      title: this.story.title,
      genre: this.story.genre,
      outline: this.story.currentDraft?.outline || [],
      characters: this.story.currentDraft?.characters || [],
      themes: this.story.currentDraft?.themes || []
    };

    this.apiService.generateFeedback(
      this.story.finalContent,
      storyContext,
      selectedAgentData
    ).subscribe({
      next: (response) => {
        if (response.success) {
          this.feedbackData = response.data;
          this.showFeedbackResults = true;

          this.snackBar.open('Feedback generated successfully!', 'Close', {
            duration: 3000
          });
        } else {
          this.handleError('Failed to generate feedback');
        }
        this.isGeneratingFeedback = false;
      },
      error: (error) => {
        console.error('Error generating feedback:', error);
        this.handleError('Error generating feedback. Please try again.');
        this.isGeneratingFeedback = false;
      }
    });
  }

  onToggleFeedbackSelection(item: FeedbackItem): void {
    const isCurrentlySelected = this.selectedFeedback.some(f => f.id === item.id);
    const isCurrentlyIgnored = this.ignoredFeedback.some(f => f.id === item.id);

    if (isCurrentlySelected) {
      // Move from selected to ignored
      this.selectedFeedback = this.selectedFeedback.filter(f => f.id !== item.id);
      this.ignoredFeedback.push(item);
    } else if (isCurrentlyIgnored) {
      // Move from ignored to selected
      this.ignoredFeedback = this.ignoredFeedback.filter(f => f.id !== item.id);
      this.selectedFeedback.push(item);
    } else {
      // Add to selected
      this.selectedFeedback.push(item);
    }
  }

  onApplySelectedFeedback(): void {
    if (this.selectedFeedback.length === 0 || !this.story || this.isApplyingFeedback) {
      return;
    }

    this.isApplyingFeedback = true;

    const storyContext = {
      title: this.story.title,
      genre: this.story.genre,
      outline: this.story.currentDraft?.outline || [],
      characters: this.story.currentDraft?.characters || []
    };

    this.apiService.applySelectedFeedback(
      this.story.finalContent,
      storyContext,
      this.selectedFeedback,
      this.ignoredFeedback
    ).subscribe({
      next: (response) => {
        if (response.success && this.story) {
          // Save refinement history
          const refinementEntry = {
            version: (this.story.refinementHistory?.length || 0) + 1,
            timestamp: new Date(),
            feedbackData: this.feedbackData,
            selectedFeedback: this.selectedFeedback,
            ignoredFeedback: this.ignoredFeedback,
            originalContent: this.story.finalContent,
            refinedContent: response.data,
            improvements: response.data.improvements || []
          };

          if (!this.story.refinementHistory) {
            this.story.refinementHistory = [];
          }
          this.story.refinementHistory.push(refinementEntry);

          // Update final content
          this.story.finalContent = response.data;
          this.story.lastModified = new Date();
          this.localStorageService.saveStory(this.story);

          this.snackBar.open('Feedback applied successfully!', 'Close', {
            duration: 3000
          });

          // Reset feedback state for potential new round
          this.resetFeedbackState();
        } else {
          this.handleError('Failed to apply feedback');
        }
        this.isApplyingFeedback = false;
      },
      error: (error) => {
        console.error('Error applying feedback:', error);
        this.handleError('Error applying feedback. Please try again.');
        this.isApplyingFeedback = false;
      }
    });
  }

  onCompleteStory(): void {
    if (this.story) {
      this.story.currentPhase = 'completed';
      this.story.lastModified = new Date();
      this.localStorageService.saveStory(this.story);

      this.snackBar.open('Story completed successfully!', 'Close', {
        duration: 3000
      });

      this.router.navigate(['/story-view', this.story.id]);
    }
  }

  onRequestMoreFeedback(): void {
    this.resetFeedbackState();
  }

  private resetFeedbackState(): void {
    this.feedbackData = [];
    this.selectedFeedback = [];
    this.ignoredFeedback = [];
    this.showFeedbackResults = false;
    this.selectedAgents.clear();
    this.agentSelectionForm.patchValue({ selectedAgents: [] });
  }

  private handleError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  get hasSelectedAgents(): boolean {
    return this.selectedAgents.size > 0;
  }

  get hasSelectedFeedback(): boolean {
    return this.selectedFeedback.length > 0;
  }

  get canGenerateFeedback(): boolean {
    return this.hasSelectedAgents && !this.isGeneratingFeedback;
  }

  get canApplyFeedback(): boolean {
    return this.hasSelectedFeedback && !this.isApplyingFeedback;
  }

  getFeedbackByAgent(agentId: string): FeedbackData | undefined {
    return this.feedbackData.find(fd => fd.agentId === agentId);
  }

  getFeedbackSelectionState(item: FeedbackItem): 'selected' | 'ignored' | 'unselected' {
    if (this.selectedFeedback.some(f => f.id === item.id)) return 'selected';
    if (this.ignoredFeedback.some(f => f.id === item.id)) return 'ignored';
    return 'unselected';
  }

  getWordCount(): number {
    if (!this.story?.finalContent?.content) return 0;
    return this.story.finalContent.content.split(/\s+/).length;
  }
}