# Writer Assistant

A multi-agent AI system for collaborative storytelling that uses specialized AI agents to create cohesive, well-crafted stories through a two-phase development process.

## Project Overview

Writer Assistant employs a sophisticated multi-agent architecture where specialized AI agents collaborate to help users create compelling stories:

- **Writer Agent**: Main orchestrator that synthesizes inputs and generates content
- **Character Sub-Agents**: Maintain individual character perspectives and memories
- **Rater Agents**: Multiple critics providing feedback from different perspectives
- **Editor Agent**: Final reviewer ensuring consistency, tone, and coherence

## Technology Stack

- **Backend**: Python + FastAPI + LangChain + LangGraph
- **Frontend**: Angular 17+ with Material Design
- **LLM Integration**: llama.cpp (local LLM)
- **Storage**: JSON files (MVP) → PostgreSQL (future)
- **Development**: Docker containerized environment

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local Angular development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd writer_assistant
   ```

2. **Start with Docker (Recommended)**
   ```bash
   # Start all services
   docker-compose up -d

   # Backend will be available at http://localhost:8000
   # Frontend will be available at http://localhost:4200
   # API docs at http://localhost:8000/docs
   ```

3. **Or run services individually**

   **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   uvicorn app.main:app --reload
   ```

   **Frontend:**
   ```bash
   cd frontend/writer-assistant-ui
   npm install
   ng serve
   ```

### API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Testing and Building

### Automated Test and Build Scripts

The project includes cross-platform scripts for testing and building:

**Quick Start:**
```bash
# Windows PowerShell (Recommended)
.\test-and-build.ps1

# Windows Command Prompt
test-and-build.bat

# Git Bash / WSL / Linux / Mac
./test-and-build.sh

# Quick development tests (fast feedback)
./quick-test.sh
```

**What gets tested:**
- ✅ Backend: Python unit tests with pytest + coverage
- ✅ Frontend: ESLint linting + Karma/Jasmine tests
- ✅ Frontend: Production build compilation

**Output locations:**
- Backend coverage: `backend/htmlcov/index.html`
- Frontend build: `frontend/dist/`
- Logs: `frontend/frontend-*.log`

For detailed documentation, see `TEST_BUILD_README.md` and `SCRIPTS_SUMMARY.md`.

## Development Workflow

### Two-Phase Story Development

1. **Phase 1: Outline Development**
   - User provides story concept and guidance
   - Writer Agent creates basic story outline
   - Rater Agents provide feedback on structure and viability
   - Iterative refinement until approval

2. **Phase 2: Chapter Development**
   - Writer Agent fleshes out chapters with detailed content
   - Character Agents contribute individual perspectives
   - Rater Agents review for authenticity and quality
   - Editor Agent performs final consistency check

### Agent Architecture

- **Memory Management**: Each agent maintains subjective experiences and perspectives
- **Workflow Coordination**: LangGraph orchestrates complex multi-agent interactions
- **Dynamic Routing**: Agents activated based on story needs and context
- **Error Recovery**: Graceful handling of agent failures and system interruptions

## Project Structure

```
writer_assistant/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Configuration and utilities
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic
│   │   ├── agents/         # AI agent implementations
│   │   └── storage/        # Data persistence layer
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Angular frontend
│   └── writer-assistant-ui/
│       ├── src/
│       │   ├── app/
│       │   │   ├── components/
│       │   │   ├── services/
│       │   │   └── models/
│       │   └── assets/
│       └── Dockerfile
├── requirements/           # Detailed project requirements
├── docker-compose.yml      # Development environment
└── README.md
```

## Current Implementation Status

### ✅ Completed (Phase 1: Foundation)
- [x] Backend project structure with FastAPI
- [x] Frontend project structure with Angular
- [x] Docker development environment
- [x] Basic API endpoints for story management
- [x] JSON-based storage system
- [x] Core data models (Story, Character, Chapter, Outline)
- [x] Basic routing and navigation

### 🚧 In Progress (Phase 2: MVP Core)
- [ ] Basic agent system implementation
- [ ] Simple UI components (Dashboard, Story Creation, Workspace)
- [ ] LangChain + LangGraph integration
- [ ] Mock LLM integration for development

### 📋 Planned (Phase 3: Enhanced Features)
- [ ] Multi-agent coordination
- [ ] Character management interface
- [ ] Real-time agent status updates
- [ ] Advanced feedback system
- [ ] Local LLM integration (llama.cpp)

## Key Features

- **Individual Agent Memory**: Each agent maintains subjective experiences
- **Memory Subjectivity**: Conflicting character memories are intentional
- **Configurable Personalities**: JSON-based agent configuration
- **Story Persistence**: Save/export stories and memory states
- **Multi-Perspective Feedback**: Evaluation from different critic perspectives

## Contributing

1. Follow the existing code structure and patterns
2. Write tests for new functionality
3. Update documentation for significant changes
4. Use the provided Docker environment for consistency

## API Endpoints

### Stories
- `POST /api/v1/stories/` - Create new story
- `GET /api/v1/stories/` - List all stories
- `GET /api/v1/stories/{id}` - Get specific story
- `PUT /api/v1/stories/{id}` - Update story
- `DELETE /api/v1/stories/{id}` - Delete story

### Future Endpoints (Planned)
- Character management
- Chapter operations
- Agent interactions
- Workflow management

## Configuration

### Backend Configuration (.env)
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATA_DIR=data
MAX_CONTEXT_LENGTH=4000
DEFAULT_TEMPERATURE=0.7
```

### Frontend Configuration
Angular environment files handle API endpoints and feature flags.

## Performance Requirements

- Response time: < 30 seconds for chapter generation
- Memory efficiency: < 4KB context per agent per chapter
- Consistency scores: > 85% character consistency across story
- User satisfaction target: > 4.0/5.0 rating on generated content

## License

[License information to be added]

## Support

For questions or issues, please refer to:
- Project documentation in `requirements/` directory
- API documentation at http://localhost:8000/docs
- [Create an issue](link-to-issues) for bug reports or feature requests