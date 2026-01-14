#!/usr/bin/env python3
"""Verification script for ralph-003: API cost calculation.

Acceptance Criteria:
1. Function calculate_api_cost(input_tokens, output_tokens, model) exists
2. Returns cost in cents as integer
3. Cost for claude-sonnet-4-5 matches Anthropic pricing
4. 1000 input + 2000 output tokens costs approximately 1-5 cents
5. Costs scale linearly with token count
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_ralph_003() -> bool:
    """Verify all acceptance criteria for ralph-003."""
    print("=" * 60)
    print("VERIFICATION: ralph-003 - API cost calculation")
    print("=" * 60)

    passed = 0
    total = 5

    # Test 1: Import test
    print("\n[1/5] Verifying import works...")
    try:
        from ralph.core.api_cost import calculate_api_cost
        print("✓ Successfully imported calculate_api_cost")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: Return type is integer
    print("\n[2/5] Verifying return type...")
    try:
        result = calculate_api_cost(1000, 2000, "claude-sonnet-4-5")
        if isinstance(result, int):
            print("✓ Returned cost is integer")
            passed += 1
        else:
            print(f"✗ Returned type is {type(result).__name__}, expected int")
    except Exception as e:
        print(f"✗ Call failed: {e}")

    # Test 3: Pricing matches claude-sonnet-4-5 rates
    print("\n[3/5] Verifying claude-sonnet-4-5 pricing...")
    try:
        cost_cents = calculate_api_cost(1_000_000, 1_000_000, "claude-sonnet-4-5")
        if cost_cents == 1800:
            print("✓ 1M in + 1M out costs 1800 cents ($18.00)")
            passed += 1
        else:
            print(f"✗ Expected 1800 cents, got {cost_cents}")
    except Exception as e:
        print(f"✗ Call failed: {e}")

    # Test 4: 1000 in + 2000 out costs ~1-5 cents
    print("\n[4/5] Verifying small token cost range...")
    try:
        cost_cents = calculate_api_cost(1000, 2000, "claude-sonnet-4-5")
        if 1 <= cost_cents <= 5:
            print(f"✓ Cost {cost_cents} cents is within expected range")
            passed += 1
        else:
            print(f"✗ Cost {cost_cents} cents out of expected range (1-5)")
    except Exception as e:
        print(f"✗ Call failed: {e}")

    # Test 5: Linear scaling
    print("\n[5/5] Verifying linear scaling...")
    try:
        cost_small = calculate_api_cost(1000, 2000, "claude-sonnet-4-5")
        cost_double = calculate_api_cost(2000, 4000, "claude-sonnet-4-5")
        if cost_double == cost_small * 2:
            print("✓ Cost scales linearly with token count")
            passed += 1
        else:
            print(f"✗ Expected {cost_small * 2}, got {cost_double}")
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
        success = verify_ralph_003()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
