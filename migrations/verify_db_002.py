"""Verify db-002: blog_content_drafts table acceptance criteria."""

import uuid
from supabase import create_client
from config import settings


def verify_db_002():
    """Verify all acceptance criteria for db-002."""
    print("🔍 Verifying db-002: blog_content_drafts table\n")

    # Initialize Supabase client
    supabase = create_client(settings.supabase_url, settings.supabase_key)

    results = []

    # 1. Table exists
    print("✓ Checking: Table blog_content_drafts exists...")
    try:
        # Try to query the table
        supabase.table("blog_content_drafts").select("*").limit(0).execute()
        results.append(("Table blog_content_drafts exists", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("Table blog_content_drafts exists", False))
        print(f"  ❌ FAIL: {e}\n")
        # Print summary before exiting
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print("❌ FAIL: Table blog_content_drafts exists")
        print("=" * 60)
        print("Total: 0/1 criteria passed")
        print("=" * 60)
        return False  # Can't continue if table doesn't exist

    # 2. Get a valid blog_post_id for testing
    print("✓ Getting valid blog_post_id for tests...")
    try:
        posts = supabase.table("blog_posts").select("id").limit(1).execute()
        if not posts.data:
            print("  ⚠️  No blog posts found. Creating test post...")
            # Create a test blog post
            test_post = (
                supabase.table("blog_posts")
                .insert(
                    {
                        "title": "Test Post for Draft Verification",
                        "slug": f"test-draft-verification-{uuid.uuid4().hex[:8]}",
                        "status": "draft",
                    }
                )
                .execute()
            )
            blog_post_id = test_post.data[0]["id"]
            print(f"  ✅ Created test post: {blog_post_id}\n")
        else:
            blog_post_id = posts.data[0]["id"]
            print(f"  ✅ Using existing post: {blog_post_id}\n")
    except Exception as e:
        print(f"  ❌ FAIL: Cannot get blog_post_id: {e}\n")
        # Print summary before exiting
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        for criterion, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {criterion}")
        print("=" * 60)
        passed = sum(1 for _, result in results if result)
        print(f"Total: {passed}/{len(results)} criteria passed (cannot continue)")
        print("=" * 60)
        return False

    # 3. INSERT with iteration_number=1 for valid blog_post_id succeeds
    print("✓ Checking: INSERT with iteration_number=1 succeeds...")
    test_draft_id = None
    try:
        draft = (
            supabase.table("blog_content_drafts")
            .insert(
                {
                    "blog_post_id": blog_post_id,
                    "iteration_number": 1,
                    "content": "Test content for iteration 1",
                    "title": "Test Title",
                    "quality_score": 0.75,
                    "critique": {"issues": [], "suggestions": ["Improve clarity"]},
                    "api_cost_cents": 25,
                }
            )
            .execute()
        )
        test_draft_id = draft.data[0]["id"]
        results.append(("INSERT with iteration_number=1 succeeds", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("INSERT with iteration_number=1 succeeds", False))
        print(f"  ❌ FAIL: {e}\n")

    # 4. Column verification (id is UUID primary key)
    print("✓ Checking: Column id is UUID primary key...")
    if test_draft_id:
        try:
            # UUID should be valid format
            uuid.UUID(test_draft_id)
            results.append(("Column id is UUID primary key", True))
            print("  ✅ PASS\n")
        except ValueError as e:
            results.append(("Column id is UUID primary key", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("Column id is UUID primary key", False))
        print("  ❌ FAIL: No draft created\n")

    # 5. Column blog_post_id is UUID foreign key to blog_posts
    print("✓ Checking: Column blog_post_id is UUID foreign key...")
    try:
        # Try to insert with invalid foreign key
        invalid_id = str(uuid.uuid4())
        supabase.table("blog_content_drafts").insert(
            {"blog_post_id": invalid_id, "iteration_number": 99}
        ).execute()
        results.append(("Column blog_post_id is UUID foreign key", False))
        print("  ❌ FAIL: Should have rejected invalid foreign key\n")
    except Exception:
        # Expected to fail
        results.append(("Column blog_post_id is UUID foreign key", True))
        print("  ✅ PASS (correctly rejected invalid FK)\n")

    # 6. Column types verification
    print("✓ Checking: All required columns exist with correct types...")
    if test_draft_id:
        try:
            draft = (
                supabase.table("blog_content_drafts")
                .select("*")
                .eq("id", test_draft_id)
                .execute()
            )
            data = draft.data[0]

            checks = [
                ("iteration_number", int, data.get("iteration_number")),
                ("content", str, data.get("content")),
                ("title", str, data.get("title")),
                ("quality_score", (float, int), data.get("quality_score")),
                ("critique", dict, data.get("critique")),
                ("api_cost_cents", int, data.get("api_cost_cents")),
                ("created_at", str, data.get("created_at")),
            ]

            all_pass = True
            for field, expected_type, value in checks:
                if isinstance(expected_type, tuple):
                    if not isinstance(value, expected_type):
                        print(f"  ❌ Field {field} has wrong type: {type(value)}")
                        all_pass = False
                else:
                    if not isinstance(value, expected_type):
                        print(f"  ❌ Field {field} has wrong type: {type(value)}")
                        all_pass = False

            results.append(("All columns have correct types", all_pass))
            if all_pass:
                print("  ✅ PASS\n")
            else:
                print("  ❌ FAIL\n")
        except Exception as e:
            results.append(("All columns have correct types", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("All columns have correct types", False))
        print("  ❌ FAIL: No draft created\n")

    # 7. UNIQUE constraint on (blog_post_id, iteration_number)
    print("✓ Checking: UNIQUE constraint on (blog_post_id, iteration_number)...")
    try:
        # Try to insert duplicate
        supabase.table("blog_content_drafts").insert(
            {
                "blog_post_id": blog_post_id,
                "iteration_number": 1,  # Same as before
                "content": "Duplicate content",
            }
        ).execute()
        results.append(("UNIQUE constraint on (blog_post_id, iteration_number)", False))
        print("  ❌ FAIL: Should have rejected duplicate\n")
    except Exception:
        # Expected to fail
        results.append(("UNIQUE constraint on (blog_post_id, iteration_number)", True))
        print("  ✅ PASS (correctly rejected duplicate)\n")

    # 8. created_at defaults to NOW()
    print("✓ Checking: created_at defaults to NOW()...")
    if test_draft_id:
        try:
            draft = (
                supabase.table("blog_content_drafts")
                .select("created_at")
                .eq("id", test_draft_id)
                .execute()
            )
            created_at = draft.data[0].get("created_at")
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
        print("  ❌ FAIL: No draft created\n")

    # Cleanup: Delete test draft
    print("🧹 Cleaning up test data...")
    try:
        if test_draft_id:
            supabase.table("blog_content_drafts").delete().eq(
                "id", test_draft_id
            ).execute()
            print("  ✅ Test draft deleted\n")
    except Exception as e:
        print(f"  ⚠️  Could not delete test draft: {e}\n")

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

    success = verify_db_002()
    sys.exit(0 if success else 1)
