"""Verify db-004: blog_rss_sources table acceptance criteria."""

import uuid
from supabase import create_client
from config import settings


def verify_db_004():
    """Verify all acceptance criteria for db-004."""
    print("🔍 Verifying db-004: blog_rss_sources table\n")

    # Initialize Supabase client
    supabase = create_client(settings.supabase_url, settings.supabase_key)

    results = []
    test_source_ids = []  # Track all test sources for cleanup

    # 1. Table exists
    print("✓ Checking: Table blog_rss_sources exists...")
    try:
        # Try to query the table
        supabase.table("blog_rss_sources").select("*").limit(0).execute()
        results.append(("Table blog_rss_sources exists", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("Table blog_rss_sources exists", False))
        print(f"  ❌ FAIL: {e}\n")
        # Print summary before exiting
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print("❌ FAIL: Table blog_rss_sources exists")
        print("=" * 60)
        print("Total: 0/1 criteria passed")
        print("=" * 60)
        return False  # Can't continue if table doesn't exist

    # 2. Column id is UUID primary key
    print("✓ Checking: Column id is UUID primary key...")
    test_source_id_1 = None
    try:
        source = (
            supabase.table("blog_rss_sources")
            .insert(
                {
                    "name": "Test Feed 1",
                    "url": "https://test-feed-1.example.com/rss",
                    "category": "manufacturing",
                    "priority": 5,
                }
            )
            .execute()
        )
        test_source_id_1 = source.data[0]["id"]
        test_source_ids.append(test_source_id_1)
        # Verify it's a valid UUID
        uuid.UUID(test_source_id_1)
        results.append(("Column id is UUID primary key", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("Column id is UUID primary key", False))
        print(f"  ❌ FAIL: {e}\n")

    # 3. Column name is non-null text
    print("✓ Checking: Column name is non-null text...")
    try:
        # Try to insert without name
        supabase.table("blog_rss_sources").insert(
            {"url": "https://test-no-name.example.com/rss"}
        ).execute()
        results.append(("Column name is non-null text", False))
        print("  ❌ FAIL: Should have rejected null name\n")
    except Exception:
        # Expected to fail
        results.append(("Column name is non-null text", True))
        print("  ✅ PASS (correctly rejected null name)\n")

    # 4. Column url is non-null text with UNIQUE constraint
    print("✓ Checking: Column url is non-null text with UNIQUE constraint...")
    try:
        # Try to insert without url
        supabase.table("blog_rss_sources").insert({"name": "Test No URL"}).execute()
        results.append(("Column url is non-null text", False))
        print("  ❌ FAIL: Should have rejected null url\n")
    except Exception:
        # Expected to fail
        results.append(("Column url is non-null text", True))
        print("  ✅ PASS (correctly rejected null url)\n")

    # 5. INSERT with valid URL succeeds
    print("✓ Checking: INSERT with valid URL succeeds...")
    test_source_id_2 = None
    try:
        source = (
            supabase.table("blog_rss_sources")
            .insert(
                {
                    "name": "Test Feed 2",
                    "url": "https://test-feed-2.example.com/rss",
                    "priority": 8,
                }
            )
            .execute()
        )
        test_source_id_2 = source.data[0]["id"]
        test_source_ids.append(test_source_id_2)
        results.append(("INSERT with valid URL succeeds", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("INSERT with valid URL succeeds", False))
        print(f"  ❌ FAIL: {e}\n")

    # 6. INSERT with duplicate URL fails with constraint error
    print("✓ Checking: INSERT with duplicate URL fails...")
    try:
        # Try to insert with same URL as test_source_id_1
        supabase.table("blog_rss_sources").insert(
            {
                "name": "Duplicate Feed",
                "url": "https://test-feed-1.example.com/rss",  # Same as first test
                "priority": 3,
            }
        ).execute()
        results.append(("INSERT with duplicate URL fails", False))
        print("  ❌ FAIL: Should have rejected duplicate URL\n")
    except Exception:
        # Expected to fail due to UNIQUE constraint
        results.append(("INSERT with duplicate URL fails", True))
        print("  ✅ PASS (correctly rejected duplicate URL)\n")

    # 7. Column category is text (nullable)
    print("✓ Checking: Column category is text (nullable)...")
    test_source_id_3 = None
    try:
        source = (
            supabase.table("blog_rss_sources")
            .insert(
                {
                    "name": "Test Feed Without Category",
                    "url": "https://test-feed-no-category.example.com/rss",
                }
            )
            .execute()
        )
        test_source_id_3 = source.data[0]["id"]
        test_source_ids.append(test_source_id_3)
        category = source.data[0].get("category")
        if category is None:
            results.append(("Column category is text (nullable)", True))
            print("  ✅ PASS (nullable)\n")
        else:
            results.append(("Column category is text (nullable)", False))
            print(f"  ❌ FAIL: Expected None but got {category}\n")
    except Exception as e:
        results.append(("Column category is text (nullable)", False))
        print(f"  ❌ FAIL: {e}\n")

    # 8. Column active is boolean defaulting to true
    print("✓ Checking: Column active defaults to true...")
    if test_source_id_3:
        try:
            source = (
                supabase.table("blog_rss_sources")
                .select("active")
                .eq("id", test_source_id_3)
                .execute()
            )
            active = source.data[0].get("active")
            if active is True:
                results.append(("Column active defaults to true", True))
                print("  ✅ PASS\n")
            else:
                results.append(("Column active defaults to true", False))
                print(f"  ❌ FAIL: Expected True but got {active}\n")
        except Exception as e:
            results.append(("Column active defaults to true", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("Column active defaults to true", False))
        print("  ❌ FAIL: No source created\n")

    # 9. Column priority is integer (1-10)
    print("✓ Checking: Column priority is integer with CHECK constraint...")
    try:
        # Try to insert with priority < 1
        supabase.table("blog_rss_sources").insert(
            {
                "name": "Invalid Priority Low",
                "url": "https://test-priority-low.example.com/rss",
                "priority": 0,
            }
        ).execute()
        results.append(("Column priority CHECK constraint (1-10)", False))
        print("  ❌ FAIL: Should have rejected priority=0\n")
    except Exception:
        # Expected to fail
        try:
            # Try to insert with priority > 10
            supabase.table("blog_rss_sources").insert(
                {
                    "name": "Invalid Priority High",
                    "url": "https://test-priority-high.example.com/rss",
                    "priority": 11,
                }
            ).execute()
            results.append(("Column priority CHECK constraint (1-10)", False))
            print("  ❌ FAIL: Should have rejected priority=11\n")
        except Exception:
            # Both validations passed
            results.append(("Column priority CHECK constraint (1-10)", True))
            print("  ✅ PASS (correctly rejected priority < 1 and > 10)\n")

    # 10. Column last_fetched_at is nullable timestamp
    print("✓ Checking: Column last_fetched_at is nullable timestamp...")
    if test_source_id_1:
        try:
            source = (
                supabase.table("blog_rss_sources")
                .select("last_fetched_at")
                .eq("id", test_source_id_1)
                .execute()
            )
            last_fetched = source.data[0].get("last_fetched_at")
            if last_fetched is None:
                results.append(("Column last_fetched_at is nullable timestamp", True))
                print("  ✅ PASS (nullable)\n")
            else:
                results.append(("Column last_fetched_at is nullable timestamp", False))
                print(f"  ❌ FAIL: Expected None but got {last_fetched}\n")
        except Exception as e:
            results.append(("Column last_fetched_at is nullable timestamp", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("Column last_fetched_at is nullable timestamp", False))
        print("  ❌ FAIL: No source created\n")

    # 11. created_at defaults to NOW()
    print("✓ Checking: created_at defaults to NOW()...")
    if test_source_id_1:
        try:
            source = (
                supabase.table("blog_rss_sources")
                .select("created_at")
                .eq("id", test_source_id_1)
                .execute()
            )
            created_at = source.data[0].get("created_at")
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
        print("  ❌ FAIL: No source created\n")

    # Cleanup: Delete all test sources
    print("🧹 Cleaning up test data...")
    for source_id in test_source_ids:
        try:
            supabase.table("blog_rss_sources").delete().eq("id", source_id).execute()
            print(f"  ✅ Test source {source_id[:8]} deleted")
        except Exception as e:
            print(f"  ⚠️  Could not delete test source {source_id[:8]}: {e}")

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

    success = verify_db_004()
    sys.exit(0 if success else 1)
