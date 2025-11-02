import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

export interface StreamingEvent {
  type: 'status' | 'result' | 'error';
  phase?: string;
  message?: string;
  progress?: number;
  data?: any;
  status?: string;
  error_code?: string;
}

export interface StreamingProgress {
  phase: string;
  message: string;
  progress: number;
}

@Injectable({
  providedIn: 'root'
})
export class StreamingService {
  private readonly baseUrl = 'http://localhost:8000/api/v1';

  /**
   * Create a Server-Sent Events connection to a streaming endpoint
   */
  createSSEConnection<T>(
    endpoint: string,
    requestData: any,
    onProgress?: (progress: StreamingProgress) => void
  ): Observable<T> {
    return new Observable<T>(observer => {
      let eventSource: EventSource | null = null;
      
      try {
        // Create a POST request to initiate the streaming
        fetch(`${this.baseUrl}${endpoint}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
          },
          body: JSON.stringify(requestData)
        }).then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const reader = response.body?.getReader();
          const decoder = new TextDecoder();
          
          if (!reader) {
            throw new Error('No response body');
          }
          
          const readStream = async () => {
            try {
              while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                  if (line.startsWith('data: ')) {
                    try {
                      const eventData: StreamingEvent = JSON.parse(line.slice(6));
                      
                      if (eventData.type === 'status' && onProgress) {
                        onProgress({
                          phase: eventData.phase || '',
                          message: eventData.message || '',
                          progress: eventData.progress || 0
                        });
                      } else if (eventData.type === 'result') {
                        observer.next(eventData.data as T);
                        observer.complete();
                        return;
                      } else if (eventData.type === 'error') {
                        observer.error(new Error(eventData.message || 'Streaming error'));
                        return;
                      }
                    } catch (parseError) {
                      console.warn('Failed to parse SSE event:', line, parseError);
                    }
                  }
                }
              }
            } catch (error) {
              observer.error(error);
            }
          };
          
          readStream();
        }).catch(error => {
          observer.error(error);
        });
        
      } catch (error) {
        observer.error(error);
      }
      
      // Cleanup function
      return () => {
        if (eventSource) {
          eventSource.close();
        }
      };
    });
  }

  /**
   * Stream rater feedback with progress updates
   */
  streamRaterFeedback(
    requestData: any,
    onProgress?: (progress: StreamingProgress) => void
  ): Observable<any> {
    return this.createSSEConnection('/rater-feedback/stream', requestData, onProgress);
  }
}
