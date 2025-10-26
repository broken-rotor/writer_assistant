import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import {
  ArchiveService,
  SearchResult,
  FileInfo,
  ArchiveStats,
  RAGChatMessage,
  RAGStatusResponse
} from '../../services/archive.service';

@Component({
  selector: 'app-archive',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './archive.component.html',
  styleUrl: './archive.component.scss'
})
export class ArchiveComponent implements OnInit, OnDestroy {
  // Search mode properties
  searchQuery = '';
  searchResults: SearchResult[] = [];
  isSearching = false;
  hasSearched = false;
  error: string | null = null;

  stats: ArchiveStats | null = null;
  files: FileInfo[] = [];
  selectedFile: FileInfo | null = null;
  fileContent: string | null = null;
  isLoadingContent = false;

  maxResults = 10;
  showAdvancedOptions = false;

  // RAG/Chat mode properties
  mode: 'search' | 'chat' = 'search';
  ragStatus: RAGStatusResponse | null = null;
  chatMessages: RAGChatMessage[] = [];
  chatInput = '';
  isChatProcessing = false;
  chatError: string | null = null;
  chatInfoMessage: string | null = null;
  currentChatSources: SearchResult[] = [];
  selectedMessageIndex: number | null = null;

  private subscriptions: Subscription[] = [];
  private archiveService = inject(ArchiveService);

  ngOnInit(): void {
    this.loadStats();
    this.loadRagStatus();
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

  getHighlightedText(text: string, maxLength = 500): string {
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

  // ============================================================================
  // RAG/Chat Mode Methods
  // ============================================================================

  loadRagStatus(): void {
    this.subscriptions.push(
      this.archiveService.getRagStatus().subscribe({
        next: (status) => {
          this.ragStatus = status;

          // If LLM is loading, poll again after a delay
          if (status.llm_loading) {
            setTimeout(() => this.loadRagStatus(), 2000);
          }
        },
        error: (err) => {
          console.error('Failed to load RAG status:', err);
          this.ragStatus = {
            archive_enabled: false,
            llm_enabled: false,
            llm_loading: false,
            rag_enabled: false,
            message: 'Could not check RAG status'
          };
        }
      })
    );
  }

  switchMode(newMode: 'search' | 'chat'): void {
    this.mode = newMode;
    if (newMode === 'chat') {
      // Clear search results when switching to chat
      this.hasSearched = false;
      this.searchResults = [];
      this.error = null;
    } else {
      // Clear chat when switching to search
      this.chatMessages = [];
      this.chatError = null;
      this.chatInfoMessage = null;
      this.currentChatSources = [];
      this.selectedMessageIndex = null;
    }
  }

  sendChatMessage(): void {
    if (!this.chatInput.trim() || this.isChatProcessing) {
      return;
    }

    // Add user message to chat
    const userMessage: RAGChatMessage = {
      role: 'user',
      content: this.chatInput.trim()
    };

    this.chatMessages.push(userMessage);
    this.chatError = null;
    this.isChatProcessing = true;

    const currentInput = this.chatInput;
    this.chatInput = '';

    // Send to RAG service
    this.subscriptions.push(
      this.archiveService.ragChat(this.chatMessages).subscribe({
        next: (response) => {
          // Add assistant response to chat with sources
          const assistantMessage: RAGChatMessage = {
            role: 'assistant',
            content: response.answer,
            sources: response.sources
          };

          this.chatMessages.push(assistantMessage);

          // Auto-select the latest assistant message
          this.selectedMessageIndex = this.chatMessages.length - 1;
          this.currentChatSources = response.sources;
          this.isChatProcessing = false;

          // Display info message if present (document retrieval warnings/errors)
          if (response.info_message) {
            this.chatInfoMessage = response.info_message;
            // Auto-clear info message after 10 seconds
            setTimeout(() => {
              this.chatInfoMessage = null;
            }, 10000);
          } else {
            this.chatInfoMessage = null;
          }

          // Scroll to bottom of chat
          setTimeout(() => {
            const chatContainer = document.querySelector('.chat-messages');
            if (chatContainer) {
              chatContainer.scrollTop = chatContainer.scrollHeight;
            }
          }, 100);
        },
        error: (err) => {
          console.error('Chat failed:', err);

          // Remove user message on error
          this.chatMessages.pop();
          this.chatInput = currentInput;

          if (err.status === 503) {
            this.chatError = err.error?.detail || 'RAG feature is not available. Please ensure both archive and LLM are configured.';
          } else {
            this.chatError = 'Failed to process your question. Please try again.';
          }

          this.isChatProcessing = false;
        }
      })
    );
  }

  onChatKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendChatMessage();
    }
  }

  clearChat(): void {
    this.chatMessages = [];
    this.chatError = null;
    this.chatInfoMessage = null;
    this.currentChatSources = [];
    this.chatInput = '';
    this.selectedMessageIndex = null;
  }

  selectMessage(index: number): void {
    const message = this.chatMessages[index];
    if (message.role === 'assistant' && message.sources) {
      this.selectedMessageIndex = index;
      this.currentChatSources = message.sources;
    }
  }

  isMessageSelected(index: number): boolean {
    return this.selectedMessageIndex === index;
  }

  // Convert markdown to HTML (simple implementation)
  parseMarkdown(text: string): string {
    if (!text) return '';

    let html = text;

    // Bold: **text** or __text__
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

    // Italic: *text* or _text_
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.+?)_/g, '<em>$1</em>');

    // Lists: lines starting with - or *
    html = html.replace(/^[-*]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    return html;
  }

  isRagEnabled(): boolean {
    return this.ragStatus?.rag_enabled || false;
  }

  isLlmLoading(): boolean {
    return this.ragStatus?.llm_loading || false;
  }

  getRagStatusMessage(): string {
    return this.ragStatus?.message || 'Checking RAG status...';
  }
}
