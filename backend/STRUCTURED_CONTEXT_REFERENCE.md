# StructuredContextContainer Reference

## Overview

The `StructuredContextContainer` is the primary data model for passing context information to AI agents in the Writer Assistant system. It uses typed collections to provide strong type safety and better developer experience.

## Table of Contents

1. [Model Structure](#model-structure)
2. [Element Types](#element-types)
3. [Query Methods](#query-methods)
4. [Token Counting](#token-counting)
5. [Usage Patterns](#usage-patterns)
6. [Best Practices](#best-practices)

## Model Structure

### StructuredContextContainer

**Location**: `app/models/generation_models.py`

```python
class StructuredContextContainer(BaseModel):
    """Container for structured context with typed collections."""

    plot_elements: List[PlotElement] = Field(default_factory=list)
    character_contexts: List[CharacterContext] = Field(default_factory=list)
    user_requests: List[UserRequest] = Field(default_factory=list)
    system_instructions: List[SystemInstruction] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**Key Features**:
- Typed collections for better IDE support
- Default empty lists (no None values)
- Pydantic validation
- Serializable to JSON

## Element Types

### 1. PlotElement

Represents plot-related context information.

```python
class PlotElement(BaseModel):
    """Plot element in the story context."""

    element_id: Optional[str] = Field(default=None, alias="id")
    type: str  # e.g., "scene", "setup", "detail", "conflict"
    content: str
    priority: str = "medium"  # "high", "medium", or "low"
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**Common Types**:
- `"scene"` - Current scene description
- `"setup"` - Background/setup information
- `"detail"` - Additional world/plot details
- `"conflict"` - Conflict or tension points
- `"resolution"` - Resolution or conclusion points

**Priority Levels**:
- `"high"` - Critical plot points, must be included
- `"medium"` - Important but can be trimmed if needed
- `"low"` - Background information, first to be trimmed

**Tags**: Used for filtering and organization
- `["current_scene"]` - Current scene marker
- `["backstory"]` - Background information
- `["worldbuilding"]` - World-building details

**Example**:
```python
plot = PlotElement(
    element_id="plot_001",
    type="scene",
    content="The hero enters a dark, ancient forest filled with magical energy.",
    priority="high",
    tags=["current_scene", "forest", "magic"]
)
```

### 2. CharacterContext

Represents character state and information.

```python
class CharacterContext(BaseModel):
    """Character context for the current scene."""

    character_id: str
    character_name: str
    current_state: Optional[str] = None
    goals: List[str] = Field(default_factory=list)
    recent_actions: List[str] = Field(default_factory=list)
    memories: List[str] = Field(default_factory=list)
    personality_traits: List[str] = Field(default_factory=list)
    relationships: Dict[str, str] = Field(default_factory=dict)
```

**Fields Explained**:
- `character_id`: Unique identifier for the character
- `character_name`: Display name
- `current_state`: Current emotional/physical state
- `goals`: Character's current goals
- `recent_actions`: Recent actions taken
- `memories`: Important memories affecting current behavior
- `personality_traits`: Core personality traits
- `relationships`: Map of character_id/name to relationship description

**Example**:
```python
char = CharacterContext(
    character_id="hero",
    character_name="Aria",
    current_state="determined but cautious",
    goals=["Find the ancient artifact", "Save the kingdom"],
    recent_actions=["Drew sword", "Entered the forest"],
    memories=["Training with Master Orin", "Village attack"],
    personality_traits=["brave", "determined", "compassionate"],
    relationships={
        "mentor": "trusting and respectful",
        "villain": "hostile and wary"
    }
)
```

### 3. UserRequest

Represents user instructions or feedback.

```python
class UserRequest(BaseModel):
    """User request or instruction."""

    id: Optional[str] = None
    type: str  # e.g., "feedback", "instruction", "modification"
    content: str
    priority: str = "medium"  # "high", "medium", or "low"
    target: Optional[str] = None  # Target aspect (e.g., "dialogue", "description")
    context: Optional[str] = None  # Additional context
    timestamp: Optional[datetime] = None
```

**Common Types**:
- `"feedback"` - User feedback on generated content
- `"instruction"` - Specific user instruction
- `"modification"` - Request to modify something
- `"preference"` - User preference or style guideline

**Example**:
```python
request = UserRequest(
    id="user_001",
    type="feedback",
    content="Make the dialogue more natural and less formal",
    priority="high",
    target="dialogue",
    context="Characters should speak like modern fantasy heroes"
)
```

### 4. SystemInstruction

Represents system-level instructions or guidelines.

```python
class SystemInstruction(BaseModel):
    """System instruction for AI behavior."""

    id: Optional[str] = None
    type: str  # e.g., "behavior", "style", "constraint"
    content: str
    scope: str = "global"  # "global", "character", "scene", "chapter", "story"
    priority: str = "medium"  # "high", "medium", or "low"
    conditions: Dict[str, Any] = Field(default_factory=dict)
```

**Common Types**:
- `"behavior"` - Behavioral guidelines
- `"style"` - Writing style instructions
- `"constraint"` - Hard constraints or requirements
- `"format"` - Formatting requirements

**Scopes**:
- `"global"` - Applies to all agents and scenarios
- `"character"` - Character-specific instructions
- `"scene"` - Scene-level instructions
- `"chapter"` - Chapter-level instructions
- `"story"` - Story-wide instructions

**Example**:
```python
instruction = SystemInstruction(
    id="sys_001",
    type="behavior",
    content="Maintain consistent character voices and personalities throughout",
    scope="global",
    priority="high"
)
```

## Query Methods

The `StructuredContextContainer` provides convenient query methods:

### By Type

```python
# Get plot elements by type
scenes = container.get_plot_elements_by_type("scene")
setups = container.get_plot_elements_by_type("setup")

# Get user requests by type
feedback = container.get_user_requests_by_type("feedback")
instructions = container.get_user_requests_by_type("instruction")

# Get system instructions by scope
global_instructions = container.get_system_instructions_by_scope("global")
scene_instructions = container.get_system_instructions_by_scope("scene")
```

### By Priority

```python
# Get plot elements by priority
high_priority_plots = container.get_plot_elements_by_priority("high")
medium_priority_plots = container.get_plot_elements_by_priority("medium")

# Get all high-priority elements across all types
high_priority_all = container.get_high_priority_elements()
```

### By Tag

```python
# Get plot elements by tag
current_scene_elements = container.get_plot_elements_by_tag("current_scene")
backstory_elements = container.get_plot_elements_by_tag("backstory")
```

### By Character

```python
# Get character by ID
hero = container.get_character_context_by_id("hero")

# Get character by name
mentor = container.get_character_context_by_name("Master Orin")
```

## Token Counting

### Calculate Total Tokens

```python
from app.services.token_management.token_counter import TokenCounter

token_counter = TokenCounter()

# Calculate total tokens
total_tokens = container.calculate_total_tokens(token_counter)

# Get detailed token breakdown
breakdown = container.get_token_breakdown(token_counter)
# Returns: {
#     "plot_elements": 150,
#     "character_contexts": 200,
#     "user_requests": 50,
#     "system_instructions": 100,
#     "total": 500
# }
```

### Token Counting Details

The token counter uses `llama.cpp` tokenization for accuracy and assigns different overhead based on content type:

- **plot_elements**: `ContentType.NARRATIVE` (overhead: 5 tokens)
- **character_contexts**: `ContentType.CHARACTER_DESCRIPTION` (overhead: 10 tokens)
- **user_requests**: `ContentType.METADATA` (overhead: 3 tokens)
- **system_instructions**: `ContentType.SYSTEM_PROMPT` (overhead: 2 tokens)

## Usage Patterns

### Pattern 1: Building Context Incrementally

```python
container = StructuredContextContainer()

# Add plot elements
container.plot_elements.append(PlotElement(
    type="scene",
    content="Opening scene",
    priority="high"
))

# Add characters
container.character_contexts.append(CharacterContext(
    character_id="hero",
    character_name="Hero"
))

# Add user requests
container.user_requests.append(UserRequest(
    type="instruction",
    content="Focus on atmosphere",
    priority="high"
))
```

### Pattern 2: Creating Complete Context

```python
container = StructuredContextContainer(
    plot_elements=[
        PlotElement(...),
        PlotElement(...)
    ],
    character_contexts=[
        CharacterContext(...)
    ],
    user_requests=[
        UserRequest(...)
    ],
    system_instructions=[
        SystemInstruction(...)
    ]
)
```

### Pattern 3: Filtering Before Processing

```python
# Get high-priority elements only
high_priority = container.get_high_priority_elements()

# Create filtered container
filtered_container = StructuredContextContainer(
    plot_elements=high_priority.get("plot_elements", []),
    character_contexts=high_priority.get("character_contexts", []),
    user_requests=high_priority.get("user_requests", []),
    system_instructions=high_priority.get("system_instructions", [])
)
```

### Pattern 4: Token Budget Management

```python
from app.services.token_management.token_counter import TokenCounter

token_counter = TokenCounter()
max_tokens = 8000

# Check if under budget
total_tokens = container.calculate_total_tokens(token_counter)

if total_tokens > max_tokens:
    # Get high-priority only to reduce tokens
    high_priority = container.get_high_priority_elements()

    # Or manually filter
    container.plot_elements = [
        p for p in container.plot_elements
        if p.priority in ["high", "medium"]
    ]
```

## Best Practices

### 1. Use Meaningful IDs

```python
# ✅ Good
PlotElement(element_id="forest_entrance_scene")

# ❌ Bad
PlotElement(element_id="p1")
```

### 2. Set Appropriate Priorities

```python
# ✅ Good - Critical information is high priority
PlotElement(
    content="Hero discovers villain's weakness",
    priority="high"
)

# ❌ Bad - Everything high priority
PlotElement(
    content="Background detail about forest",
    priority="high"  # Should be "low"
)
```

### 3. Use Tags for Organization

```python
# ✅ Good - Descriptive tags
PlotElement(
    content="...",
    tags=["current_scene", "conflict", "turning_point"]
)

# ❌ Bad - No tags
PlotElement(
    content="...",
    tags=[]
)
```

### 4. Keep Content Focused

```python
# ✅ Good - One concept per element
PlotElement(
    type="scene",
    content="Hero enters forest"
)
PlotElement(
    type="detail",
    content="Forest has ancient magic"
)

# ❌ Bad - Multiple concepts mixed
PlotElement(
    content="Hero enters forest which has ancient magic and meets mentor"
)
```

### 5. Use Appropriate Scopes

```python
# ✅ Good - Scope matches instruction
SystemInstruction(
    content="Maintain consistent character voice",
    scope="global"  # Applies everywhere
)

SystemInstruction(
    content="Use vivid imagery in this scene",
    scope="scene"  # Applies to current scene only
)

# ❌ Bad - Wrong scope
SystemInstruction(
    content="Use vivid imagery in this scene",
    scope="global"  # Would apply everywhere
)
```

### 6. Validate Character Relationships

```python
# ✅ Good - Symmetric relationships
container.character_contexts = [
    CharacterContext(
        character_id="hero",
        relationships={"mentor": "trusting"}
    ),
    CharacterContext(
        character_id="mentor",
        relationships={"hero": "protective"}
    )
]
```

### 7. Use Token Counting

```python
# ✅ Good - Check token count before processing
token_counter = TokenCounter()
tokens = container.calculate_total_tokens(token_counter)

if tokens > max_tokens:
    # Handle overflow
    pass

# ❌ Bad - Process without checking
formatted = manager.process_context_for_agent(container, config)
# Might exceed token limits
```

## Common Patterns

### Empty Container

```python
# Create empty container
container = StructuredContextContainer()

# All collections are empty lists (not None)
assert container.plot_elements == []
assert container.character_contexts == []
```

### Validation

```python
# Pydantic validates on creation
try:
    container = StructuredContextContainer(
        plot_elements="not a list"  # Wrong type!
    )
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Serialization

```python
# To dict
data = container.model_dump()

# To JSON
json_str = container.model_dump_json()

# From dict
container = StructuredContextContainer(**data)

# From JSON
container = StructuredContextContainer.model_validate_json(json_str)
```

## Performance Tips

### 1. Batch Operations

```python
# ✅ Good - Batch append
container.plot_elements.extend([
    PlotElement(...),
    PlotElement(...),
    PlotElement(...)
])

# ❌ Bad - Individual appends
for element in elements:
    container.plot_elements.append(element)
```

### 2. Filter Early

```python
# ✅ Good - Filter before processing
high_priority = container.get_high_priority_elements()
process_context(high_priority)

# ❌ Bad - Process everything then filter
process_context(container)  # Wastes tokens
```

### 3. Reuse Token Counter

```python
# ✅ Good - Reuse instance
token_counter = TokenCounter()
for container in containers:
    tokens = container.calculate_total_tokens(token_counter)

# ❌ Bad - Create new instance each time
for container in containers:
    tokens = container.calculate_total_tokens(TokenCounter())
```

## See Also

- [Migration Guide](STRUCTURED_CONTEXT_MIGRATION_GUIDE.md)
- [ContextManager Reference](../app/services/context_manager.py)
- [Test Examples](../tests/test_context_manager_newmodel.py)
- [Model Definitions](../app/models/generation_models.py)
