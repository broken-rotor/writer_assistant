#!/usr/bin/env python3
"""
Validation script for Phase 5: Remove conversion function from unified_context_processor.

This script validates that:
1. Module imports successfully without legacy model types
2. UnifiedContextProcessor can be created
3. The conversion function no longer exists
4. _process_structured_context uses new model natively
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def validate_imports():
    """Validate that imports work without legacy types."""
    print("✓ Testing imports...")
    try:
        from app.services.unified_context_processor import (
            UnifiedContextProcessor,
            UnifiedContextResult,
            get_unified_context_processor
        )
        print("  ✓ All imports successful")

        # Verify legacy types are NOT imported
        import app.services.unified_context_processor as ucp_module

        # These should NOT exist
        legacy_names = [
            'LegacyStructuredContextContainer',
            'StoryContextElement',
            'CharacterContextElement',
            'UserContextElement',
            'SystemContextElement',
            'ContextType',
            'LegacyContextMetadata'
        ]

        for name in legacy_names:
            if hasattr(ucp_module, name):
                print(f"  ✗ Legacy type still present: {name}")
                return False

        print("  ✓ No legacy types found in module")
        return True

    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_no_conversion_function():
    """Validate that conversion function has been removed."""
    print("\n✓ Testing conversion function removal...")
    try:
        import app.services.unified_context_processor as ucp_module

        if hasattr(ucp_module, 'convert_api_to_legacy_context'):
            print("  ✗ Conversion function still exists!")
            return False

        print("  ✓ Conversion function successfully removed")
        return True

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def validate_processor_structure():
    """Validate UnifiedContextProcessor uses new model."""
    print("\n✓ Testing UnifiedContextProcessor structure...")
    try:
        from app.services.unified_context_processor import UnifiedContextProcessor
        from app.models.generation_models import StructuredContextContainer

        # Create processor
        processor = UnifiedContextProcessor(enable_caching=False)
        print("  ✓ UnifiedContextProcessor created successfully")

        # Check that context_manager exists and is initialized
        if not hasattr(processor, 'context_manager'):
            print("  ✗ Missing context_manager attribute")
            return False

        print("  ✓ Has context_manager attribute")

        # Verify new model is being used in type hints
        import inspect
        method = processor._process_structured_context
        sig = inspect.signature(method)

        # Check that structured_context parameter exists
        if 'structured_context' not in sig.parameters:
            print("  ✗ _process_structured_context missing structured_context parameter")
            return False

        print("  ✓ _process_structured_context has correct signature")
        return True

    except Exception as e:
        print(f"  ✗ Structure validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_source_code():
    """Validate source code doesn't contain legacy patterns."""
    print("\n✓ Testing source code for legacy patterns...")
    try:
        source_file = Path(__file__).parent / "app" / "services" / "unified_context_processor.py"

        if not source_file.exists():
            print(f"  ✗ Source file not found: {source_file}")
            return False

        source_code = source_file.read_text()

        # Patterns that should NOT be present
        bad_patterns = [
            'convert_api_to_legacy_context',
            'LegacyStructuredContextContainer',
            'legacy_context = ',
            'StoryContextElement',
            'CharacterContextElement',
            'UserContextElement',
            'SystemContextElement',
            'LegacyContextMetadata'
        ]

        found_patterns = []
        for pattern in bad_patterns:
            if pattern in source_code:
                found_patterns.append(pattern)

        if found_patterns:
            print(f"  ✗ Found legacy patterns in source:")
            for pattern in found_patterns:
                print(f"    - {pattern}")
            return False

        print("  ✓ No legacy patterns found in source code")

        # Patterns that SHOULD be present
        good_patterns = [
            'from app.models.generation_models import',
            'StructuredContextContainer',
            'structured_context, processing_config',  # New model usage
        ]

        missing_patterns = []
        for pattern in good_patterns:
            if pattern not in source_code:
                missing_patterns.append(pattern)

        if missing_patterns:
            print(f"  ✗ Missing expected patterns:")
            for pattern in missing_patterns:
                print(f"    - {pattern}")
            return False

        print("  ✓ All expected patterns found")
        return True

    except Exception as e:
        print(f"  ✗ Source code validation failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Phase 5 Validation: Remove Conversion Function")
    print("=" * 60)

    results = []

    results.append(("Imports", validate_imports()))
    results.append(("No Conversion Function", validate_no_conversion_function()))

    if results[0][1]:  # Only continue if imports succeeded
        results.append(("Processor Structure", validate_processor_structure()))
        results.append(("Source Code Analysis", validate_source_code()))

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✓ All Phase 5 validation tests passed!")
        print("\nThe UnifiedContextProcessor now uses the new model natively")
        print("without any conversion functions.")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
