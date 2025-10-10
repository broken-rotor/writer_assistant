# User Interface Requirements

## Overview

The Writer Assistant frontend provides a tabbed interface that gives users complete control over story development. Built with Angular, the interface manages all state client-side in browser local storage and coordinates with stateless backend AI services. The UI emphasizes a simple, direct workflow for creating stories chapter by chapter with AI assistance.

## Core UI Structure

The application uses a single-page, tabbed interface for story creation and management:

### Story Creation Page

The main workspace consists of five tabs:

1. **General Tab** - Overall story configuration
2. **Characters Tab** - Character creation and management
3. **Raters Tab** - Feedback agent configuration
4. **Story Tab** - View generated story content
5. **Chapter Creation Tab** - Interactive chapter development workspace

All data is automatically persisted to browser local storage.

## Tab 1: General

**Purpose**: Configure global story settings and system prompts

**Components**:

### Story Title Field
```typescript
interface StoryTitleComponent {
  title: string;
  placeholder: "Enter story title";
  validation: {
    required: true;
    maxLength: 200;
  };
}
```

### System Prompt Configuration
```typescript
interface SystemPromptConfig {
  mainPrefix: string;  // Added before every agent system prompt
  mainSuffix: string;  // Added after every agent system prompt
  assistantSystemPrompt: string;  // Writer assistant's system prompt
  editorSystemPrompt: string;     // Editor agent's system prompt

  promptComposition: {
    // Final prompt = mainPrefix + agentPrompt + mainSuffix
    example: "[prefix] [agent specific prompt] [suffix]";
  };
}
```

### Worldbuilding Section
```typescript
interface WorldbuildingComponent {
  content: string;
  source: "user" | "ai_assisted" | "mixed";

  actions: {
    aiFleshOut(): void;      // User can request AI to expand
    userEdit(): void;        // User can manually edit
    resetToOriginal(): void; // Restore to initial version
  };

  history: {
    userProvided: string;
    aiExpansions: Array<{
      timestamp: Date;
      content: string;
      userPrompt: string;
    }>;
  };
}
```

**Layout**:
```
┌─────────────────────────────────────────────────┐
│ General Tab                                     │
├─────────────────────────────────────────────────┤
│ Story Title                                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ [Enter story title]                         │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Main System Prompt Prefix (optional)           │
│ ┌─────────────────────────────────────────────┐ │
│ │ [Text added before every agent prompt]      │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Main System Prompt Suffix (optional)           │
│ ┌─────────────────────────────────────────────┐ │
│ │ [Text added after every agent prompt]       │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Writer Assistant System Prompt                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ [Assistant's system prompt configuration]   │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Editor System Prompt                           │
│ ┌─────────────────────────────────────────────┐ │
│ │ [Editor's system prompt configuration]      │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Overall Setting / Worldbuilding                │
│ ┌─────────────────────────────────────────────┐ │
│ │ [User-provided worldbuilding]               │ │
│ │                                             │ │
│ │ [AI can flesh out, user can edit]          │ │
│ └─────────────────────────────────────────────┘ │
│ [AI Flesh Out] [Reset to Original]            │
└─────────────────────────────────────────────────┘
```

## Tab 2: Characters

**Purpose**: Create, configure, and manage story characters

**Components**:

### Character List Panel
```typescript
interface CharacterListComponent {
  characters: Character[];

  displayStates: {
    active: Character[];    // is_hidden: false
    hidden: Character[];    // is_hidden: true
  };

  actions: {
    addCharacter(): void;
    removeCharacter(id: string): void;
    hideCharacter(id: string): void;
    unhideCharacter(id: string): void;
  };
}
```

### Character Detail Editor
```typescript
interface CharacterDetailComponent {
  basicBio: string;  // User-provided foundation

  // AI-generated from basic bio, user can edit
  generatedFields: {
    name: string;
    sex: string;
    gender: string;
    sexualPreference: string;
    age: number;
    physicalAppearance: string;
    usualClothing: string;
    personality: string;
    motivations: string;
    fears: string;
    relationships: string;
  };

  actions: {
    generateFromBio(): void;           // Generate all fields from basic bio
    regenerateField(field: string): void;  // Regenerate specific field
    regenerateRelationships(): void;   // Update relationships to account for other characters
    userEdit(field: string): void;     // Manual user editing
  };

  metadata: {
    isHidden: boolean;
    creationSource: "user" | "ai_generated" | "imported";
    lastModified: Date;
  };
}
```

**Workflow**:
1. User clicks "Add Character"
2. User provides basic bio
3. User triggers AI generation (or manually enters all fields)
4. AI generates name, demographics, appearance, personality, motivations, fears
5. AI generates initial relationships based on basic bio
6. User reviews and edits any generated fields
7. User can click "regenerate/expand" button for relationships to account for other characters
8. Character saved to local storage

**Layout**:
```
┌─────────────────────────────────────────────────┐
│ Characters Tab                                  │
├─────────────┬───────────────────────────────────┤
│ Character   │ Character Details                 │
│ List        │                                   │
│ ┌─────────┐ │ Basic Bio (user-provided)         │
│ │ Active: │ │ ┌───────────────────────────────┐ │
│ │ Sarah   │ │ │ A curious journalist who...   │ │
│ │  [Edit] │ │ └───────────────────────────────┘ │
│ │  [Hide] │ │                                   │
│ │         │ │ Name (AI-generated, user editable)│
│ │ John    │ │ ┌───────────────────────────────┐ │
│ │  [Edit] │ │ │ Sarah Chen                    │ │
│ │  [Hide] │ │ └───────────────────────────────┘ │
│ │         │ │                                   │
│ └─────────┘ │ Demographics (AI-generated)       │
│             │ Sex: [Female] Gender: [Female]    │
│ ┌─────────┐ │ Sexual Pref: [Heterosexual]       │
│ │ Hidden: │ │ Age: [32]                         │
│ │ Mayor   │ │                                   │
│ │ [Unhide]│ │ Physical Appearance               │
│ │         │ │ ┌───────────────────────────────┐ │
│ └─────────┘ │ │ [AI-generated description]    │ │
│             │ └───────────────────────────────┘ │
│ [+ Add]     │                                   │
│             │ Usual Clothing, Personality,      │
│             │ Motivations, Fears...             │
│             │ (all AI-generated, user-editable) │
│             │                                   │
│             │ Relationships                     │
│             │ ┌───────────────────────────────┐ │
│             │ │ [AI-generated relationships]  │ │
│             │ └───────────────────────────────┘ │
│             │ [Regenerate for Other Characters] │
│             │                                   │
│             │ [Generate from Bio] [Save]        │
└─────────────┴───────────────────────────────────┘
```

## Tab 3: Raters

**Purpose**: Configure feedback agents for story evaluation

**Components**:

### Rater List and Configuration
```typescript
interface RaterComponent {
  raters: Rater[];

  raterConfig: {
    name: string;              // User-provided name
    systemPrompt: string;      // User-provided system prompt
    specialty?: string;        // Optional specialty description
    enabled: boolean;          // Active/inactive toggle
  };

  actions: {
    addRater(): void;
    removeRater(id: string): void;
    editRaterPrompt(id: string): void;
    toggleRater(id: string): void;
  };
}
```

**Layout**:
```
┌─────────────────────────────────────────────────┐
│ Raters Tab                                      │
├─────────────────────────────────────────────────┤
│ Configured Raters                               │
│ ┌─────────────────────────────────────────────┐ │
│ │ Character Consistency Rater  [Edit] [Remove]│ │
│ │ System Prompt: "Evaluate character..."      │ │
│ │ [Enabled ✓]                                 │ │
│ ├─────────────────────────────────────────────┤ │
│ │ Narrative Flow Rater        [Edit] [Remove] │ │
│ │ System Prompt: "Assess story flow..."      │ │
│ │ [Enabled ✓]                                 │ │
│ ├─────────────────────────────────────────────┤ │
│ │ Genre Expert                [Edit] [Remove] │ │
│ │ System Prompt: "Review genre fit..."       │ │
│ │ [Enabled ☐]                                 │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [+ Add New Rater]                              │
│                                                 │
│ Add/Edit Rater                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Name: [                    ]                │ │
│ │                                             │ │
│ │ System Prompt:                              │ │
│ │ ┌─────────────────────────────────────────┐ │ │
│ │ │                                         │ │ │
│ │ │                                         │ │ │
│ │ └─────────────────────────────────────────┘ │ │
│ │                                             │ │
│ │ [Save Rater] [Cancel]                       │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## Tab 4: Story

**Purpose**: Display generated story content and manage chapters

**Components**:

### Story Summary Display
```typescript
interface StorySummaryComponent {
  summary: string;  // AI-generated overall story summary
  autoUpdate: boolean;  // Regenerate when chapters change

  actions: {
    regenerateSummary(): void;
    editSummary(): void;
  };
}
```

### Chapter List and Management
```typescript
interface ChapterListComponent {
  chapters: Chapter[];

  chapterDisplay: {
    number: number;
    title: string;
    content: string;
    wordCount: number;
    lastModified: Date;
  };

  actions: {
    addChapterAtEnd(): void;
    insertChapterAfter(position: number): void;
    editChapter(id: string): void;
    deleteChapter(id: string): void;
    moveChapter(from: number, to: number): void;
  };
}
```

**Layout**:
```
┌─────────────────────────────────────────────────┐
│ Story Tab                                       │
├─────────────────────────────────────────────────┤
│ Overall Story Summary (AI-generated)            │
│ ┌─────────────────────────────────────────────┐ │
│ │ This mystery follows Sarah Chen as she...  │ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│ [Regenerate Summary]                            │
├─────────────────────────────────────────────────┤
│ Chapters                                        │
│ ┌─────────────────────────────────────────────┐ │
│ │ Chapter 1: The Arrival                      │ │
│ │ [Edit] [Delete] [Insert After]             │ │
│ │ ┌───────────────────────────────────────┐   │ │
│ │ │ Sarah Chen's car crunched over the... │   │ │
│ │ │ [Expand to read full chapter]         │   │ │
│ │ └───────────────────────────────────────┘   │ │
│ ├─────────────────────────────────────────────┤ │
│ │ Chapter 2: First Impressions                │ │
│ │ [Edit] [Delete] [Insert After]             │ │
│ │ ┌───────────────────────────────────────┐   │ │
│ │ │ The diner smelled of coffee and...   │   │ │
│ │ │ [Expand to read full chapter]         │   │ │
│ │ └───────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [+ Add Chapter at End] [+ Insert Chapter]      │
└─────────────────────────────────────────────────┘
```

## Tab 5: Chapter Creation

**Purpose**: Interactive workspace for creating new chapters with AI assistance

**Workflow**:
1. User provides plot point
2. User can request AI to flesh out plot point
3. User selects characters/raters to get feedback
4. Each selected agent generates their feedback
5. User can iterate with agents (suggest changes, regenerate)
6. User accepts some or all feedback to incorporate
7. User clicks "Generate" to create chapter from plot point + incorporated feedback
8. User can directly edit generated chapter or prompt assistant for changes
9. User clicks "Review" to get editor suggestions
10. User decides which editor suggestions to follow
11. User accepts final chapter or continues iterating

**Components**:

### Plot Point Editor
```typescript
interface PlotPointComponent {
  plotPoint: string;  // User-provided
  source: "user" | "ai_assisted" | "mixed";

  actions: {
    aiFleshOut(): void;    // Ask AI to expand plot point
    userEdit(): void;      // Direct editing
    reset(): void;         // Back to original
  };
}
```

### Incorporated Feedback List
```typescript
interface IncorporatedFeedbackComponent {
  feedbackItems: Array<{
    source: string;        // Character or rater name
    type: "action" | "dialog" | "sensation" | "emotion" | "thought" | "suggestion";
    content: string;
    incorporated: boolean;
  }>;

  actions: {
    removeFeedback(id: string): void;
    editFeedback(id: string): void;
  };
}
```

### Agent Feedback Panel
```typescript
interface AgentFeedbackComponent {
  availableAgents: {
    characters: Character[];  // Only non-hidden characters
    raters: Rater[];          // All enabled raters
  };

  feedbackRequests: Map<string, {
    status: "pending" | "generating" | "ready";
    feedback: CharacterFeedback | RaterFeedback;
  }>;

  actions: {
    requestFeedback(agentId: string): void;
    suggestChanges(agentId: string, userFeedback: string): void;
    acceptFeedback(agentId: string, items: string[]): void;
  };
}
```

### Character Feedback Structure
```typescript
interface CharacterFeedback {
  characterName: string;

  feedback: {
    actions: string[];           // What they would do
    dialog: string[];            // What they would say
    physicalSensations: string[]; // What they would experience
    emotions: string[];          // What they would feel
    internalMonologue: string[]; // What they would think
  };

  userInteraction: {
    canSuggestChanges: boolean;
    canRequestAlternative: boolean;
    canAcceptSelectively: boolean;
  };
}
```

### Rater Feedback Structure
```typescript
interface RaterFeedback {
  raterName: string;

  feedback: {
    opinion: string;        // Overall assessment of plot point + incorporated feedback
    suggestions: string[];  // Specific suggestions
  };

  userInteraction: {
    canSuggestChanges: boolean;
    canRequestAlternative: boolean;
    canAcceptSelectively: boolean;
  };
}
```

### Chapter Generation and Editing
```typescript
interface ChapterGenerationComponent {
  status: "not_started" | "generating" | "ready" | "user_editing" | "under_review";

  generatedContent: {
    text: string;
    wordCount: number;
    metadata: {
      plotPoint: string;
      incorporatedFeedback: string[];
      generationTimestamp: Date;
    };
  };

  actions: {
    generate(): void;              // Generate from plot point + feedback
    directEdit(): void;            // User manual editing
    promptAssistant(change: string): void;  // Ask AI for specific changes
    requestReview(): void;         // Get editor feedback
    acceptChapter(): void;         // Finalize and add to story
  };
}
```

### Editor Review Interface
```typescript
interface EditorReviewComponent {
  editorSuggestions: Array<{
    issue: string;
    suggestion: string;
    priority: "high" | "medium" | "low";
    selected: boolean;
  }>;

  actions: {
    acceptSelected(): void;        // Apply selected suggestions
    acceptAll(): void;             // Apply all suggestions
    rejectAll(): void;             // Ignore all suggestions
    customEdit(suggestion: string): void;  // Modify suggestion before applying
  };
}
```

**Layout**:
```
┌─────────────────────────────────────────────────┐
│ Chapter Creation Tab                            │
├─────────────────────────────────────────────────┤
│ Plot Point                                      │
│ ┌─────────────────────────────────────────────┐ │
│ │ Sarah discovers a hidden letter in the...  │ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│ [AI Flesh Out] [Reset]                         │
├─────────────────────────────────────────────────┤
│ Incorporated Feedback                           │
│ ┌─────────────────────────────────────────────┐ │
│ │ • Sarah (Action): "Carefully open letter"  │ │
│ │   [Remove]                                  │ │
│ │ • Consistency Rater: "Add tension"         │ │
│ │   [Remove]                                  │ │
│ └─────────────────────────────────────────────┘ │
├─────────────┬───────────────────────────────────┤
│ Agent List  │ Agent Feedback                    │
│ Characters: │                                   │
│ ☐ Sarah     │ (Click agent to get feedback)     │
│ ☐ John      │                                   │
│ ☐ Detective │ Sarah (Character)                 │
│             │ ┌───────────────────────────────┐ │
│ Raters:     │ │ Actions:                      │ │
│ ☐ Consistency│ │ • Carefully unfold the letter│ │
│ ☐ Flow      │ │ ☐ Accept                      │ │
│ ☐ Quality   │ │                               │ │
│             │ │ Dialog:                       │ │
│             │ │ • "This changes everything"   │ │
│             │ │ ☑ Accept                      │ │
│             │ │                               │ │
│             │ │ Emotions:                     │ │
│             │ │ • Shock mixed with excitement │ │
│             │ │ ☑ Accept                      │ │
│             │ └───────────────────────────────┘ │
│             │                                   │
│             │ User Changes: [                 ] │
│             │ [Suggest Changes] [Regenerate]    │
│             │ [Accept Selected]                 │
└─────────────┴───────────────────────────────────┘
│                                                 │
│ [Generate Chapter]                              │
│                                                 │
│ Generated Chapter                               │
│ ┌─────────────────────────────────────────────┐ │
│ │ Sarah's hand trembled as she unfolded the   │ │
│ │ letter. The paper was yellowed with age...  │ │
│ │                                             │ │
│ │ (Full chapter text - editable)              │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [Direct Edit] [Prompt Assistant for Changes]   │
│ [Request Editor Review]                         │
│                                                 │
│ Editor Suggestions                              │
│ ┌─────────────────────────────────────────────┐ │
│ │ ☑ Add more sensory detail in opening       │ │
│ │ ☑ Strengthen emotional reaction             │ │
│ │ ☐ Consider pacing in middle section         │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [Apply Selected] [Apply All] [Keep Iterating]  │
│ [Accept Chapter - Add to Story]                │
└─────────────────────────────────────────────────┘
```

## Data Storage Architecture

All data persisted to browser local storage:

```typescript
interface LocalStorageSchema {
  stories: Map<string, {
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

    characters: Map<string, Character>;
    raters: Map<string, Rater>;

    story: {
      summary: string;
      chapters: Chapter[];
    };

    chapterDrafts: Map<string, ChapterDraft>;

    metadata: {
      created: Date;
      lastModified: Date;
      version: string;
    };
  }>;
}
```

## Key UI/UX Features

### Auto-Save
- All changes automatically saved to local storage every 30 seconds
- Immediate save on tab switch
- Save indicator shows last save time

### AI Generation Indicators
- Loading spinners during AI generation
- Progress messages
- Ability to cancel long-running operations

### Responsive Design
- Desktop-first design
- Tablet support with optimized layouts
- Mobile support for viewing (limited editing)

### Accessibility
- Keyboard navigation for all features
- Screen reader support
- High contrast mode
- Font scaling support

## Performance Requirements

- Initial load: < 2 seconds
- Tab switching: < 100ms
- AI generation: Show progress, allow cancellation
- Local storage operations: < 50ms
- Character limit warnings before storage quota exceeded

## Error Handling

- Clear error messages for AI generation failures
- Recovery options for interrupted operations
- Validation messages for required fields
- Confirmation dialogs for destructive actions (delete character, delete chapter)

This simplified, tab-based interface provides users with direct control over every aspect of story creation while seamlessly integrating AI assistance throughout the creative process.
