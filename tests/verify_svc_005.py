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
        print("✓ Import successful: from services.rss_service import fetch_active_feeds")
        passed += 1
    except ImportError as e:
        print(f"✗ Failed to import function: {e}")
        return False

    # Test 2: Function returns list of RSS source records
    print("\n[2/5] Verifying function returns list of RSS source records...")
    try:
        feeds = fetch_active_feeds()

        if not isinstance(feeds, list):
            print(f"✗ Function returned {type(feeds)}, expected list")
        elif len(feeds) == 0:
            print("⚠ Function returned empty list - database may not be seeded")
            # Still pass if it returns a list, even if empty
            passed += 1
        else:
            # Check that each item is a dict with expected keys
            expected_keys = ["id", "name", "url", "active", "priority"]
            first_feed = feeds[0]

            if isinstance(first_feed, dict):
                missing_keys = [k for k in expected_keys if k not in first_feed]
                if missing_keys:
                    print(f"⚠ First record missing keys: {missing_keys}")
                    print(f"  Available keys: {list(first_feed.keys())}")
                else:
                    print(f"✓ Function returns list of dict records with expected keys")
                passed += 1
            else:
                print(f"✗ List items are {type(first_feed)}, expected dict")
    except Exception as e:
        print(f"✗ Failed to call function: {e}")

    # Test 3: All returned sources have active=true
    print("\n[3/5] Verifying all returned sources have active=true...")
    try:
        feeds = fetch_active_feeds()

        if len(feeds) == 0:
            print("⚠ No feeds returned - cannot verify active flag")
            # Pass since there are no inactive sources in an empty list
            passed += 1
        else:
            inactive_feeds = [f for f in feeds if f.get("active") is not True]
            if len(inactive_feeds) > 0:
                print(f"✗ Found {len(inactive_feeds)} inactive feeds in results")
                for f in inactive_feeds[:3]:
                    print(f"  - {f.get('name')}: active={f.get('active')}")
            else:
                print(f"✓ All {len(feeds)} feeds have active=true")
                passed += 1
    except Exception as e:
        print(f"✗ Failed to verify active flag: {e}")

    # Test 4: Sources ordered by priority DESC
    print("\n[4/5] Verifying sources are ordered by priority DESC...")
    try:
        feeds = fetch_active_feeds()

        if len(feeds) < 2:
            print("⚠ Less than 2 feeds - cannot verify ordering")
            # Pass since ordering is trivially correct for 0-1 items
            passed += 1
        else:
            priorities = [f.get("priority", 0) for f in feeds]
            is_descending = all(priorities[i] >= priorities[i+1] for i in range(len(priorities)-1))

            if is_descending:
                print(f"✓ Sources ordered by priority DESC: {priorities}")
                passed += 1
            else:
                print(f"✗ Sources not in descending order: {priorities}")
    except Exception as e:
        print(f"✗ Failed to verify ordering: {e}")

    # Test 5: Returns at least 5 sources when database is seeded
    print("\n[5/5] Verifying at least 5 sources returned (seeded database)...")
    try:
        feeds = fetch_active_feeds()

        if len(feeds) >= 5:
            print(f"✓ Returns {len(feeds)} sources (>= 5 required)")
            passed += 1
        else:
            print(f"✗ Only {len(feeds)} sources returned (expected >= 5)")
            print("  Hint: Run db-007 migration to seed RSS sources")
    except Exception as e:
        print(f"✗ Failed to verify source count: {e}")

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
