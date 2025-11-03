import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { SSEStreamingService, SSEStreamingOptions } from './sse-streaming.service';

export interface SearchResult {
  file_path: string;
  file_name: string;
  matching_section: string;
  chunk_index: number;
  similarity_score: number;
  char_start: number;
  char_end: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
}

export interface FileInfo {
  file_path: string;
  file_name: string;
}

export interface FileListResponse {
  files: FileInfo[];
  total_files: number;
}

export interface ArchiveStats {
  total_chunks: number;
  total_files: number;
  collection_name: string;
  db_path: string;
}

export interface RAGChatMessage {
  role: string;
  content: string;
  sources?: RAGSource[];  // Sources for assistant messages
}

export interface RAGSource {
  file_path: string;
  file_name: string;
  matching_section: string;
  similarity_score: number;
}

export interface RAGResponse {
  query: string;
  answer: string;
  sources: RAGSource[];
  total_sources: number;
  info_message?: string;  // Informational message about retrieval status
}

export interface RAGStatusResponse {
  archive_enabled: boolean;
  llm_enabled: boolean;
  llm_loading: boolean;
  rag_enabled: boolean;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ArchiveService {
  private apiUrl = `${environment.apiUrl}/archive`;

  private http = inject(HttpClient);
  private sseStreamingService = inject(SSEStreamingService);

  /**
   * Search the story archive using semantic search
   */
  search(query: string, maxResults = 10, filterFileName?: string): Observable<SearchResponse> {
    const body = {
      query: query,
      max_results: maxResults,
      filter_file_name: filterFileName
    };

    return this.http.post<SearchResponse>(`${this.apiUrl}/search`, body);
  }

  /**
   * Get a list of all files in the archive
   */
  listFiles(): Observable<FileListResponse> {
    return this.http.get<FileListResponse>(`${this.apiUrl}/files`);
  }

  /**
   * Get the full content of a specific file
   */
  getFileContent(filePath: string): Observable<{ file_path: string; content: string }> {
    const params = new HttpParams().set('file_path', filePath);
    return this.http.get<{ file_path: string; content: string }>(
      `${this.apiUrl}/files/content`,
      { params }
    );
  }

  /**
   * Get archive statistics
   */
  getStats(): Observable<ArchiveStats> {
    return this.http.get<ArchiveStats>(`${this.apiUrl}/stats`);
  }

  /**
   * Check RAG (Retrieval-Augmented Generation) status
   */
  getRagStatus(): Observable<RAGStatusResponse> {
    return this.http.get<RAGStatusResponse>(`${this.apiUrl}/rag/status`);
  }

  /**
   * Ask a question using RAG (single-turn query)
   */
  ragQuery(
    question: string,
    nContextChunks = 5,
    maxTokens = 1024,
    temperature = 0.3,
    filterFileName?: string
  ): Observable<RAGResponse> {
    const body = {
      question: question,
      n_context_chunks: nContextChunks,
      max_tokens: maxTokens,
      temperature: temperature,
      filter_file_name: filterFileName
    };

    return this.http.post<RAGResponse>(`${this.apiUrl}/rag/query`, body);
  }

  /**
   * Ask a question using RAG with streaming progress updates
   */
  ragQueryStream(
    question: string,
    nContextChunks = 5,
    maxTokens = 1024,
    temperature = 0.3,
    filterFileName?: string,
    options?: SSEStreamingOptions
  ): Observable<RAGResponse> {
    const body = {
      question: question,
      n_context_chunks: nContextChunks,
      max_tokens: maxTokens,
      temperature: temperature,
      filter_file_name: filterFileName
    };

    return this.sseStreamingService.createSSEObservable<RAGResponse>(
      `${this.apiUrl}/rag/query/stream`,
      body,
      options
    );
  }

  /**
   * Chat with RAG context (multi-turn conversation) with streaming progress updates
   */
  ragChat(
    messages: RAGChatMessage[],
    nContextChunks = 5,
    maxTokens = 1024,
    temperature = 0.4,
    filterFileName?: string,
    onProgress?: (update: { phase: string; message: string; progress: number }) => void
  ): Observable<RAGResponse> {
    const body = {
      messages: messages,
      n_context_chunks: nContextChunks,
      max_tokens: maxTokens,
      temperature: temperature,
      filter_file_name: filterFileName
    };

    return this.sseStreamingService.createSSEObservable<RAGResponse>(
      `${this.apiUrl}/rag/chat`,
      body,
      {
        onProgress: onProgress,
        onError: (error) => {
          console.error('RAG chat streaming error:', error);
        }
      }
    );
  }
}
