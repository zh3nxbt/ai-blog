#!/usr/bin/env python3
"""Verification script for svc-011: validate_brand_voice() function.

Acceptance Criteria:
1. Function validate_brand_voice(content) exists
2. Content with 5+ exclamation marks returns (False, issues, low_score)
3. Content with 'revolutionary' or 'game-changer' returns (False, issues, low_score)
4. Professional manufacturing content returns (True, [], high_score)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_svc_011() -> bool:
    """Verify all acceptance criteria for svc-011."""
    print("=" * 60)
    print("VERIFICATION: svc-011 - validate_brand_voice() function")
    print("=" * 60)

    passed = 0
    total = 4

    # Test 1: Import test - Function exists
    print("\n[1/4] Verifying function exists and can be imported...")
    try:
        from services.quality_validator import validate_brand_voice
        print("✓ Successfully imported validate_brand_voice")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: Content with 5+ exclamation marks returns (False, issues, low_score)
    print("\n[2/4] Verifying excessive exclamation marks are penalized...")
    try:
        loud_content = "This is amazing!!!!! It's unbelievable!!!!!"
        result = validate_brand_voice(loud_content)
        is_valid, issues, score = result

        if not is_valid and score < 0.6 and "excessive exclamation marks" in issues:
            print(f"✓ Returned is_valid={is_valid}, score={score} (< 0.6)")
            print(f"  Issues: {issues}")
            passed += 1
        else:
            print("✗ Expected is_valid=False, score < 0.6 with exclamation issue")
            print(f"  Got is_valid={is_valid}, score={score}, issues={issues}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 3: Content with 'revolutionary' or 'game-changer' returns (False, issues, low_score)
    print("\n[3/4] Verifying buzzwords are penalized...")
    try:
        buzz_content = "This revolutionary process is a game-changer for shops."
        result = validate_brand_voice(buzz_content)
        is_valid, issues, score = result

        if not is_valid and score < 0.6:
            has_buzz_issue = any("marketing buzzwords" in issue for issue in issues)
            if has_buzz_issue:
                print(f"✓ Returned is_valid={is_valid}, score={score} (< 0.6)")
                print(f"  Issues: {issues}")
                passed += 1
            else:
                print("✗ Expected marketing buzzwords issue")
                print(f"  Issues: {issues}")
        else:
            print("✗ Expected is_valid=False, score < 0.6")
            print(f"  Got is_valid={is_valid}, score={score}, issues={issues}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 4: Professional manufacturing content returns (True, [], high_score)
    print("\n[4/4] Verifying professional content passes...")
    try:
        professional_content = (
            "Surface finish isn't cosmetic. It changes how parts wear and how they seal. "
            "If you're holding +/- 0.001\" on a bore, call it out early so the shop can "
            "choose tooling that matches the tolerance."
        )
        result = validate_brand_voice(professional_content)
        is_valid, issues, score = result

        if is_valid and len(issues) == 0 and score >= 0.8:
            print(f"✓ Returned is_valid={is_valid}, issues={issues}, score={score} (>= 0.8)")
            passed += 1
        else:
            print("✗ Expected is_valid=True, issues=[], score >= 0.8")
            print(f"  Got is_valid={is_valid}, issues={issues}, score={score}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

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
        success = verify_svc_011()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
