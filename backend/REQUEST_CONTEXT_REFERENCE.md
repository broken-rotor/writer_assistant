# RequestContext Reference Guide

## Overview

The `RequestContext` object encapsulates all story state information from the frontend, providing a complete and self-contained representation for backend processing. It replaces the previous `StructuredContextContainer` with a richer, more comprehensive data structure that preserves all frontend information without transformation loss.

## Table of Contents

1. [Model Structure](#model-structure)
2. [Core Components](#core-components)
3. [Usage Examples](#usage-examples)
4. [Migration from StructuredContextContainer](#migration-from-structuredcontextcontainer)
5. [Best Practices](#best-practices)

## Model Structure

### RequestContext

**Location**: `app/models/request_context.py`

```python
class RequestContext(BaseModel):
    """
    Comprehensive context object encapsulating all story state from frontend.
    """
    
    # === CONFIGURATION ===
    configuration: StoryConfiguration = Field(
        description="System prompts and agent configuration"
    )
    
    # === WORLDBUILDING ===
    worldbuilding: WorldbuildingInfo = Field(
        description="Complete worldbuilding context and history"
    )
    
    # === CHARACTERS ===
    characters: List[CharacterDetails] = Field(
        default_factory=list,
        description="Complete character information and context"
    )
    
    # === STORY STRUCTURE ===
    story_outline: StoryOutline = Field(
        description="Complete story structure and outline"
    )
    
    # === CHAPTERS ===
    chapters: List[ChapterDetails] = Field(
        default_factory=list,
        description="Complete chapter content and feedback"
    )
    
    # === METADATA ===
    context_metadata: RequestContextMetadata = Field(
        description="Context processing metadata and optimization hints"
    )
```

**Key Features**:
- Complete story state preservation
- Rich character and chapter details
- Comprehensive feedback integration
- Conversation history tracking
- Hierarchical outline structure
- Extensive metadata for optimization

## Core Components

### 1. StoryConfiguration

Contains system prompts and agent configuration.

```python
class StoryConfiguration(BaseModel):
    system_prompts: SystemPrompts  # Agent-specific prompts
    raters: List[RaterConfig]      # Configured rater agents
    generation_preferences: Dict[str, Any]  # User preferences
```

**SystemPrompts Structure**:
```python
class SystemPrompts(BaseModel):
    main_prefix: str      # Main system prompt prefix
    main_suffix: str      # Main system prompt suffix
    assistant_prompt: str # Assistant agent prompt
    editor_prompt: str    # Editor agent prompt
```

### 2. WorldbuildingInfo

Complete worldbuilding context with conversation history.

```python
class WorldbuildingInfo(BaseModel):
    content: str                    # Main worldbuilding content
    chat_history: List[ChatMessage] # Conversation history
    key_elements: List[WorldElement] # Extracted key elements
```

**WorldElement Types**:
- `location`: Physical places in the story world
- `culture`: Cultural aspects and societies
- `magic_system`: Magical or supernatural systems
- `history`: Historical background and events
- `politics`: Political structures and conflicts
- `technology`: Technological level and devices

### 3. CharacterDetails

Comprehensive character information and context.

```python
class CharacterDetails(BaseModel):
    # Basic Info
    id: str
    name: str
    basic_bio: str
    
    # Demographics
    sex: str
    gender: str
    sexual_preference: str
    age: int
    
    # Appearance
    physical_appearance: str
    usual_clothing: str
    
    # Psychology
    personality: str
    motivations: str
    fears: str
    relationships: str
    
    # Story Context
    current_state: Dict[str, Any]
    recent_actions: List[str]
    goals: List[str]
    memories: List[str]
    
    # Metadata
    is_hidden: bool
    creation_source: Literal["user", "ai_generated", "imported"]
    last_modified: datetime
```

### 4. StoryOutline

Complete story structure and outline information.

```python
class StoryOutline(BaseModel):
    summary: str                        # Story summary
    status: str                         # Overall outline status
    content: str                        # Full outline text
    outline_items: List[OutlineItem]    # Structured outline items
    rater_feedback: List[OutlineFeedback] # Feedback on outline
    chat_history: List[ChatMessage]     # Development conversation
```

**OutlineItem Structure**:
```python
class OutlineItem(BaseModel):
    id: str
    type: Literal["chapter", "scene", "plot-point", "character-arc"]
    title: str
    description: str
    key_plot_items: List[str]
    order: int
    parent_id: Optional[str]  # For hierarchical structure
    involved_characters: List[str]
    status: Literal["draft", "reviewed", "approved"]
    word_count_estimate: Optional[int]
```

### 5. ChapterDetails

Complete chapter information with all feedback types.

```python
class ChapterDetails(BaseModel):
    # Basic Info
    id: str
    number: int
    title: str
    content: str
    
    # Plot Context
    plot_point: Optional[str]
    key_plot_items: List[str]
    
    # Feedback Integration
    incorporated_feedback: List[FeedbackItem]
    character_feedback: List[CharacterFeedbackItem]
    rater_feedback: List[RaterFeedbackItem]
    editor_suggestions: List[EditorSuggestion]
    
    # Metadata
    word_count: int
    created: datetime
    last_modified: datetime
```

### 6. RequestContextMetadata

Processing optimization metadata.

```python
class RequestContextMetadata(BaseModel):
    story_id: str
    story_title: str
    version: str
    created_at: datetime
    total_characters: int
    total_chapters: int
    total_word_count: int
    context_size_estimate: int
    processing_hints: Dict[str, Any]
```

## Usage Examples

### Creating a RequestContext

```python
from app.models.request_context import (
    RequestContext,
    StoryConfiguration,
    SystemPrompts,
    WorldbuildingInfo,
    CharacterDetails,
    StoryOutline,
    RequestContextMetadata
)
from datetime import datetime

# Create a basic RequestContext
context = RequestContext(
    configuration=StoryConfiguration(
        system_prompts=SystemPrompts(
            main_prefix="You are a creative writing assistant",
            main_suffix="Focus on character development",
            assistant_prompt="Help develop the story",
            editor_prompt="Review for quality and consistency"
        ),
        generation_preferences={
            "genre": "fantasy",
            "style": "descriptive"
        }
    ),
    worldbuilding=WorldbuildingInfo(
        content="A medieval fantasy world with magic and dragons"
    ),
    characters=[
        CharacterDetails(
            id="hero_001",
            name="Aria Stormwind",
            basic_bio="A young mage discovering her powers",
            creation_source="user",
            last_modified=datetime.now()
        )
    ],
    story_outline=StoryOutline(
        summary="A coming-of-age story about a young mage",
        status="draft",
        content="Chapter 1: The Discovery..."
    ),
    context_metadata=RequestContextMetadata(
        story_id="story_001",
        story_title="The Mage's Journey",
        version="1.0",
        created_at=datetime.now(),
        total_characters=1,
        total_chapters=0,
        total_word_count=0,
        context_size_estimate=1500
    )
)
```

### Accessing Context Data

```python
# Access configuration
system_prompts = context.configuration.system_prompts
main_prompt = system_prompts.main_prefix

# Access worldbuilding
world_content = context.worldbuilding.content
world_elements = context.worldbuilding.key_elements

# Access characters
for character in context.characters:
    print(f"Character: {character.name}")
    print(f"Bio: {character.basic_bio}")
    print(f"Current goals: {character.goals}")

# Access story structure
outline_summary = context.story_outline.summary
outline_items = context.story_outline.outline_items

# Access chapters
for chapter in context.chapters:
    print(f"Chapter {chapter.number}: {chapter.title}")
    print(f"Word count: {chapter.word_count}")
    
    # Access feedback
    for feedback in chapter.character_feedback:
        print(f"Character feedback from {feedback.character_name}")
        print(f"Suggested actions: {feedback.actions}")

# Access metadata
story_info = context.context_metadata
print(f"Story: {story_info.story_title}")
print(f"Total word count: {story_info.total_word_count}")
print(f"Processing hints: {story_info.processing_hints}")
```

### Working with Feedback

```python
# Access different types of feedback
chapter = context.chapters[0]

# Character feedback
for char_feedback in chapter.character_feedback:
    character_name = char_feedback.character_name
    actions = char_feedback.actions
    dialog = char_feedback.dialog
    emotions = char_feedback.emotions

# Rater feedback
for rater_feedback in chapter.rater_feedback:
    rater_name = rater_feedback.rater_name
    opinion = rater_feedback.opinion
    suggestions = rater_feedback.suggestions

# Editor suggestions
for suggestion in chapter.editor_suggestions:
    issue = suggestion.issue
    improvement = suggestion.suggestion
    priority = suggestion.priority
    is_selected = suggestion.selected
```

## Migration from StructuredContextContainer

The RequestContext replaces the previous StructuredContextContainer with a more comprehensive structure. Here's how the components map:

### Mapping Guide

| Old StructuredContextContainer | New RequestContext |
|-------------------------------|-------------------|
| `plot_elements` | `story_outline.outline_items` + `chapters[].key_plot_items` |
| `character_contexts` | `characters` (with expanded CharacterDetails) |
| `user_requests` | `configuration.generation_preferences` |
| `system_instructions` | `configuration.system_prompts` |
| `metadata` | `context_metadata` (greatly expanded) |

### Migration Example

**Old StructuredContextContainer**:
```python
# OLD
container = StructuredContextContainer(
    plot_elements=[
        PlotElement(
            id="scene_001",
            type="scene",
            content="Hero discovers magic",
            priority="high"
        )
    ],
    character_contexts=[
        CharacterContext(
            character_id="hero_001",
            character_name="Aria",
            current_state={"emotion": "excited"},
            goals=["Learn magic"]
        )
    ],
    user_requests=[
        UserRequest(
            content="Focus on character development",
            priority="medium"
        )
    ],
    system_instructions=[
        SystemInstruction(
            content="You are a fantasy writing assistant",
            priority="high"
        )
    ]
)
```

**New RequestContext**:
```python
# NEW
context = RequestContext(
    configuration=StoryConfiguration(
        system_prompts=SystemPrompts(
            main_prefix="You are a fantasy writing assistant",
            main_suffix="Focus on character development",
            assistant_prompt="Help develop the story",
            editor_prompt="Review content"
        ),
        generation_preferences={
            "focus": "character_development",
            "priority": "medium"
        }
    ),
    worldbuilding=WorldbuildingInfo(
        content="Fantasy world with magic"
    ),
    characters=[
        CharacterDetails(
            id="hero_001",
            name="Aria",
            basic_bio="Young mage",
            current_state={"emotion": "excited"},
            goals=["Learn magic"],
            creation_source="user",
            last_modified=datetime.now()
        )
    ],
    story_outline=StoryOutline(
        summary="Hero's journey to learn magic",
        status="draft",
        content="Story outline...",
        outline_items=[
            OutlineItem(
                id="scene_001",
                type="scene",
                title="Magic Discovery",
                description="Hero discovers magic",
                key_plot_items=["Discovery moment", "Initial reaction"],
                order=1,
                involved_characters=["Aria"],
                status="draft"
            )
        ]
    ),
    context_metadata=RequestContextMetadata(
        story_id="story_001",
        story_title="The Magic Discovery",
        version="1.0",
        created_at=datetime.now(),
        total_characters=1,
        total_chapters=0,
        total_word_count=0,
        context_size_estimate=2000
    )
)
```

## Best Practices

### 1. Context Construction

- Always provide complete `RequestContextMetadata` for processing optimization
- Include conversation histories for better context understanding
- Use appropriate `importance` levels for world elements
- Set realistic `word_count_estimate` values for outline items

### 2. Character Management

- Use descriptive `character_id` values (e.g., "protagonist_aria" not "char_1")
- Keep `current_state` updated with relevant emotional and physical states
- Include recent actions and memories for better character consistency
- Use `is_hidden` flag to exclude characters from certain processing

### 3. Feedback Integration

- Mark feedback as `incorporated` when applied to avoid duplication
- Use appropriate `priority` levels for feedback items
- Include `timestamp` information for feedback tracking
- Set `selected` flag for editor suggestions that should be applied

### 4. Performance Optimization

- Use `processing_hints` in metadata to guide backend optimization
- Provide accurate `context_size_estimate` for token management
- Include relevant `key_elements` in worldbuilding for focused context
- Use hierarchical `outline_items` with proper `parent_id` relationships

### 5. Data Consistency

- Ensure `character_id` values match between characters and outline items
- Keep `total_word_count` and `word_count` fields synchronized
- Update `last_modified` timestamps when making changes
- Maintain consistent `status` values across related components

### 6. Error Handling

- Validate required fields before creating RequestContext instances
- Use appropriate default values for optional fields
- Handle missing or invalid data gracefully in processing logic
- Log warnings for inconsistent or suspicious data patterns

## Advanced Usage

### Custom Processing Hints

```python
context_metadata = RequestContextMetadata(
    # ... other fields ...
    processing_hints={
        "optimization_level": "aggressive",
        "focus_areas": ["character_development", "world_building"],
        "token_budget": "high",
        "streaming_enabled": True,
        "cache_strategy": "aggressive"
    }
)
```

### Hierarchical Outline Structure

```python
outline_items = [
    OutlineItem(
        id="act_1",
        type="plot-point",
        title="Act 1: Setup",
        description="Introduction and setup",
        order=1,
        parent_id=None  # Top level
    ),
    OutlineItem(
        id="chapter_1",
        type="chapter",
        title="Chapter 1: The Beginning",
        description="Story opening",
        order=1,
        parent_id="act_1"  # Child of Act 1
    ),
    OutlineItem(
        id="scene_1_1",
        type="scene",
        title="Opening Scene",
        description="Character introduction",
        order=1,
        parent_id="chapter_1"  # Child of Chapter 1
    )
]
```

### Complex Character Relationships

```python
character = CharacterDetails(
    id="protagonist_aria",
    name="Aria Stormwind",
    relationships="Mentor: Master Eldrin (trusting), Rival: Kael (competitive), Friend: Luna (supportive)",
    current_state={
        "emotion": "determined",
        "location": "magic_academy",
        "mental_state": "focused_on_training",
        "physical_state": "tired_but_energized",
        "relationship_tensions": {
            "kael": "high",
            "eldrin": "low",
            "luna": "none"
        }
    },
    recent_actions=[
        "Completed advanced spell training",
        "Had argument with Kael about technique",
        "Received encouragement from Luna",
        "Studied late into the night"
    ],
    memories=[
        "First successful spell casting",
        "Master Eldrin's warning about overconfidence",
        "Kael's dismissive comment about her abilities",
        "Luna's promise to always support her"
    ]
)
```

This comprehensive RequestContext system provides a rich, flexible foundation for story development and AI-assisted writing, replacing the simpler StructuredContextContainer with a more powerful and complete representation of story state.
