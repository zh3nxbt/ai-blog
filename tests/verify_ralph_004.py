#!/usr/bin/env python3
"""Verification script for ralph-004: AI slop keywords constant.

Acceptance Criteria:
1. `python -c 'from ralph_content.prompts.critique import AI_SLOP_KEYWORDS; print(len(AI_SLOP_KEYWORDS))'` prints >= 15
2. AI_SLOP_KEYWORDS contains 'delve'
3. AI_SLOP_KEYWORDS contains 'leverage'
4. AI_SLOP_KEYWORDS contains 'unlock'
5. AI_SLOP_KEYWORDS contains 'landscape'
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_ralph_004() -> bool:
    """Verify all acceptance criteria for ralph-004."""
    print("=" * 60)
    print("VERIFICATION: ralph-004 - AI slop keywords constant")
    print("=" * 60)

    passed = 0
    total = 5

    print("\n[1/5] Verifying AI_SLOP_KEYWORDS import and size...")
    try:
        from ralph_content.prompts.critique import AI_SLOP_KEYWORDS
        if len(AI_SLOP_KEYWORDS) >= 15:
            print(f"✓ AI_SLOP_KEYWORDS contains {len(AI_SLOP_KEYWORDS)} entries")
            passed += 1
        else:
            print(f"✗ AI_SLOP_KEYWORDS too short: {len(AI_SLOP_KEYWORDS)} entries")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    print("\n[2/5] Verifying keyword 'delve' is present...")
    if "delve" in AI_SLOP_KEYWORDS:
        print("✓ 'delve' found")
        passed += 1
    else:
        print("✗ 'delve' missing")

    print("\n[3/5] Verifying keyword 'leverage' is present...")
    if "leverage" in AI_SLOP_KEYWORDS:
        print("✓ 'leverage' found")
        passed += 1
    else:
        print("✗ 'leverage' missing")

    print("\n[4/5] Verifying keyword 'unlock' is present...")
    if "unlock" in AI_SLOP_KEYWORDS:
        print("✓ 'unlock' found")
        passed += 1
    else:
        print("✗ 'unlock' missing")

    print("\n[5/5] Verifying keyword 'landscape' is present...")
    if "landscape" in AI_SLOP_KEYWORDS:
        print("✓ 'landscape' found")
        passed += 1
    else:
        print("✗ 'landscape' missing")

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
        success = verify_ralph_004()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
