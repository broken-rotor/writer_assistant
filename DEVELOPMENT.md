# Development Guide

This guide provides detailed information for developers working on the Writer Assistant project.

## Development Environment Setup

### Prerequisites

- **Docker**: Latest version with Docker Compose
- **Node.js**: Version 18 or higher
- **Python**: Version 3.11 or higher
- **Git**: For version control

### Local Development Setup

#### Option 1: Docker Development (Recommended)

1. **Clone and Start Services**
   ```bash
   git clone <repository-url>
   cd writer_assistant
   docker-compose up -d
   ```

2. **Access Services**
   - Frontend: http://localhost:4200
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Redis: localhost:6379

3. **Development Workflow**
   ```bash
   # View logs
   docker-compose logs -f backend
   docker-compose logs -f frontend

   # Restart specific service
   docker-compose restart backend
   docker-compose restart frontend

   # Stop all services
   docker-compose down
   ```

#### Option 2: Native Development

**Backend Setup:**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup:**
```bash
cd frontend/writer-assistant-ui
npm install

# Start development server
ng serve --host 0.0.0.0 --port 4200
```

## Project Architecture

### Backend Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API routes and endpoints
│   │   └── v1/
│   │       ├── api.py       # API router aggregation
│   │       └── endpoints/   # Individual endpoint modules
│   ├── core/                # Core application configuration
│   │   └── config.py        # Application settings
│   ├── models/              # Pydantic data models
│   │   └── story.py         # Story-related models
│   ├── services/            # Business logic layer
│   │   └── story_service.py # Story management service
│   ├── storage/             # Data persistence layer
│   │   └── json_storage.py  # JSON file storage implementation
│   └── agents/              # AI agent implementations (future)
└── requirements.txt         # Python dependencies
```

### Frontend Architecture

```
frontend/writer-assistant-ui/src/
├── app/
│   ├── app.component.*      # Root application component
│   ├── app.routes.ts        # Application routing configuration
│   ├── app.config.ts        # Application configuration
│   ├── components/          # Angular components
│   │   ├── dashboard/       # Story dashboard component
│   │   ├── story-creation/  # Story creation component
│   │   └── story-workspace/ # Story editing workspace
│   ├── services/            # Angular services
│   │   ├── api.service.ts   # HTTP API communication
│   │   └── story.service.ts # Story state management
│   └── models/              # TypeScript type definitions
│       └── story.model.ts   # Story-related types
```

## Coding Standards

### Backend (Python)

- **Code Style**: Follow PEP 8
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings
- **Async/Await**: Use async/await for all I/O operations

**Example:**
```python
from typing import List, Optional
from app.models.story import Story, StoryCreate

async def create_story(story_data: StoryCreate) -> Story:
    """Create a new story.

    Args:
        story_data: Story creation data

    Returns:
        Created story instance

    Raises:
        ValueError: If story data is invalid
    """
    # Implementation here
    pass
```

### Frontend (TypeScript/Angular)

- **Code Style**: Follow Angular style guide
- **Type Safety**: Use strict TypeScript configuration
- **Component Structure**: Use OnPush change detection where possible
- **Services**: Use dependency injection for all services

**Example:**
```typescript
@Component({
  selector: 'app-story-card',
  template: `<div>{{ story.title }}</div>`,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class StoryCardComponent {
  @Input() story!: Story;

  constructor(private storyService: StoryService) {}
}
```

## Testing Strategy

### Backend Testing

```bash
# Run tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_story_service.py
```

**Test Structure:**
```python
import pytest
from app.services.story_service import StoryService

@pytest.mark.asyncio
async def test_create_story():
    service = StoryService()
    story_data = StoryCreate(title="Test Story", genre="mystery")

    story = await service.create_story(story_data)

    assert story.title == "Test Story"
    assert story.genre == "mystery"
```

### Frontend Testing

```bash
# Run unit tests
cd frontend/writer-assistant-ui
ng test

# Run e2e tests
ng e2e

# Run tests with coverage
ng test --code-coverage
```

## API Development

### Adding New Endpoints

1. **Define Pydantic Models** (if needed)
   ```python
   # app/models/character.py
   class Character(BaseModel):
       id: str
       name: str
       role: str
   ```

2. **Create Service Layer**
   ```python
   # app/services/character_service.py
   class CharacterService:
       async def create_character(self, character_data: CharacterCreate) -> Character:
           # Business logic here
           pass
   ```

3. **Create API Endpoints**
   ```python
   # app/api/v1/endpoints/characters.py
   router = APIRouter()

   @router.post("/", response_model=Character)
   async def create_character(character_data: CharacterCreate):
       service = CharacterService()
       return await service.create_character(character_data)
   ```

4. **Register Router**
   ```python
   # app/api/v1/api.py
   from app.api.v1.endpoints import characters

   api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
   ```

## Database/Storage Development

Currently using JSON file storage for MVP. Migration to PostgreSQL planned.

### JSON Storage Usage

```python
from app.storage.json_storage import JSONStorage

# Initialize storage for a collection
storage = JSONStorage("stories")

# Save data
await storage.save("story_123", story_data)

# Load data
story_data = await storage.load("story_123")

# List all items
all_stories = await storage.list_all()
```

### Future Database Migration

When migrating to PostgreSQL:
1. Create SQLAlchemy models
2. Implement database service layer
3. Add Alembic migrations
4. Update dependency injection

## Agent Development (Future)

### Base Agent Structure

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.memory = AgentMemory()

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return response."""
        pass
```

### LangGraph Integration

```python
from langgraph import StateGraph, END

def create_story_workflow():
    workflow = StateGraph(state_schema)

    workflow.add_node("writer", writer_agent)
    workflow.add_node("rater", rater_agent)
    workflow.add_node("editor", editor_agent)

    workflow.add_edge("writer", "rater")
    workflow.add_edge("rater", "editor")
    workflow.add_edge("editor", END)

    return workflow.compile()
```

## Frontend Development

### Component Development

1. **Generate Component**
   ```bash
   ng generate component components/feature-name
   ```

2. **Component Structure**
   ```typescript
   @Component({
     selector: 'app-feature',
     templateUrl: './feature.component.html',
     styleUrls: ['./feature.component.scss']
   })
   export class FeatureComponent implements OnInit {
     constructor(private service: FeatureService) {}

     ngOnInit(): void {
       // Initialization logic
     }
   }
   ```

### Service Development

```typescript
@Injectable({
  providedIn: 'root'
})
export class FeatureService {
  private apiUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) {}

  getItems(): Observable<Item[]> {
    return this.http.get<Item[]>(`${this.apiUrl}/items`);
  }
}
```

## Debugging

### Backend Debugging

```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use breakpoints
import pdb; pdb.set_trace()

# FastAPI debug mode
uvicorn app.main:app --reload --log-level debug
```

### Frontend Debugging

```typescript
// Console logging
console.log('Debug info:', data);

// Angular DevTools
// Install Angular DevTools browser extension

// Network debugging
// Use browser dev tools Network tab
```

## Performance Optimization

### Backend Optimization

- Use async/await for all I/O operations
- Implement proper error handling
- Add request/response logging
- Use connection pooling (future database)

### Frontend Optimization

- Use OnPush change detection
- Implement lazy loading for routes
- Optimize bundle size
- Use Angular CDK virtual scrolling for large lists

## Common Development Tasks

### Adding a New Feature

1. Update requirements documentation
2. Create backend API endpoints
3. Add frontend service methods
4. Create UI components
5. Add routing if needed
6. Write tests
7. Update documentation

### Fixing a Bug

1. Reproduce the issue
2. Add a test that fails
3. Fix the code
4. Ensure test passes
5. Check for regression
6. Update documentation if needed

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port
lsof -i :8000
# Kill process
kill -9 <PID>
```

**Docker issues:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Node modules issues:**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

## Deployment

### Development Deployment

Currently using Docker Compose for development. Production deployment guide will be added later.

### Environment Variables

**Backend (.env):**
```
DEBUG=True
SECRET_KEY=dev-secret-key
DATA_DIR=data
MAX_CONTEXT_LENGTH=4000
DEFAULT_TEMPERATURE=0.7
```

**Frontend (environment.ts):**
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1'
};
```