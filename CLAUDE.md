# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Writer Assistant is a multi-agent AI storytelling system built with:
- **Backend**: FastAPI + Python with local LLM inference (llama-cpp-python)
- **Frontend**: Angular 17 + TypeScript + Angular Material
- **Architecture**: Multi-agent system using LangChain/LangGraph for collaborative story generation

The system enables user-driven narrative creation through specialized AI agents (Writer, Editor, Character, Rater) with sophisticated context management and token budgeting.

## Development Commands

### Quick Start (Development Mode)

```bash
# Start both frontend and backend servers
./start-dev.sh
# Frontend: http://localhost:4200
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Backend Commands

```bash
cd backend

# Setup (Windows Git Bash)
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt

# Run server
./venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_api_endpoints.py -v

# Run specific test
pytest tests/test_api_endpoints.py::test_specific_function -v

# Code formatting
black app/
isort app/
flake8 app/
```

### Frontend Commands

```bash
cd frontend

# Setup
npm install

# Development server
npm start
# or
ng serve

# Build
npm run build
# or
ng build

# Run tests
npm test
# or
ng test

# Run tests (headless)
npm test -- --watch=false --browsers=ChromeHeadless

# Run tests with coverage
npm test -- --watch=false --code-coverage --browsers=ChromeHeadless

# Lint
npm run lint
# or
ng lint

# Run specific test file
ng test --include='**/context-builder.service.spec.ts'
```

### Full Build and Test

```bash
# Run comprehensive build and test suite for both frontend and backend
./build-and-test.sh
```

## Backend Architecture

### Core Components

1. **LLM Inference Service** (`app/services/llm_inference.py`)
   - Manages local LLM using llama-cpp-python
   - Loads GGUF models asynchronously on startup
   - Provides singleton LLM instance via `get_llm()`
   - Configuration via environment variables (MODEL_PATH, LLM_N_CTX, etc.)

2. **Context Management System** (`app/services/context_manager.py`)
   - **StructuredContextContainer** (`app/models/generation_models.py`): Main context model with typed collections:
     - `plot_elements`: Story/plot information
     - `character_contexts`: Character state and goals
     - `user_requests`: User instructions and feedback
     - `system_instructions`: System-level guidelines
   - **Token Budget Management** (`app/services/token_management/`):
     - Layered token allocation (System, Recent Story, Characters, Plot Summary, etc.)
     - Priority-based trimming ("high", "medium", "low")
     - Configurable via `CONTEXT_LAYER_*_TOKENS` settings
   - **Context Distillation** (`app/services/context_distillation/`): Summarizes content when approaching token limits

3. **RAG Service** (`app/services/rag_service.py`)
   - Optional ChromaDB integration for semantic search
   - Archive previous story content for retrieval
   - Enabled when `ARCHIVE_DB_PATH` is set

4. **API Endpoints** (`app/api/v1/endpoints/`)
   - **ai_generation.py**: Main generation orchestrator
   - **generate_chapter.py**: Chapter generation
   - **modify_chapter.py**: Chapter modification
   - **character_feedback.py**: Character agent feedback
   - **editor_review.py**: Editor agent review
   - **rater_feedback.py**: Rater agent feedback
   - **flesh_out.py**: Content expansion
   - **generate_character_details.py**: Character detail generation
   - **llm_chat.py**: General chat interface
   - **archive.py**: Archive storage and retrieval
   - **tokens.py**: Token counting utilities

### Configuration System

All configuration is managed through `app/core/config.py` using Pydantic Settings. Configuration is loaded from:
1. Default values in code
2. `.env` file in `backend/` directory
3. Environment variables

**Critical Settings:**
- `MODEL_PATH`: Path to GGUF model file (required for LLM functionality)
- `LLM_N_CTX`: Context window size (default: 4096)
- `LLM_N_GPU_LAYERS`: GPU layers (-1 = all, 0 = CPU only)
- `CONTEXT_MAX_TOKENS`: Maximum context size (default: 32000)
- `CONTEXT_LAYER_*_TOKENS`: Token allocations per layer
- `ENDPOINT_*_TEMPERATURE`: Per-endpoint temperature settings
- `ARCHIVE_DB_PATH`: ChromaDB path (optional, disables archive if None)

See `backend/README.md` for comprehensive configuration documentation.

### Key Architectural Patterns

1. **Structured Context Container Pattern**
   - Frontend builds typed context objects
   - Backend processes with priority-based token management
   - Agent-specific filtering and formatting
   - See `backend/STRUCTURED_CONTEXT_REFERENCE.md` for details

2. **Multi-Agent System**
   - Each agent (Writer, Editor, Character, Rater) has specific prompts and parameters
   - Agents share context but format it differently based on role
   - Temperature and token limits vary by agent type

3. **Token Budget Enforcement**
   - Layered allocation: System Instructions → Recent Story → Characters → Plot Summary
   - Priority-based trimming when over budget
   - Automatic summarization when exceeding thresholds

4. **Async LLM Loading**
   - LLM loads in background on startup (lifespan event)
   - Endpoints check LLM availability before processing
   - `/health` endpoint shows LLM loading state

## Frontend Architecture

### Core Structure

1. **Main Components** (`src/app/components/`)
   - **dashboard**: Story list and creation
   - **story-workspace**: Main story editing interface
   - **chat-interface**: Conversational story development
   - **worldbuilding-tab**: World-building management
   - **plot-outline-tab**: Plot outline editor
   - **archive**: Archive browsing and search
   - **feedback-sidebar**: Agent feedback display
   - **review-feedback-panel**: Editorial review display

2. **Services** (`src/app/services/`)
   - **context-builder.service.ts**: Builds structured context from Story model
   - **context-manager.service.ts**: Manages context state and caching
   - **story.service.ts**: Story CRUD operations
   - **generation.service.ts**: AI generation requests
   - **token-counting.service.ts**: Client-side token estimation
   - **api.service.ts**: Base HTTP client for backend API
   - **streaming.service.ts**: Server-sent events for streaming responses
   - **archive.service.ts**: Archive storage/retrieval
   - **local-storage.service.ts**: Browser storage management

3. **State Management**
   - **Local Storage**: Story data persisted in browser
   - **Context Storage Service**: Manages context snapshots
   - **Context Versioning Service**: Tracks context history
   - No external state library (uses services + RxJS)

4. **Models** (`src/app/models/`)
   - **story.model.ts**: Core Story interface (chapters, characters, worldbuilding, etc.)
   - **context-builder.model.ts**: Context structure definitions
   - **generation-request.model.ts**: API request/response models
   - **archive.model.ts**: Archive-related models

### Routing

- `/` or `/dashboard`: Story list and management
- `/story/:id`: Story workspace editor
- `/archive`: Archive browsing

### Key Frontend Patterns

1. **Context Building Flow**
   - StoryWorkspace collects user input
   - ContextBuilderService transforms Story → StructuredContext
   - GenerationService sends to backend API
   - Response updates Story model
   - LocalStorageService persists changes

2. **Token Management**
   - Client-side token estimation (approximate)
   - Token limits service validates before API calls
   - Backend performs authoritative token counting

3. **Streaming Support**
   - SSE-based streaming for chapter generation
   - Progressive UI updates during generation
   - Fallback to regular HTTP if streaming unavailable

## Important Development Notes

### Backend

1. **LLM Initialization**
   - Model path MUST be set via `MODEL_PATH` environment variable
   - Server starts immediately but LLM loads asynchronously
   - Check `/health` endpoint for LLM status before testing generation
   - No MODEL_PATH = LLM features disabled (server still runs)

2. **Context System Migration**
   - New structured context model in `app/models/generation_models.py`
   - Typed collections replace generic element lists
   - Use string priorities ("high", "medium", "low") not numeric
   - See `STRUCTURED_CONTEXT_MIGRATION_GUIDE.md` if updating old code

3. **Token Counting**
   - Use `TokenCounter` service for accurate counts
   - Different strategies available (exact, approximate, cached)
   - Layer allocation MUST NOT exceed `CONTEXT_MAX_TOKENS - CONTEXT_BUFFER_TOKENS`

4. **Testing**
   - Tests use pytest with async support (pytest-asyncio)
   - Integration tests in `tests/integration/`
   - Unit tests in `tests/` root
   - Coverage reports in `htmlcov/index.html`

### Frontend

1. **Angular 17 Patterns**
   - Uses standalone components (no NgModule)
   - Signals not widely adopted yet (mostly RxJS)
   - SCSS for styling with Angular Material theme

2. **Story Model**
   - Complex nested structure (chapters, characters, worldbuilding, feedback, etc.)
   - Stored entirely in browser localStorage
   - No backend persistence (stateless backend)

3. **Token Estimation**
   - Frontend uses approximate token counting
   - Backend uses llama-cpp tokenizer (authoritative)
   - Always validate with backend before assuming token counts

4. **Testing**
   - Karma + Jasmine test framework
   - ChromeHeadless for CI/headless testing
   - Coverage reports in `coverage/` directory

## Windows (Git Bash) Specifics

This project is developed on Windows using Git Bash (MINGW64):
- Use `source venv/Scripts/activate` (not `venv/bin/activate`)
- Python executable: `./venv/Scripts/python.exe`
- Scripts use Windows-aware path handling
- `start-dev.sh` and `build-and-test.sh` detect Windows environment

## Common Gotchas

1. **Backend won't generate**: Check MODEL_PATH is set and model file exists
2. **Token overflow errors**: Reduce context layer allocations in settings
3. **Tests fail intermittently**: ChromeHeadless may need `--no-sandbox` flag
4. **Frontend build fails**: Check Node.js version (needs 20+) and run `npm install`
5. **CORS errors**: Backend allows `http://localhost:4200` only; check ports match
