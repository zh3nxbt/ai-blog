#!/usr/bin/env python3
"""
Verification script for test-005: Zero AI slop in published content.

Acceptance criteria:
1. No published post contains 'delve'
2. No published post contains 'leverage'
3. No published post contains 'unlock'
4. detect_ai_slop() returns (False, []) for all published content
"""

import sys
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from services.quality_validator import detect_ai_slop  # noqa: E402
from services.supabase_service import get_supabase_client  # noqa: E402


FORBIDDEN_TERMS = ("delve", "leverage", "unlock")


def _fetch_published_posts() -> List[dict]:
    """Fetch all published blog posts."""
    client = get_supabase_client()
    response = (
        client.table("blog_posts")
        .select("id,title,content,status")
        .eq("status", "published")
        .execute()
    )
    return response.data or []


def _find_term_hits(content: str, term: str) -> bool:
    """Return True if the forbidden term appears in the content."""
    return term in content.lower()


def _check_term(posts: List[dict], term: str) -> Tuple[bool, List[str]]:
    """Check that no published posts contain the specific forbidden term."""
    hits: List[Tuple[str, List[str]]] = []
    for post in posts:
        content = post.get("content") or ""
        if _find_term_hits(content, term):
            hits.append(post.get("id", "unknown"))
    return (len(hits) == 0, hits)


def _check_detect_ai_slop(posts: List[dict]) -> Tuple[bool, List[Tuple[str, List[str]]]]:
    """Ensure detect_ai_slop returns no hits for all published content."""
    slop_hits: List[Tuple[str, List[str]]] = []
    for post in posts:
        content = post.get("content") or ""
        has_slop, found = detect_ai_slop(content)
        if has_slop:
            slop_hits.append((post.get("id", "unknown"), list(found)))
    return (len(slop_hits) == 0, slop_hits)


def run_tests() -> bool:
    """Run all verification tests."""
    passed = 0
    total = 4

    print("=" * 60)
    print("test-005: Zero AI slop in published content")
    print("=" * 60)

    posts = _fetch_published_posts()

    # Test 1: No published post contains 'delve'
    print("\nTest 1: No published post contains 'delve'")
    try:
        term_passed, hits = _check_term(posts, "delve")
        if term_passed:
            print("  PASS: No published posts contain 'delve'")
            passed += 1
        else:
            for post_id in hits:
                print(f"  FAIL: Post {post_id} contains 'delve'")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 2: No published post contains 'leverage'
    print("\nTest 2: No published post contains 'leverage'")
    try:
        term_passed, hits = _check_term(posts, "leverage")
        if term_passed:
            print("  PASS: No published posts contain 'leverage'")
            passed += 1
        else:
            for post_id in hits:
                print(f"  FAIL: Post {post_id} contains 'leverage'")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: No published post contains 'unlock'
    print("\nTest 3: No published post contains 'unlock'")
    try:
        term_passed, hits = _check_term(posts, "unlock")
        if term_passed:
            print("  PASS: No published posts contain 'unlock'")
            passed += 1
        else:
            for post_id in hits:
                print(f"  FAIL: Post {post_id} contains 'unlock'")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 4: detect_ai_slop returns (False, []) for all published content
    print("\nTest 4: detect_ai_slop returns (False, []) for all published content")
    try:
        slop_passed, slop_hits = _check_detect_ai_slop(posts)
        if slop_passed:
            print("  PASS: detect_ai_slop() found no issues")
            passed += 1
        else:
            print("  FAIL: detect_ai_slop() reported slop in published posts")
            for post_id, found in slop_hits:
                print(f"    - Post {post_id} contains {sorted(found)}")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
