import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Observable } from 'rxjs';
import { Story, LocalStorageInfo } from '../../shared/models';
import { LocalStorageService } from '../../core/services/local-storage.service';

@Component({
  selector: 'app-story-list',
  templateUrl: './story-list.component.html',
  styleUrls: ['./story-list.component.scss']
})
export class StoryListComponent implements OnInit {
  stories: Story[] = [];
  storageInfo$: Observable<LocalStorageInfo>;
  selectedStories: Set<string> = new Set();

  displayedColumns: string[] = ['select', 'title', 'genre', 'phase', 'lastModified', 'actions'];

  phaseLabels: { [key: string]: string } = {
    'draft': 'Draft Development',
    'character_dialog': 'Character Dialog',
    'detailed_content': 'Content Generation',
    'refinement': 'Refinement',
    'completed': 'Completed'
  };

  constructor(
    private localStorageService: LocalStorageService,
    private router: Router,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {
    this.storageInfo$ = this.localStorageService.getStorageInfo$();
  }

  ngOnInit(): void {
    this.loadStories();
  }

  private loadStories(): void {
    this.stories = this.localStorageService.getAllStories()
      .sort((a, b) => new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime());
  }

  onCreateNew(): void {
    this.router.navigate(['/story-input']);
  }

  onContinueStory(story: Story): void {
    switch (story.currentPhase) {
      case 'draft':
        this.router.navigate(['/draft-review', story.id]);
        break;
      case 'character_dialog':
        this.router.navigate(['/character-dialog', story.id]);
        break;
      case 'detailed_content':
        this.router.navigate(['/content-generation', story.id]);
        break;
      case 'refinement':
        this.router.navigate(['/refinement', story.id]);
        break;
      case 'completed':
        this.router.navigate(['/story-view', story.id]);
        break;
    }
  }

  onDuplicateStory(story: Story): void {
    const duplicatedStory = this.localStorageService.duplicateStory(story.id);
    if (duplicatedStory) {
      this.loadStories();
      this.snackBar.open(`Story "${duplicatedStory.title}" duplicated successfully!`, 'Close', {
        duration: 3000
      });
    } else {
      this.snackBar.open('Failed to duplicate story', 'Close', {
        duration: 3000
      });
    }
  }

  onExportStory(story: Story): void {
    const exportData = this.localStorageService.exportStory(story.id);
    this.downloadFile(exportData, `${story.title}_export.json`, 'application/json');

    this.snackBar.open('Story exported successfully!', 'Close', {
      duration: 3000
    });
  }

  onDeleteStory(story: Story): void {
    if (confirm(`Are you sure you want to delete "${story.title}"? This action cannot be undone.`)) {
      this.localStorageService.deleteStory(story.id);
      this.loadStories();
      this.selectedStories.delete(story.id);

      this.snackBar.open(`Story "${story.title}" deleted successfully`, 'Close', {
        duration: 3000
      });
    }
  }

  onImportStory(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          const importData = e.target?.result as string;
          const importedStory = this.localStorageService.importStory(importData);

          if (importedStory) {
            this.loadStories();
            this.snackBar.open(`Story "${importedStory.title}" imported successfully!`, 'Close', {
              duration: 3000
            });
          } else {
            this.snackBar.open('Failed to import story. Please check the file format.', 'Close', {
              duration: 5000
            });
          }
        } catch (error) {
          this.snackBar.open('Invalid file format', 'Close', {
            duration: 3000
          });
        }
      };

      reader.readAsText(file);
    }

    // Reset input
    input.value = '';
  }

  onToggleStorySelection(storyId: string): void {
    if (this.selectedStories.has(storyId)) {
      this.selectedStories.delete(storyId);
    } else {
      this.selectedStories.add(storyId);
    }
  }

  onToggleAllSelection(): void {
    if (this.selectedStories.size === this.stories.length) {
      this.selectedStories.clear();
    } else {
      this.selectedStories.clear();
      this.stories.forEach(story => this.selectedStories.add(story.id));
    }
  }

  onBulkExport(): void {
    if (this.selectedStories.size === 0) return;

    const selectedStoriesData = Array.from(this.selectedStories).map(storyId => {
      return JSON.parse(this.localStorageService.exportStory(storyId));
    });

    const bulkExportData = {
      stories: selectedStoriesData,
      exportedAt: new Date(),
      version: '1.0'
    };

    const exportData = JSON.stringify(bulkExportData, null, 2);
    this.downloadFile(exportData, `bulk_export_${new Date().toISOString().split('T')[0]}.json`, 'application/json');

    this.snackBar.open(`${this.selectedStories.size} stories exported successfully!`, 'Close', {
      duration: 3000
    });
  }

  onBulkDelete(): void {
    if (this.selectedStories.size === 0) return;

    const confirmed = confirm(`Are you sure you want to delete ${this.selectedStories.size} selected stories? This action cannot be undone.`);

    if (confirmed) {
      Array.from(this.selectedStories).forEach(storyId => {
        this.localStorageService.deleteStory(storyId);
      });

      this.loadStories();
      this.selectedStories.clear();

      this.snackBar.open('Selected stories deleted successfully', 'Close', {
        duration: 3000
      });
    }
  }

  onBackupAll(): void {
    const backupData = this.localStorageService.backupAllData();
    this.downloadFile(backupData, `writer_assistant_backup_${new Date().toISOString().split('T')[0]}.json`, 'application/json');

    this.snackBar.open('Complete backup created successfully!', 'Close', {
      duration: 3000
    });
  }

  private downloadFile(content: string, filename: string, contentType: string): void {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  get hasSelectedStories(): boolean {
    return this.selectedStories.size > 0;
  }

  get isAllSelected(): boolean {
    return this.selectedStories.size === this.stories.length && this.stories.length > 0;
  }

  get isIndeterminate(): boolean {
    return this.selectedStories.size > 0 && this.selectedStories.size < this.stories.length;
  }

  getPhaseProgress(phase: string): number {
    const progressMap: { [key: string]: number } = {
      'draft': 25,
      'character_dialog': 50,
      'detailed_content': 75,
      'refinement': 90,
      'completed': 100
    };
    return progressMap[phase] || 0;
  }

  getPhaseColor(phase: string): string {
    const colorMap: { [key: string]: string } = {
      'draft': 'accent',
      'character_dialog': 'primary',
      'detailed_content': 'primary',
      'refinement': 'warn',
      'completed': 'primary'
    };
    return colorMap[phase] || 'primary';
  }
}