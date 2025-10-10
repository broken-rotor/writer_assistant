# System Architecture Requirements

## Overview

The Writer Assistant uses a simplified multi-agent architecture with a completely stateless backend. The system provides a tabbed web interface for chapter-by-chapter story creation, with all state managed client-side in browser local storage. The server provides stateless AI agent services that process each request independently without retaining any session data or user information.

## High-Level Architecture

### Core Components

1. **Tabbed Web Interface**: Angular-based UI with 5 tabs (General, Characters, Raters, Story, Chapter Creation)
2. **Stateless Agent Services**: Independent AI agent endpoints that process requests without maintaining state
3. **Browser Local Storage**: Complete story and character configuration persistence in client browser
4. **Client-Side State Management**: All workflow and story state managed in frontend
5. **Stateless API Gateway**: RESTful interface providing AI services only
6. **Stateless LLM Interface**: Request-response LLM processing without session persistence

### Stateless Client-Server Interactions

```
Client-Side (Angular Frontend)           Stateless Server Services
┌─────────────────────────────┐          ┌─────────────────────────────┐
│ Tabbed Web Interface        │◄────────►│ Stateless API Gateway       │
│ ┌─────────────────────────┐ │          │ ┌─────────────────────────┐ │
│ │ General Tab             │ │          │ │ Character Feedback      │ │
│ │ Characters Tab          │ │          │ │ Service                 │ │
│ │ Raters Tab              │ │          │ └─────────────────────────┘ │
│ │ Story Tab               │ │          │ ┌─────────────────────────┐ │
│ │ Chapter Creation Tab    │ │          │ │ Rater Feedback          │ │
│ └─────────────────────────┘ │          │ │ Service                 │ │
│ ┌─────────────────────────┐ │          │ └─────────────────────────┘ │
│ │ Local Storage Service   │ │          │ ┌─────────────────────────┐ │
│ │ - Story data            │ │          │ │ Chapter Generation      │ │
│ │ - Character configs     │ │          │ │ Service                 │ │
│ │ - Rater configs         │ │          │ └─────────────────────────┘ │
│ │ - Chapter drafts        │ │          │ ┌─────────────────────────┐ │
│ └─────────────────────────┘ │          │ │ Editor Review           │ │
│                             │          │ │ Service                 │ │
│ All state in browser        │          │ └─────────────────────────┘ │
│ No server persistence       │          │ ┌─────────────────────────┐ │
└─────────────────────────────┘          │ │ Stateless LLM Interface │ │
                                         │ │ (llama.cpp)             │ │
              ▲                          │ └─────────────────────────┘ │
              │                          └─────────────────────────────┘
              │ All requests include                   ▲
              │ complete context                       │
              │ No session state on server             │
              └────────────────────────────────────────┘
```

## Stateless Backend Architecture (Python + LangChain)

### Stateless Service Framework
- **Stateless API Endpoints**: Each service processes requests independently
- **Request-Scoped Processing**: All context provided in individual requests
- **No State Persistence**: Server maintains zero state between requests
- **Independent Services**: Character feedback, rater feedback, chapter generation, editor review
- **Zero Session Dependencies**: No workflow state or user data maintained

### Key Services

**Character Feedback Service**:
- Receives: character config, plot point, incorporated feedback, story context
- Returns: actions, dialog, sensations, emotions, internal monologue
- No state retained

**Rater Feedback Service**:
- Receives: rater config, plot point, incorporated feedback, story context
- Returns: opinion and suggestions
- No state retained

**Chapter Generation Service**:
- Receives: plot point, incorporated feedback, characters, previous chapters, worldbuilding
- Returns: generated chapter text
- No state retained

**Editor Review Service**:
- Receives: chapter draft, story context
- Returns: list of suggestions with priorities
- No state retained

**AI Flesh-Out Service**:
- Receives: content to expand (worldbuilding, plot point, character details)
- Returns: expanded content
- No state retained

### Stateless LLM Integration
- **llama.cpp Interface**: Local LLM integration without session persistence
- **Request-Scoped Context**: Context window populated from request data only
- **Stateless Model Access**: Model serves requests without retaining history
- **Independent Response Processing**: Each request processed independently

### Complete Client-Side Data Management
- **Exclusive Local Storage**: ALL story content and configuration stored only in browser
- **No Server Persistence**: Server maintains no user data, sessions, or state
- **Client State Serialization**: Complete application state serializable to JSON for export
- **Client-Only Configuration**: All character and rater configurations in browser storage
- **Client-Side Export/Import**: Complete story portability through JSON export

## Frontend Architecture (Angular)

### Core UI Components

**Tab Components**:
- **GeneralTabComponent**: Story title, system prompts, worldbuilding
- **CharactersTabComponent**: Character list and detail editor
- **RatersTabComponent**: Rater configuration and management
- **StoryTabComponent**: Chapter list and story summary display
- **ChapterCreationTabComponent**: Plot point, feedback collection, chapter generation

**Shared Services**:
- **LocalStorageService**: All browser storage operations
- **StoryService**: Story state management and updates
- **AgentService**: HTTP calls to backend API
- **WorkflowService**: Tab navigation and workflow state

### State Management

**Local Storage Schema**:
```typescript
interface StoryState {
  general: {
    title: string;
    systemPrompts: SystemPrompts;
    worldbuilding: string;
  };
  characters: Map<string, Character>;
  raters: Map<string, Rater>;
  story: {
    summary: string;
    chapters: Chapter[];
  };
  chapterCreation: ChapterCreationState;
  metadata: StoryMetadata;
}
```

**Auto-Save Strategy**:
- Save on every user action (debounced 300ms)
- Full save every 30 seconds
- Immediate save on tab switch
- Save indicator shows last save time

### Communication Layer
- **HTTP Client**: RESTful API calls to stateless backend
- **Error Handling**: Retry logic, user notifications
- **Loading States**: Progress indicators for all AI operations
- **Offline Support**: Allow editing without backend connection

## Integration Points

### LangChain Integration
- **Individual Chains**: Separate chains for each service endpoint
- **No Persistent Memory**: Context built from request parameters
- **Structured Output**: Consistent JSON response formats
- **Context Building**: Helper functions to format request context for LLM

### Backend API Endpoints

```
POST /api/character-feedback
POST /api/rater-feedback
POST /api/generate-chapter
POST /api/modify-chapter
POST /api/editor-review
POST /api/flesh-out
POST /api/generate-character-details
```

All endpoints are stateless and include complete context in request.

## Scalability Considerations

### Performance Optimization
- **Client-Side Caching**: Cache chapter text and agent configurations
- **Lazy Loading**: Load chapter content on-demand in Story tab
- **Incremental Saves**: Debounced auto-save to reduce storage operations
- **Parallel Requests**: Client sends multiple agent requests simultaneously

### Resource Management
- **Context Window Optimization**: Send only necessary chapters to backend
- **Model Resource Sharing**: Single LLM instance serves all requests
- **Request Queuing**: Handle concurrent users with request queue
- **Timeout Management**: Reasonable timeouts for long-running generations

## Security and Reliability

### Data Protection
- **Complete Client Privacy**: ALL user data remains in user's browser
- **Zero Server Data Exposure**: Server never stores any user story content
- **Stateless Request Processing**: Each request independent, no retention
- **Optional Local Encryption**: Client-side encryption for local storage
- **Input Sanitization**: Server-side validation of all request inputs

### Error Recovery
- **Client-Side Auto-Save**: Regular snapshots to local storage
- **Stateless Retry**: Failed requests can be retried independently
- **Graceful Degradation**: System continues working if backend unavailable
- **Export Safety**: Users can export stories at any time
- **Local Storage Backups**: Automatic backup of story data

## Deployment Architecture

### Local Development
- **Docker Compose**: Frontend, backend, and LLM in containers
- **llama.cpp**: Local LLM for development
- **Hot Reloading**: Angular dev server and Python auto-reload
- **CORS Configuration**: Allow localhost frontend to call backend API

### Production Deployment
- **Static Frontend**: Angular build served via nginx or similar
- **Python Backend**: FastAPI or Flask application with gunicorn
- **Local LLM**: llama.cpp with suitable model
- **Simple Architecture**: Single server can run entire stack
- **No Database Needed**: All state in client browsers

This simplified architecture prioritizes user privacy, ease of deployment, and straightforward development while providing powerful AI-assisted story creation capabilities.