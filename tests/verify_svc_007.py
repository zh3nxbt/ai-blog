#!/usr/bin/env python3
"""Verification script for svc-007: mark_items_as_used() function.

Acceptance Criteria:
1. Function mark_items_as_used(item_ids, blog_id) exists
2. Function updates used_in_blog column for specified items
3. After call, SELECT shows used_in_blog = blog_id for those items
4. Items not in list remain unchanged
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from services.rss_service import mark_items_as_used  # noqa: E402
from services.supabase_service import get_supabase_client, create_blog_post  # noqa: E402


def verify_svc_007() -> bool:
    """Verify all acceptance criteria for svc-007."""
    print("=" * 60)
    print("VERIFICATION: svc-007 - mark_items_as_used() function")
    print("=" * 60)

    passed = 0
    total = 4
    test_source_id = None
    test_item_ids = []
    test_blog_id = None
    unchanged_item_id = None

    # Setup: Create test RSS source and items
    print("\n[SETUP] Creating test data...")
    try:
        client = get_supabase_client()

        # Create a test RSS source
        source_response = client.table("blog_rss_sources").insert({
            "name": "Test Source for svc-007",
            "url": "https://test-svc-007.example.com/rss",
            "active": True,
            "priority": 1
        }).execute()

        if source_response.data:
            test_source_id = source_response.data[0]["id"]
            print(f"✓ Created test RSS source: {test_source_id}")
        else:
            print("✗ Failed to create test RSS source")
            return False

        # Create test RSS items
        for i in range(3):
            item_response = client.table("blog_rss_items").insert({
                "source_id": test_source_id,
                "title": f"Test Item {i+1} for svc-007",
                "url": f"https://test-svc-007.example.com/item-{i+1}",
                "summary": f"Test summary {i+1}"
            }).execute()

            if item_response.data:
                test_item_ids.append(item_response.data[0]["id"])
                print(f"✓ Created test RSS item {i+1}: {test_item_ids[-1]}")

        # Create an additional item that should remain unchanged
        unchanged_response = client.table("blog_rss_items").insert({
            "source_id": test_source_id,
            "title": "Unchanged Test Item",
            "url": "https://test-svc-007.example.com/unchanged",
            "summary": "This item should remain unchanged"
        }).execute()

        if unchanged_response.data:
            unchanged_item_id = unchanged_response.data[0]["id"]
            print(f"✓ Created unchanged test item: {unchanged_item_id}")

        # Create a test blog post to reference
        test_blog_id = create_blog_post(
            title="Test Blog for svc-007",
            content="Test content for svc-007 verification",
            status="draft"
        )
        print(f"✓ Created test blog post: {test_blog_id}")

    except Exception as e:
        print(f"✗ Setup failed: {e}")
        cleanup(client, test_source_id, test_item_ids, unchanged_item_id, test_blog_id)
        return False

    # Test 1: Function exists with correct signature
    print("\n[1/4] Verifying mark_items_as_used() function exists...")
    try:
        import inspect
        sig = inspect.signature(mark_items_as_used)
        params = list(sig.parameters.keys())

        if "item_ids" in params and "blog_id" in params:
            print(f"✓ Function exists with parameters: {params}")
            passed += 1
        else:
            print(f"✗ Missing parameters. Found: {params}, expected: ['item_ids', 'blog_id']")
    except ImportError as e:
        print(f"✗ Failed to import function: {e}")
        cleanup(client, test_source_id, test_item_ids, unchanged_item_id, test_blog_id)
        return False

    # Test 2: Function updates used_in_blog column
    print("\n[2/4] Verifying function updates used_in_blog column...")
    try:
        # Mark only the first two items as used
        items_to_mark = test_item_ids[:2]
        updated_count = mark_items_as_used(items_to_mark, str(test_blog_id))

        if updated_count == 2:
            print(f"✓ Function updated {updated_count} items")
            passed += 1
        else:
            print(f"✗ Expected 2 items updated, got {updated_count}")
    except Exception as e:
        print(f"✗ Failed to mark items as used: {e}")

    # Test 3: SELECT shows used_in_blog = blog_id for marked items
    print("\n[3/4] Verifying used_in_blog is set correctly for marked items...")
    try:
        verified_count = 0
        for item_id in items_to_mark:
            response = client.table("blog_rss_items").select("used_in_blog").eq("id", item_id).execute()

            if response.data and response.data[0]["used_in_blog"] == str(test_blog_id):
                verified_count += 1

        if verified_count == 2:
            print(f"✓ All {verified_count} marked items have correct used_in_blog value")
            passed += 1
        else:
            print(f"✗ Only {verified_count}/2 items have correct used_in_blog value")
    except Exception as e:
        print(f"✗ Failed to verify used_in_blog: {e}")

    # Test 4: Items not in list remain unchanged
    print("\n[4/4] Verifying items not in list remain unchanged...")
    try:
        # Check the third test item (not marked)
        unmarked_item_id = test_item_ids[2]
        response = client.table("blog_rss_items").select("used_in_blog").eq("id", unmarked_item_id).execute()

        if response.data and response.data[0]["used_in_blog"] is None:
            print(f"✓ Unmarked item {unmarked_item_id} still has used_in_blog = NULL")

            # Also check the unchanged item
            response2 = client.table("blog_rss_items").select("used_in_blog").eq("id", unchanged_item_id).execute()

            if response2.data and response2.data[0]["used_in_blog"] is None:
                print(f"✓ Unchanged item {unchanged_item_id} still has used_in_blog = NULL")
                passed += 1
            else:
                print("✗ Unchanged item was modified unexpectedly")
        else:
            print("✗ Unmarked item was modified unexpectedly")
    except Exception as e:
        print(f"✗ Failed to verify unchanged items: {e}")

    # Cleanup
    cleanup(client, test_source_id, test_item_ids, unchanged_item_id, test_blog_id)

    # Summary
    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    return passed == total


def cleanup(client, source_id, item_ids, unchanged_item_id, blog_id):
    """Clean up test data."""
    print("\n[CLEANUP] Deleting test data...")
    try:
        # Delete RSS items first (foreign key constraint)
        all_item_ids = item_ids + ([unchanged_item_id] if unchanged_item_id else [])
        for item_id in all_item_ids:
            if item_id:
                try:
                    client.table("blog_rss_items").delete().eq("id", item_id).execute()
                    print(f"✓ Deleted test RSS item: {item_id}")
                except Exception as e:
                    print(f"⚠ Failed to delete RSS item {item_id}: {e}")

        # Delete RSS source
        if source_id:
            try:
                client.table("blog_rss_sources").delete().eq("id", source_id).execute()
                print(f"✓ Deleted test RSS source: {source_id}")
            except Exception as e:
                print(f"⚠ Failed to delete RSS source: {e}")

        # Delete blog post
        if blog_id:
            try:
                client.table("blog_posts").delete().eq("id", str(blog_id)).execute()
                print(f"✓ Deleted test blog post: {blog_id}")
            except Exception as e:
                print(f"⚠ Failed to delete blog post: {e}")

    except Exception as e:
        print(f"⚠ Cleanup failed: {e}")


if __name__ == "__main__":
    try:
        success = verify_svc_007()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
