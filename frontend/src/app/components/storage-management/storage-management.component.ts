import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { LocalStorageService, StorageQuota, StoryIndex } from '../../services/local-storage.service';
import { StoryService } from '../../services/story.service';

@Component({
  selector: 'app-storage-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './storage-management.component.html',
  styleUrl: './storage-management.component.scss'
})
export class StorageManagementComponent implements OnInit, OnDestroy {
  storageQuota: StorageQuota = { used: 0, available: 0, total: 0, percentage: 0 };
  storiesIndex: StoryIndex[] = [];
  storageStats: { [key: string]: number } = {};

  private subscriptions: Subscription[] = [];

  // UI state
  showCleanupDialog = false;
  cleanupMaxAge = 30; // days
  showExportDialog = false;
  isExporting = false;
  importFile: File | null = null;
  isImporting = false;
  importResult: { success: number; errors: string[] } | null = null;

  constructor(
    private localStorageService: LocalStorageService,
    private storyService: StoryService
  ) {}

  ngOnInit(): void {
    // Subscribe to storage updates
    this.subscriptions.push(
      this.localStorageService.getStorageQuota().subscribe(quota => {
        this.storageQuota = quota;
      })
    );

    this.subscriptions.push(
      this.localStorageService.getStoriesIndex().subscribe(index => {
        this.storiesIndex = index;
      })
    );

    this.updateStorageStats();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  updateStorageStats(): void {
    this.storageStats = this.localStorageService.getStorageStats();
  }

  // Storage quota helpers
  getUsedStorageInMB(): string {
    return (this.storageQuota.used / (1024 * 1024)).toFixed(2);
  }

  getAvailableStorageInMB(): string {
    return (this.storageQuota.available / (1024 * 1024)).toFixed(2);
  }

  getTotalStorageInMB(): string {
    return (this.storageQuota.total / (1024 * 1024)).toFixed(2);
  }

  getStoragePercentageClass(): string {
    if (this.storageQuota.percentage > 90) return 'storage-critical';
    if (this.storageQuota.percentage > 75) return 'storage-warning';
    return 'storage-normal';
  }

  // Story size helpers
  getStorySizeInKB(story: StoryIndex): string {
    return (story.size / 1024).toFixed(1);
  }

  getFormattedDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  // Cleanup operations
  openCleanupDialog(): void {
    this.showCleanupDialog = true;
  }

  closeCleanupDialog(): void {
    this.showCleanupDialog = false;
  }

  async performCleanup(): Promise<void> {
    try {
      const cleanedCount = this.localStorageService.cleanupOldStories(this.cleanupMaxAge);
      alert(`Successfully cleaned up ${cleanedCount} old stories.`);
      this.closeCleanupDialog();
      this.updateStorageStats();
    } catch (error) {
      console.error('Error during cleanup:', error);
      alert('Error occurred during cleanup. Please try again.');
    }
  }

  async deleteStory(storyId: string): Promise<void> {
    if (confirm('Are you sure you want to delete this story? This action cannot be undone.')) {
      try {
        const success = await this.storyService.deleteStory(storyId);
        if (success) {
          this.updateStorageStats();
        } else {
          alert('Failed to delete story. Please try again.');
        }
      } catch (error) {
        console.error('Error deleting story:', error);
        alert('Error occurred while deleting story.');
      }
    }
  }

  // Export operations
  openExportDialog(): void {
    this.showExportDialog = true;
  }

  closeExportDialog(): void {
    this.showExportDialog = false;
  }

  async exportAllStories(): Promise<void> {
    try {
      this.isExporting = true;
      const blob = this.localStorageService.exportAllStories();

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `writer_assistant_export_${new Date().toISOString().split('T')[0]}.json`;
      link.click();

      // Cleanup
      window.URL.revokeObjectURL(url);

      this.closeExportDialog();
    } catch (error) {
      console.error('Error exporting stories:', error);
      alert('Error occurred during export. Please try again.');
    } finally {
      this.isExporting = false;
    }
  }

  // Import operations
  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file && file.type === 'application/json') {
      this.importFile = file;
    } else {
      alert('Please select a valid JSON file.');
      this.importFile = null;
    }
  }

  async importStories(): Promise<void> {
    if (!this.importFile) {
      alert('Please select a file to import.');
      return;
    }

    try {
      this.isImporting = true;
      this.importResult = await this.localStorageService.importStories(this.importFile);

      if (this.importResult.success > 0) {
        this.updateStorageStats();
      }
    } catch (error) {
      console.error('Error importing stories:', error);
      this.importResult = { success: 0, errors: [`Import failed: ${error}`] };
    } finally {
      this.isImporting = false;
    }
  }

  closeImportResult(): void {
    this.importResult = null;
    this.importFile = null;
  }

  // Storage optimization
  async optimizeStorage(): Promise<void> {
    try {
      // This could implement compression, duplicate removal, etc.
      alert('Storage optimization feature coming soon!');
    } catch (error) {
      console.error('Error optimizing storage:', error);
      alert('Error occurred during storage optimization.');
    }
  }

  // Backup operations
  async createBackup(): Promise<void> {
    await this.exportAllStories();
  }

  formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}