#!/usr/bin/env python3
"""Verification script for ralph-006: Content generation prompts.

Acceptance Criteria:
1. `python -c 'from ralph.prompts.content_generation import INITIAL_DRAFT_PROMPT'` exits with code 0
2. `python -c 'from ralph.prompts.content_generation import IMPROVEMENT_PROMPT_TEMPLATE'` exits with code 0
3. INITIAL_DRAFT_PROMPT mentions manufacturing industry
4. INITIAL_DRAFT_PROMPT mentions MAS Precision Parts
5. IMPROVEMENT_PROMPT_TEMPLATE has placeholder for critique
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_ralph_006() -> bool:
    """Verify all acceptance criteria for ralph-006."""
    print("=" * 60)
    print("VERIFICATION: ralph-006 - Content generation prompts")
    print("=" * 60)

    passed = 0
    total = 5

    # Test 1: Import INITIAL_DRAFT_PROMPT
    print("\n[1/5] Verifying INITIAL_DRAFT_PROMPT import...")
    try:
        from ralph.prompts.content_generation import INITIAL_DRAFT_PROMPT
        print("✓ Successfully imported INITIAL_DRAFT_PROMPT")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: Import IMPROVEMENT_PROMPT_TEMPLATE
    print("\n[2/5] Verifying IMPROVEMENT_PROMPT_TEMPLATE import...")
    try:
        from ralph.prompts.content_generation import IMPROVEMENT_PROMPT_TEMPLATE
        print("✓ Successfully imported IMPROVEMENT_PROMPT_TEMPLATE")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 3: Mentions manufacturing industry
    print("\n[3/5] Verifying manufacturing mention...")
    try:
        if "manufacturing" in INITIAL_DRAFT_PROMPT.lower():
            print("✓ INITIAL_DRAFT_PROMPT mentions manufacturing")
            passed += 1
        else:
            print("✗ INITIAL_DRAFT_PROMPT does not mention manufacturing")
    except Exception as e:
        print(f"✗ Check failed: {e}")

    # Test 4: Mentions MAS Precision Parts
    print("\n[4/5] Verifying MAS Precision Parts mention...")
    try:
        if "mas precision parts" in INITIAL_DRAFT_PROMPT.lower():
            print("✓ INITIAL_DRAFT_PROMPT mentions MAS Precision Parts")
            passed += 1
        else:
            print("✗ INITIAL_DRAFT_PROMPT does not mention MAS Precision Parts")
    except Exception as e:
        print(f"✗ Check failed: {e}")

    # Test 5: Improvement prompt has critique placeholder
    print("\n[5/5] Verifying critique placeholder...")
    try:
        if "{critique}" in IMPROVEMENT_PROMPT_TEMPLATE:
            print("✓ IMPROVEMENT_PROMPT_TEMPLATE includes critique placeholder")
            passed += 1
        else:
            print("✗ IMPROVEMENT_PROMPT_TEMPLATE missing critique placeholder")
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
        success = verify_ralph_006()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
