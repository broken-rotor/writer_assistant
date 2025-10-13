# RAG Feature - Retrieval-Augmented Generation for Story Archive

## Overview

The RAG (Retrieval-Augmented Generation) feature enhances the Story Archive with AI-powered question answering. Instead of just searching for relevant text chunks, you can now ask natural language questions and receive AI-generated answers based on the retrieved content from your archived stories.

## What is RAG?

RAG combines two powerful techniques:

1. **Retrieval**: Uses semantic search (vector embeddings) to find the most relevant sections from your story archive
2. **Generation**: Uses a Large Language Model (LLM) to generate coherent, context-aware answers based on the retrieved content

This approach provides more accurate and contextual answers than using an LLM alone, because the model is grounded in your actual story content.

## Features

### Two Modes

The Archive component now has two modes accessible via tabs:

1. **Search Mode** (🔍): Traditional semantic search - returns matching text chunks
2. **Chat Mode** (💬): RAG-powered Q&A - ask questions and get AI-generated answers

### Chat Capabilities

- **Natural Language Questions**: Ask questions in plain English
- **Context-Aware Answers**: The AI uses relevant story excerpts to generate accurate responses
- **Multi-Turn Conversations**: Continue asking follow-up questions that reference previous exchanges
- **Source Transparency**: See exactly which story sections were used to generate each answer
- **Conversation History**: Full chat history is maintained during your session

### Example Questions

- "What themes appear most frequently in my stories?"
- "Tell me about the character development in [story name]"
- "What are the main conflicts in my fantasy stories?"
- "Summarize the plot of [story name]"
- "How do my protagonists typically resolve their conflicts?"
- "What writing style do I use most often?"

## Requirements

For the RAG feature to work, you need **both** of the following configured:

### 1. Archive Database (ChromaDB)

```bash
# In backend/.env
ARCHIVE_DB_PATH=./chroma_db
ARCHIVE_COLLECTION_NAME=story_archive
```

See [ARCHIVE_SETUP.md](ARCHIVE_SETUP.md) for full setup instructions.

### 2. Local LLM (Language Model)

```bash
# In backend/.env
MODEL_PATH=/path/to/your/model.gguf

# Optional LLM settings
LLM_N_CTX=4096                    # Context window size
LLM_N_GPU_LAYERS=-1               # GPU layers (-1 = all, 0 = CPU only)
LLM_TEMPERATURE=0.7               # Sampling temperature
LLM_MAX_TOKENS=2048               # Maximum tokens to generate
```

The system uses **llama.cpp** via the `llama-cpp-python` library. You'll need a GGUF format model file.

#### Recommended Models

For story analysis and Q&A:
- **Llama 3.2 3B** (small, fast, good for basic Q&A)
- **Mistral 7B Instruct** (balanced performance and accuracy)
- **Llama 3.1 8B** (better reasoning, more context-aware)

Download models from:
- [Hugging Face](https://huggingface.co/models?sort=trending&search=gguf)
- Look for models with "Instruct" or "Chat" in the name

## Installation

### 1. Install Python Dependencies

```bash
cd backend
pip install llama-cpp-python
```

For GPU acceleration (recommended):
```bash
# CUDA (NVIDIA)
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python

# Metal (Apple Silicon)
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python
```

### 2. Download a Model

```bash
# Example: Download Mistral 7B Instruct
mkdir -p models
cd models
wget https://huggingface.co/.../mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

### 3. Configure Environment

```bash
# backend/.env
ARCHIVE_DB_PATH=./chroma_db
MODEL_PATH=./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

### 4. Restart Backend

```bash
cd backend
uvicorn app.main:app --reload
```

## Usage

### In the Frontend

1. Navigate to the **Archive** tab
2. Check the stats bar - if both archive and LLM are configured, you'll see the "Chat (RAG)" button enabled
3. Click **💬 Chat (RAG)** to switch to chat mode
4. Ask your questions in the text input at the bottom
5. Press **Enter** or click **Send**
6. View the AI-generated answer along with the source sections used

### API Usage

The RAG feature exposes three new endpoints:

#### Check RAG Status

```bash
GET /api/v1/archive/rag/status
```

Response:
```json
{
  "archive_enabled": true,
  "llm_enabled": true,
  "rag_enabled": true,
  "message": "RAG feature is fully enabled and ready to use."
}
```

#### Single-Turn Query

```bash
POST /api/v1/archive/rag/query
Content-Type: application/json

{
  "question": "What themes appear in my stories?",
  "n_context_chunks": 5,
  "max_tokens": 1024,
  "temperature": 0.3,
  "filter_file_name": "optional_file_filter.txt"
}
```

Response:
```json
{
  "query": "What themes appear in my stories?",
  "answer": "Based on your stories, several recurring themes emerge...",
  "sources": [
    {
      "file_path": "/path/to/story.txt",
      "file_name": "story.txt",
      "matching_section": "Relevant text excerpt...",
      "similarity_score": 0.87
    }
  ],
  "total_sources": 5
}
```

#### Multi-Turn Chat

```bash
POST /api/v1/archive/rag/chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "Tell me about character development in my stories"},
    {"role": "assistant", "content": "Your stories show strong character arcs..."},
    {"role": "user", "content": "Which story has the best character arc?"}
  ],
  "n_context_chunks": 5,
  "max_tokens": 1024,
  "temperature": 0.4
}
```

## Architecture

### Backend Components

1. **`rag_service.py`**: Core RAG logic
   - Combines vector search with LLM generation
   - Manages context building and prompt engineering
   - Supports both single-turn and multi-turn conversations

2. **`archive.py` (endpoints)**: New API endpoints
   - `/rag/status` - Check feature availability
   - `/rag/query` - Single-turn question answering
   - `/rag/chat` - Multi-turn conversations

3. **`llm_inference.py`**: LLM interface (existing)
   - Wraps llama.cpp functionality
   - Handles model loading and text generation

4. **`archive_service.py`**: Vector search (existing)
   - ChromaDB integration
   - Semantic search over story chunks

### Frontend Components

1. **`archive.service.ts`**: New methods
   - `getRagStatus()` - Check RAG availability
   - `ragQuery()` - Single-turn queries
   - `ragChat()` - Multi-turn chat

2. **`archive.component.ts`**: Enhanced UI
   - Mode switcher (Search/Chat)
   - Chat message display
   - Source transparency

3. **`archive.component.html`**: New sections
   - Mode switcher buttons
   - Chat interface with message history
   - Source display panel

## How It Works

### Query Flow

1. **User asks a question**: "What themes appear in my stories?"

2. **Retrieval Phase**:
   - Question is embedded using the same model as story ingestion (all-mpnet-base-v2)
   - ChromaDB performs semantic search to find the most relevant story chunks
   - Top N chunks are retrieved (default: 5)

3. **Context Building**:
   - Retrieved chunks are formatted into a context string
   - Each chunk is labeled with its source file

4. **Generation Phase**:
   - A prompt is constructed with:
     - System instructions (answer based on context)
     - Retrieved context
     - User's question
   - LLM generates an answer based solely on the provided context

5. **Response**:
   - Answer is returned to the user
   - Source chunks are displayed for transparency
   - Chat history is maintained for follow-up questions

### Context Management

For multi-turn conversations:
- Previous questions and answers are included in the prompt
- Only the **latest** user question is used for retrieval
- This allows follow-up questions while keeping context relevant

### Prompt Engineering

The system uses carefully crafted prompts to ensure:
- **Grounding**: Answers are based on provided context, not general knowledge
- **Transparency**: The AI acknowledges when context is insufficient
- **Relevance**: Answers stay focused on the user's stories

## Configuration Options

### Backend Settings

All settings can be configured via environment variables:

```bash
# Archive
ARCHIVE_DB_PATH=./chroma_db
ARCHIVE_COLLECTION_NAME=story_archive

# Model
MODEL_PATH=./models/your-model.gguf

# Performance
LLM_N_CTX=4096                    # Larger = more context, more memory
LLM_N_GPU_LAYERS=-1               # -1 = all layers on GPU
LLM_N_THREADS=8                   # CPU threads (if not using GPU)

# Generation Quality
LLM_TEMPERATURE=0.3               # Lower = more focused, 0.7-0.9 = more creative
LLM_TOP_P=0.95                    # Nucleus sampling
LLM_TOP_K=40                      # Top-k sampling
LLM_MAX_TOKENS=2048               # Maximum answer length
LLM_REPEAT_PENALTY=1.1            # Reduce repetition
LLM_VERBOSE=false                 # Debug logging
```

### Frontend Settings

In the UI, you can adjust:
- **Number of context chunks**: More chunks = more context but slower (1-20)
- **Max tokens**: Longer answers (50-4096)
- **Temperature**: Lower = more factual, higher = more creative (0.0-1.0)

## Performance Tips

### Speed Optimization

1. **Use GPU acceleration**: Configure `CMAKE_ARGS` during installation
2. **Choose appropriate model size**: 3B-7B models are fast and accurate for most use cases
3. **Reduce context chunks**: Fewer chunks = faster retrieval and generation
4. **Use quantized models**: Q4_K_M or Q5_K_M provide good speed/quality balance

### Quality Optimization

1. **Use larger models**: 7B-13B models provide better reasoning
2. **Increase context chunks**: More context = more informed answers
3. **Lower temperature**: More factual, grounded responses (0.2-0.3)
4. **Use Instruct-tuned models**: Better at following instructions

## Troubleshooting

### "RAG feature is not available"

Check both requirements:
```bash
# Check archive status
curl http://localhost:8000/api/v1/archive/stats

# Check RAG status
curl http://localhost:8000/api/v1/archive/rag/status
```

### Slow Responses

- Use GPU acceleration (if available)
- Try a smaller model (3B instead of 7B)
- Reduce `n_context_chunks` (default: 5)
- Reduce `LLM_MAX_TOKENS`

### Out of Memory Errors

- Reduce `LLM_N_CTX` (try 2048 instead of 4096)
- Reduce `LLM_N_GPU_LAYERS` (or set to 0 for CPU-only)
- Use a more quantized model (Q4_0 instead of Q4_K_M)
- Close other applications

### Answers Not Relevant

- Ensure your stories are properly indexed (see ARCHIVE_SETUP.md)
- Try increasing `n_context_chunks` (up to 10-15)
- Lower temperature (0.2-0.3) for more grounded answers
- Check that relevant stories are in the archive

## Limitations

- **No Internet Access**: The LLM cannot access external information, only your archived stories
- **Context Window**: Limited by model's context size (typically 4096-8192 tokens)
- **Local Processing**: Slower than cloud APIs but fully private
- **Model Knowledge**: The LLM's base knowledge is from its training, but answers should be grounded in your stories

## Privacy & Security

- **Fully Local**: All processing happens on your machine
- **No External APIs**: Your stories never leave your computer
- **No Telemetry**: ChromaDB telemetry is disabled by default
- **Transparent Sources**: Always shows which story sections were used

## Future Enhancements

Potential improvements for future versions:

- [ ] Streaming responses (real-time token generation)
- [ ] Citation/quote formatting in answers
- [ ] Export chat conversations
- [ ] Conversation branching/history management
- [ ] Custom prompt templates
- [ ] Multiple model support/switching
- [ ] Fine-tuning on your writing style
- [ ] Story comparison queries
- [ ] Writing style analysis

## API Reference

See the auto-generated API documentation at:
```
http://localhost:8000/docs
```

Look for the `/archive/rag/*` endpoints.

## Support

For issues or questions:
1. Check this documentation
2. Review [ARCHIVE_SETUP.md](ARCHIVE_SETUP.md) for archive configuration
3. Check backend logs for error messages
4. Verify both archive and LLM are properly configured

## License

This feature is part of the Writer Assistant project and follows the same license.
