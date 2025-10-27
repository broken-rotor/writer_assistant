import { Component, OnInit, OnDestroy, ViewChild, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';
import { StoryListItem } from '../../models/story.model';
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
  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  stories: StoryListItem[] = [];
  storageQuota: StorageQuota = { used: 0, available: 0, total: 0, percentage: 0 };

  private subscriptions: Subscription[] = [];
  private storyService = inject(StoryService);
  private localStorageService = inject(LocalStorageService);
  private router = inject(Router);

  ngOnInit(): void {
    this.loadStories();
    this.loadStorageInfo();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  loadStories(): void {
    this.subscriptions.push(
      this.storyService.getStoryList().subscribe(stories => {
        this.stories = stories;
      })
    );
  }

  loadStorageInfo(): void {
    this.subscriptions.push(
      this.localStorageService.getStorageQuota().subscribe(quota => {
        this.storageQuota = quota;
      })
    );
  }

  createNewStory(): void {
    const story = this.storyService.createStory('Untitled Story');
    this.router.navigate(['/story', story.id]);
  }

  deleteStory(storyId: string): void {
    if (confirm('Are you sure you want to delete this story?')) {
      const success = this.storyService.deleteStory(storyId);
      if (!success) {
        alert('Failed to delete story. Please try again.');
      }
    }
  }

  getStoragePercentageClass(): string {
    if (this.storageQuota.percentage > 90) return 'storage-critical';
    if (this.storageQuota.percentage > 75) return 'storage-warning';
    return 'storage-normal';
  }

  getFormattedDate(date: Date): string {
    return date.toLocaleDateString();
  }

  exportStory(storyId: string): void {
    const story = this.storyService.getStory(storyId);
    if (!story) {
      alert('Story not found');
      return;
    }

    const blob = new Blob([JSON.stringify(story, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const filename = story.general.title.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    window.URL.revokeObjectURL(url);
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

  triggerImport(): void {
    this.fileInput.nativeElement.click();
  }

  async onFileSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) return;

    if (file.type !== 'application/json') {
      alert('Please select a valid JSON file');
      return;
    }

    try {
      const result = await this.localStorageService.importStory(file);

      if (result.success) {
        alert('Successfully imported story');
        this.loadStories();
        this.loadStorageInfo();
      } else {
        alert(`Import failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Import failed:', error);
      alert('Failed to import story. Please check the file format.');
    } finally {
      // Reset the file input
      input.value = '';
    }
  }
}
