import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { ArchiveService, SearchResult, FileInfo, ArchiveStats } from '../../services/archive.service';

@Component({
  selector: 'app-archive',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './archive.component.html',
  styleUrl: './archive.component.scss'
})
export class ArchiveComponent implements OnInit, OnDestroy {
  searchQuery: string = '';
  searchResults: SearchResult[] = [];
  isSearching: boolean = false;
  hasSearched: boolean = false;
  error: string | null = null;

  stats: ArchiveStats | null = null;
  files: FileInfo[] = [];
  selectedFile: FileInfo | null = null;
  fileContent: string | null = null;
  isLoadingContent: boolean = false;

  maxResults: number = 10;
  showAdvancedOptions: boolean = false;

  private subscriptions: Subscription[] = [];

  constructor(private archiveService: ArchiveService) {}

  ngOnInit(): void {
    this.loadStats();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  loadStats(): void {
    this.subscriptions.push(
      this.archiveService.getStats().subscribe({
        next: (stats) => {
          this.stats = stats;
          this.error = null;
        },
        error: (err) => {
          console.error('Failed to load archive stats:', err);
          // Check if it's a 503 (service unavailable) - archive not configured
          if (err.status === 503) {
            this.error = err.error?.detail || 'Archive feature is not enabled. Please configure ARCHIVE_DB_PATH to enable this feature. See ARCHIVE_SETUP.md for instructions.';
          } else {
            this.error = 'Archive not available. Please ensure the database has been initialized.';
          }
        }
      })
    );
  }

  onSearch(): void {
    if (!this.searchQuery.trim()) {
      return;
    }

    this.isSearching = true;
    this.hasSearched = true;
    this.error = null;
    this.selectedFile = null;
    this.fileContent = null;

    this.subscriptions.push(
      this.archiveService.search(this.searchQuery, this.maxResults).subscribe({
        next: (response) => {
          this.searchResults = response.results;
          this.isSearching = false;

          if (this.searchResults.length === 0) {
            this.error = 'No results found for your query.';
          }
        },
        error: (err) => {
          console.error('Search failed:', err);
          if (err.status === 503) {
            this.error = err.error?.detail || 'Archive feature is not enabled.';
          } else {
            this.error = 'Search failed. Please try again.';
          }
          this.isSearching = false;
          this.searchResults = [];
        }
      })
    );
  }

  onSearchKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      this.onSearch();
    }
  }

  viewFileContent(result: SearchResult): void {
    this.isLoadingContent = true;
    this.error = null;

    this.subscriptions.push(
      this.archiveService.getFileContent(result.file_path).subscribe({
        next: (response) => {
          this.fileContent = response.content;
          this.selectedFile = {
            file_path: result.file_path,
            file_name: result.file_name
          };
          this.isLoadingContent = false;

          // Scroll to content viewer
          setTimeout(() => {
            const element = document.getElementById('content-viewer');
            element?.scrollIntoView({ behavior: 'smooth' });
          }, 100);
        },
        error: (err) => {
          console.error('Failed to load file content:', err);
          this.error = 'Failed to load file content.';
          this.isLoadingContent = false;
        }
      })
    );
  }

  closeFileContent(): void {
    this.selectedFile = null;
    this.fileContent = null;
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.searchResults = [];
    this.hasSearched = false;
    this.error = null;
    this.selectedFile = null;
    this.fileContent = null;
  }

  toggleAdvancedOptions(): void {
    this.showAdvancedOptions = !this.showAdvancedOptions;
  }

  getHighlightedText(text: string, maxLength: number = 500): string {
    if (text.length <= maxLength) {
      return text;
    }
    return text.substring(0, maxLength) + '...';
  }

  getSimilarityBadgeClass(score: number): string {
    if (score >= 0.8) return 'badge-high';
    if (score >= 0.6) return 'badge-medium';
    return 'badge-low';
  }

  getSimilarityLabel(score: number): string {
    if (score >= 0.8) return 'High Match';
    if (score >= 0.6) return 'Medium Match';
    return 'Low Match';
  }
}
