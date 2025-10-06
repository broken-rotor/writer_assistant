import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';
import { Story } from '../../models/story.model';
import { StoryService } from '../../services/story.service';
import { LocalStorageService, StorageQuota } from '../../services/local-storage.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit, OnDestroy {
  stories: Story[] = [];
  storageQuota: StorageQuota = { used: 0, available: 0, total: 0, percentage: 0 };

  private subscriptions: Subscription[] = [];

  constructor(
    private storyService: StoryService,
    private localStorageService: LocalStorageService
  ) {}

  ngOnInit(): void {
    this.loadStories();
    this.loadStorageInfo();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  async loadStories(): Promise<void> {
    try {
      await this.storyService.loadStories();
      this.subscriptions.push(
        this.storyService.stories$.subscribe(stories => {
          this.stories = stories;
        })
      );
    } catch (error) {
      console.error('Failed to load stories:', error);
    }
  }

  loadStorageInfo(): void {
    this.subscriptions.push(
      this.localStorageService.getStorageQuota().subscribe(quota => {
        this.storageQuota = quota;
      })
    );
  }

  async deleteStory(storyId: string): Promise<void> {
    if (confirm('Are you sure you want to delete this story?')) {
      try {
        await this.storyService.deleteStory(storyId);
      } catch (error) {
        console.error('Failed to delete story:', error);
        alert('Failed to delete story. Please try again.');
      }
    }
  }

  getProgressPercentage(story: Story): number {
    return story.progress?.['overall_progress'] || 0;
  }

  getProgressClass(story: Story): string {
    const progress = this.getProgressPercentage(story);
    if (progress >= 80) return 'progress-high';
    if (progress >= 40) return 'progress-medium';
    return 'progress-low';
  }

  getStoragePercentageClass(): string {
    if (this.storageQuota.percentage > 90) return 'storage-critical';
    if (this.storageQuota.percentage > 75) return 'storage-warning';
    return 'storage-normal';
  }

  getFormattedDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  exportAllStories(): void {
    const blob = this.localStorageService.exportAllStories();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `writer_assistant_backup_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    window.URL.revokeObjectURL(url);
  }
}
