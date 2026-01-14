#!/usr/bin/env python3
"""Verification script for ralph-002: TimeoutManager class.

Acceptance Criteria:
1. `python -c 'from ralph.core.timeout_manager import TimeoutManager'` exits with code 0
2. TimeoutManager(timeout_minutes=30, cost_limit_cents=100) instantiates
3. is_timeout_exceeded() returns False immediately after creation
4. is_cost_limit_exceeded(50) returns False when limit is 100
5. is_cost_limit_exceeded(110) returns True when limit is 100
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_ralph_002() -> bool:
    """Verify all acceptance criteria for ralph-002."""
    print("=" * 60)
    print("VERIFICATION: ralph-002 - TimeoutManager class")
    print("=" * 60)

    passed = 0
    total = 5

    # Test 1: Import test
    print("\n[1/5] Verifying import works...")
    try:
        from ralph.core.timeout_manager import TimeoutManager
        print("✓ Successfully imported TimeoutManager")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: Instantiation
    print("\n[2/5] Verifying instantiation...")
    try:
        manager = TimeoutManager(timeout_minutes=30, cost_limit_cents=100)
        print("✓ TimeoutManager instantiated successfully")
        passed += 1
    except Exception as e:
        print(f"✗ Instantiation failed: {e}")
        return False

    # Test 3: is_timeout_exceeded returns False immediately
    print("\n[3/5] Verifying is_timeout_exceeded() returns False immediately...")
    try:
        if manager.is_timeout_exceeded() is False:
            print("✓ is_timeout_exceeded() returned False")
            passed += 1
        else:
            print("✗ is_timeout_exceeded() returned True unexpectedly")
    except Exception as e:
        print(f"✗ Call failed: {e}")

    # Test 4: is_cost_limit_exceeded(50) returns False
    print("\n[4/5] Verifying cost under limit...")
    try:
        if manager.is_cost_limit_exceeded(50) is False:
            print("✓ is_cost_limit_exceeded(50) returned False")
            passed += 1
        else:
            print("✗ is_cost_limit_exceeded(50) returned True unexpectedly")
    except Exception as e:
        print(f"✗ Call failed: {e}")

    # Test 5: is_cost_limit_exceeded(110) returns True
    print("\n[5/5] Verifying cost over limit...")
    try:
        if manager.is_cost_limit_exceeded(110) is True:
            print("✓ is_cost_limit_exceeded(110) returned True")
            passed += 1
        else:
            print("✗ is_cost_limit_exceeded(110) returned False unexpectedly")
    except Exception as e:
        print(f"✗ Call failed: {e}")

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
        success = verify_ralph_002()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
