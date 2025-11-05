# Phase 6: Test Migration Analysis

## Test Files Found

### 1. Files Using Old Model (Need Updates)
- `backend/tests/test_context_manager.py` - Uses old model + ContextSummarizer (OBSOLETE)
- `backend/tests/unit/test_context_manager.py` - Uses old model with conversion helpers
- `backend/tests/integration/test_full_context_pipeline.py` - Unknown (needs inspection)
- `backend/tests/integration/test_structured_context_api.py` - Unknown (needs inspection)

### 2. Files Testing Legacy Models (Keep As-Is)
- `backend/tests/test_context_models.py` - Specifically tests old model types

### 3. Files Already Using New Model (No Changes Needed)
- `backend/tests/test_generation_models.py` - Already tests new model

## Analysis

### backend/tests/test_context_manager.py
**Status**: OBSOLETE

**Issues**:
1. Tests `ContextSummarizer` class - REMOVED in Phase 3
2. Tests old `_trim_by_priority()` method - signature changed
3. Uses `StructuredContextContainer(elements=[...])` - old model format
4. Tests methods that no longer exist

**Recommendation**:
- Mark as deprecated/obsolete
- Create new test file `test_context_manager_new.py` for new model testing
- Or completely rewrite to test new model behavior

### backend/tests/test_context_models.py
**Status**: KEEP AS-IS

**Reason**:
- This file explicitly tests the legacy model from `context_models.py`
- The legacy model still exists (will be deprecated in Phase 8)
- These tests ensure the legacy model continues to work for backwards compatibility
- No changes needed

### backend/tests/test_generation_models.py
**Status**: GOOD - NO CHANGES NEEDED

**Coverage**:
- Tests new `StructuredContextContainer` with typed collections
- Tests `PlotElement`, `CharacterContext`, `UserRequest`, `SystemInstruction`
- Tests request/response models with structured context support

### backend/tests/unit/test_context_manager.py
**Status**: NEEDS UPDATES

**Issues**:
1. Uses `_create_context_container_from_scenario()` helper that creates old model objects
2. Converts ContextItem to old model element types
3. Tests may be using old ContextManager API

**Recommendation**:
- Update helper methods to create new model objects
- Ensure tests use new ContextManager API

## Phase 6 Implementation Plan

### Option A: Minimal Update (Recommended)

1. **Create new test file**: `backend/tests/test_context_manager_newmodel.py`
   - Tests for new ContextManager with new model
   - Tests for ContextFormatter with Dict[str, List] format
   - Tests token budget management with TokenCounter

2. **Mark obsolete**: `backend/tests/test_context_manager.py`
   - Add comment marking it as deprecated
   - Add skip decorator to all tests
   - Keep file for reference

3. **Update unit tests**: `backend/tests/unit/test_context_manager.py`
   - Update `_create_context_container_from_scenario()` to use new model
   - Verify tests still pass with new model

4. **Validate integration tests**: Check if they need updates

### Option B: Complete Rewrite

1. Delete `backend/tests/test_context_manager.py`
2. Create comprehensive new test suite
3. Update all unit and integration tests

**Chosen**: Option A - Less disruptive, maintains legacy test coverage

## Test Coverage Gaps

After migration, we should have tests for:

1. **New ContextManager** (test_context_manager_newmodel.py):
   - ✅ Filtering typed collections by agent/phase
   - ✅ Priority-based sorting of typed collections
   - ✅ Token budget management with TokenCounter
   - ✅ ContextFormatter with new model

2. **Legacy ContextManager** (test_context_models.py):
   - ✅ Old model elements (keep existing tests)

3. **Integration** (integration tests):
   - ❓ End-to-end processing with new model
   - ❓ API endpoints with structured context

## Files to Create/Modify

### Create:
1. `backend/tests/test_context_manager_newmodel.py` - New model tests

### Modify:
1. `backend/tests/test_context_manager.py` - Mark as deprecated
2. `backend/tests/unit/test_context_manager.py` - Update helpers
3. Integration test files (if needed)

### Keep As-Is:
1. `backend/tests/test_context_models.py` - Legacy model tests
2. `backend/tests/test_generation_models.py` - New model tests (already good)
