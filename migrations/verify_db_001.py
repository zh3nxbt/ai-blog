"""Verify db-001: blog_posts table schema and constraints."""

import uuid

from supabase import create_client

from config import settings


REQUIRED_COLUMNS = {
    "id",
    "title",
    "slug",
    "excerpt",
    "content",
    "status",
    "published_at",
    "created_at",
}


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


def verify_db_001() -> bool:
    """Verify all acceptance criteria for db-001."""
    print("🔍 Verifying db-001: blog_posts table schema\n")

    supabase_key = settings.supabase_secret or settings.supabase_key
    supabase = create_client(settings.supabase_url, supabase_key)

    results: list[tuple[str, bool]] = []
    test_post_id: str | None = None
    duplicate_post_id: str | None = None
    test_slug = f"test-blog-post-{uuid.uuid4().hex[:8]}"

    # 1. Table exists
    print("✓ Checking: Table blog_posts exists...")
    try:
        supabase.table("blog_posts").select("*").limit(0).execute()
        results.append(("Table blog_posts exists", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("Table blog_posts exists", False))
        print(f"  ❌ FAIL: {e}\n")
        _print_summary(results)
        return False

    # 2. Insert with status='draft' succeeds
    print("✓ Checking: INSERT with status='draft' succeeds...")
    try:
        record = (
            supabase.table("blog_posts")
            .insert(
                {
                    "title": "Test Blog Post",
                    "slug": test_slug,
                    "content": "Test content",
                    "status": "draft",
                }
            )
            .execute()
        )
        test_post_id = record.data[0]["id"]
        uuid.UUID(test_post_id)
        results.append(("INSERT with status='draft' succeeds", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("INSERT with status='draft' succeeds", False))
        print(f"  ❌ FAIL: {e}\n")

    # 3. Required columns exist in returned row
    print("✓ Checking: Required columns exist...")
    try:
        row = record.data[0] if test_post_id else {}
        missing = REQUIRED_COLUMNS - set(row.keys())
        if missing:
            results.append(("Required columns present", False))
            print(f"  ❌ FAIL: Missing columns {sorted(missing)}\n")
        else:
            results.append(("Required columns present", True))
            print("  ✅ PASS\n")
    except Exception as e:
        results.append(("Required columns present", False))
        print(f"  ❌ FAIL: {e}\n")

    # 4. Column published_at is nullable
    print("✓ Checking: published_at is nullable...")
    try:
        if row.get("published_at") is None:
            results.append(("published_at is nullable", True))
            print("  ✅ PASS\n")
        else:
            results.append(("published_at is nullable", False))
            print(f"  ❌ FAIL: published_at not null ({row.get('published_at')})\n")
    except Exception as e:
        results.append(("published_at is nullable", False))
        print(f"  ❌ FAIL: {e}\n")

    # 5. Column created_at defaults to NOW()
    print("✓ Checking: created_at defaults to NOW()...")
    try:
        if row.get("created_at"):
            results.append(("created_at defaults to NOW()", True))
            print("  ✅ PASS\n")
        else:
            results.append(("created_at defaults to NOW()", False))
            print("  ❌ FAIL: created_at missing\n")
    except Exception as e:
        results.append(("created_at defaults to NOW()", False))
        print(f"  ❌ FAIL: {e}\n")

    # 6. Slug unique constraint
    print("✓ Checking: slug UNIQUE constraint...")
    try:
        duplicate = (
            supabase.table("blog_posts")
            .insert(
                {
                    "title": "Duplicate Slug",
                    "slug": test_slug,
                    "content": "Duplicate content",
                    "status": "draft",
                }
            )
            .execute()
        )
        duplicate_post_id = duplicate.data[0]["id"]
        results.append(("slug UNIQUE constraint enforced", False))
        print("  ❌ FAIL: duplicate slug accepted\n")
    except Exception:
        results.append(("slug UNIQUE constraint enforced", True))
        print("  ✅ PASS (duplicate rejected)\n")

    # 7. status CHECK constraint
    print("✓ Checking: status CHECK constraint...")
    try:
        supabase.table("blog_posts").insert(
            {
                "title": "Invalid Status",
                "slug": f"invalid-status-{uuid.uuid4().hex[:8]}",
                "content": "Invalid status",
                "status": "invalid",
            }
        ).execute()
        results.append(("status CHECK constraint enforced", False))
        print("  ❌ FAIL: invalid status accepted\n")
    except Exception:
        results.append(("status CHECK constraint enforced", True))
        print("  ✅ PASS (invalid status rejected)\n")

    # Cleanup
    if duplicate_post_id:
        supabase.table("blog_posts").delete().eq("id", duplicate_post_id).execute()
    if test_post_id:
        supabase.table("blog_posts").delete().eq("id", test_post_id).execute()

    _print_summary(results)
    return all(ok for _, ok in results)


if __name__ == "__main__":
    raise SystemExit(0 if verify_db_001() else 1)
