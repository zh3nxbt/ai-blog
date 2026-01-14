#!/usr/bin/env python3
"""Verification script for ralph-005: CRITIQUE_PROMPT_TEMPLATE.

Acceptance Criteria:
1. `python -c 'from ralph_content.prompts.critique import CRITIQUE_PROMPT_TEMPLATE'` exits with code 0
2. Template contains 'quality_score' field specification
3. Template contains 'ai_slop_detected' field specification
4. Template contains 'improvements' field specification
5. Template includes example JSON response format
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_ralph_005() -> bool:
    """Verify all acceptance criteria for ralph-005."""
    print("=" * 60)
    print("VERIFICATION: ralph-005 - CRITIQUE_PROMPT_TEMPLATE")
    print("=" * 60)

    passed = 0
    total = 5

    print("\n[1/5] Verifying CRITIQUE_PROMPT_TEMPLATE import...")
    try:
        from ralph_content.prompts.critique import CRITIQUE_PROMPT_TEMPLATE
        if CRITIQUE_PROMPT_TEMPLATE.strip():
            print("✓ CRITIQUE_PROMPT_TEMPLATE imported")
            passed += 1
        else:
            print("✗ CRITIQUE_PROMPT_TEMPLATE is empty")
            return False
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    print("\n[2/5] Verifying 'quality_score' field specification...")
    if "quality_score" in CRITIQUE_PROMPT_TEMPLATE:
        print("✓ 'quality_score' present")
        passed += 1
    else:
        print("✗ 'quality_score' missing")

    print("\n[3/5] Verifying 'ai_slop_detected' field specification...")
    if "ai_slop_detected" in CRITIQUE_PROMPT_TEMPLATE:
        print("✓ 'ai_slop_detected' present")
        passed += 1
    else:
        print("✗ 'ai_slop_detected' missing")

    print("\n[4/5] Verifying 'improvements' field specification...")
    if "improvements" in CRITIQUE_PROMPT_TEMPLATE:
        print("✓ 'improvements' present")
        passed += 1
    else:
        print("✗ 'improvements' missing")

    print("\n[5/5] Verifying example JSON response format...")
    has_json_example = "{" in CRITIQUE_PROMPT_TEMPLATE and "}" in CRITIQUE_PROMPT_TEMPLATE
    if has_json_example:
        print("✓ Example JSON response format present")
        passed += 1
    else:
        print("✗ Example JSON response format missing")

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
        success = verify_ralph_005()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
