# DEPRECATION NOTICE: Old StructuredContextContainer Model

## Status: DEPRECATED

**Effective Date**: January 2025
**Removal Target**: Version 3.0 (TBD)
**Severity**: HIGH - Affects core context management system

## Summary

The old `StructuredContextContainer` and related element types in `app/models/context_models.py` are **DEPRECATED** and will be removed in a future version.

All code should migrate to the new typed collections model in `app/models/generation_models.py`.

## Deprecated Classes

The following classes in `app/models/context_models.py` are deprecated:

| Deprecated Class | Replacement | Notes |
|-----------------|-------------|-------|
| `StructuredContextContainer` | `generation_models.StructuredContextContainer` | Use typed collections |
| `BaseContextElement` | No direct replacement | Use typed collection items |
| `SystemContextElement` | `generation_models.SystemInstruction` | Direct replacement |
| `StoryContextElement` | `generation_models.PlotElement` | Direct replacement |
| `CharacterContextElement` | `generation_models.CharacterContext` | Direct replacement |
| `UserContextElement` | `generation_models.UserRequest` | Direct replacement |
| `PhaseContextElement` | `SystemInstruction` or `PlotElement` | Choose appropriate type |
| `ConversationContextElement` | `SystemInstruction` or `PlotElement` | Choose appropriate type |
| `ContextMetadata` | Element-level fields | Use priority/metadata fields |
| `ContextRelationship` | `CharacterContext.relationships` | For character relationships |

## Reasons for Deprecation

### 1. Type Safety Issues
- Generic `List[BaseContextElement]` lost type information
- Required runtime type checking
- Poor IDE support and autocomplete

### 2. Maintenance Burden
- Dual implementation required conversion functions
- Changes needed in two places
- Confusing for developers

### 3. Performance
- Conversion overhead on every request
- Complex filtering logic
- Inefficient priority management

### 4. Developer Experience
- Unclear which model to use
- Numeric priorities (0.0-1.0) unintuitive
- Generic structure hard to understand

## Migration Path

### Old Code (DEPRECATED)
```python
from app.models.context_models import (
    StructuredContextContainer,
    StoryContextElement,
    CharacterContextElement,
    UserContextElement,
    SystemContextElement,
    ContextMetadata
)

# Creating container
container = StructuredContextContainer(
    elements=[
        StoryContextElement(
            id="plot1",
            type=ContextType.PLOT_OUTLINE,
            content="Plot content",
            metadata=ContextMetadata(priority=0.8)  # Numeric priority
        ),
        CharacterContextElement(
            id="char1",
            type=ContextType.CHARACTER_PROFILE,
            content="Character info",
            character_id="hero",
            character_name="Hero"
        )
    ]
)
```

### New Code (CURRENT)
```python
from app.models.generation_models import (
    StructuredContextContainer,
    PlotElement,
    CharacterContext,
    UserRequest,
    SystemInstruction
)

# Creating container with typed collections
container = StructuredContextContainer(
    plot_elements=[
        PlotElement(
            element_id="plot1",
            type="scene",
            content="Plot content",
            priority="high"  # String priority
        )
    ],
    character_contexts=[
        CharacterContext(
            character_id="hero",
            character_name="Hero",
            current_state="determined",
            goals=["Find artifact"],
            personality_traits=["brave"]
        )
    ],
    user_requests=[],
    system_instructions=[]
)
```

## Timeline

| Date | Event |
|------|-------|
| **January 2025** | Deprecation warnings added |
| **Phase 1-7** | Migration completed for all core components |
| **Phase 8** | Deprecation notices added (current) |
| **TBD** | Removal from codebase (version 3.0+) |

## Migration Resources

### Documentation
- **Migration Guide**: `backend/STRUCTURED_CONTEXT_MIGRATION_GUIDE.md`
- **API Reference**: `backend/STRUCTURED_CONTEXT_REFERENCE.md`
- **Backend README**: `backend/README.md` (Structured Context System section)

### Phase Documentation
- `backend/PHASE1_COMPLETE.md` - Extended new model
- `backend/PHASE2_PROGRESS.md` - Refactored ContextManager
- `backend/PHASE4_VALIDATION.md` - Updated ContextStateManager
- `backend/PHASE5_COMPLETION.md` - Removed conversion functions
- `backend/PHASE6_COMPLETION.md` - Updated tests
- `backend/PHASE7_COMPLETION.md` - Documentation

### Code Examples
- **New Test Suite**: `backend/tests/test_context_manager_newmodel.py`
- **New Model Tests**: `backend/tests/test_generation_models.py`

## Components Already Migrated

The following components have been migrated to the new model:

✅ **Core Services**:
- `app/services/context_manager.py` (Phase 2)
- `app/services/context_session_manager.py` (Phase 4)
- `app/services/unified_context_processor.py` (Phase 5)

✅ **Tests**:
- `tests/test_context_manager_newmodel.py` (Phase 6)
- `tests/test_generation_models.py` (existing)

✅ **Documentation**:
- Migration guide (Phase 7)
- API reference (Phase 7)
- README updates (Phase 7)

## Components Using Deprecated Model

### Legacy Tests
- `tests/test_context_models.py` - Tests old model (kept for backward compat)
- `tests/test_context_manager.py` - Deprecated, skipped in Phase 6

### Note
These legacy tests will be removed when the old model is removed.

## What You Need to Do

### If You're Using the Old Model

1. **Update Imports**
   ```python
   # OLD
   from app.models.context_models import StructuredContextContainer

   # NEW
   from app.models.generation_models import StructuredContextContainer
   ```

2. **Change Structure**
   ```python
   # OLD
   container = StructuredContextContainer(elements=[...])

   # NEW
   container = StructuredContextContainer(
       plot_elements=[...],
       character_contexts=[...],
       user_requests=[...],
       system_instructions=[...]
   )
   ```

3. **Update Priorities**
   ```python
   # OLD
   priority=0.8  # Float 0.0-1.0

   # NEW
   priority="high"  # String: "high", "medium", "low"
   ```

4. **Update Element Types**
   ```python
   # OLD
   StoryContextElement(...)
   CharacterContextElement(...)
   UserContextElement(...)
   SystemContextElement(...)

   # NEW
   PlotElement(...)
   CharacterContext(...)
   UserRequest(...)
   SystemInstruction(...)
   ```

### Migration Checklist

- [ ] Update all imports to use `generation_models`
- [ ] Change `elements=[]` to typed collections
- [ ] Convert numeric priorities to strings
- [ ] Remove conversion function calls
- [ ] Update tests to use new model
- [ ] Update type hints to use new types
- [ ] Test with deprecation warnings enabled
- [ ] Review migration guide for edge cases

## Deprecation Warnings

When you import or use the deprecated classes, you will see warnings:

```
DeprecationWarning: app.models.context_models.StructuredContextContainer and related classes are deprecated.
Use app.models.generation_models.StructuredContextContainer with typed collections instead.
See backend/STRUCTURED_CONTEXT_MIGRATION_GUIDE.md for migration instructions.
```

These warnings are shown:
- When the module is imported
- In the docstrings of deprecated classes
- At runtime (via Python warnings module)

## Benefits of Migrating

### Type Safety
- Strong typing throughout
- IDE autocomplete and type hints
- Catch errors at development time

### Performance
- No conversion overhead
- Direct use of typed collections
- Faster filtering and sorting

### Maintainability
- Single source of truth
- Clearer code structure
- Easier to understand and modify

### Developer Experience
- Better IDE support
- More intuitive API
- Self-documenting code

## Support

### Questions or Issues?

1. **Read the Migration Guide**: `backend/STRUCTURED_CONTEXT_MIGRATION_GUIDE.md`
2. **Check the Reference**: `backend/STRUCTURED_CONTEXT_REFERENCE.md`
3. **Review Examples**: `tests/test_context_manager_newmodel.py`
4. **Consult Phase Docs**: `backend/PHASE*_*.md`

### Common Issues

See the **Troubleshooting** section in `STRUCTURED_CONTEXT_MIGRATION_GUIDE.md` for:
- Type errors
- Priority value errors
- Import errors
- Missing conversion function errors

## Version Compatibility

| Version | Old Model | New Model | Status |
|---------|-----------|-----------|--------|
| 2.x | ✅ Supported (deprecated) | ✅ Supported | Current |
| 3.0+ | ❌ Removed | ✅ Supported | Future |

## Contact

For questions about the deprecation or migration:
- Review documentation in `backend/` directory
- Check test examples
- Consult phase completion documents

---

**Last Updated**: January 2025
**Deprecation Phase**: 8 of 8
**Status**: Deprecation notices complete, removal pending
