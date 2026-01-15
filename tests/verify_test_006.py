#!/usr/bin/env python3
"""
Verification script for test-006: API costs below target.

Acceptance criteria:
1. Average api_cost_cents per blog_post is < 50
2. No single post exceeds 100 cents (cost limit)
3. Cost tracking is accurate to within 10%
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

from services.supabase_service import get_supabase_client  # noqa: E402


def _fetch_published_posts() -> List[dict]:
    """Fetch published blog posts."""
    client = get_supabase_client()
    response = (
        client.table("blog_posts")
        .select("id,title,content,status,published_at")
        .eq("status", "published")
        .execute()
    )
    return response.data or []


def _fetch_publish_activity(blog_ids: List[str]) -> List[dict]:
    """Fetch publish/finalize activity logs for blog posts."""
    if not blog_ids:
        return []

    client = get_supabase_client()
    response = (
        client.table("blog_agent_activity")
        .select("context_id,activity_type,metadata,created_at")
        .in_("context_id", blog_ids)
        .in_("activity_type", ["publish", "finalize"])
        .execute()
    )
    return response.data or []


def _fetch_draft_costs(blog_ids: List[str]) -> List[dict]:
    """Fetch draft costs for published posts."""
    if not blog_ids:
        return []

    client = get_supabase_client()
    response = (
        client.table("blog_content_drafts")
        .select("blog_post_id,iteration_number,api_cost_cents")
        .in_("blog_post_id", blog_ids)
        .execute()
    )
    return response.data or []


def _latest_activity_by_post(activities: List[dict]) -> Dict[str, dict]:
    """Return latest publish/finalize activity per post based on created_at."""
    latest: Dict[str, dict] = {}
    for activity in activities:
        post_id = activity.get("context_id")
        if not post_id:
            continue
        current = latest.get(post_id)
        if current is None or activity.get("created_at", "") > current.get("created_at", ""):
            latest[post_id] = activity
    return latest


def _sum_draft_cost_by_post(drafts: List[dict]) -> Dict[str, int]:
    """Return summed api_cost_cents per blog post from drafts."""
    costs: Dict[str, int] = {}
    for draft in drafts:
        post_id = draft.get("blog_post_id")
        if not post_id:
            continue
        cost = draft.get("api_cost_cents")
        if cost is None:
            continue
        cost_int = int(cost)
        costs[post_id] = costs.get(post_id, 0) + cost_int
    return costs


def _extract_total_cost(activity: dict) -> int | None:
    """Extract total_cost_cents from activity metadata."""
    metadata = activity.get("metadata") or {}
    total_cost = metadata.get("total_cost_cents")
    if total_cost is None:
        return None
    try:
        return int(total_cost)
    except (TypeError, ValueError):
        return None


def _cost_accuracy_ok(total_cost: int, draft_cost_sum: int) -> bool:
    """Check that total cost is within 10% of summed draft costs."""
    if total_cost <= 0:
        return False
    diff = abs(total_cost - draft_cost_sum)
    return diff / total_cost <= 0.10


def run_tests() -> bool:
    """Run all verification tests."""
    passed = 0
    total = 3

    print("=" * 60)
    print("test-006: API costs below target")
    print("=" * 60)

    posts = _fetch_published_posts()
    post_ids = [post["id"] for post in posts]

    activities = _fetch_publish_activity(post_ids)
    latest_activity = _latest_activity_by_post(activities)

    if not latest_activity:
        print("\nNo publish/finalize activity found for published posts.")
        print("Results: 0/3 tests passed")
        return False

    total_costs: List[int] = []
    missing_costs: List[str] = []
    for post_id, activity in latest_activity.items():
        total_cost = _extract_total_cost(activity)
        if total_cost is None:
            missing_costs.append(post_id)
        else:
            total_costs.append(total_cost)

    # Test 1: Average api_cost_cents per blog_post is < 50
    print("\nTest 1: Average api_cost_cents per blog_post is < 50")
    try:
        if not total_costs:
            print("  FAIL: No total_cost_cents values found")
        else:
            avg_cost = sum(total_costs) / len(total_costs)
            if avg_cost < 50:
                print(f"  PASS: Average cost {avg_cost:.2f} cents < 50")
                passed += 1
            else:
                print(f"  FAIL: Average cost {avg_cost:.2f} cents >= 50")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 2: No single post exceeds 100 cents
    print("\nTest 2: No single post exceeds 100 cents")
    try:
        if not total_costs:
            print("  FAIL: No total_cost_cents values found")
        else:
            max_cost = max(total_costs)
            if max_cost <= 100:
                print(f"  PASS: Max cost {max_cost} cents <= 100")
                passed += 1
            else:
                print(f"  FAIL: Max cost {max_cost} cents > 100")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: Cost tracking is accurate to within 10%
    print("\nTest 3: Cost tracking is accurate to within 10%")
    try:
        drafts = _fetch_draft_costs(post_ids)
        draft_costs = _sum_draft_cost_by_post(drafts)

        accuracy_failures: List[Tuple[str, int, int]] = []
        for post_id, activity in latest_activity.items():
            total_cost = _extract_total_cost(activity)
            draft_cost_sum = draft_costs.get(post_id)
            if total_cost is None or draft_cost_sum is None:
                continue
            if not _cost_accuracy_ok(total_cost, draft_cost_sum):
                accuracy_failures.append((post_id, total_cost, draft_cost_sum))

        if missing_costs:
            print(f"  FAIL: Missing total_cost_cents for {len(missing_costs)} posts")
        elif accuracy_failures:
            print("  FAIL: Cost tracking outside 10% tolerance")
            for post_id, total_cost, max_draft_cost in accuracy_failures:
                print(
                    f"    - Post {post_id}: total={total_cost} cents, "
                    f"draft_sum={draft_cost_sum} cents"
                )
        else:
            print("  PASS: Total cost within 10% of draft costs for all posts")
            passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
