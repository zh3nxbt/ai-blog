#!/usr/bin/env python3
"""Verification script for svc-005: fetch_active_feeds() function.

Acceptance Criteria:
1. `python -c 'from services.rss_service import fetch_active_feeds'` exits with code 0
2. Function returns list of RSS source records
3. All returned sources have active=true
4. Sources ordered by priority DESC
5. Returns at least 5 sources when database is seeded
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()


def verify_svc_005() -> bool:
    """Verify all acceptance criteria for svc-005."""
    print("=" * 60)
    print("VERIFICATION: svc-005 - fetch_active_feeds() function")
    print("=" * 60)

    passed = 0
    total = 5

    # Test 1: Function can be imported
    print("\n[1/5] Verifying fetch_active_feeds() can be imported...")
    try:
        from services.rss_service import fetch_active_feeds
        print("✓ Successfully imported fetch_active_feeds from services.rss_service")
        passed += 1
    except ImportError as e:
        print(f"✗ Failed to import function: {e}")
        return False

    # Test 2: Function returns list of RSS source records
    print("\n[2/5] Verifying function returns list of RSS source records...")
    try:
        sources = fetch_active_feeds()
        if isinstance(sources, list):
            print(f"✓ Function returns list with {len(sources)} records")
            passed += 1
        else:
            print(f"✗ Function returned {type(sources)}, expected list")
    except Exception as e:
        print(f"✗ Failed to call fetch_active_feeds(): {e}")
        return False

    # Test 3: All returned sources have active=true
    print("\n[3/5] Verifying all returned sources have active=true...")
    all_active = True
    for source in sources:
        if not source.get("active"):
            all_active = False
            print(f"✗ Source '{source.get('name')}' has active={source.get('active')}")
            break

    if all_active and len(sources) > 0:
        print(f"✓ All {len(sources)} sources have active=true")
        passed += 1
    elif len(sources) == 0:
        print("⚠ No sources returned - cannot verify active status")
    else:
        print("✗ Some sources do not have active=true")

    # Test 4: Sources ordered by priority DESC
    print("\n[4/5] Verifying sources are ordered by priority DESC...")
    if len(sources) >= 2:
        priorities = [s.get("priority", 0) for s in sources]
        is_descending = all(priorities[i] >= priorities[i + 1] for i in range(len(priorities) - 1))
        if is_descending:
            print(f"✓ Sources ordered by priority DESC: {priorities}")
            passed += 1
        else:
            print(f"✗ Sources not in descending order: {priorities}")
    elif len(sources) == 1:
        print(f"✓ Only one source returned (priority={sources[0].get('priority')}), order is trivially correct")
        passed += 1
    else:
        print("⚠ No sources returned - cannot verify ordering")

    # Test 5: Returns at least 5 sources when database is seeded
    print("\n[5/5] Verifying at least 5 sources returned when seeded...")
    if len(sources) >= 5:
        print(f"✓ Returned {len(sources)} sources (>= 5)")
        passed += 1
    else:
        print(f"✗ Returned only {len(sources)} sources, expected >= 5")

    # Summary
    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    try:
        success = verify_svc_005()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
