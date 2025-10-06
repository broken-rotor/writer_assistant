import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { StoryCreate } from '../../models/story.model';
import { StoryService } from '../../services/story.service';

@Component({
  selector: 'app-story-creation',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './story-creation.component.html',
  styleUrl: './story-creation.component.scss'
})
export class StoryCreationComponent {
  storyData: StoryCreate = {
    title: '',
    genre: '',
    description: '',
    initial_guidance: ''
  };

  isSubmitting = false;

  constructor(
    private storyService: StoryService,
    private router: Router
  ) {}

  async onSubmit(): Promise<void> {
    if (this.isSubmitting) return;

    this.isSubmitting = true;
    try {
      const story = await this.storyService.createStory(this.storyData);
      console.log('Story created:', story);
      this.router.navigate(['/dashboard']);
    } catch (error) {
      console.error('Failed to create story:', error);
      alert('Failed to create story. Please try again.');
    } finally {
      this.isSubmitting = false;
    }
  }
}
