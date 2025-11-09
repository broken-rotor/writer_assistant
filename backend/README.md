# Writer Assistant Backend

FastAPI-based backend for the Writer Assistant multi-agent storytelling system. Provides REST API endpoints for AI-powered story generation using local LLM inference.

## Overview

The backend is built on FastAPI and provides a stateless REST API for story generation, context management, and AI agent interactions. It uses llama-cpp-python for local LLM inference with GGUF models and optionally integrates ChromaDB for semantic search and archival.

### Key Capabilities

- **Local LLM Inference**: Run GGUF models locally with GPU acceleration
- **Multi-Agent System**: Writer, Editor, Character, and Rater agents with specialized prompts
- **Context Management**: Sophisticated token budgeting and priority-based context assembly
- **Streaming Support**: Server-sent events (SSE) for real-time generation feedback
- **Archive System**: Optional ChromaDB integration for semantic search
- **Async Architecture**: Non-blocking LLM loading and request processing

## Architecture

### Directory Structure

```
backend/
├── app/
│   ├── api/                    # API layer
│   │   └── v1/
│   │       ├── api.py         # Main router
│   │       └── endpoints/      # Endpoint implementations
│   │           ├── ai_generation.py          # Main generation orchestrator
│   │           ├── generate_chapter.py       # Chapter generation
│   │           ├── modify_chapter.py         # Chapter modification
│   │           ├── character_feedback.py     # Character agent
│   │           ├── editor_review.py          # Editor agent
│   │           ├── rater_feedback.py         # Rater agent
│   │           ├── flesh_out.py              # Content expansion
│   │           ├── generate_character_details.py
│   │           ├── generate_chapter_outlines.py
│   │           ├── regenerate_bio.py
│   │           ├── llm_chat.py               # General chat
│   │           ├── archive.py                # Archive operations
│   │           └── tokens.py                 # Token utilities
│   │
│   ├── core/                   # Core configuration
│   │   └── config.py          # Pydantic settings (all env vars)
│   │
│   ├── models/                 # Pydantic models
│   │   ├── generation_models.py    # StructuredContextContainer
│   │   ├── context_models.py       # Context processing models
│   │   ├── chapter_models.py       # Chapter-specific models
│   │   ├── chat_models.py          # Chat models
│   │   ├── streaming_models.py     # SSE models
│   │   └── token_models.py         # Token counting models
│   │
│   ├── services/               # Business logic layer
│   │   ├── llm_inference.py           # LLM loading and inference
│   │   ├── context_manager.py         # Context processing
│   │   ├── context_session_manager.py # Context state persistence
│   │   ├── unified_context_processor.py
│   │   ├── rag_service.py             # RAG/Archive service
│   │   ├── query_analyzer.py          # Query analysis
│   │   ├── plot_outline_extractor.py  # Plot extraction
│   │   │
│   │   ├── context_distillation/      # Summarization
│   │   │   ├── context_distiller.py
│   │   │   └── summarization_strategies.py
│   │   │
│   │   └── token_management/          # Token budgeting
│   │       ├── token_counter.py       # Token counting
│   │       ├── allocator.py           # Budget allocation
│   │       └── layers.py              # Layer definitions
│   │
│   ├── utils/                  # Utility functions
│   └── main.py                 # Application entry point
│
├── tests/                      # Test suite
│   ├── integration/            # Integration tests
│   ├── conftest.py            # Pytest configuration
│   └── test_*.py              # Unit tests
│
├── scripts/                    # Utility scripts
├── requirements.txt            # Python dependencies
├── pytest.ini                 # Pytest configuration
├── CONFIGURATION.md           # Configuration guide
└── STRUCTURED_CONTEXT_REFERENCE.md  # Context system docs
```

### Core Components

#### 1. LLM Inference Service (`services/llm_inference.py`)

Manages the local LLM instance:

```python
from app.services.llm_inference import get_llm

llm = get_llm()  # Singleton LLM instance
if llm:
    response = llm.invoke("Your prompt here")
```

**Features:**
- Asynchronous loading on app startup
- Singleton pattern for memory efficiency
- Configuration via `LLMInferenceConfig`
- GPU/CPU control with `LLM_N_GPU_LAYERS`
- Per-endpoint temperature and token overrides

#### 2. Context Management System

**StructuredContextContainer** (`models/generation_models.py`):
```python
class StructuredContextContainer(BaseModel):
    plot_elements: List[PlotElement]
    character_contexts: List[CharacterContext]
    user_requests: List[UserRequest]
    system_instructions: List[SystemInstruction]
    metadata: Dict[str, Any]
```

**ContextManager** (`services/context_manager.py`):
- Filters context by agent type and phase
- Applies priority-based sorting
- Manages token budget with layered allocation
- Formats context for specific agents
- Triggers summarization when needed

**Token Management** (`services/token_management/`):
- `TokenCounter`: Accurate token counting with multiple strategies
- `Allocator`: Distributes tokens across layers
- `LayerType`: Defines context layers (System, Story, Characters, Plot)

**Context Distillation** (`services/context_distillation/`):
- Automatic summarization when approaching token limits
- Content-type specific strategies
- Configurable temperature per distillation type

#### 3. API Endpoints

All endpoints are registered in `api/v1/api.py`:

```python
api_router.include_router(ai_generation.router, tags=["ai-generation"])
api_router.include_router(archive.router, prefix="/archive", tags=["archive"])
# ... etc
```

**Endpoint Pattern:**
```python
@router.post("/generate-chapter")
async def generate_chapter(request: ChapterGenerationRequest):
    # 1. Validate request
    # 2. Check LLM availability
    # 3. Build context
    # 4. Get endpoint-specific config
    # 5. Generate with LLM
    # 6. Return response
```

**Key Endpoints:**
- `POST /api/v1/generate-chapter`: Generate story chapter
- `POST /api/v1/modify-chapter`: Modify existing chapter
- `POST /api/v1/character-feedback`: Get character perspective
- `POST /api/v1/editor-review`: Get editorial review
- `POST /api/v1/rater-feedback`: Get quality rating
- `POST /api/v1/flesh-out`: Expand content
- `POST /api/v1/llm-chat`: General chat interface
- `POST /api/v1/archive/*`: Archive operations
- `POST /api/v1/tokens/count`: Count tokens

#### 4. Configuration System (`core/config.py`)

All configuration via Pydantic Settings:

```python
from app.core.config import settings

model_path = settings.MODEL_PATH
temperature = settings.LLM_TEMPERATURE
max_tokens = settings.ENDPOINT_GENERATE_CHAPTER_MAX_TOKENS
```

**Configuration Sources** (in order of precedence):
1. Environment variables
2. `.env` file in backend/ directory
3. Default values in `config.py`

See [CONFIGURATION.md](CONFIGURATION.md) for complete documentation.

#### 5. Archive/RAG Service (`services/rag_service.py`)

Optional ChromaDB integration:

```python
from app.services.rag_service import ArchiveService

service = ArchiveService()  # Uses settings.ARCHIVE_DB_PATH
await service.store_content(content_id, text, metadata)
results = await service.search(query, n_results=5)
```

**Features:**
- Semantic search with embeddings
- Metadata filtering
- Automatic chunking for large content
- Optional: disabled if `ARCHIVE_DB_PATH` not set

### Request Flow

1. **Client Request** → FastAPI endpoint
2. **Validation** → Pydantic models validate request
3. **LLM Check** → Verify LLM is loaded and available
4. **Context Building** → Assemble StructuredContextContainer
5. **Context Processing** → ContextManager applies filters, priorities, token budget
6. **Agent Selection** → Select prompt template and parameters for agent type
7. **LLM Inference** → Generate response with llama-cpp-python
8. **Response** → Return formatted response to client

### Context Processing Pipeline

```
StructuredContextContainer (from frontend)
    ↓
ContextManager.process_context_for_agent()
    ↓
1. Filter by agent type and phase
2. Apply custom filters
3. Sort by priority
4. Calculate token usage
5. Trim if over budget
6. Format for agent
    ↓
Formatted string context → LLM
```

### Multi-Agent System

Each agent has specific characteristics:

| Agent | Temperature | Max Tokens | Purpose |
|-------|-------------|------------|---------|
| Writer | 0.8 | 2000 | Creative narrative generation |
| Editor | 0.6 | 800 | Analytical review and critique |
| Character | 0.8 | 800 | In-character feedback |
| Rater | 0.7 | 600 | Quality and engagement scoring |

Configuration via `ENDPOINT_*_TEMPERATURE` and `ENDPOINT_*_MAX_TOKENS` settings.

## Development Setup

### Prerequisites

- Python 3.10+
- A GGUF format LLM model
- (Optional) CUDA-capable GPU for acceleration

### Installation

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows Git Bash)
source venv/Scripts/activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the `backend/` directory:

```bash
# Required
MODEL_PATH=/path/to/your/model.gguf

# Optional (with defaults shown)
LLM_N_CTX=4096
LLM_N_GPU_LAYERS=-1  # -1 = all layers on GPU, 0 = CPU only
LLM_TEMPERATURE=0.7
CONTEXT_MAX_TOKENS=32000

# Optional: Enable archive
ARCHIVE_DB_PATH=./story_archive
```

See [CONFIGURATION.md](CONFIGURATION.md) for all available options.

### Running

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the Python module syntax
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_api_endpoints.py -v

# Run specific test
pytest tests/test_api_endpoints.py::test_function_name -v

# Run integration tests only
pytest tests/integration/ -v
```

Coverage report: `htmlcov/index.html`

### Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/
```

## API Usage Examples

### Generate Chapter

```bash
curl -X POST http://localhost:8000/api/v1/generate-chapter \
  -H "Content-Type: application/json" \
  -d '{
    "structured_context": {
      "plot_elements": [
        {"type": "scene", "content": "Hero enters forest", "priority": "high"}
      ],
      "character_contexts": [
        {"character_id": "hero", "character_name": "Aria", "current_state": "determined"}
      ],
      "user_requests": [
        {"type": "instruction", "content": "Add sensory details", "priority": "high"}
      ]
    }
  }'
```

### Count Tokens

```bash
curl -X POST http://localhost:8000/api/v1/tokens/count \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here"}'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Key Concepts

### Structured Context

The system uses typed context containers instead of generic dictionaries:

- **plot_elements**: Story and plot information
- **character_contexts**: Character state and goals
- **user_requests**: User instructions and feedback
- **system_instructions**: System-level guidelines

Each element has:
- Type-specific fields
- Priority ("high", "medium", "low")
- Optional tags and metadata

See [STRUCTURED_CONTEXT_REFERENCE.md](STRUCTURED_CONTEXT_REFERENCE.md) for complete documentation.

### Token Budget Management

Context is allocated across layers:

1. **Layer A** (System): Core system instructions (~2k tokens)
2. **Layer C** (Story): Recent story content (~13k tokens)
3. **Layer D** (Characters): Character and scene data (~5k tokens)
4. **Layer E** (Plot): Plot summaries and worldbuilding (~10k tokens)

Total must not exceed `CONTEXT_MAX_TOKENS - CONTEXT_BUFFER_TOKENS`.

### Priority System

Content is prioritized as:
- **high**: Must be included, kept during trimming
- **medium**: Important but can be reduced if needed
- **low**: First to be trimmed when over budget

### Context Distillation

When context approaches token limits:
1. System identifies verbose sections
2. Applies content-type specific summarization
3. Maintains key information while reducing tokens
4. Configurable temperature per content type

## Performance Tuning

### GPU Acceleration

```bash
# Use all GPU layers
LLM_N_GPU_LAYERS=-1

# Use specific number of layers
LLM_N_GPU_LAYERS=35

# CPU only (slower but works without GPU)
LLM_N_GPU_LAYERS=0
```

### Context Size

```bash
# Larger context for longer stories (requires more VRAM)
LLM_N_CTX=8192
CONTEXT_MAX_TOKENS=64000

# Smaller context for lower resource usage
LLM_N_CTX=2048
CONTEXT_MAX_TOKENS=16000
```

### Generation Speed

- Lower `LLM_MAX_TOKENS` for faster responses
- Increase `LLM_N_THREADS` for CPU inference
- Reduce `CONTEXT_MAX_TOKENS` to process less context

## Troubleshooting

### LLM Not Loading

Check:
1. `MODEL_PATH` points to valid GGUF file
2. File permissions allow reading
3. Sufficient RAM/VRAM for model
4. Check `/health` endpoint for error details

### Out of Memory

Reduce:
- `LLM_N_CTX` (context window)
- `LLM_N_GPU_LAYERS` (use fewer GPU layers)
- `CONTEXT_MAX_TOKENS` (process less context)

### Slow Performance

Increase:
- `LLM_N_GPU_LAYERS` (offload more to GPU)
- `LLM_N_THREADS` (for CPU inference)

Check:
- GPU utilization during inference
- CPU usage patterns
- Model size vs available VRAM

### Token Overflow Errors

Reduce layer allocations:
```bash
CONTEXT_LAYER_C_TOKENS=10000  # Reduce recent story
CONTEXT_LAYER_E_TOKENS=7000   # Reduce plot summaries
```

Or increase limits:
```bash
CONTEXT_MAX_TOKENS=40000
LLM_N_CTX=8192  # Must be >= max tokens used
```

## Additional Documentation

- **[CONFIGURATION.md](CONFIGURATION.md)**: Complete configuration reference with all environment variables
- **[STRUCTURED_CONTEXT_REFERENCE.md](STRUCTURED_CONTEXT_REFERENCE.md)**: Context system API and usage patterns
- **[../CLAUDE.md](../CLAUDE.md)**: High-level architecture and development guidance

## Contributing

When working on the backend:

1. Follow existing patterns for endpoints and services
2. Use Pydantic models for all data validation
3. Add type hints to all functions
4. Write tests for new functionality
5. Update configuration documentation if adding new settings
6. Use the `TokenCounter` service for token counting
7. Respect the layered architecture (API → Services → Models)
