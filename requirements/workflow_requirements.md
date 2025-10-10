# Workflow Requirements

## Overview

The Writer Assistant uses a simplified, chapter-by-chapter workflow where users directly control story creation through a tabbed interface. All workflow state is managed client-side in browser local storage, while the backend provides stateless AI agent services.

## Core Workflow Principles

1. **Tabbed Interface**: Users navigate between General, Characters, Raters, Story, and Chapter Creation tabs
2. **Chapter-Centric Development**: Stories are built chapter by chapter with AI assistance
3. **User-Driven Feedback**: Users explicitly request feedback from selected agents
4. **Iterative Refinement**: Users iterate with agents until satisfied, then finalize
5. **Client-Side State**: All workflow state persisted in browser local storage
6. **Stateless Services**: Backend provides independent AI responses without session state

## Workflow Phases

### Phase 1: Story Setup

**Tab: General**

User configures story-level settings:

```
User Actions:
1. Enter story title
2. Configure system prompts (optional):
   - Main prefix (added before all agent prompts)
   - Main suffix (added after all agent prompts)
   - Writer assistant system prompt
   - Editor system prompt
3. Provide worldbuilding/setting
4. (Optional) Request AI to flesh out worldbuilding
```

**State Updates**:
- Save all settings to local storage on change
- Auto-save every 30 seconds
- Immediate save on tab switch

### Phase 2: Character Configuration

**Tab: Characters**

User creates and configures story characters:

```
User Actions:
1. Click "Add Character"
2. Provide basic bio
3. (Option A) Click "Generate from Bio" for AI assistance:
   - AI generates: name, demographics, appearance, clothing,
     personality, motivations, fears, relationships
   - User reviews and edits any generated fields
4. (Option B) Manually fill all character fields
5. Click "Regenerate Relationships" to update for all characters
6. Save character

Character Management:
- Hide/Unhide characters (soft delete)
- Edit existing characters
- Remove characters permanently
```

**State Updates**:
- Character configurations saved to local storage
- Hidden characters retain all data (is_hidden: true)
- Only non-hidden characters available for chapter creation

### Phase 3: Rater Configuration

**Tab: Raters**

User configures feedback agents:

```
User Actions:
1. Click "Add New Rater"
2. Provide name
3. Write system prompt defining rater's role and criteria
4. Save rater
5. Enable/disable raters as needed

Rater Management:
- Edit rater prompts
- Remove raters
- Toggle enabled/disabled status
```

**State Updates**:
- Rater configurations saved to local storage
- Only enabled raters available for chapter creation

### Phase 4: Chapter Creation

**Tab: Chapter Creation**

Core workflow for creating each chapter:

#### Step 1: Plot Point Definition

```
User Actions:
1. Enter plot point describing what should happen in chapter
2. (Optional) Click "AI Flesh Out" to expand plot point
3. User can edit fleshed-out version
```

**Client State**:
```json
{
  "plotPoint": {
    "original": "user entered text",
    "current": "potentially AI-expanded text",
    "source": "user | ai_assisted | mixed"
  }
}
```

#### Step 2: Agent Feedback Collection

```
User Actions:
1. Click on character names (non-hidden only) to request feedback
2. Click on rater names (enabled only) to request feedback
3. Review agent feedback when ready

For Characters:
- Agent generates:
  * Actions (what they would do)
  * Dialog (what they would say)
  * Physical sensations (what they would experience)
  * Emotions (what they would feel)
  * Internal monologue (what they would think)

For Raters:
- Agent generates:
  * Opinion (assessment of plot point + incorporated feedback)
  * Suggestions (specific recommendations)
```

**Backend Request** (stateless):
```json
{
  "agentType": "character | rater",
  "agentConfig": {...},
  "context": {
    "storyTitle": "...",
    "worldbuilding": "...",
    "allCharacters": [...],
    "previousChapters": [...],
    "plotPoint": "...",
    "incorporatedFeedback": [...]
  }
}
```

**Backend Response** (stateless):
```json
{
  "agentName": "Sarah",
  "feedback": {
    "actions": ["Carefully open the letter"],
    "dialog": ["This changes everything"],
    "physicalSensations": ["Heart racing"],
    "emotions": ["Shock mixed with excitement"],
    "internalMonologue": ["Could this be the evidence?"]
  }
}
```

**Client State Update**:
```json
{
  "feedbackRequests": {
    "sarah_character": {
      "status": "ready",
      "feedback": {...}
    }
  }
}
```

#### Step 3: Feedback Iteration

```
User Actions:
1. Review agent feedback
2. (Optional) Enter user feedback in text box
3. Click "Suggest Changes" to ask agent to regenerate with user guidance
4. Click "Regenerate" to get alternative version without user input
5. Select specific feedback items to accept (checkboxes)
6. Click "Accept Selected" to move feedback to incorporated list
```

**Iteration Loop**:
- User can iterate with same agent multiple times
- Each iteration sends new stateless request with updated context
- Previous feedback not automatically included (user must explicitly incorporate)

**Client State Update**:
```json
{
  "incorporatedFeedback": [
    {
      "source": "Sarah",
      "type": "dialog",
      "content": "This changes everything",
      "incorporated": true
    },
    {
      "source": "Consistency Rater",
      "type": "suggestion",
      "content": "Add more tension",
      "incorporated": true
    }
  ]
}
```

#### Step 4: Chapter Generation

```
User Actions:
1. Click "Generate Chapter"
2. Wait for AI to generate full chapter text
3. Review generated chapter
```

**Backend Request** (stateless):
```json
{
  "operation": "generateChapter",
  "context": {
    "storyTitle": "...",
    "worldbuilding": "...",
    "characters": [...],
    "previousChapters": [...],
    "plotPoint": "...",
    "incorporatedFeedback": [...]
  },
  "systemPrompt": "[prefix] + [assistant prompt] + [suffix]"
}
```

**Backend Response**:
```json
{
  "chapterText": "Full generated chapter content...",
  "wordCount": 2347,
  "metadata": {
    "generatedAt": "2025-10-10T14:30:00Z"
  }
}
```

**Client State Update**:
```json
{
  "chapterDraft": {
    "text": "...",
    "status": "ready",
    "plotPoint": "...",
    "incorporatedFeedback": [...],
    "metadata": {...}
  }
}
```

#### Step 5: Chapter Editing

```
User Actions:
(Option A) Direct editing:
1. Click "Direct Edit"
2. Modify chapter text in editor
3. Save changes

(Option B) AI-assisted editing:
1. Enter desired changes in prompt box
2. Click "Prompt Assistant for Changes"
3. Review modified chapter
4. Accept or iterate further
```

**Backend Request for AI-assisted editing** (stateless):
```json
{
  "operation": "modifyChapter",
  "currentChapter": "...",
  "userRequest": "Add more sensory details",
  "context": {...},
  "systemPrompt": "[prefix] + [assistant prompt] + [suffix]"
}
```

#### Step 6: Editor Review

```
User Actions:
1. Click "Request Editor Review"
2. Review editor suggestions
3. Select suggestions to apply (checkboxes)
4. Click "Apply Selected" or "Apply All"
5. (Optional) Click "Reject All" to ignore suggestions
```

**Backend Request** (stateless):
```json
{
  "operation": "editorReview",
  "chapterText": "...",
  "context": {...},
  "systemPrompt": "[prefix] + [editor prompt] + [suffix]"
}
```

**Backend Response**:
```json
{
  "suggestions": [
    {
      "issue": "Opening lacks sensory detail",
      "suggestion": "Add description of sounds, smells",
      "priority": "high"
    },
    {
      "issue": "Emotional reaction could be stronger",
      "suggestion": "Show physical manifestation of emotion",
      "priority": "medium"
    }
  ]
}
```

**Client State Update**:
```json
{
  "editorReview": {
    "suggestions": [...],
    "userSelections": [true, true, false]
  }
}
```

#### Step 7: Chapter Finalization

```
User Actions:
1. Review final chapter
2. (Optional) Continue iterating:
   - More editor reviews
   - More assistant edits
   - More direct edits
3. Click "Accept Chapter - Add to Story"
```

**Client State Update**:
- Move chapter from draft to finalized chapters list
- Clear chapter creation workspace
- Update story summary (optional automatic regeneration)
- Save to local storage

**Navigation**:
- User switches to Story tab to see new chapter
- User can start new chapter in Chapter Creation tab

### Phase 5: Story Management

**Tab: Story**

User views and manages completed story:

```
User Actions:
1. View overall story summary
2. Click "Regenerate Summary" to update based on chapters
3. Read/expand individual chapters
4. Click "Edit" to modify existing chapter (loads into Chapter Creation tab)
5. Click "Delete" to remove chapter
6. Click "Insert After" to create new chapter between existing ones
7. Use "Add Chapter at End" to create next chapter
```

**State Management**:
- Chapters stored as ordered list
- Each chapter retains metadata (plot point, feedback used, timestamps)
- Story summary regenerated on demand or automatically

## State Management

### Client-Side State Structure

All state maintained in browser local storage:

```typescript
interface StoryState {
  general: {
    title: string;
    systemPrompts: {
      mainPrefix: string;
      mainSuffix: string;
      assistantPrompt: string;
      editorPrompt: string;
    };
    worldbuilding: string;
  };

  characters: Map<string, {
    basicBio: string;
    name: string;
    demographics: {...};
    physicalAppearance: string;
    usualClothing: string;
    personality: string;
    motivations: string;
    fears: string;
    relationships: string;
    isHidden: boolean;
    metadata: {...};
  }>;

  raters: Map<string, {
    name: string;
    systemPrompt: string;
    enabled: boolean;
  }>;

  story: {
    summary: string;
    chapters: Array<{
      number: number;
      title: string;
      content: string;
      plotPoint: string;
      incorporatedFeedback: FeedbackItem[];
      metadata: {
        created: Date;
        lastModified: Date;
        wordCount: number;
      };
    }>;
  };

  chapterCreation: {
    plotPoint: string;
    incorporatedFeedback: FeedbackItem[];
    feedbackRequests: Map<string, AgentFeedback>;
    generatedChapter?: {
      text: string;
      status: string;
      metadata: {...};
    };
    editorReview?: {
      suggestions: EditorSuggestion[];
      userSelections: boolean[];
    };
  };

  metadata: {
    storyId: string;
    version: string;
    created: Date;
    lastModified: Date;
  };
}
```

### State Persistence

**Auto-Save Strategy**:
- Save on every user action (debounced 300ms)
- Full save every 30 seconds
- Immediate save on tab switch
- Save indicator shows last save time

**Storage Keys**:
```
writer_assistant_story_{storyId}
writer_assistant_active_story  // Currently active story ID
writer_assistant_story_list   // List of all story IDs
```

## Backend Service Patterns

### Stateless Request-Response

All backend services are completely stateless:

**Character Feedback Service**:
```python
@app.post("/api/character-feedback")
def character_feedback(request: CharacterFeedbackRequest):
    # Build system prompt
    system_prompt = (
        request.systemPrompts.mainPrefix +
        request.character.systemPrompt +
        request.systemPrompts.mainSuffix
    )

    # Build context from request
    context = build_context(request)

    # Generate feedback (no state retained)
    feedback = llm.generate(system_prompt, context)

    # Return response (no state saved)
    return CharacterFeedbackResponse(feedback)
```

**Chapter Generation Service**:
```python
@app.post("/api/generate-chapter")
def generate_chapter(request: ChapterGenerationRequest):
    system_prompt = (
        request.systemPrompts.mainPrefix +
        request.systemPrompts.assistantPrompt +
        request.systemPrompts.mainSuffix
    )

    context = build_chapter_context(request)

    chapter_text = llm.generate(system_prompt, context)

    return ChapterGenerationResponse(chapter_text)
```

**Editor Review Service**:
```python
@app.post("/api/editor-review")
def editor_review(request: EditorReviewRequest):
    system_prompt = (
        request.systemPrompts.mainPrefix +
        request.systemPrompts.editorPrompt +
        request.systemPrompts.mainSuffix
    )

    context = build_review_context(request)

    suggestions = llm.generate(system_prompt, context)

    return EditorReviewResponse(suggestions)
```

### Context Building

Each stateless request includes all necessary context:

**Character Feedback Context**:
- Story title
- Worldbuilding
- All character configurations
- Previous chapters (full text)
- Current plot point
- Already incorporated feedback

**Chapter Generation Context**:
- Story title
- Worldbuilding
- Character configurations
- Previous chapters
- Plot point
- Incorporated feedback from characters and raters

**Editor Review Context**:
- Story title and worldbuilding
- Previous chapters
- Current chapter draft
- Plot point and incorporated feedback

## Workflow State Transitions

### Chapter Creation State Machine

```
States:
- plot_point_entry
- requesting_feedback
- reviewing_feedback
- generating_chapter
- editing_chapter
- requesting_review
- reviewing_editor_suggestions
- finalizing

Transitions:
plot_point_entry -> requesting_feedback (user clicks character/rater)
requesting_feedback -> reviewing_feedback (agent response ready)
reviewing_feedback -> requesting_feedback (user requests more feedback)
reviewing_feedback -> generating_chapter (user clicks "Generate Chapter")
generating_chapter -> editing_chapter (generation complete)
editing_chapter -> requesting_review (user clicks "Request Editor Review")
editing_chapter -> finalizing (user clicks "Accept Chapter")
requesting_review -> reviewing_editor_suggestions (editor response ready)
reviewing_editor_suggestions -> editing_chapter (user applies suggestions)
reviewing_editor_suggestions -> finalizing (user accepts without changes)
finalizing -> plot_point_entry (chapter added, workspace cleared)
```

### User Decision Points

Users control all major transitions:
1. When to request feedback (which agents)
2. When to stop iterating with agents
3. When to generate chapter
4. Whether to edit directly or use AI assistance
5. Whether to request editor review
6. Which editor suggestions to apply
7. When to finalize chapter

## Error Handling

### Client-Side Error Recovery

**Failed AI Requests**:
- Show error message
- Retain all user input
- Offer retry button
- Allow user to continue with other actions

**Local Storage Errors**:
- Detect storage quota exceeded
- Offer to export story
- Suggest deleting old stories
- Provide manual save option

**Network Errors**:
- Queue requests for retry
- Show offline indicator
- Allow continued editing
- Retry when connection restored

### Backend Error Responses

**Stateless Error Handling**:
```json
{
  "error": true,
  "errorType": "generation_failed",
  "message": "Failed to generate content",
  "retryable": true
}
```

Client decides how to handle:
- Retry immediately
- Retry with modifications
- Cancel and continue without AI
- Switch to manual editing

## Performance Optimization

### Client-Side Caching

**Previous Chapters**:
- Cache formatted chapter text
- Only send necessary chapters to backend (recent + referenced)

**Agent Configurations**:
- Cache system prompt compositions
- Avoid re-composition on every request

### Request Batching

**Multiple Agent Requests**:
- Client can send parallel requests for multiple agents
- Display results as they arrive
- No server-side coordination needed

### Incremental Loading

**Story Tab**:
- Load chapter list first
- Load chapter content on expand
- Lazy load older chapters

## Integration Points

### Angular Frontend

**Services**:
- `LocalStorageService`: All state persistence
- `StoryService`: Story state management
- `AgentService`: Backend API calls
- `WorkflowService`: Tab navigation and state transitions

**Components**:
- `GeneralTabComponent`
- `CharactersTabComponent`
- `RatersTabComponent`
- `StoryTabComponent`
- `ChapterCreationTabComponent`

### Python Backend

**Endpoints**:
- `POST /api/character-feedback`: Character agent responses
- `POST /api/rater-feedback`: Rater agent responses
- `POST /api/generate-chapter`: Chapter text generation
- `POST /api/modify-chapter`: Chapter editing assistance
- `POST /api/editor-review`: Editor suggestions
- `POST /api/flesh-out`: AI expansion (worldbuilding, plot points)
- `POST /api/generate-character`: Character detail generation

**LangChain Integration**:
- Individual chains for each operation
- No persistent memory between requests
- Context building from request parameters

This simplified workflow provides a clear, user-controlled process for story creation with AI assistance at every step.
