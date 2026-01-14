#!/usr/bin/env python3
"""Verification script for svc-012: validate_content() aggregator function.

Acceptance Criteria:
1. Function validate_content(content, title) exists
2. High-quality content (1500 words, headings, no slop) returns score >= 0.85
3. Content with 'delve' keyword returns score < 0.50
4. Content with missing headings returns score < 0.70
5. Returns dict with all sub-validator results
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _build_body(word_count: int) -> str:
    """Build a word-counted body for repeatable testing."""
    return " ".join(["chip"] * word_count)


def verify_svc_012() -> bool:
    """Verify all acceptance criteria for svc-012."""
    print("=" * 60)
    print("VERIFICATION: svc-012 - validate_content() aggregator function")
    print("=" * 60)

    passed = 0
    total = 5

    # Test 1: Import test - Function exists
    print("\n[1/5] Verifying function exists and can be imported...")
    try:
        from services.quality_validator import validate_content
        print("✓ Successfully imported validate_content")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: High-quality content returns score >= 0.85
    print("\n[2/5] Verifying high-quality content scores >= 0.85...")
    try:
        content = (
            "## Shop Reality Check\n\n"
            + _build_body(400)
            + "\n\n### Tooling Choices\n\n"
            + _build_body(550)
            + "\n\n## Process Notes\n\n"
            + _build_body(550)
        )
        result = validate_content(content, "Shop Reality Check")
        score = result.get("overall_score", 0)

        if score >= 0.85:
            print(f"✓ Returned score={score} (>= 0.85)")
            passed += 1
        else:
            print("✗ Expected score >= 0.85")
            print(f"  Got score={score}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 3: Content with 'delve' keyword returns score < 0.50
    print("\n[3/5] Verifying AI slop keyword caps score...")
    try:
        content = (
            "## Intro\n\n"
            + _build_body(700)
            + " delve "
            + _build_body(700)
            + "\n\n## Close\n\n"
            + _build_body(200)
        )
        result = validate_content(content, "Slop Example")
        score = result.get("overall_score", 1.0)

        if score < 0.50:
            print(f"✓ Returned score={score} (< 0.50)")
            passed += 1
        else:
            print("✗ Expected score < 0.50 for AI slop")
            print(f"  Got score={score}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 4: Content with missing headings returns score < 0.70
    print("\n[4/5] Verifying missing headings are penalized...")
    try:
        content = _build_body(1500)
        result = validate_content(content, "No Headings")
        score = result.get("overall_score", 1.0)

        if score < 0.70:
            print(f"✓ Returned score={score} (< 0.70)")
            passed += 1
        else:
            print("✗ Expected score < 0.70 for missing headings")
            print(f"  Got score={score}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")

    # Test 5: Returns dict with all sub-validator results
    print("\n[5/5] Verifying response contains all sub-validator results...")
    try:
        content = "## Heading\n\n" + _build_body(1100)
        result = validate_content(content, "Structured Output")
        required_keys = {"ai_slop", "length", "structure", "brand_voice", "overall_score"}
        missing = required_keys.difference(result.keys())

        if isinstance(result, dict) and not missing:
            print("✓ Returned dict with all required keys")
            passed += 1
        else:
            print("✗ Missing required keys in response")
            print(f"  Missing keys: {sorted(missing)}")
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
        success = verify_svc_012()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
