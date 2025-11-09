# Writer Assistant

A multi-agent AI storytelling system that enables collaborative, user-driven narrative creation through specialized AI agents with sophisticated context management.

## Overview

Writer Assistant is a full-stack application that combines local LLM inference with a multi-agent architecture to help users create stories interactively. The system features multiple specialized AI agents (Writer, Editor, Character, Rater) that work together to generate, review, and refine narrative content based on user input and story context.

### Key Features

- **Multi-Agent System**: Specialized AI agents for different aspects of storytelling
  - Writer Agent: Generates narrative content
  - Editor Agent: Reviews and suggests improvements
  - Character Agent: Provides character-specific feedback
  - Rater Agent: Evaluates story quality and engagement

- **Sophisticated Context Management**
  - Structured context with typed collections
  - Priority-based token budgeting
  - Layered context allocation (System, Story, Characters, Plot)
  - Automatic summarization when approaching token limits

- **Local LLM Inference**
  - Run entirely offline with local GGUF models
  - GPU acceleration support via llama-cpp-python
  - Configurable model parameters per endpoint

- **Interactive Story Development**
  - Conversational worldbuilding interface
  - Plot outline management
  - Chapter-by-chapter generation and editing
  - Real-time feedback from multiple agent perspectives

- **Archive System** (Optional)
  - ChromaDB-based semantic search
  - Store and retrieve past story content
  - RAG-enhanced context retrieval

## Architecture

### Technology Stack

**Backend**
- FastAPI (Python 3.x)
- llama-cpp-python for local LLM inference
- LangChain/LangGraph for agent orchestration
- ChromaDB for vector storage (optional)
- Pydantic for data validation and settings

**Frontend**
- Angular 17 (TypeScript)
- Angular Material for UI components
- RxJS for reactive state management
- SCSS for styling
- Local storage for persistence

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Angular)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │   Workspace  │  │   Archive    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                  │
│                          │                                       │
│                  Context Builder                                 │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │ REST API / SSE
┌──────────────────────────┼───────────────────────────────────────┐
│                          │                                       │
│                   FastAPI Backend                                │
│  ┌───────────────────────┴────────────────────────┐             │
│  │           API Endpoints Layer                  │             │
│  │  (generation, chat, archive, tokens)           │             │
│  └───────────────────┬────────────────────────────┘             │
│                      │                                           │
│  ┌───────────────────┴────────────────────────────┐             │
│  │         Context Management Layer               │             │
│  │  • StructuredContextContainer                  │             │
│  │  • Token Budget Management                     │             │
│  │  • Priority-based Trimming                     │             │
│  │  • Context Distillation                        │             │
│  └───────────────────┬────────────────────────────┘             │
│                      │                                           │
│  ┌───────────────────┴────────────────────────────┐             │
│  │              Agent Layer                       │             │
│  │  Writer │ Editor │ Character │ Rater           │             │
│  └───────────────────┬────────────────────────────┘             │
│                      │                                           │
│  ┌───────────────────┴────────────────────────────┐             │
│  │          LLM Inference Service                 │             │
│  │         (llama-cpp-python)                     │             │
│  └────────────────────────────────────────────────┘             │
│                                                                  │
│  ┌────────────────────────────────────────────────┐             │
│  │        RAG Service (Optional)                  │             │
│  │          ChromaDB Vector Store                 │             │
│  └────────────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+ with pip
- Node.js 20+ with npm
- Git Bash (for Windows) or standard bash shell
- A GGUF format LLM model file

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd writer_assistant
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/Scripts/activate  # Windows Git Bash
   # source venv/bin/activate     # Linux/Mac
   pip install -r requirements.txt
   ```

3. **Configure the Backend**
   ```bash
   # Create .env file
   cp .env.example .env  # If .env.example exists

   # Or create .env manually with:
   echo "MODEL_PATH=/path/to/your/model.gguf" > .env
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

**Development Mode (Recommended)**

```bash
# From project root - starts both frontend and backend
./start-dev.sh
```

Access the application:
- Frontend: http://localhost:4200
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

**Manual Start**

Backend:
```bash
cd backend
source venv/Scripts/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm start
```

## Development

### Project Structure

```
writer_assistant/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration
│   │   ├── models/      # Pydantic models
│   │   ├── services/    # Business logic
│   │   └── main.py      # Application entry point
│   ├── tests/           # Backend tests
│   └── requirements.txt
├── frontend/            # Angular frontend
│   ├── src/
│   │   └── app/
│   │       ├── components/  # UI components
│   │       ├── services/    # Frontend services
│   │       ├── models/      # TypeScript models
│   │       └── app.routes.ts
│   ├── angular.json
│   └── package.json
├── docs/                # Additional documentation
├── scripts/             # Utility scripts
├── start-dev.sh         # Development startup script
├── build-and-test.sh    # CI/test script
└── CLAUDE.md            # AI assistant guidance
```

### Running Tests

**Backend**
```bash
cd backend
pytest tests/ -v
pytest tests/ -v --cov=app --cov-report=html  # With coverage
```

**Frontend**
```bash
cd frontend
npm test
npm test -- --watch=false --browsers=ChromeHeadless  # CI mode
```

**Full Test Suite**
```bash
./build-and-test.sh
```

### Code Quality

**Backend**
```bash
cd backend
black app/          # Format code
isort app/          # Sort imports
flake8 app/         # Lint
```

**Frontend**
```bash
cd frontend
npm run lint        # ESLint
ng lint             # Alternative
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)**: Guidance for AI assistants working with this codebase
- **[backend/README.md](backend/README.md)**: Backend architecture and structure
- **[backend/CONFIGURATION.md](backend/CONFIGURATION.md)**: Comprehensive configuration guide
- **[backend/STRUCTURED_CONTEXT_REFERENCE.md](backend/STRUCTURED_CONTEXT_REFERENCE.md)**: Context system reference
- **[frontend/README.md](frontend/README.md)**: Frontend architecture and structure

## Configuration

The backend uses environment variables for configuration. Key settings:

- `MODEL_PATH`: Path to GGUF model file (required)
- `LLM_N_CTX`: Context window size (default: 4096)
- `LLM_N_GPU_LAYERS`: GPU layers to use (-1 = all, 0 = CPU only)
- `CONTEXT_MAX_TOKENS`: Maximum context size (default: 32000)
- `ARCHIVE_DB_PATH`: ChromaDB path (optional, enables archive features)

See [backend/CONFIGURATION.md](backend/CONFIGURATION.md) for complete configuration documentation.

## Features in Detail

### Context Management

The system uses a sophisticated layered context management approach:

1. **Layer A**: System instructions (2k tokens)
2. **Layer B**: Immediate instructions (configurable)
3. **Layer C**: Recent story segments (13k tokens)
4. **Layer D**: Character and scene data (5k tokens)
5. **Layer E**: Plot and world summaries (10k tokens)

Context is automatically trimmed based on priority when token limits are approached.

### Multi-Agent Collaboration

Each agent has specialized capabilities:

- **Writer**: Creative content generation with high temperature
- **Editor**: Analytical review with lower temperature for consistency
- **Character**: In-character feedback from story personas
- **Rater**: Quality assessment and engagement scoring

Agents receive the same base context but format it differently based on their role.

### Archive System

The optional archive system uses ChromaDB for semantic search:
- Store completed chapters and story segments
- Semantic search for relevant past content
- RAG-enhanced context retrieval
- Improves consistency across long stories

## Troubleshooting

**Backend won't start or LLM not working**
- Check that `MODEL_PATH` environment variable points to a valid GGUF file
- Check `/health` endpoint: http://localhost:8000/health
- Look for errors in backend startup logs

**Frontend build errors**
- Ensure Node.js 20+ is installed: `node --version`
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check for TypeScript errors: `ng build`

**Token overflow errors**
- Reduce context layer allocations in backend configuration
- Lower `CONTEXT_MAX_TOKENS` or increase model's `LLM_N_CTX`

**Tests failing**
- Backend: Ensure virtual environment is activated
- Frontend: ChromeHeadless may need `--no-sandbox` flag on some systems

## Contributing

When contributing to this project:

1. Read [CLAUDE.md](CLAUDE.md) for architecture overview
2. Follow existing code style and patterns
3. Write tests for new features
4. Update documentation as needed
5. Run the test suite before submitting changes

## License

[Your License Here]

## Support

For issues, questions, or contributions, please refer to the project's issue tracker or documentation.
