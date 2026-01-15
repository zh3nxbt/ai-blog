#!/usr/bin/env python3
"""
Verification script for test-004: 5 successful posts end-to-end.

Acceptance criteria:
1. 5 blog_posts records exist with status='published'
2. Average quality score across 5 posts >= 0.85
3. No published post contains AI slop keywords
4. Average iterations per post is 2-4
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from services.quality_validator import detect_ai_slop  # noqa: E402
from services.supabase_service import get_supabase_client  # noqa: E402


def _fetch_published_posts(limit: int = 5) -> List[dict]:
    """Fetch published blog posts ordered by published_at desc."""
    client = get_supabase_client()
    response = (
        client.table("blog_posts")
        .select("id,title,content,status,published_at,created_at")
        .eq("status", "published")
        .order("published_at", desc=True)
        .limit(limit)
        .execute()
    )

    return response.data or []


def _fetch_all_published_ids() -> List[str]:
    """Fetch all published blog post IDs."""
    client = get_supabase_client()
    response = (
        client.table("blog_posts")
        .select("id")
        .eq("status", "published")
        .execute()
    )
    return [row["id"] for row in (response.data or [])]


def _fetch_drafts_for_posts(blog_ids: List[str]) -> List[dict]:
    """Fetch content drafts for the specified blog posts."""
    if not blog_ids:
        return []

    client = get_supabase_client()
    response = (
        client.table("blog_content_drafts")
        .select("blog_post_id,iteration_number,quality_score")
        .in_("blog_post_id", blog_ids)
        .execute()
    )
    return response.data or []


def _summarize_latest_iterations(
    drafts: List[dict],
) -> Dict[str, Tuple[int, float]]:
    """
    Build a map of blog_post_id -> (latest_iteration_number, quality_score).
    """
    latest_by_post: Dict[str, Tuple[int, float]] = {}
    for draft in drafts:
        blog_id = draft["blog_post_id"]
        iteration = int(draft["iteration_number"])
        score = float(draft["quality_score"])

        if blog_id not in latest_by_post or iteration > latest_by_post[blog_id][0]:
            latest_by_post[blog_id] = (iteration, score)

    return latest_by_post


def run_tests() -> bool:
    """Run all verification tests."""
    passed = 0
    total = 4

    print("=" * 60)
    print("test-004: 5 successful posts end-to-end")
    print("=" * 60)

    # Test 1: 5 blog_posts records exist with status='published'
    print("\nTest 1: 5 blog_posts records exist with status='published'")
    try:
        published_ids = _fetch_all_published_ids()
        published_count = len(published_ids)

        if published_count >= 5:
            print(f"  PASS: Found {published_count} published posts")
            passed += 1
        else:
            print(f"  FAIL: Expected >= 5 published posts, found {published_count}")
    except Exception as e:
        print(f"  FAIL: {e}")
        published_ids = []

    # Use the 5 most recent published posts for averages/slop checks
    posts = _fetch_published_posts(limit=5)
    post_ids = [post["id"] for post in posts]

    # Test 2: Average quality score across 5 posts >= 0.85
    print("\nTest 2: Average quality score across 5 posts >= 0.85")
    try:
        drafts = _fetch_drafts_for_posts(post_ids)
        latest_by_post = _summarize_latest_iterations(drafts)

        if len(latest_by_post) < 5:
            print(
                "  FAIL: Expected drafts for 5 published posts, "
                f"found {len(latest_by_post)}"
            )
        else:
            scores = [score for _, score in latest_by_post.values()]
            avg_quality = sum(scores) / len(scores)

            if avg_quality >= 0.85:
                print(f"  PASS: Average quality {avg_quality:.2f} >= 0.85")
                passed += 1
            else:
                print(f"  FAIL: Average quality {avg_quality:.2f} < 0.85")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: No published post contains AI slop keywords
    print("\nTest 3: No published post contains AI slop keywords")
    try:
        slop_hits = []
        for post in posts:
            content = post.get("content") or ""
            has_slop, found = detect_ai_slop(content)
            if has_slop:
                slop_hits.append((post.get("id"), found))

        if slop_hits:
            print("  FAIL: AI slop detected in published content")
            for post_id, found in slop_hits:
                print(f"    - Post {post_id} contains {sorted(found)}")
        else:
            print("  PASS: No AI slop detected in published posts")
            passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 4: Average iterations per post is 2-4
    print("\nTest 4: Average iterations per post is 2-4")
    try:
        drafts = _fetch_drafts_for_posts(post_ids)
        latest_by_post = _summarize_latest_iterations(drafts)

        if len(latest_by_post) < 5:
            print(
                "  FAIL: Expected draft iterations for 5 published posts, "
                f"found {len(latest_by_post)}"
            )
        else:
            iterations = [iteration for iteration, _ in latest_by_post.values()]
            avg_iterations = sum(iterations) / len(iterations)

            if 2 <= avg_iterations <= 4:
                print(f"  PASS: Average iterations {avg_iterations:.1f} (target 2-4)")
                passed += 1
            else:
                print(f"  FAIL: Average iterations {avg_iterations:.1f} outside target 2-4")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
