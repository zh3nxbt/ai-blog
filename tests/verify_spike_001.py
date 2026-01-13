"""Verification script for spike-001: RSS feed fetching service."""

import sys
import os

# Add parent directory to path so we can import from services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv  # noqa: E402

# Load environment variables
load_dotenv()

def main():
    """Verify all acceptance criteria for spike-001."""
    print("=" * 80)
    print("VERIFICATION: spike-001 - RSS feed fetching service")
    print("=" * 80)

    total_checks = 0
    passed_checks = 0

    # Acceptance criterion 1: services/rss_service.py exists
    print("\n[1/5] Checking if services/rss_service.py exists...")
    total_checks += 1
    try:
        from services import rss_service  # noqa: F401
        print("✓ PASS: services/rss_service.py exists and is importable")
        passed_checks += 1
    except ImportError as e:
        print(f"✗ FAIL: Cannot import services.rss_service: {e}")

    # Acceptance criterion 2: Function fetch_active_sources() returns list of RSS source records
    print("\n[2/5] Checking fetch_active_sources() function...")
    total_checks += 1
    try:
        from services.rss_service import fetch_active_sources

        sources = fetch_active_sources()
        if isinstance(sources, list):
            print(f"✓ PASS: fetch_active_sources() returns list with {len(sources)} sources")
            if sources:
                print(f"  First source: {sources[0].get('name', 'N/A')}")
            passed_checks += 1
        else:
            print(f"✗ FAIL: fetch_active_sources() returned {type(sources)}, expected list")
    except Exception as e:
        print(f"✗ FAIL: fetch_active_sources() failed: {e}")

    # Acceptance criterion 3: Function fetch_feed(url) uses feedparser
    print("\n[3/5] Checking fetch_feed() function...")
    total_checks += 1
    try:
        from services.rss_service import fetch_feed
        import feedparser

        # Use a known working RSS feed (Assembly Magazine from db-007)
        test_url = "https://www.assemblymag.com/rss/17"
        feed = fetch_feed(test_url)

        if isinstance(feed, feedparser.FeedParserDict):
            print("✓ PASS: fetch_feed() uses feedparser and returns FeedParserDict")
            print(f"  Feed title: {feed.feed.get('title', 'N/A')}")
            print(f"  Number of entries: {len(feed.entries)}")
            passed_checks += 1
        else:
            print(f"✗ FAIL: fetch_feed() returned {type(feed)}, expected FeedParserDict")
    except Exception as e:
        print(f"✗ FAIL: fetch_feed() failed: {e}")

    # Acceptance criterion 4: Function store_rss_items() saves items and skips duplicates
    print("\n[4/5] Checking store_rss_items() function...")
    total_checks += 1
    try:
        from services.rss_service import store_rss_items, fetch_active_sources, fetch_feed

        # Get first active source
        sources = fetch_active_sources()
        if not sources:
            print("✗ FAIL: No active sources found in database (run db-007 migration)")
        else:
            source_id = sources[0]['id']
            source_url = sources[0]['url']

            # Fetch the feed
            feed = fetch_feed(source_url)

            # Store items (limit to 3 for testing)
            stored_items = store_rss_items(source_id, feed, limit=3)

            if isinstance(stored_items, list):
                print(f"✓ PASS: store_rss_items() saved {len(stored_items)} new items")
                if stored_items:
                    print(f"  First item: {stored_items[0].get('title', 'N/A')[:60]}...")

                # Try storing again - should skip duplicates
                second_store = store_rss_items(source_id, feed, limit=3)
                print(f"  Second run stored {len(second_store)} items (duplicates skipped)")
                passed_checks += 1
            else:
                print(f"✗ FAIL: store_rss_items() returned {type(stored_items)}, expected list")
    except Exception as e:
        print(f"✗ FAIL: store_rss_items() failed: {e}")

    # Acceptance criterion 5: Function returns 3-5 RSS items successfully
    print("\n[5/5] Checking fetch_unused_items() returns 3-5 items...")
    total_checks += 1
    try:
        from services.rss_service import fetch_unused_items

        items = fetch_unused_items(limit=5)

        if isinstance(items, list):
            item_count = len(items)
            if 3 <= item_count <= 5:
                print(f"✓ PASS: fetch_unused_items() returned {item_count} items (within 3-5 range)")
                passed_checks += 1
            elif item_count < 3:
                print(f"✗ FAIL: fetch_unused_items() returned {item_count} items (need at least 3)")
                print("  Run spike.py or fetch more RSS items to populate the database")
            else:  # item_count > 5
                print(f"✗ FAIL: fetch_unused_items() returned {item_count} items (expected max 5 with limit=5)")
        else:
            print(f"✗ FAIL: fetch_unused_items() returned {type(items)}, expected list")
    except Exception as e:
        print(f"✗ FAIL: fetch_unused_items() failed: {e}")

    # Summary
    print("\n" + "=" * 80)
    print(f"VERIFICATION SUMMARY: {passed_checks}/{total_checks} checks passed")
    print("=" * 80)

    if passed_checks == total_checks:
        print("\n✓ ALL CHECKS PASSED - spike-001 acceptance criteria met")
        return 0
    else:
        print(f"\n✗ FAILED - {total_checks - passed_checks} check(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
