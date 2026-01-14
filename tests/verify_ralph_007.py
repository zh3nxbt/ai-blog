#!/usr/bin/env python3
"""Verification script for ralph-007: BaseAgent abstract class.

Acceptance Criteria:
1. `python -c 'from ralph.agents.base_agent import BaseAgent'` exits with code 0
2. BaseAgent is abstract (cannot instantiate directly)
3. BaseAgent has _call_claude() method
4. BaseAgent has total_input_tokens attribute
5. BaseAgent has total_output_tokens attribute
6. BaseAgent has get_total_tokens() method
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_ralph_007() -> bool:
    """Verify all acceptance criteria for ralph-007."""
    print("=" * 60)
    print("VERIFICATION: ralph-007 - BaseAgent abstract class")
    print("=" * 60)

    passed = 0
    total = 6

    # Test 1: Import test
    print("\n[1/6] Verifying import works...")
    try:
        from ralph.agents.base_agent import BaseAgent
        print("✓ Successfully imported BaseAgent")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: BaseAgent is abstract
    print("\n[2/6] Verifying BaseAgent is abstract...")
    try:
        try:
            BaseAgent()  # type: ignore[abstract]
            print("✗ BaseAgent instantiated (should be abstract)")
        except TypeError:
            print("✓ BaseAgent is abstract and cannot be instantiated")
            passed += 1
    except Exception as e:
        print(f"✗ Check failed: {e}")

    # Test 3-6: Verify methods and attributes via a concrete subclass
    class _TestAgent(BaseAgent):
        @property
        def agent_name(self) -> str:
            return "test-agent"

    print("\n[3/6] Verifying _call_claude() method exists...")
    try:
        if hasattr(BaseAgent, "_call_claude"):
            print("✓ _call_claude() method exists")
            passed += 1
        else:
            print("✗ _call_claude() method missing")
    except Exception as e:
        print(f"✗ Check failed: {e}")

    print("\n[4/6] Verifying total_input_tokens attribute...")
    try:
        agent = _TestAgent()
        if hasattr(agent, "total_input_tokens"):
            print("✓ total_input_tokens attribute exists")
            passed += 1
        else:
            print("✗ total_input_tokens attribute missing")
    except Exception as e:
        print(f"✗ Check failed: {e}")

    print("\n[5/6] Verifying total_output_tokens attribute...")
    try:
        if hasattr(agent, "total_output_tokens"):
            print("✓ total_output_tokens attribute exists")
            passed += 1
        else:
            print("✗ total_output_tokens attribute missing")
    except Exception as e:
        print(f"✗ Check failed: {e}")

    print("\n[6/6] Verifying get_total_tokens() method exists...")
    try:
        if callable(getattr(agent, "get_total_tokens", None)):
            print("✓ get_total_tokens() method exists")
            passed += 1
        else:
            print("✗ get_total_tokens() method missing")
    except Exception as e:
        print(f"✗ Check failed: {e}")

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
        success = verify_ralph_007()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
