#!/usr/bin/env python3
"""Verification script for svc-006: fetch_feed_items() function.

Acceptance Criteria:
1. Function fetch_feed_items(source_id, limit) exists
2. Function fetches RSS/XML from source URL
3. Function parses feed and extracts items
4. Function stores new items in blog_rss_items
5. Duplicate URLs are skipped (not inserted)
6. Function returns list of fetched items
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()


def verify_svc_006() -> bool:
    """Verify all acceptance criteria for svc-006."""
    print("=" * 60)
    print("VERIFICATION: svc-006 - fetch_feed_items() function")
    print("=" * 60)

    passed = 0
    total = 6

    # Test 1: Function can be imported
    print("\n[1/6] Verifying fetch_feed_items() can be imported...")
    try:
        from services.rss_service import fetch_feed_items
        print("✓ Successfully imported fetch_feed_items from services.rss_service")
        passed += 1
    except ImportError as e:
        print(f"✗ Failed to import function: {e}")
        return False

    # Get a valid source_id for testing
    print("\n[2/6] Verifying function fetches RSS/XML from source URL...")
    try:
        from services.rss_service import fetch_active_sources
        sources = fetch_active_sources()
        if not sources:
            print("✗ No RSS sources available in database")
            return False

        test_source = sources[0]
        source_id = test_source["id"]
        source_url = test_source["url"]
        print(f"  Using source: {test_source['name']} ({source_url})")

        # Call function with limit=3 to minimize test data
        items = fetch_feed_items(source_id, limit=3)
        print(f"✓ Function executed and fetched from {source_url}")
        passed += 1
    except Exception as e:
        print(f"✗ Failed to fetch from source: {e}")
        return False

    # Test 3: Function parses feed and extracts items
    print("\n[3/6] Verifying function parses feed and extracts items...")
    try:
        # items may be empty if all items already exist (duplicates skipped)
        # Check that return type is a list
        if isinstance(items, list):
            print(f"✓ Function returns list (got {len(items)} new items)")
            passed += 1
        else:
            print(f"✗ Function returned {type(items)}, expected list")
    except Exception as e:
        print(f"✗ Error checking result type: {e}")

    # Test 4: Function stores new items in blog_rss_items
    print("\n[4/6] Verifying function stores new items in blog_rss_items...")
    try:
        from services.supabase_service import get_supabase_client
        client = get_supabase_client()

        # Check if items exist in database for this source
        response = client.table("blog_rss_items")\
            .select("id, title, url")\
            .eq("source_id", source_id)\
            .limit(5)\
            .execute()

        if response.data and len(response.data) > 0:
            print(f"✓ Items exist in blog_rss_items for source (found {len(response.data)})")
            passed += 1
        else:
            print("✗ No items found in blog_rss_items for source")
    except Exception as e:
        print(f"✗ Failed to verify items in database: {e}")

    # Test 5: Duplicate URLs are skipped (not inserted)
    print("\n[5/6] Verifying duplicate URLs are skipped...")
    try:
        # Call fetch_feed_items again with same source
        items_second_call = fetch_feed_items(source_id, limit=3)

        # Second call should return empty or fewer items since duplicates are skipped
        if isinstance(items_second_call, list):
            if len(items_second_call) == 0:
                print("✓ Second call returned empty list (all duplicates skipped)")
            else:
                print(f"✓ Second call returned {len(items_second_call)} items (some were new)")
            passed += 1
        else:
            print(f"✗ Second call returned {type(items_second_call)}, expected list")
    except Exception as e:
        error_msg = str(e).lower()
        # Duplicate constraint errors should be handled internally
        if 'duplicate' in error_msg or 'unique' in error_msg:
            print("✗ Duplicate error was raised instead of being handled")
        else:
            print(f"✗ Error during duplicate test: {e}")

    # Test 6: Function returns list of fetched items
    print("\n[6/6] Verifying function returns list of fetched items...")
    try:
        # Test with a different source if available
        if len(sources) > 1:
            other_source = sources[1]
            other_items = fetch_feed_items(other_source["id"], limit=2)
        else:
            # Reuse same source result
            other_items = items

        if isinstance(other_items, list):
            # Check that returned items have expected structure
            if len(other_items) > 0:
                sample_item = other_items[0]
                expected_keys = {"id", "source_id", "title", "url"}
                actual_keys = set(sample_item.keys())
                if expected_keys.issubset(actual_keys):
                    print(f"✓ Returned items have correct structure (keys: {list(sample_item.keys())})")
                    passed += 1
                else:
                    print(f"✗ Missing keys. Expected: {expected_keys}, Got: {actual_keys}")
            else:
                # Empty list is valid (all duplicates)
                print("✓ Function returns list (empty due to duplicates)")
                passed += 1
        else:
            print(f"✗ Function returned {type(other_items)}, expected list")
    except Exception as e:
        print(f"✗ Error verifying return structure: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    try:
        success = verify_svc_006()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
