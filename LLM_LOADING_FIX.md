# LLM Loading Fix

## Problem

When the backend server starts, users would initially get errors when trying to use RAG features. After waiting several seconds, the features would start working. This was confusing and created a poor user experience.

## Root Cause

The LLM (Large Language Model) was being loaded **synchronously** during server startup in `backend/app/main.py`. Loading a large model can take 5-30 seconds depending on:
- Model size (2GB-8GB+ GGUF files)
- Hardware (CPU vs GPU, RAM speed)
- GPU layer offloading configuration

During this loading period:
1. FastAPI started accepting HTTP requests
2. But `get_llm()` returned `None` because loading wasn't complete
3. RAG endpoints would return 503 errors
4. Once loading finished, everything worked normally

## Solution

Changed LLM initialization to **asynchronous background loading**:

### Backend Changes

**`backend/app/main.py`:**
- Added `load_llm_async()` function that runs LLM initialization in a thread pool
- Used FastAPI's `lifespan` context manager to start loading in background
- Added global state tracking: `llm_loading` and `llm_load_error`
- Updated health endpoints to report loading status

**`backend/app/api/v1/endpoints/archive.py`:**
- Added `llm_loading` field to `RAGStatusResponse`
- Updated `/rag/status` endpoint to check and report loading state
- Better error messages that distinguish "loading" from "not configured"

### Frontend Changes

**`frontend/src/app/services/archive.service.ts`:**
- Added `llm_loading: boolean` to `RAGStatusResponse` interface

**`frontend/src/app/components/archive/archive.component.ts`:**
- Added polling: when `llm_loading` is true, re-check status every 2 seconds
- Added `isLlmLoading()` helper method
- Auto-detects when LLM finishes loading

**`frontend/src/app/components/story-workspace/story-workspace.component.ts`:**
- Enhanced error handling to detect "loading" errors
- Shows user-friendly message: "The AI model is still loading. Please wait a moment and try again."

## Benefits

1. **Server starts immediately** - no blocking on LLM load
2. **Clear status feedback** - users see "loading" instead of generic errors
3. **Automatic detection** - frontend polls and auto-enables when ready
4. **Better error messages** - distinguishes loading vs configuration issues
5. **Non-blocking** - other API endpoints work while LLM loads

## User Experience

### Before Fix:
```
User: [Clicks Research Archive]
Error: "RAG feature is not available. Please ensure both archive and LLM are configured."
User: "But it IS configured! 😡"
[Waits 30 seconds, tries again]
User: [Clicks Research Archive]
Success: Works now! ✅
User: "Why didn't it work before? 🤔"
```

### After Fix:
```
User: [Clicks Research Archive immediately after server start]
Error: "The AI model is still loading. Please wait a moment and try again."
User: "Oh, it's loading. I'll wait."
[Waits 30 seconds]
User: [Clicks Research Archive]
Success: Works! ✅
User: "That makes sense. 😊"
```

Or in Archive chat mode:
```
[Chat tab shows status badge]
Status: "⏳ LLM is currently loading. Please wait a moment and try again."
[Auto-refreshes every 2 seconds]
Status: "✅ RAG feature is fully enabled and ready to use."
```

## Technical Details

### Asynchronous Loading Flow

1. **Server Start** (0s):
   ```python
   # FastAPI lifespan starts
   asyncio.create_task(load_llm_async())  # Non-blocking!
   # Server immediately ready for requests
   ```

2. **During Load** (0-30s):
   ```python
   llm_loading = True
   # Background: Loading model into memory...
   # API requests get 503 with helpful message
   ```

3. **Load Complete** (30s):
   ```python
   llm_loading = False
   # get_llm() now returns the loaded instance
   # RAG features fully operational
   ```

### Thread Pool Execution

```python
# Run blocking LLM load in executor to avoid blocking async loop
loop = asyncio.get_event_loop()
await loop.run_in_executor(None, initialize_llm, config)
```

This ensures the async event loop remains responsive while the CPU-intensive model loading happens in a separate thread.

## Testing

To verify the fix works:

1. **Stop the backend server**
2. **Start the backend server**
3. **Immediately open the frontend**
4. **Try to use RAG features** (Archive chat or Research Archive)
5. **You should see**: "The AI model is still loading..."
6. **Wait 10-30 seconds**
7. **Try again** - should work now

## Configuration

No configuration changes needed. The fix works automatically with existing settings:
- `MODEL_PATH` - Path to GGUF model file
- `ARCHIVE_DB_PATH` - Path to ChromaDB archive database

## Error States

The system now clearly distinguishes three states:

| State | `llm_loading` | `llm_enabled` | Message |
|-------|--------------|---------------|---------|
| Not Configured | `false` | `false` | "LLM is not configured. Please set MODEL_PATH" |
| Loading | `true` | `false` | "LLM is currently loading. Please wait..." |
| Load Error | `false` | `false` | "Failed to load LLM: [error details]" |
| Ready | `false` | `true` | "RAG feature is fully enabled and ready" |

## Performance Impact

- **No performance degradation** - LLM loads in background
- **Faster server startup** - Server accepts requests immediately
- **Same LLM performance** - Once loaded, identical to before
- **Minimal polling overhead** - Frontend only polls during loading (2s intervals)

## Related Files

- `backend/app/main.py` - Async LLM loading
- `backend/app/api/v1/endpoints/archive.py` - Status endpoint updates
- `frontend/src/app/services/archive.service.ts` - Status interface
- `frontend/src/app/components/archive/archive.component.ts` - Status polling
- `frontend/src/app/components/story-workspace/story-workspace.component.ts` - Error handling
