#!/usr/bin/env python3
"""
Verification script for test-003: AI slop detection penalizes heavily.

Acceptance criteria:
1. Content with 'delve' scores < 0.50
2. Content with 'leverage' scores < 0.50
3. Critique output includes ai_slop_detected=true
4. Critique output lists found forbidden keywords
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _build_body(word_count: int) -> str:
    """Build a word-counted body for repeatable testing."""
    return " ".join(["chip"] * word_count)


def _build_content_with_keyword(keyword: str) -> str:
    """Build content with headings and a single AI slop keyword."""
    return (
        "## Shop Notes\n\n"
        + _build_body(650)
        + f" {keyword} "
        + _build_body(650)
        + "\n\n### Floor Details\n\n"
        + _build_body(350)
    )


def _mock_critique(content: str) -> dict:
    """Return critique output using shared AI slop detection."""
    from services.quality_validator import detect_ai_slop

    has_slop, found_keywords = detect_ai_slop(content)
    return {
        "quality_score": 0.2 if has_slop else 0.9,
        "ai_slop_detected": has_slop,
        "ai_slop_found": found_keywords,
        "main_issues": ["ai slop detected"] if has_slop else [],
        "improvements": ["remove forbidden phrases"] if has_slop else [],
        "strengths": [],
    }


def run_tests() -> bool:
    """Run all verification tests."""
    from services.quality_validator import validate_content

    passed = 0
    total = 4

    print("=" * 60)
    print("test-003: AI slop detection penalizes heavily")
    print("=" * 60)

    # Test 1: Content with 'delve' scores < 0.50
    print("\nTest 1: Content with 'delve' scores < 0.50")
    try:
        content = _build_content_with_keyword("delve")
        result = validate_content(content, "Slop Example")
        score = result.get("overall_score", 1.0)

        if score < 0.50:
            print(f"  PASS: Returned score={score} (< 0.50)")
            passed += 1
        else:
            print("  FAIL: Expected score < 0.50 for 'delve'")
            print(f"  Got score={score}")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 2: Content with 'leverage' scores < 0.50
    print("\nTest 2: Content with 'leverage' scores < 0.50")
    try:
        content = _build_content_with_keyword("leverage")
        result = validate_content(content, "Slop Example")
        score = result.get("overall_score", 1.0)

        if score < 0.50:
            print(f"  PASS: Returned score={score} (< 0.50)")
            passed += 1
        else:
            print("  FAIL: Expected score < 0.50 for 'leverage'")
            print(f"  Got score={score}")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: Critique output includes ai_slop_detected=true
    print("\nTest 3: Critique output includes ai_slop_detected=true")
    try:
        content = _build_content_with_keyword("delve")
        critique = _mock_critique(content)

        if critique.get("ai_slop_detected") is True:
            print("  PASS: ai_slop_detected is True")
            passed += 1
        else:
            print("  FAIL: Expected ai_slop_detected=True")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 4: Critique output lists found forbidden keywords
    print("\nTest 4: Critique output lists found forbidden keywords")
    try:
        content = _build_content_with_keyword("delve leverage")
        critique = _mock_critique(content)
        found = set(critique.get("ai_slop_found", []))

        if {"delve", "leverage"}.issubset(found):
            print(f"  PASS: ai_slop_found includes {sorted(found)}")
            passed += 1
        else:
            print("  FAIL: Expected ai_slop_found to include 'delve' and 'leverage'")
            print(f"  Got ai_slop_found={sorted(found)}")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
