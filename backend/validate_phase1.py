"""
Validate Phase 1 implementation by checking method signatures and structure.
This doesn't require dependencies to be installed.
"""

import ast
import sys


def validate_structured_context_container():
    """Validate that StructuredContextContainer has all required methods."""

    # Parse the file
    with open('app/models/generation_models.py', 'r') as f:
        tree = ast.parse(f.read())

    # Find StructuredContextContainer class
    target_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'StructuredContextContainer':
            target_class = node
            break

    if not target_class:
        print("✗ StructuredContextContainer class not found!")
        return False

    # Extract method names
    methods = [n.name for n in target_class.body if isinstance(n, ast.FunctionDef)]

    print("Found StructuredContextContainer class with methods:")
    for method in methods:
        print(f"  - {method}")

    # Required new methods from Phase 1
    required_methods = [
        'get_plot_elements_by_type',
        'get_plot_elements_by_priority',
        'get_plot_elements_by_tag',
        'get_character_context_by_id',
        'get_character_context_by_name',
        'get_high_priority_elements',
        'get_user_requests_by_type',
        'get_system_instructions_by_scope',
        'calculate_total_tokens',
        'get_token_breakdown',
        '_format_character_for_counting'
    ]

    print("\n" + "=" * 60)
    print("Checking for required Phase 1 methods:")
    all_present = True
    for method in required_methods:
        if method in methods:
            print(f"  ✓ {method}")
        else:
            print(f"  ✗ {method} - MISSING!")
            all_present = False

    return all_present


def check_method_signatures():
    """Check that methods have proper signatures."""
    print("\n" + "=" * 60)
    print("Checking method signatures:")

    with open('app/models/generation_models.py', 'r') as f:
        content = f.read()

    # Check for key signatures
    checks = [
        ('get_plot_elements_by_type', 'element_type: str'),
        ('get_character_context_by_id', 'character_id: str'),
        ('calculate_total_tokens', 'token_counter'),
        ('get_token_breakdown', 'Dict[str, int]'),
    ]

    all_good = True
    for method_name, expected_part in checks:
        if expected_part in content:
            print(f"  ✓ {method_name} has expected signature with '{expected_part}'")
        else:
            print(f"  ✗ {method_name} missing expected part '{expected_part}'")
            all_good = False

    return all_good


def check_imports():
    """Check that necessary imports are present."""
    print("\n" + "=" * 60)
    print("Checking imports:")

    with open('app/models/generation_models.py', 'r') as f:
        content = f.read()

    # Required types
    required = [
        ('List', 'typing'),
        ('Optional', 'typing'),
        ('Dict', 'typing'),
        ('Literal', 'typing'),
    ]

    all_present = True
    for type_name, module in required:
        if f'from {module} import' in content and type_name in content:
            print(f"  ✓ {type_name} from {module}")
        else:
            print(f"  ✗ {type_name} from {module} - may be missing")
            all_present = False

    return all_present


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1 Implementation Validation")
    print("=" * 60)

    results = []

    results.append(("Class and methods", validate_structured_context_container()))
    results.append(("Method signatures", check_method_signatures()))
    results.append(("Imports", check_imports()))

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✓ All validations passed!")
        sys.exit(0)
    else:
        print("\n✗ Some validations failed")
        sys.exit(1)
