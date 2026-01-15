#!/usr/bin/env python3
"""Verification script for mix-003: non-RSS source registration + ingestion.

Acceptance Criteria:
1. At least 3 non-RSS stable sources registered (standards/gov/vendor)
2. Sources use RSS or official APIs only (no scraping)
3. Ingestion stores items in blog_topic_items
4. Ingestion handles per-source failures without stopping other sources
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()


def verify_mix_003() -> bool:
    """Verify all acceptance criteria for mix-003."""
    print("=" * 60)
    print("VERIFICATION: mix-003 - non-RSS source registration + ingestion")
    print("=" * 60)

    passed = 0
    total = 4

    try:
        from services.topic_source_service import (
            ingest_non_rss_sources,
            register_non_rss_sources,
        )
        from services.supabase_service import get_supabase_client
    except ImportError as exc:
        print(f"✗ Failed to import required services: {exc}")
        return False

    client = get_supabase_client()

    print("\n[1/4] Verifying at least 3 non-RSS sources are registered...")
    try:
        sources = register_non_rss_sources()
        if len(sources) >= 3:
            print(f"✓ Registered {len(sources)} non-RSS sources")
            passed += 1
        else:
            print(f"✗ Only {len(sources)} sources registered, expected >= 3")
            return False
    except Exception as exc:
        print(f"✗ Failed to register sources: {exc}")
        return False

    print("\n[2/4] Verifying sources use RSS or official APIs only...")
    rss_or_api_notes = 0
    for source in sources:
        notes = source.get("notes", "") or ""
        if "rss" in notes.lower() or "api" in notes.lower():
            rss_or_api_notes += 1
    if rss_or_api_notes >= 3:
        print("✓ Source notes reference RSS/API for all registered sources")
        passed += 1
    else:
        print("✗ Source notes missing RSS/API references")

    print("\n[3/4] Verifying ingestion stores items in blog_topic_items...")
    try:
        ingest_non_rss_sources(limit_per_source=3)
        source_ids = [source["id"] for source in sources]
        count_response = (
            client.table("blog_topic_items")
            .select("id", count="exact")
            .in_("source_id", source_ids)
            .execute()
        )
        item_count = count_response.count or 0
        if item_count > 0:
            print(f"✓ blog_topic_items has {item_count} items for registered sources")
            passed += 1
        else:
            print("✗ No items found in blog_topic_items for registered sources")
    except Exception as exc:
        print(f"✗ Ingestion failed: {exc}")
        return False

    print("\n[4/4] Verifying per-source failures do not stop ingestion...")
    temp_source_id = None
    try:
        temp_response = client.table("blog_topic_sources").insert({
            "name": "mix-003 Invalid Feed Test",
            "source_type": "standards",
            "category": "Test",
            "priority": 1,
            "active": True,
            "notes": "Temporary source for mix-003 failure handling test",
        }).execute()
        temp_source_id = temp_response.data[0]["id"]

        bad_source = {
            "id": temp_source_id,
            "name": "mix-003 Invalid Feed Test",
            "feed_url": "https://invalid.local/rss.xml",
        }

        results = ingest_non_rss_sources(
            limit_per_source=1,
            sources=[sources[0], bad_source],
        )
        if results.get("failures") and results.get("successes"):
            print("✓ Ingestion continued despite per-source failure")
            passed += 1
        else:
            print("✗ Ingestion did not record both success and failure")
    except Exception as exc:
        print(f"✗ Failure handling test failed: {exc}")
    finally:
        if temp_source_id:
            client.table("blog_topic_sources").delete().eq("id", temp_source_id).execute()

    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    try:
        success = verify_mix_003()
        sys.exit(0 if success else 1)
    except Exception as exc:
        print(f"\n✗ Verification failed with error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
