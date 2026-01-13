#!/usr/bin/env python3
"""Verification script for svc-008: detect_ai_slop() function.

Acceptance Criteria:
1. `python -c 'from services.quality_validator import detect_ai_slop'` exits with code 0
2. detect_ai_slop('Let us delve into') returns (True, ['delve'])
3. detect_ai_slop('We leverage this') returns (True, ['leverage'])
4. detect_ai_slop('Simple plain text') returns (False, [])
5. Function checks at least 15 forbidden keywords
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_svc_008() -> bool:
    """Verify all acceptance criteria for svc-008."""
    print("=" * 60)
    print("VERIFICATION: svc-008 - detect_ai_slop() function")
    print("=" * 60)

    passed = 0
    total = 5

    # Test 1: Import test
    print("\n[1/5] Verifying import works...")
    try:
        from services.quality_validator import detect_ai_slop, AI_SLOP_KEYWORDS
        print("✓ Successfully imported detect_ai_slop and AI_SLOP_KEYWORDS")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: detect_ai_slop('Let us delve into') returns (True, ['delve'])
    print("\n[2/5] Verifying detect_ai_slop('Let us delve into')...")
    try:
        result = detect_ai_slop("Let us delve into")
        expected = (True, ["delve"])
        if result == expected:
            print(f"✓ Returned {result} as expected")
            passed += 1
        else:
            print(f"✗ Expected {expected}, got {result}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 3: detect_ai_slop('We leverage this') returns (True, ['leverage'])
    print("\n[3/5] Verifying detect_ai_slop('We leverage this')...")
    try:
        result = detect_ai_slop("We leverage this")
        expected = (True, ["leverage"])
        if result == expected:
            print(f"✓ Returned {result} as expected")
            passed += 1
        else:
            print(f"✗ Expected {expected}, got {result}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 4: detect_ai_slop('Simple plain text') returns (False, [])
    print("\n[4/5] Verifying detect_ai_slop('Simple plain text')...")
    try:
        result = detect_ai_slop("Simple plain text")
        expected = (False, [])
        if result == expected:
            print(f"✓ Returned {result} as expected")
            passed += 1
        else:
            print(f"✗ Expected {expected}, got {result}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 5: Function checks at least 15 forbidden keywords
    print("\n[5/5] Verifying at least 15 forbidden keywords...")
    try:
        keyword_count = len(AI_SLOP_KEYWORDS)
        if keyword_count >= 15:
            print(f"✓ AI_SLOP_KEYWORDS contains {keyword_count} keywords (>= 15)")
            passed += 1
        else:
            print(f"✗ AI_SLOP_KEYWORDS only has {keyword_count} keywords, expected >= 15")
    except Exception as e:
        print(f"✗ Failed to check keywords: {e}")

    # Additional edge case tests (informational, not part of acceptance criteria)
    print("\n[ADDITIONAL TESTS] Edge cases...")

    # Test case insensitivity
    result = detect_ai_slop("We LEVERAGE this DELVE into")
    if result[0] and "leverage" in result[1] and "delve" in result[1]:
        print("✓ Case insensitivity works (LEVERAGE, DELVE detected)")
    else:
        print(f"⚠ Case sensitivity issue: {result}")

    # Test phrase detection
    result = detect_ai_slop("In today's fast-paced world, things change quickly")
    if result[0] and "in today's fast-paced world" in result[1]:
        print("✓ Multi-word phrase detection works")
    else:
        print(f"⚠ Phrase detection issue: {result}")

    # Test empty string
    result = detect_ai_slop("")
    if result == (False, []):
        print("✓ Empty string returns (False, [])")
    else:
        print(f"⚠ Empty string issue: {result}")

    # Test content without slop
    result = detect_ai_slop("This machining process uses carbide tooling for precision cuts.")
    if result == (False, []):
        print("✓ Clean manufacturing content returns (False, [])")
    else:
        print(f"⚠ False positive detected: {result}")

    # Test multiple keywords
    result = detect_ai_slop("Let's delve into how to leverage this robust paradigm")
    if len(result[1]) >= 3:
        print(f"✓ Multiple keywords detected: {result[1]}")
    else:
        print(f"⚠ Expected multiple keywords, got: {result}")

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
        success = verify_svc_008()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
