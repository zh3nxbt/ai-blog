"""Verify mix-001: blog_topic_sources and blog_topic_items tables."""

import uuid

from supabase import create_client

from config import settings


ALLOWED_SOURCE_TYPES = ("rss", "evergreen", "standards", "vendor", "internal")


def _print_summary(results: list[tuple[str, bool]]) -> None:
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    for label, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status}: {label}")
    print("=" * 60)
    print(f"Total: {passed}/{total} criteria passed")
    print("=" * 60)


def verify_db_008() -> bool:
    """Verify all acceptance criteria for mix-001."""
    print("🔍 Verifying mix-001: unified topic source tables\n")

    supabase = create_client(settings.supabase_url, settings.supabase_key)

    results: list[tuple[str, bool]] = []
    test_source_ids: list[str] = []
    test_item_ids: list[str] = []
    test_blog_post_id: str | None = None

    # 1. Table blog_topic_sources exists
    print("✓ Checking: Table blog_topic_sources exists...")
    try:
        supabase.table("blog_topic_sources").select("*").limit(0).execute()
        results.append(("Table blog_topic_sources exists", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("Table blog_topic_sources exists", False))
        print(f"  ❌ FAIL: {e}\n")
        _print_summary(results)
        return False

    # 2. Table blog_topic_items exists
    print("✓ Checking: Table blog_topic_items exists...")
    try:
        supabase.table("blog_topic_items").select("*").limit(0).execute()
        results.append(("Table blog_topic_items exists", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("Table blog_topic_items exists", False))
        print(f"  ❌ FAIL: {e}\n")
        _print_summary(results)
        return False

    # 3. blog_topic_sources.source_type supports required values
    print("✓ Checking: source_type supports required values...")
    try:
        for source_type in ALLOWED_SOURCE_TYPES:
            record = (
                supabase.table("blog_topic_sources")
                .insert(
                    {
                        "source_type": source_type,
                        "name": f"Test Source {source_type}",
                        "category": "test",
                        "priority": 5,
                    }
                )
                .execute()
            )
            source_id = record.data[0]["id"]
            test_source_ids.append(source_id)
            uuid.UUID(source_id)
        results.append(("source_type supports rss/evergreen/standards/vendor/internal", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("source_type supports rss/evergreen/standards/vendor/internal", False))
        print(f"  ❌ FAIL: {e}\n")

    # 4. Invalid source_type is rejected
    print("✓ Checking: invalid source_type rejected...")
    try:
        supabase.table("blog_topic_sources").insert(
            {"source_type": "invalid", "name": "Invalid Source"}
        ).execute()
        results.append(("invalid source_type rejected", False))
        print("  ❌ FAIL: invalid source_type accepted\n")
    except Exception:
        results.append(("invalid source_type rejected", True))
        print("  ✅ PASS (rejected)\n")

    # 5. blog_topic_items.url is nullable
    print("✓ Checking: blog_topic_items.url is nullable...")
    try:
        source_id = test_source_ids[0]
        item = (
            supabase.table("blog_topic_items")
            .insert(
                {
                    "source_id": source_id,
                    "title": "Item without URL",
                    "summary": "Summary without URL",
                }
            )
            .execute()
        )
        item_id = item.data[0]["id"]
        test_item_ids.append(item_id)
        if item.data[0].get("url") is None:
            results.append(("blog_topic_items.url is nullable", True))
            print("  ✅ PASS\n")
        else:
            results.append(("blog_topic_items.url is nullable", False))
            print(f"  ❌ FAIL: url not null ({item.data[0].get('url')})\n")
    except Exception as e:
        results.append(("blog_topic_items.url is nullable", False))
        print(f"  ❌ FAIL: {e}\n")

    # 6. blog_topic_items.used_in_blog references blog_posts
    print("✓ Checking: blog_topic_items.used_in_blog references blog_posts...")
    try:
        blog_post = (
            supabase.table("blog_posts")
            .insert(
                {
                    "title": "Test Blog Post for Topic Item",
                    "slug": f"test-topic-post-{uuid.uuid4().hex[:8]}",
                    "content": "Test content",
                    "status": "draft",
                }
            )
            .execute()
        )
        test_blog_post_id = blog_post.data[0]["id"]
        item = (
            supabase.table("blog_topic_items")
            .insert(
                {
                    "source_id": test_source_ids[1],
                    "title": "Item with Blog Reference",
                    "url": f"https://example.com/topic-item-{uuid.uuid4().hex}",
                    "used_in_blog": test_blog_post_id,
                }
            )
            .execute()
        )
        test_item_ids.append(item.data[0]["id"])
        results.append(("blog_topic_items.used_in_blog references blog_posts", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("blog_topic_items.used_in_blog references blog_posts", False))
        print(f"  ❌ FAIL: {e}\n")

    # 7. UNIQUE constraint prevents duplicate topic items by url when url present
    print("✓ Checking: UNIQUE constraint on blog_topic_items.url...")
    try:
        duplicate_url = f"https://example.com/dup-{uuid.uuid4().hex}"
        first = (
            supabase.table("blog_topic_items")
            .insert(
                {
                    "source_id": test_source_ids[2],
                    "title": "Item with URL",
                    "url": duplicate_url,
                }
            )
            .execute()
        )
        test_item_ids.append(first.data[0]["id"])
        supabase.table("blog_topic_items").insert(
            {
                "source_id": test_source_ids[3],
                "title": "Duplicate URL Item",
                "url": duplicate_url,
            }
        ).execute()
        results.append(("UNIQUE constraint prevents duplicate topic items by url", False))
        print("  ❌ FAIL: duplicate URL accepted\n")
    except Exception:
        results.append(("UNIQUE constraint prevents duplicate topic items by url", True))
        print("  ✅ PASS (rejected duplicate)\n")

    # Cleanup
    if test_item_ids:
        supabase.table("blog_topic_items").delete().in_("id", test_item_ids).execute()
    if test_source_ids:
        supabase.table("blog_topic_sources").delete().in_("id", test_source_ids).execute()
    if test_blog_post_id:
        supabase.table("blog_posts").delete().eq("id", test_blog_post_id).execute()

    _print_summary(results)
    return all(ok for _, ok in results)


if __name__ == "__main__":
    raise SystemExit(0 if verify_db_008() else 1)
