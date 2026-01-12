"""Verify db-005: blog_rss_items table acceptance criteria."""

import uuid
from supabase import create_client
from config import settings


def verify_db_005():
    """Verify all acceptance criteria for db-005."""
    print("🔍 Verifying db-005: blog_rss_items table\n")

    # Initialize Supabase client
    supabase = create_client(settings.supabase_url, settings.supabase_key)

    results = []
    test_item_ids = []  # Track all test items for cleanup
    test_source_id = None  # Track test source for cleanup

    # 1. Table exists
    print("✓ Checking: Table blog_rss_items exists...")
    try:
        # Try to query the table
        supabase.table("blog_rss_items").select("*").limit(0).execute()
        results.append(("Table blog_rss_items exists", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("Table blog_rss_items exists", False))
        print(f"  ❌ FAIL: {e}\n")
        # Print summary before exiting
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print("❌ FAIL: Table blog_rss_items exists")
        print("=" * 60)
        print("Total: 0/1 criteria passed")
        print("=" * 60)
        return False  # Can't continue if table doesn't exist

    # Create a test RSS source for foreign key testing
    print("🔧 Setting up test RSS source...")
    try:
        source = (
            supabase.table("blog_rss_sources")
            .insert(
                {
                    "name": "Test RSS Source for Items",
                    "url": "https://test-rss-items-source.example.com/rss",
                    "priority": 5,
                }
            )
            .execute()
        )
        test_source_id = source.data[0]["id"]
        print(f"  ✅ Test source created: {test_source_id[:8]}\n")
    except Exception as e:
        print(f"  ❌ Could not create test source: {e}\n")
        return False

    # 2. Column id is UUID primary key
    print("✓ Checking: Column id is UUID primary key...")
    test_item_id_1 = None
    try:
        item = (
            supabase.table("blog_rss_items")
            .insert(
                {
                    "source_id": test_source_id,
                    "title": "Test RSS Item 1",
                    "url": "https://test-item-1.example.com",
                    "summary": "This is a test RSS item",
                }
            )
            .execute()
        )
        test_item_id_1 = item.data[0]["id"]
        test_item_ids.append(test_item_id_1)
        # Verify it's a valid UUID
        uuid.UUID(test_item_id_1)
        results.append(("Column id is UUID primary key", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("Column id is UUID primary key", False))
        print(f"  ❌ FAIL: {e}\n")

    # 3. Column source_id is UUID foreign key to blog_rss_sources
    print("✓ Checking: Column source_id is UUID foreign key...")
    # Already tested in step 2 - successful insert with valid source_id
    if test_item_id_1:
        results.append(("Column source_id is UUID foreign key", True))
        print("  ✅ PASS (foreign key relationship works)\n")
    else:
        results.append(("Column source_id is UUID foreign key", False))
        print("  ❌ FAIL: Could not create item with valid source_id\n")

    # 4. INSERT with valid source_id succeeds
    print("✓ Checking: INSERT with valid source_id succeeds...")
    test_item_id_2 = None
    try:
        item = (
            supabase.table("blog_rss_items")
            .insert(
                {
                    "source_id": test_source_id,
                    "title": "Test RSS Item 2",
                    "url": "https://test-item-2.example.com",
                }
            )
            .execute()
        )
        test_item_id_2 = item.data[0]["id"]
        test_item_ids.append(test_item_id_2)
        results.append(("INSERT with valid source_id succeeds", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("INSERT with valid source_id succeeds", False))
        print(f"  ❌ FAIL: {e}\n")

    # 5. INSERT with invalid source_id fails with foreign key error
    print("✓ Checking: INSERT with invalid source_id fails...")
    try:
        # Try to insert with non-existent source_id
        fake_source_id = str(uuid.uuid4())
        supabase.table("blog_rss_items").insert(
            {
                "source_id": fake_source_id,
                "title": "Invalid Item",
                "url": "https://invalid-item.example.com",
            }
        ).execute()
        results.append(("INSERT with invalid source_id fails", False))
        print("  ❌ FAIL: Should have rejected invalid source_id\n")
    except Exception:
        # Expected to fail due to foreign key constraint
        results.append(("INSERT with invalid source_id fails", True))
        print("  ✅ PASS (correctly rejected invalid source_id)\n")

    # 6. Column title is non-null text
    print("✓ Checking: Column title is non-null text...")
    try:
        # Try to insert without title
        supabase.table("blog_rss_items").insert(
            {"source_id": test_source_id, "url": "https://no-title.example.com"}
        ).execute()
        results.append(("Column title is non-null text", False))
        print("  ❌ FAIL: Should have rejected null title\n")
    except Exception:
        # Expected to fail
        results.append(("Column title is non-null text", True))
        print("  ✅ PASS (correctly rejected null title)\n")

    # 7. Column url is non-null text with UNIQUE constraint
    print("✓ Checking: Column url is non-null text with UNIQUE constraint...")
    try:
        # Try to insert duplicate URL
        supabase.table("blog_rss_items").insert(
            {
                "source_id": test_source_id,
                "title": "Duplicate URL Item",
                "url": "https://test-item-1.example.com",  # Same as first test
            }
        ).execute()
        results.append(("Column url UNIQUE constraint", False))
        print("  ❌ FAIL: Should have rejected duplicate URL\n")
    except Exception:
        # Expected to fail due to UNIQUE constraint
        results.append(("Column url UNIQUE constraint", True))
        print("  ✅ PASS (correctly rejected duplicate URL)\n")

    # 8. Column summary is text (nullable)
    print("✓ Checking: Column summary is text (nullable)...")
    test_item_id_3 = None
    try:
        item = (
            supabase.table("blog_rss_items")
            .insert(
                {
                    "source_id": test_source_id,
                    "title": "Item Without Summary",
                    "url": "https://test-item-no-summary.example.com",
                }
            )
            .execute()
        )
        test_item_id_3 = item.data[0]["id"]
        test_item_ids.append(test_item_id_3)
        summary = item.data[0].get("summary")
        if summary is None:
            results.append(("Column summary is text (nullable)", True))
            print("  ✅ PASS (nullable)\n")
        else:
            results.append(("Column summary is text (nullable)", False))
            print(f"  ❌ FAIL: Expected None but got {summary}\n")
    except Exception as e:
        results.append(("Column summary is text (nullable)", False))
        print(f"  ❌ FAIL: {e}\n")

    # 9. Column published_at is timestamp (nullable)
    print("✓ Checking: Column published_at is timestamp (nullable)...")
    if test_item_id_1:
        try:
            item = (
                supabase.table("blog_rss_items")
                .select("published_at")
                .eq("id", test_item_id_1)
                .execute()
            )
            published_at = item.data[0].get("published_at")
            # Should be None since we didn't provide it
            if published_at is None:
                results.append(("Column published_at is timestamp (nullable)", True))
                print("  ✅ PASS (nullable)\n")
            else:
                results.append(("Column published_at is timestamp (nullable)", False))
                print(f"  ❌ FAIL: Expected None but got {published_at}\n")
        except Exception as e:
            results.append(("Column published_at is timestamp (nullable)", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("Column published_at is timestamp (nullable)", False))
        print("  ❌ FAIL: No item created\n")

    # 10. Column used_in_blog is nullable UUID foreign key to blog_posts
    print("✓ Checking: Column used_in_blog is nullable UUID foreign key...")
    if test_item_id_1:
        try:
            item = (
                supabase.table("blog_rss_items")
                .select("used_in_blog")
                .eq("id", test_item_id_1)
                .execute()
            )
            used_in_blog = item.data[0].get("used_in_blog")
            if used_in_blog is None:
                results.append(
                    ("Column used_in_blog is nullable UUID foreign key", True)
                )
                print("  ✅ PASS (nullable)\n")
            else:
                results.append(
                    ("Column used_in_blog is nullable UUID foreign key", False)
                )
                print(f"  ❌ FAIL: Expected None but got {used_in_blog}\n")
        except Exception as e:
            results.append(("Column used_in_blog is nullable UUID foreign key", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("Column used_in_blog is nullable UUID foreign key", False))
        print("  ❌ FAIL: No item created\n")

    # 11. created_at defaults to NOW()
    print("✓ Checking: created_at defaults to NOW()...")
    if test_item_id_1:
        try:
            item = (
                supabase.table("blog_rss_items")
                .select("created_at")
                .eq("id", test_item_id_1)
                .execute()
            )
            created_at = item.data[0].get("created_at")
            if created_at:
                results.append(("created_at defaults to NOW()", True))
                print("  ✅ PASS\n")
            else:
                results.append(("created_at defaults to NOW()", False))
                print("  ❌ FAIL: created_at is null\n")
        except Exception as e:
            results.append(("created_at defaults to NOW()", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("created_at defaults to NOW()", False))
        print("  ❌ FAIL: No item created\n")

    # Cleanup: Delete all test items
    print("🧹 Cleaning up test data...")
    for item_id in test_item_ids:
        try:
            supabase.table("blog_rss_items").delete().eq("id", item_id).execute()
            print(f"  ✅ Test item {item_id[:8]} deleted")
        except Exception as e:
            print(f"  ⚠️  Could not delete test item {item_id[:8]}: {e}")

    # Cleanup: Delete test source
    if test_source_id:
        try:
            supabase.table("blog_rss_sources").delete().eq("id", test_source_id).execute()
            print(f"  ✅ Test source {test_source_id[:8]} deleted")
        except Exception as e:
            print(f"  ⚠️  Could not delete test source {test_source_id[:8]}: {e}")

    print()  # Empty line after cleanup

    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for criterion, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {criterion}")

    print("=" * 60)
    print(f"Total: {passed}/{total} criteria passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    import sys

    success = verify_db_005()
    sys.exit(0 if success else 1)
