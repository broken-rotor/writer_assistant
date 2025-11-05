#!/usr/bin/env python3
"""
Validation script for Phase 4: ContextStateManager migration to new model.

This script validates that:
1. Module imports successfully
2. ContextStateManager can be created
3. Initial state can be created with new model
4. State serialization/deserialization works with new model
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def validate_imports():
    """Validate that all imports work correctly."""
    print("✓ Testing imports...")
    try:
        from app.services.context_session_manager import (
            ContextStateManager,
            ContextState,
            get_context_state_manager
        )
        from app.models.generation_models import StructuredContextContainer
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def validate_structure():
    """Validate that the classes have expected structure."""
    print("\n✓ Testing class structure...")
    try:
        from app.services.context_session_manager import ContextStateManager
        from app.models.generation_models import StructuredContextContainer

        # Check ContextStateManager methods
        manager = ContextStateManager()
        required_methods = [
            'create_initial_state',
            'serialize_state',
            'deserialize_state',
            'update_state_context',
            'add_processing_history'
        ]

        for method in required_methods:
            if not hasattr(manager, method):
                print(f"  ✗ Missing method: {method}")
                return False

        print("  ✓ ContextStateManager has all required methods")

        # Check that we can create initial state with new model
        container = StructuredContextContainer(
            plot_elements=[],
            character_contexts=[],
            user_requests=[],
            system_instructions=[]
        )

        state = manager.create_initial_state(
            story_id="test_story",
            initial_context=container
        )

        print("  ✓ Can create initial state with new model")
        print(f"    - State ID: {state.state_id}")
        print(f"    - Story ID: {state.story_id}")
        print(f"    - Context container type: {type(state.context_container).__name__}")

        return True
    except Exception as e:
        print(f"  ✗ Structure validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_serialization():
    """Validate state serialization/deserialization with new model."""
    print("\n✓ Testing serialization/deserialization...")
    try:
        from app.services.context_session_manager import ContextStateManager
        from app.models.generation_models import (
            StructuredContextContainer,
            PlotElement,
            CharacterContext
        )

        manager = ContextStateManager()

        # Create container with some data using new model
        container = StructuredContextContainer(
            plot_elements=[
                PlotElement(
                    element_id="plot1",
                    type="scene",
                    content="Test plot element",
                    priority="high",
                    tags=["test"]
                )
            ],
            character_contexts=[
                CharacterContext(
                    character_id="char1",
                    character_name="Test Character",
                    current_state="active",
                    goals=["test goal"],
                    recent_actions=["test action"],
                    memories=["test memory"],
                    personality_traits=["brave"],
                    relationships={"char2": "friend"}
                )
            ],
            user_requests=[],
            system_instructions=[]
        )

        # Create state
        state = manager.create_initial_state(
            story_id="test_story",
            initial_context=container
        )

        print("  ✓ Created state with new model data")
        print(f"    - Plot elements: {len(state.context_container.plot_elements)}")
        print(f"    - Character contexts: {len(state.context_container.character_contexts)}")

        # Serialize
        serialized = manager.serialize_state(state)
        print(f"  ✓ Serialized state ({len(serialized)} chars)")

        # Deserialize
        restored_state = manager.deserialize_state(serialized)
        print(f"  ✓ Deserialized state")
        print(f"    - State ID matches: {restored_state.state_id == state.state_id}")
        print(f"    - Story ID matches: {restored_state.story_id == state.story_id}")
        print(f"    - Plot elements restored: {len(restored_state.context_container.plot_elements)}")
        print(f"    - Character contexts restored: {len(restored_state.context_container.character_contexts)}")

        # Verify data integrity
        if len(restored_state.context_container.plot_elements) != 1:
            print("  ✗ Plot elements count mismatch")
            return False

        if len(restored_state.context_container.character_contexts) != 1:
            print("  ✗ Character contexts count mismatch")
            return False

        plot = restored_state.context_container.plot_elements[0]
        if plot.content != "Test plot element":
            print("  ✗ Plot element content mismatch")
            return False

        char = restored_state.context_container.character_contexts[0]
        if char.character_name != "Test Character":
            print("  ✗ Character name mismatch")
            return False

        print("  ✓ All data integrity checks passed")
        return True

    except Exception as e:
        print(f"  ✗ Serialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Phase 4 Validation: ContextStateManager Migration")
    print("=" * 60)

    results = []

    results.append(("Imports", validate_imports()))

    if results[-1][1]:  # Only continue if imports succeeded
        results.append(("Structure", validate_structure()))
        results.append(("Serialization", validate_serialization()))

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✓ All Phase 4 validation tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
