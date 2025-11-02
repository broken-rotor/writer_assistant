import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface SSEProgressUpdate {
  phase: string;
  message: string;
  progress: number;
}

export interface SSEStreamingOptions {
  onProgress?: (update: SSEProgressUpdate) => void;
  onError?: (error: Error) => void;
}

@Injectable({
  providedIn: 'root'
})
export class SSEStreamingService {

  /**
   * Creates an Observable that handles SSE streaming for POST requests
   * @param url The endpoint URL
   * @param requestBody The request body to send
   * @param options Optional callbacks for progress and error handling
   * @returns Observable that emits the final result
   */
  createSSEObservable<T>(
    url: string, 
    requestBody: any, 
    options?: SSEStreamingOptions
  ): Observable<T> {
    return new Observable(observer => {
      // Use fetch for POST with SSE
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache'
        },
        body: JSON.stringify(requestBody)
      }).then(response => {
        if (!response.ok) {
          const error = new Error(`HTTP error! status: ${response.status}`);
          if (options?.onError) {
            options.onError(error);
          }
          observer.error(error);
          return;
        }
        
        const reader = response.body?.getReader();
        if (!reader) {
          const error = new Error('No response body reader available');
          if (options?.onError) {
            options.onError(error);
          }
          observer.error(error);
          return;
        }
        
        const decoder = new TextDecoder();
        let buffer = '';
        
        const readStream = () => {
          reader.read().then(({ done, value }) => {
            if (done) {
              observer.complete();
              return;
            }
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6)); // Remove 'data: ' prefix
                  
                  if (data.type === 'result') {
                    // Final result - emit the data and complete
                    observer.next(data.data as T);
                    observer.complete();
                    return;
                  } else if (data.type === 'error') {
                    const error = new Error(data.message);
                    if (options?.onError) {
                      options.onError(error);
                    }
                    observer.error(error);
                    return;
                  } else if (data.type === 'status' && options?.onProgress) {
                    // Progress update
                    options.onProgress({
                      phase: data.phase,
                      message: data.message,
                      progress: data.progress
                    });
                  }
                } catch (e) {
                  console.warn('Failed to parse SSE data:', line, e);
                }
              }
            }
            
            readStream(); // Continue reading
          }).catch(error => {
            if (options?.onError) {
              options.onError(error);
            }
            observer.error(error);
          });
        };
        
        readStream();
      }).catch(error => {
        if (options?.onError) {
          options.onError(error);
        }
        observer.error(error);
      });
    });
  }
}
