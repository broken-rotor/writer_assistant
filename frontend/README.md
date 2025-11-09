# Writer Assistant Frontend

Angular 17 single-page application providing an interactive interface for collaborative storytelling with AI agents.

## Overview

The frontend is a stateful Angular application that manages story creation, context building, and interaction with multiple AI agents. It uses local storage for persistence, provides real-time feedback during generation, and offers specialized interfaces for worldbuilding, plotting, and chapter development.

### Key Features

- **Dashboard**: Story management and creation
- **Story Workspace**: Integrated environment for story development
- **Worldbuilding Chat**: Conversational interface for building story world
- **Plot Outline**: Visual plot management and chapter planning
- **Multi-Agent Feedback**: View responses from Writer, Editor, Character, and Rater agents
- **Context Management**: Build and manage structured context with token awareness
- **Local Persistence**: All story data stored in browser localStorage
- **Streaming Support**: Real-time updates during AI generation via SSE

## Architecture

### Directory Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── components/           # UI Components
│   │   │   ├── dashboard/        # Story list and management
│   │   │   ├── story-workspace/  # Main editing interface
│   │   │   ├── chat-interface/   # Chat UI
│   │   │   ├── worldbuilding-chat/
│   │   │   ├── worldbuilding-tab/
│   │   │   ├── plot-outline-tab/
│   │   │   ├── archive/          # Archive browser
│   │   │   ├── feedback-sidebar/ # Agent feedback display
│   │   │   ├── review-feedback-panel/
│   │   │   ├── system-prompt-field/
│   │   │   ├── token-counter/    # Token display
│   │   │   ├── storage-management/
│   │   │   ├── loading-spinner/
│   │   │   └── toast/            # Notifications
│   │   │
│   │   ├── services/             # Business Logic
│   │   │   ├── api.service.ts              # HTTP client base
│   │   │   ├── story.service.ts            # Story CRUD
│   │   │   ├── generation.service.ts       # AI generation
│   │   │   ├── streaming.service.ts        # SSE streaming
│   │   │   ├── context-builder.service.ts  # Context assembly
│   │   │   ├── context-manager.service.ts  # Context state
│   │   │   ├── context-storage.service.ts  # Context persistence
│   │   │   ├── context-versioning.service.ts
│   │   │   ├── token-counting.service.ts   # Token estimation
│   │   │   ├── token-limits.service.ts
│   │   │   ├── token-validation.service.ts
│   │   │   ├── local-storage.service.ts    # Browser storage
│   │   │   ├── archive.service.ts          # Archive operations
│   │   │   ├── conversation.service.ts
│   │   │   ├── feedback.service.ts
│   │   │   ├── review.service.ts
│   │   │   ├── request-converter.service.ts
│   │   │   ├── request-optimizer.service.ts
│   │   │   ├── request-validator.service.ts
│   │   │   ├── plot-outline.service.ts
│   │   │   ├── plot-outline-context.service.ts
│   │   │   ├── worldbuilding-validator.service.ts
│   │   │   ├── loading.service.ts
│   │   │   ├── toast.service.ts
│   │   │   └── configuration.service.ts
│   │   │
│   │   ├── models/               # TypeScript Interfaces
│   │   │   ├── story.model.ts            # Core Story interface
│   │   │   ├── context-builder.model.ts  # Context types
│   │   │   ├── generation-request.model.ts
│   │   │   ├── archive.model.ts
│   │   │   └── ...
│   │   │
│   │   ├── pipes/                # Custom pipes
│   │   ├── utils/                # Utility functions
│   │   ├── constants/            # Constants and configs
│   │   ├── app.component.ts      # Root component
│   │   ├── app.config.ts         # App configuration
│   │   └── app.routes.ts         # Routing configuration
│   │
│   ├── assets/                   # Static assets
│   ├── styles.scss              # Global styles
│   └── index.html               # HTML entry point
│
├── angular.json                 # Angular CLI config
├── tsconfig.json               # TypeScript config
├── package.json                # NPM dependencies
├── karma.conf.js               # Test configuration
└── eslint.config.js            # ESLint configuration
```

### Core Components

#### 1. Dashboard Component

Story list and management:
- Create new stories
- Load existing stories from localStorage
- Delete stories
- View story metadata

#### 2. Story Workspace Component

Main editing interface with tabs:
- **Worldbuilding**: Define story world, characters, themes
- **Plot Outline**: Manage story structure and chapter outlines
- **Chapters**: Write and edit story chapters
- **Archive**: Search archived content
- **Review**: View agent feedback and reviews

Coordinates between:
- Context building
- AI generation
- Feedback display
- State persistence

#### 3. Chat Interface Component

Conversational UI for:
- Worldbuilding discussions
- Story brainstorming
- Character development
- Maintaining conversation history

Features:
- Message threading
- Conversation context management
- Token-aware truncation
- Export conversation summaries

### Service Layer

#### Context Services

**ContextBuilderService** (`context-builder.service.ts`):
```typescript
// Build structured context from story data
buildSystemPromptsContext(story, options): ContextBuilderResponse
buildWorldbuildingContext(story, options): ContextBuilderResponse
buildCharactersContext(story, options): ContextBuilderResponse
buildChaptersContext(story, options): ContextBuilderResponse
buildPlotContext(story, options): ContextBuilderResponse
buildFeedbackContext(story, options): ContextBuilderResponse

// Full context assembly
buildFullContext(story, options): FullContextResponse
```

**ContextManagerService** (`context-manager.service.ts`):
- Manages context state across components
- Coordinates context updates
- Handles context invalidation

**ContextStorageService** (`context-storage.service.ts`):
- Persists context snapshots
- Manages context history
- Provides context restoration

#### Generation Services

**GenerationService** (`generation.service.ts`):
```typescript
// Primary generation methods
generateChapter(request): Observable<GenerationResponse>
modifyChapter(request): Observable<ModificationResponse>
getCharacterFeedback(request): Observable<FeedbackResponse>
getEditorReview(request): Observable<ReviewResponse>
getRaterFeedback(request): Observable<RatingResponse>
fleshOut(request): Observable<FleshOutResponse>
generateCharacterDetails(request): Observable<CharacterDetailsResponse>

// Streaming support
generateChapterStream(request): Observable<StreamEvent>
```

**StreamingService** (`streaming.service.ts`):
- Server-sent events (SSE) handling
- Progress updates during generation
- Error handling and reconnection
- Token counting during stream

#### Storage Services

**LocalStorageService** (`local-storage.service.ts`):
```typescript
// Story persistence
saveStory(story: Story): void
getStory(id: string): Story | null
getAllStories(): Story[]
deleteStory(id: string): void

// Export/Import
exportStory(id: string): Blob
importStory(file: File): Promise<Story>
```

**StoryService** (`story.service.ts`):
- Story CRUD operations
- Story validation
- Story metadata management
- Coordinates with LocalStorageService

#### Token Services

**TokenCountingService** (`token-counting.service.ts`):
```typescript
// Approximate token counting (client-side)
estimateTokens(text: string): number
estimateContextTokens(context: StructuredContext): TokenBreakdown

// Remote counting (authoritative)
countTokensRemote(text: string): Observable<number>
```

**TokenLimitsService** (`token-limits.service.ts`):
- Enforces token budgets
- Validates requests before API calls
- Provides warnings when approaching limits

**TokenValidationService** (`token-validation.service.ts`):
- Validates context fits within limits
- Suggests optimizations
- Reports token usage breakdowns

### Data Flow

#### Story Creation and Editing

```
User Input (Workspace Component)
    ↓
Story Model Update
    ↓
LocalStorageService.saveStory()
    ↓
Browser localStorage
```

#### AI Generation Flow

```
User Request (Workspace Component)
    ↓
ContextBuilderService.buildFullContext()
    ↓
TokenValidationService.validate()
    ↓
GenerationService.generateChapter()
    ↓
RequestConverterService.toBackendRequest()
    ↓
ApiService.post() → Backend API
    ↓
Response Processing
    ↓
Story Model Update
    ↓
LocalStorageService.saveStory()
    ↓
UI Update
```

#### Streaming Generation Flow

```
User Request
    ↓
GenerationService.generateChapterStream()
    ↓
StreamingService connects SSE
    ↓
Progressive UI Updates (each token/chunk)
    ↓
Final Response → Story Update
```

### State Management

The frontend uses a **service-based state management** approach:

1. **Story State**: Managed by StoryService + LocalStorageService
2. **Context State**: Managed by ContextManagerService
3. **UI State**: Component-local state with RxJS for reactivity
4. **Shared State**: Services with BehaviorSubjects for cross-component communication

**No external state library** (Redux, NgRx, etc.) - keeps architecture simple.

### Models

#### Story Model (`story.model.ts`)

```typescript
interface Story {
  id: string;
  title: string;
  general: {
    systemPrompts: SystemPrompts;
    general: GeneralInfo;
    worldbuilding: Worldbuilding;
    characters: Character[];
  };
  chapters: Chapter[];
  plotOutlines: PlotOutline[];
  conversations: ConversationThread[];
  feedback: FeedbackItem[];
  reviews: ReviewItem[];
  metadata: StoryMetadata;
}
```

The Story model is the **central data structure** containing all story-related information.

#### Context Models (`context-builder.model.ts`)

Structured context interfaces matching backend expectations:
- `SystemPromptsContext`
- `WorldbuildingContext`
- `CharacterContext`
- `ChaptersContext`
- `PlotContext`
- `FeedbackContext`
- `ConversationContext`

### Routing

```typescript
const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'story/:id', component: StoryWorkspaceComponent },
  { path: 'archive', component: ArchiveComponent },
  { path: '**', redirectTo: '/dashboard' }
];
```

## Development Setup

### Prerequisites

- Node.js 20+
- npm 9+

### Installation

```bash
cd frontend

# Install dependencies
npm install
```

### Running

```bash
# Development server
npm start
# or
ng serve

# Open browser to http://localhost:4200
```

The app will automatically reload when source files change.

### Building

```bash
# Development build
npm run build
# or
ng build

# Production build
ng build --configuration production

# Output in dist/writer-assistant/
```

### Testing

```bash
# Run tests in watch mode
npm test
# or
ng test

# Run tests once (CI mode)
npm test -- --watch=false --browsers=ChromeHeadless

# Run with coverage
npm test -- --watch=false --code-coverage --browsers=ChromeHeadless

# Run specific test file
ng test --include='**/context-builder.service.spec.ts'
```

Coverage reports in `coverage/` directory.

### Linting

```bash
# Run ESLint
npm run lint
# or
ng lint

# Auto-fix issues
ng lint --fix
```

## Configuration

### API Endpoint

Backend API URL is configured in environment files (if using Angular environments) or directly in services.

Default: `http://localhost:8000`

To change, update `ApiService` base URL:

```typescript
// src/app/services/api.service.ts
private apiUrl = 'http://localhost:8000/api/v1';
```

### Storage Limits

Browser localStorage has limits (~5-10MB). Large stories may hit this limit.

The application includes:
- Storage usage monitoring
- Export/import functionality
- Compression options (if implemented)

## Key Concepts

### Structured Context Building

The frontend transforms the Story model into structured context for the backend:

1. **System Prompts**: Instructions for AI behavior
2. **Worldbuilding**: Story world, themes, tone
3. **Characters**: Character details, relationships, arcs
4. **Chapters**: Story content, recent chapters prioritized
5. **Plot**: Plot outline, story structure
6. **Feedback**: Previous agent feedback and reviews
7. **Conversation**: Chat history and worldbuilding discussions

Each section is:
- Token-counted
- Prioritized
- Cached for performance
- Validated before sending

### Token Management

Client-side token counting is **approximate**:
- Uses simple word-based estimation
- Backend has authoritative count
- Always validate with backend for accuracy

Token limits enforced:
- Per-section limits
- Total context limits
- Generation output limits

### Local-First Architecture

All story data lives in the browser:
- No backend database
- No user authentication needed
- Export/import for backup
- Privacy-focused (data never leaves device except during API calls)

### Component Communication

Components communicate via:
1. **Services**: Shared state via BehaviorSubjects
2. **Input/Output**: Parent-child component communication
3. **Routing**: Navigation state via route params
4. **Events**: Custom events for loosely-coupled interactions

## Styling

### CSS Architecture

- **Global Styles**: `src/styles.scss`
- **Angular Material Theme**: Custom theme configuration
- **Component Styles**: Scoped SCSS per component
- **Responsive Design**: Mobile-friendly layouts

### Material Components

Heavy use of Angular Material:
- Tabs, Cards, Buttons
- Form Fields, Inputs, Textareas
- Dialogs, Snackbars
- Icons, Progress Indicators

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Components loaded on demand
2. **OnPush Change Detection**: Where applicable
3. **Context Caching**: Avoid rebuilding unchanged context
4. **Token Counting Debouncing**: Reduce calculation frequency
5. **Virtual Scrolling**: For large chapter/archive lists

### Storage Optimization

- Compress story data before storing
- Clean up old context snapshots
- Export large stories to files
- Monitor storage usage

## Testing

### Unit Tests

Tests follow Angular testing patterns:
- TestBed for component testing
- Jasmine for assertions
- Karma as test runner

Example:
```typescript
describe('ContextBuilderService', () => {
  let service: ContextBuilderService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ContextBuilderService);
  });

  it('should build system prompts context', () => {
    const story = createMockStory();
    const result = service.buildSystemPromptsContext(story);
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
  });
});
```

### Integration Testing

Test flows across multiple services:
- Context building → Generation → Story update
- Token validation → API call → Response handling

### E2E Testing

(If configured)
- User workflows
- Full story creation flow
- API integration testing

## Troubleshooting

### Build Errors

**Node version mismatch**
```bash
node --version  # Should be 20+
npm install     # Reinstall dependencies
```

**TypeScript errors**
```bash
ng build        # Shows all errors
```

### Runtime Errors

**API connection failed**
- Check backend is running on http://localhost:8000
- Check CORS configuration in backend
- Check browser console for details

**localStorage quota exceeded**
- Export and delete old stories
- Clear browser cache
- Use smaller models or reduce chapter count

**Token counting mismatch**
- Client-side counting is approximate
- Backend has authoritative count
- Use backend's count for validation

### Test Failures

**ChromeHeadless crashes**
```bash
# Add --no-sandbox flag
ng test -- --browsers=ChromeHeadless --no-sandbox
```

**Async test timeouts**
- Increase jasmine timeout in `karma.conf.js`
- Use `fakeAsync` and `tick` for time-based tests

## Additional Documentation

- **[../README.md](../README.md)**: Project overview and setup
- **[../CLAUDE.md](../CLAUDE.md)**: Architecture and development guidance
- **[../backend/README.md](../backend/README.md)**: Backend architecture
- **API Documentation**: http://localhost:8000/docs (when backend running)

## Contributing

When working on the frontend:

1. Follow Angular style guide
2. Use TypeScript strict mode
3. Write tests for services and components
4. Update models when backend API changes
5. Use RxJS operators appropriately (avoid nested subscriptions)
6. Follow existing patterns for context building
7. Document complex logic with comments
8. Keep components focused (single responsibility)
