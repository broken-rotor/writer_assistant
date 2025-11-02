# Streaming API Documentation

## Overview

The Writer Assistant API now supports Server-Sent Events (SSE) streaming for real-time progress updates during long-running operations like rater feedback generation.

## Streaming Rater Feedback Endpoint

### Endpoint
```
POST /api/v1/rater-feedback/stream
```

### Description
Generate rater feedback with real-time progress updates through Server-Sent Events (SSE).

### Request Format
The request format is identical to the synchronous `/rater-feedback` endpoint:

```json
{
  "raterPrompt": "You are a story critic. Evaluate this plot point.",
  "plotPoint": "The hero discovers a hidden door in the basement.",
  "structured_context": {
    "systemPrompts": {
      "mainPrefix": "You are a helpful assistant.",
      "mainSuffix": "Be creative and engaging.",
      "assistantPrompt": "Provide detailed feedback."
    },
    "worldbuilding": {
      "content": "A fantasy world with magic.",
      "lastModified": "2024-01-01T00:00:00Z",
      "wordCount": 5
    },
    "storySummary": {
      "summary": "A hero's journey begins.",
      "lastModified": "2024-01-01T00:00:00Z",
      "wordCount": 4
    },
    "previousChapters": [],
    "characters": [],
    "plotContext": {
      "plotPoint": "The hero discovers a hidden door in the basement.",
      "plotOutline": "Hero finds door, explores, finds treasure.",
      "plotOutlineStatus": "draft"
    }
  }
}
```

### Response Format
The endpoint returns Server-Sent Events with the following event types:

#### Status Events
Progress updates during processing:
```json
{
  "type": "status",
  "phase": "context_processing",
  "message": "Processing rater context and plot point...",
  "progress": 20
}
```

#### Result Event
Final result with complete rater feedback:
```json
{
  "type": "result",
  "data": {
    "raterName": "Rater",
    "feedback": {
      "opinion": "This is an intriguing plot point that creates mystery and draws the reader in.",
      "suggestions": [
        "Add more sensory details about the door's appearance",
        "Consider the character's emotional state when discovering the door",
        "Describe the basement's atmosphere to build tension"
      ]
    },
    "context_metadata": {
      "tokens": 150,
      "processing_time": 2.5
    }
  },
  "status": "complete"
}
```

#### Error Event
Error information if something goes wrong:
```json
{
  "type": "error",
  "message": "LLM not initialized. Start server with --model-path",
  "error_code": "LLM_NOT_AVAILABLE"
}
```

### Streaming Phases

The streaming process includes 5 distinct phases:

1. **context_processing** (20% progress)
   - Processing structured context and rater prompt
   - Validating input data and preparing context

2. **evaluating** (50% progress)
   - LLM is evaluating the plot point
   - Analyzing content against rater criteria

3. **generating_feedback** (75% progress)
   - Generating opinion and suggestions
   - LLM is producing the actual feedback content

4. **parsing** (90% progress)
   - Parsing JSON response and validating feedback
   - Processing LLM output into structured format

5. **complete** (100% progress)
   - Final result with complete rater feedback
   - Process completed successfully

## Frontend Integration

### JavaScript/TypeScript Example

```typescript
async function generateRaterFeedbackWithUpdates(requestData: any) {
    const response = await fetch('/api/v1/rater-feedback/stream', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        },
        body: JSON.stringify(requestData)
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) throw new Error('No response body');

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'status') {
                    updateProgressUI(data.phase, data.message, data.progress);
                } else if (data.type === 'result') {
                    handleRaterFeedbackResult(data.data);
                    return;
                } else if (data.type === 'error') {
                    handleError(data.message);
                    return;
                }
            }
        }
    }
}

function updateProgressUI(phase: string, message: string, progress: number) {
    console.log(`Phase: ${phase}, Progress: ${progress}%, Message: ${message}`);
    // Update your UI progress indicators here
}

function handleRaterFeedbackResult(data: any) {
    console.log('Rater feedback received:', data);
    // Handle the final result
}

function handleError(message: string) {
    console.error('Streaming error:', message);
    // Handle errors appropriately
}
```

### Angular Service Example

```typescript
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class StreamingService {
  streamRaterFeedback(
    requestData: any,
    onProgress?: (progress: {phase: string, message: string, progress: number}) => void
  ): Observable<any> {
    return new Observable(observer => {
      fetch('/api/v1/rater-feedback/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(requestData)
      }).then(response => {
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        
        const readStream = async () => {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const eventData = JSON.parse(line.slice(6));
                
                if (eventData.type === 'status' && onProgress) {
                  onProgress({
                    phase: eventData.phase,
                    message: eventData.message,
                    progress: eventData.progress
                  });
                } else if (eventData.type === 'result') {
                  observer.next(eventData.data);
                  observer.complete();
                  return;
                } else if (eventData.type === 'error') {
                  observer.error(new Error(eventData.message));
                  return;
                }
              }
            }
          }
        };
        
        readStream();
      });
    });
  }
}
```

## Error Handling

The streaming endpoint handles errors gracefully by sending error events through the SSE stream. Common error scenarios include:

- **LLM Not Available**: When the LLM service is not initialized
- **Context Processing Errors**: Issues with processing the structured context
- **Generation Failures**: LLM generation errors or timeouts
- **Parsing Errors**: Issues parsing the LLM response into structured format

All errors are communicated through error events, allowing the client to handle them appropriately without losing the connection.

## Backward Compatibility

The original synchronous `/rater-feedback` endpoint remains available and unchanged. Clients can choose between:

- **Synchronous**: `/api/v1/rater-feedback` - Returns complete result when finished
- **Streaming**: `/api/v1/rater-feedback/stream` - Provides real-time progress updates

Both endpoints accept the same request format and return the same final result structure, ensuring easy migration between approaches.

## Performance Considerations

- Streaming responses provide better user experience for long-running operations
- Progress updates help users understand processing status
- Connection management is handled automatically by the browser
- Small delays between chunks prevent overwhelming the client
- Proper error handling ensures graceful degradation

## Testing

The streaming functionality includes comprehensive tests covering:

- Successful streaming with all phases
- Error handling scenarios
- Invalid request validation
- LLM availability checks
- Connection management

Run tests with:
```bash
pytest backend/tests/test_rater_feedback_streaming.py -v
```
