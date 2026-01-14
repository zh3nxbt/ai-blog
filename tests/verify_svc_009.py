#!/usr/bin/env python3
"""Verification script for svc-009: validate_length() function.

Acceptance Criteria:
1. Function validate_length(content) exists
2. Content with 500 words returns (False, 500, score < 0.5)
3. Content with 1500 words returns (True, 1500, score > 0.8)
4. Content with 3000 words returns (False, 3000, score < 0.7)
5. Target range is 1000-2500 words
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_svc_009() -> bool:
    """Verify all acceptance criteria for svc-009."""
    print("=" * 60)
    print("VERIFICATION: svc-009 - validate_length() function")
    print("=" * 60)

    passed = 0
    total = 5

    # Test 1: Function exists and import works
    print("\n[1/5] Verifying validate_length function exists...")
    try:
        from services.quality_validator import validate_length

        print("✓ Successfully imported validate_length")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: Content with 500 words returns (False, 500, score < 0.5)
    print("\n[2/5] Verifying 500-word content returns (False, 500, score < 0.5)...")
    try:
        content_500 = "word " * 500
        is_valid, word_count, score = validate_length(content_500)

        # Check all conditions
        conditions = [
            (is_valid is False, f"is_valid should be False, got {is_valid}"),
            (word_count == 500, f"word_count should be 500, got {word_count}"),
            (score < 0.5, f"score should be < 0.5, got {score}"),
        ]

        all_passed = True
        for condition, msg in conditions:
            if not condition:
                print(f"  ✗ {msg}")
                all_passed = False

        if all_passed:
            print(f"✓ Returned ({is_valid}, {word_count}, {score}) - all conditions met")
            passed += 1
        else:
            print(f"  Result: ({is_valid}, {word_count}, {score})")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 3: Content with 1500 words returns (True, 1500, score > 0.8)
    print("\n[3/5] Verifying 1500-word content returns (True, 1500, score > 0.8)...")
    try:
        content_1500 = "word " * 1500
        is_valid, word_count, score = validate_length(content_1500)

        # Check all conditions
        conditions = [
            (is_valid is True, f"is_valid should be True, got {is_valid}"),
            (word_count == 1500, f"word_count should be 1500, got {word_count}"),
            (score > 0.8, f"score should be > 0.8, got {score}"),
        ]

        all_passed = True
        for condition, msg in conditions:
            if not condition:
                print(f"  ✗ {msg}")
                all_passed = False

        if all_passed:
            print(f"✓ Returned ({is_valid}, {word_count}, {score}) - all conditions met")
            passed += 1
        else:
            print(f"  Result: ({is_valid}, {word_count}, {score})")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 4: Content with 3000 words returns (False, 3000, score < 0.7)
    print("\n[4/5] Verifying 3000-word content returns (False, 3000, score < 0.7)...")
    try:
        content_3000 = "word " * 3000
        is_valid, word_count, score = validate_length(content_3000)

        # Check all conditions
        conditions = [
            (is_valid is False, f"is_valid should be False, got {is_valid}"),
            (word_count == 3000, f"word_count should be 3000, got {word_count}"),
            (score < 0.7, f"score should be < 0.7, got {score}"),
        ]

        all_passed = True
        for condition, msg in conditions:
            if not condition:
                print(f"  ✗ {msg}")
                all_passed = False

        if all_passed:
            print(f"✓ Returned ({is_valid}, {word_count}, {score}) - all conditions met")
            passed += 1
        else:
            print(f"  Result: ({is_valid}, {word_count}, {score})")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 5: Target range is 1000-2500 words
    print("\n[5/5] Verifying target range is 1000-2500 words...")
    try:
        from services.quality_validator import MIN_WORDS, MAX_WORDS

        # Test boundary values
        boundary_tests = [
            (999, False, "999 words should be invalid (below range)"),
            (1000, True, "1000 words should be valid (at lower bound)"),
            (1500, True, "1500 words should be valid (in range)"),
            (2500, True, "2500 words should be valid (at upper bound)"),
            (2501, False, "2501 words should be invalid (above range)"),
        ]

        all_boundary_passed = True
        for word_count, expected_valid, description in boundary_tests:
            content = "word " * word_count
            is_valid, _, _ = validate_length(content)
            if is_valid == expected_valid:
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description} - got is_valid={is_valid}")
                all_boundary_passed = False

        # Also verify constants are correct
        if MIN_WORDS == 1000 and MAX_WORDS == 2500:
            print(f"  ✓ MIN_WORDS={MIN_WORDS}, MAX_WORDS={MAX_WORDS}")
        else:
            print(f"  ✗ Expected MIN_WORDS=1000, MAX_WORDS=2500, got {MIN_WORDS}, {MAX_WORDS}")
            all_boundary_passed = False

        if all_boundary_passed:
            print("✓ Target range 1000-2500 words verified")
            passed += 1
    except ImportError:
        # If constants not exported, just test behavior
        print("  ⚠ MIN_WORDS/MAX_WORDS not exported, testing behavior only")
        boundary_tests = [
            (999, False, "999 words should be invalid"),
            (1000, True, "1000 words should be valid"),
            (2500, True, "2500 words should be valid"),
            (2501, False, "2501 words should be invalid"),
        ]
        all_boundary_passed = True
        for word_count, expected_valid, description in boundary_tests:
            content = "word " * word_count
            is_valid, _, _ = validate_length(content)
            if is_valid != expected_valid:
                all_boundary_passed = False
                print(f"  ✗ {description}")
        if all_boundary_passed:
            print("✓ Target range 1000-2500 words verified by behavior")
            passed += 1
    except Exception as e:
        print(f"✗ Range verification failed: {e}")

    # Additional edge case tests (informational, not part of acceptance criteria)
    print("\n[ADDITIONAL TESTS] Edge cases...")

    # Test empty string
    is_valid, word_count, score = validate_length("")
    if not is_valid and word_count == 0 and score == 0.0:
        print("✓ Empty string returns (False, 0, 0.0)")
    else:
        print(f"⚠ Empty string result: ({is_valid}, {word_count}, {score})")

    # Test ideal range (1200-2000 words)
    is_valid, word_count, score = validate_length("word " * 1600)
    if is_valid and score >= 0.9:
        print(f"✓ Ideal range (1600 words) scores high: score={score}")
    else:
        print(f"⚠ Ideal range score lower than expected: {score}")

    # Test score scaling (should increase as word count approaches ideal)
    scores = []
    for wc in [500, 800, 1000, 1200, 1500, 1800, 2000, 2200, 2500, 3000]:
        _, _, s = validate_length("word " * wc)
        scores.append((wc, s))
    print(f"  Score distribution: {scores}")

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
        success = verify_svc_009()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
