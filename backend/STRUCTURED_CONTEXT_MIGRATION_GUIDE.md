# StructuredContextContainer Migration Guide

## Overview

This document explains the migration from the old `StructuredContextContainer` model to the new typed collections model. This migration was completed across 8 phases to eliminate dual implementations and improve type safety.

## Table of Contents

1. [Background](#background)
2. [What Changed](#what-changed)
3. [Migration Timeline](#migration-timeline)
4. [Developer Guide](#developer-guide)
5. [API Changes](#api-changes)
6. [Testing Changes](#testing-changes)
7. [Troubleshooting](#troubleshooting)

## Background

### Why Migrate?

The original implementation had **two different** `StructuredContextContainer` classes:

1. **Old Model** (`app/models/context_models.py`):
   - Generic list of `BaseContextElement` objects
   - Lost type information
   - Required complex filtering and type checking
   - Used numeric priorities (0.0-1.0 floats)

2. **New Model** (`app/models/generation_models.py`):
   - Typed collections (`PlotElement`, `CharacterContext`, etc.)
   - Better type safety and IDE support
   - String priorities ("high", "medium", "low")
   - More maintainable

### Problems with Dual Implementation

- **Conversion Overhead**: Every request required translation between models
- **Maintenance Burden**: Changes needed in two places
- **Type Safety Issues**: Lost typing information in conversions
- **Code Duplication**: Similar logic implemented twice
- **Confusion**: Developers unsure which model to use

## What Changed

### Model Structure

#### Old Model (Deprecated)
```python
from app.models.context_models import (
    StructuredContextContainer,
    BaseContextElement,
    StoryContextElement,
    CharacterContextElement,
    UserContextElement,
    SystemContextElement
)

# Generic list of elements
container = StructuredContextContainer(
    elements=[
        StoryContextElement(...),
        CharacterContextElement(...),
        UserContextElement(...),
        SystemContextElement(...)
    ]
)

# Numeric priorities
element = StoryContextElement(
    ...,
    metadata=ContextMetadata(priority=0.8)  # Float 0.0-1.0
)
```

#### New Model (Current)
```python
from app.models.generation_models import (
    StructuredContextContainer,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction
)

# Typed collections
container = StructuredContextContainer(
    plot_elements=[PlotElement(...)],
    character_contexts=[CharacterContext(...)],
    user_requests=[UserRequest(...)],
    system_instructions=[SystemInstruction(...)]
)

# String priorities
element = PlotElement(
    ...,
    priority="high"  # String: "high", "medium", or "low"
)
```

### Priority System

| Old Model | New Model |
|-----------|-----------|
| `priority=0.9` | `priority="high"` |
| `priority=0.5` | `priority="medium"` |
| `priority=0.2` | `priority="low"` |

### Key Differences

| Aspect | Old Model | New Model |
|--------|-----------|-----------|
| **Structure** | `List[BaseContextElement]` | `Dict[str, List]` with typed collections |
| **Type Safety** | Minimal (base class only) | Strong (specific types) |
| **Priorities** | Float 0.0-1.0 | String "high"/"medium"/"low" |
| **Filtering** | Type checking at runtime | Type-safe at compile time |
| **IDE Support** | Limited autocomplete | Full type hints |
| **Model Location** | `context_models.py` | `generation_models.py` |

## Migration Timeline

### Phase 1: Extend New Model
**Status**: ✅ Complete (Commit: 0a962dd)

- Added query methods to new model
- Added token counting with TokenCounter
- Made new model feature-complete

### Phase 2: Refactor ContextManager
**Status**: ✅ Complete (Commit: 4d9b458)

- Updated ContextManager to use new model natively
- Changed from `List[BaseContextElement]` to `Dict[str, List]`
- Integrated TokenCounter for accurate token counting

### Phase 3: Remove Old Methods
**Status**: ✅ Complete (Commit: 4be8448)

- Removed ContextSummarizer class
- Removed old formatting methods
- File reduced from 955 to 806 lines

### Phase 4: Update ContextStateManager
**Status**: ✅ Complete (Commit: b9e3a33)

- Updated imports to use new model
- State serialization now uses typed collections

### Phase 5: Remove Conversion Function
**Status**: ✅ Complete (Commit: 26c0bcf)

- Removed `convert_api_to_legacy_context()` function
- Eliminated translation layer
- File reduced from 763 to 660 lines

### Phase 6: Update Tests
**Status**: ✅ Complete (Commit: 63db06f)

- Created new test suite (`test_context_manager_newmodel.py`)
- Deprecated old tests
- 25+ tests for new model

### Phase 7: Update Documentation
**Status**: ✅ Complete (Current phase)

- Created migration guide
- Updated README
- Documented new model usage

### Phase 8: Deprecate Old Model
**Status**: 🔄 Pending

- Mark old model as deprecated
- Add deprecation warnings
- Plan removal timeline

## Developer Guide

### Using the New Model

#### Creating a StructuredContextContainer

```python
from app.models.generation_models import (
    StructuredContextContainer,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction
)

# Create container with typed collections
container = StructuredContextContainer(
    plot_elements=[
        PlotElement(
            element_id="plot_001",
            type="scene",
            content="The hero enters the dark forest",
            priority="high",
            tags=["current_scene", "forest"]
        ),
        PlotElement(
            element_id="plot_002",
            type="setup",
            content="Background information",
            priority="medium",
            tags=["background"]
        )
    ],
    character_contexts=[
        CharacterContext(
            character_id="hero",
            character_name="Aria",
            current_state="determined",
            goals=["Find artifact", "Save kingdom"],
            recent_actions=["Drew sword", "Entered forest"],
            memories=["Training with mentor"],
            personality_traits=["brave", "determined"],
            relationships={"mentor": "trusting"}
        )
    ],
    user_requests=[
        UserRequest(
            id="user_001",
            type="feedback",
            content="Add more sensory details",
            priority="high",
            target="description"
        )
    ],
    system_instructions=[
        SystemInstruction(
            id="sys_001",
            type="behavior",
            content="Maintain character consistency",
            scope="global",
            priority="high"
        )
    ]
)
```

#### Processing Context with ContextManager

```python
from app.services.context_manager import ContextManager
from app.models.context_models import (
    ContextProcessingConfig,
    AgentType,
    ComposePhase
)

# Create manager
manager = ContextManager()

# Create configuration
config = ContextProcessingConfig(
    target_agent=AgentType.WRITER,
    current_phase=ComposePhase.CHAPTER_DETAIL,
    max_tokens=8000,
    summarization_threshold=6000,
    prioritize_recent=True,
    include_relationships=True
)

# Process context
formatted_context, metadata = manager.process_context_for_agent(
    container, config
)

# Use formatted context
print(formatted_context)
print(f"Tokens used: {metadata['final_token_count']}")
```

#### Querying the Container

```python
# Get high-priority plot elements
high_priority_plots = container.get_plot_elements_by_priority("high")

# Get plot elements by type
scenes = container.get_plot_elements_by_type("scene")

# Get character by ID
char = container.get_character_context_by_id("hero")

# Get all high-priority elements
high_priority_all = container.get_high_priority_elements()

# Calculate total tokens
total_tokens = container.calculate_total_tokens(token_counter)
```

### ContextManager API

#### Main Methods

```python
# Process context for an agent
formatted_context, metadata = manager.process_context_for_agent(
    context_container=container,
    config=processing_config
)

# Process with state management
formatted_context, metadata = manager.process_context_with_state(
    context_container=container,
    config=processing_config,
    context_state=serialized_state,  # Optional
    story_id="story_123"              # Optional
)
```

#### Internal Methods (for advanced use)

```python
# Filter by agent and phase
collections = manager._filter_elements_for_agent_and_phase(
    container, AgentType.WRITER, ComposePhase.CHAPTER_DETAIL
)
# Returns: Dict[str, List] with keys:
# - plot_elements
# - character_contexts
# - user_requests
# - system_instructions

# Sort by priority
sorted_collections = manager._sort_elements_by_priority(
    collections, prioritize_recent=True
)

# Apply token budget
final_collections, was_summarized = manager._apply_token_budget(
    collections, max_tokens=8000, summarization_threshold=6000
)

# Count tokens
token_count = manager._count_collection_tokens(collections)
```

### Token Budget Management

The new system uses **priority-based trimming** instead of text summarization:

```python
# When token count exceeds budget:
# 1. High-priority system instructions (kept first)
# 2. High-priority plot elements
# 3. Character contexts (always included if possible)
# 4. High-priority user requests
# 5. Medium-priority items (if room remains)
# 6. Low-priority items (discarded during trimming)
```

**Note**: Unlike the old system, the new implementation does **not** compress or summarize text. Elements are either kept intact or discarded entirely.

## API Changes

### Request Models

All request models now use the new `StructuredContextContainer`:

```python
# Character Feedback
request = CharacterFeedbackRequest(
    structured_context=container,  # New model!
    plotPoint="Scene description"
)

# Chapter Generation
request = GenerateChapterRequest(
    structured_context=container,  # New model!
    # ... other fields
)

# Rater Feedback
request = RaterFeedbackRequest(
    structured_context=container,  # New model!
    # ... other fields
)

# Editor Review
request = EditorReviewRequest(
    structured_context=container,  # New model!
    # ... other fields
)
```

### Response Models

Response models include context metadata:

```python
response = CharacterFeedbackResponse(
    actions="...",
    dialog="...",
    context_metadata=ContextMetadata(
        total_elements=10,
        processing_applied=True,
        processing_mode="structured",
        optimization_level="moderate"
    )
)
```

## Testing Changes

### New Test Suite

Use `test_context_manager_newmodel.py` for new model tests:

```python
from app.models.generation_models import (
    StructuredContextContainer,
    PlotElement,
    CharacterContext
)

def test_context_processing():
    container = StructuredContextContainer(
        plot_elements=[PlotElement(...)],
        character_contexts=[CharacterContext(...)]
    )

    config = ContextProcessingConfig(...)
    formatted, metadata = manager.process_context_for_agent(
        container, config
    )

    assert isinstance(formatted, str)
    assert metadata["target_agent"] == "writer"
```

### Deprecated Tests

Tests in `test_context_manager.py` are deprecated and skipped:

```python
# These tests use old model and are skipped:
# - TestContextManager
# - TestContextSummarizer
# - TestContextFormatter (old version)

# Use new tests instead:
# - TestContextManagerNewModel
# - TestContextFormatterNewModel
```

## Troubleshooting

### Common Issues

#### Type Errors

**Problem**: Getting type errors with context container

```python
TypeError: 'PlotElement' object is not subscriptable
```

**Solution**: Use new model with typed collections:
```python
# ❌ Old way
container = StructuredContextContainer(elements=[...])

# ✅ New way
container = StructuredContextContainer(
    plot_elements=[...],
    character_contexts=[...]
)
```

#### Priority Value Errors

**Problem**: Priority not working as expected

```python
# ❌ Old way (numeric)
PlotElement(priority=0.8)

# ✅ New way (string)
PlotElement(priority="high")
```

#### Import Errors

**Problem**: Can't import StructuredContextContainer

```python
# ❌ Old import
from app.models.context_models import StructuredContextContainer

# ✅ New import
from app.models.generation_models import StructuredContextContainer
```

#### Missing Conversion Function

**Problem**: Code looking for `convert_api_to_legacy_context()`

**Solution**: This function was removed in Phase 5. Use new model directly:

```python
# ❌ Old way
legacy_container = convert_api_to_legacy_context(api_container)

# ✅ New way
# Pass new model directly to ContextManager
formatted, metadata = manager.process_context_for_agent(
    api_container, config
)
```

### Migration Checklist

When updating code to use new model:

- [ ] Update imports to use `generation_models.py`
- [ ] Change `elements=[]` to typed collections
- [ ] Convert numeric priorities to strings
- [ ] Remove any conversion function calls
- [ ] Update tests to use new model
- [ ] Use `Dict[str, List]` instead of `List[BaseContextElement]`
- [ ] Verify token counting uses TokenCounter
- [ ] Check formatting methods use new API

## Benefits of New Model

### 1. Type Safety
- Strong typing throughout
- IDE autocomplete and type hints
- Catch errors at development time

### 2. Performance
- No conversion overhead
- Direct use of typed collections
- Faster filtering and sorting

### 3. Maintainability
- Single source of truth
- Clearer code structure
- Easier to understand and modify

### 4. Developer Experience
- Better IDE support
- More intuitive API
- Self-documenting code

## Further Reading

- **Phase Documentation**: See `PHASE1_COMPLETE.md` through `PHASE6_COMPLETION.md`
- **Model Reference**: `app/models/generation_models.py`
- **Manager Reference**: `app/services/context_manager.py`
- **Test Examples**: `tests/test_context_manager_newmodel.py`

## Support

If you encounter issues during migration:

1. Check this guide's troubleshooting section
2. Review phase completion documents
3. Examine test examples in `test_context_manager_newmodel.py`
4. Consult the model definitions in `generation_models.py`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-XX | Initial migration guide |

## Appendix: Complete Example

Here's a complete example of using the new model:

```python
from app.models.generation_models import (
    StructuredContextContainer,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction
)
from app.services.context_manager import ContextManager
from app.models.context_models import (
    ContextProcessingConfig,
    AgentType,
    ComposePhase
)

# 1. Create structured context
context = StructuredContextContainer(
    plot_elements=[
        PlotElement(
            element_id="p1",
            type="scene",
            content="Hero enters forest",
            priority="high",
            tags=["current"]
        )
    ],
    character_contexts=[
        CharacterContext(
            character_id="c1",
            character_name="Hero",
            current_state="determined",
            goals=["Find artifact"],
            personality_traits=["brave"]
        )
    ],
    user_requests=[
        UserRequest(
            id="u1",
            type="instruction",
            content="Add sensory details",
            priority="high"
        )
    ],
    system_instructions=[
        SystemInstruction(
            id="s1",
            type="behavior",
            content="Be consistent",
            scope="global",
            priority="high"
        )
    ]
)

# 2. Create configuration
config = ContextProcessingConfig(
    target_agent=AgentType.WRITER,
    current_phase=ComposePhase.CHAPTER_DETAIL,
    max_tokens=8000
)

# 3. Process context
manager = ContextManager()
formatted_text, metadata = manager.process_context_for_agent(
    context, config
)

# 4. Use results
print(f"Formatted Context:\\n{formatted_text}")
print(f"\\nMetadata: {metadata}")
print(f"Elements processed: {metadata['final_element_count']}")
print(f"Was trimmed: {metadata.get('was_summarized', False)}")
```

This example demonstrates the complete workflow from creating a structured context to processing it for an agent.
