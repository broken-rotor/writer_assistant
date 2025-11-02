/**
 * Example TypeScript code for consuming the streaming modify-chapter endpoint
 * This demonstrates how to handle Server-Sent Events (SSE) from the backend
 */

interface ModifyChapterRequest {
  currentChapter: string;
  userRequest: string;
  compose_phase?: any;
  phase_context?: any;
  structured_context: any;
  context_processing_config?: any;
}

interface ModifyChapterResponse {
  modifiedChapter: string;
  wordCount: number;
  changesSummary: string;
  context_metadata?: any;
  metadata?: any;
}

interface StreamingStatus {
  type: 'status';
  phase: 'context_processing' | 'analyzing' | 'modifying' | 'finalizing';
  message: string;
  progress: number;
}

interface StreamingResult {
  type: 'result';
  data: ModifyChapterResponse;
  status: 'complete';
}

interface StreamingError {
  type: 'error';
  message: string;
}

type StreamingMessage = StreamingStatus | StreamingResult | StreamingError;

/**
 * Modify a chapter with real-time progress updates
 */
async function modifyChapterWithUpdates(
  requestData: ModifyChapterRequest,
  onProgress?: (phase: string, message: string, progress: number) => void,
  onError?: (error: string) => void
): Promise<ModifyChapterResponse> {
  const response = await fetch('/api/v1/modify-chapter', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('No response body');
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data: StreamingMessage = JSON.parse(line.slice(6));
            
            if (data.type === 'status') {
              // Update progress UI
              onProgress?.(data.phase, data.message, data.progress);
            } else if (data.type === 'result') {
              // Return final result
              return data.data;
            } else if (data.type === 'error') {
              // Handle error
              onError?.(data.message);
              throw new Error(data.message);
            }
          } catch (parseError) {
            console.warn('Failed to parse SSE data:', line, parseError);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  throw new Error('Stream ended without result');
}

/**
 * Example usage with progress updates
 */
async function exampleUsage() {
  const requestData: ModifyChapterRequest = {
    currentChapter: "Detective Chen walked into the dimly lit room...",
    userRequest: "Add more tension and suspense to this scene",
    structured_context: {
      // Your structured context data here
    }
  };

  try {
    const result = await modifyChapterWithUpdates(
      requestData,
      // Progress callback
      (phase, message, progress) => {
        console.log(`Phase: ${phase} (${progress}%) - ${message}`);
        updateProgressUI(phase, message, progress);
      },
      // Error callback
      (error) => {
        console.error('Modification error:', error);
        showErrorMessage(error);
      }
    );

    console.log('Modified chapter:', result.modifiedChapter);
    console.log('Word count:', result.wordCount);
    console.log('Changes summary:', result.changesSummary);
    
    // Handle the final result
    handleModifyChapterResult(result);
  } catch (error) {
    console.error('Failed to modify chapter:', error);
  }
}

/**
 * UI update functions (implement these based on your UI framework)
 */
function updateProgressUI(phase: string, message: string, progress: number) {
  // Update your progress bar and status message
  const progressBar = document.getElementById('progress-bar');
  const statusMessage = document.getElementById('status-message');
  
  if (progressBar) {
    progressBar.style.width = `${progress}%`;
  }
  
  if (statusMessage) {
    statusMessage.textContent = message;
  }
  
  // Add phase-specific styling or icons
  const phaseIcon = getPhaseIcon(phase);
  // Update UI with phase icon...
}

function getPhaseIcon(phase: string): string {
  switch (phase) {
    case 'context_processing': return '⚙️';
    case 'analyzing': return '🔍';
    case 'modifying': return '✏️';
    case 'finalizing': return '✅';
    default: return '📝';
  }
}

function showErrorMessage(error: string) {
  // Show error message to user
  console.error('Error:', error);
}

function handleModifyChapterResult(result: ModifyChapterResponse) {
  // Handle the final modified chapter result
  console.log('Chapter modification complete!', result);
}

export {
  modifyChapterWithUpdates,
  type ModifyChapterRequest,
  type ModifyChapterResponse,
  type StreamingMessage
};
