#!/usr/bin/env python3
"""Verification script for ralph-001: ralph package structure.

Acceptance Criteria:
1. `python -c 'import ralph'` exits with code 0
2. `python -c 'import ralph_content.core'` exits with code 0
3. `python -c 'import ralph_content.agents'` exits with code 0
4. `python -c 'import ralph_content.prompts'` exits with code 0
5. ralph/__init__.py exists
6. ralph/core/__init__.py exists
7. ralph/agents/__init__.py exists
8. ralph/prompts/__init__.py exists
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_ralph_001() -> bool:
    """Verify all acceptance criteria for ralph-001."""
    print("=" * 60)
    print("VERIFICATION: ralph-001 - ralph package structure")
    print("=" * 60)

    passed = 0
    total = 8

    # Test 1: Import ralph
    print("\n[1/8] Verifying import ralph...")
    try:
        import ralph  # noqa: F401
        print("✓ Successfully imported ralph")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")

    # Test 2: Import ralph_content.core
    print("\n[2/8] Verifying import ralph_content.core...")
    try:
        import ralph_content.core  # noqa: F401
        print("✓ Successfully imported ralph_content.core")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")

    # Test 3: Import ralph_content.agents
    print("\n[3/8] Verifying import ralph_content.agents...")
    try:
        import ralph_content.agents  # noqa: F401
        print("✓ Successfully imported ralph_content.agents")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")

    # Test 4: Import ralph_content.prompts
    print("\n[4/8] Verifying import ralph_content.prompts...")
    try:
        import ralph_content.prompts  # noqa: F401
        print("✓ Successfully imported ralph_content.prompts")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")

    # Test 5: ralph/__init__.py exists
    print("\n[5/8] Verifying ralph/__init__.py exists...")
    if (project_root / "ralph" / "__init__.py").exists():
        print("✓ ralph/__init__.py exists")
        passed += 1
    else:
        print("✗ ralph/__init__.py missing")

    # Test 6: ralph/core/__init__.py exists
    print("\n[6/8] Verifying ralph/core/__init__.py exists...")
    if (project_root / "ralph" / "core" / "__init__.py").exists():
        print("✓ ralph/core/__init__.py exists")
        passed += 1
    else:
        print("✗ ralph/core/__init__.py missing")

    # Test 7: ralph/agents/__init__.py exists
    print("\n[7/8] Verifying ralph/agents/__init__.py exists...")
    if (project_root / "ralph" / "agents" / "__init__.py").exists():
        print("✓ ralph/agents/__init__.py exists")
        passed += 1
    else:
        print("✗ ralph/agents/__init__.py missing")

    # Test 8: ralph/prompts/__init__.py exists
    print("\n[8/8] Verifying ralph/prompts/__init__.py exists...")
    if (project_root / "ralph" / "prompts" / "__init__.py").exists():
        print("✓ ralph/prompts/__init__.py exists")
        passed += 1
    else:
        print("✗ ralph/prompts/__init__.py missing")

    # Summary
    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    if passed == total:
        print("\n✓ All acceptance criteria PASSED")
    else:
        print(f"\n✗ {total - passed} acceptance criteria FAILED")

    return passed == total


if __name__ == "__main__":
    try:
        success = verify_ralph_001()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
