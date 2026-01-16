#!/usr/bin/env python3
"""Verification script for mix-004: mixed-source selection in RalphLoop.

Acceptance Criteria:
1. RalphLoop selects 3-5 items using a source mix (default ratio documented)
2. Selection falls back gracefully when a source type is short
3. All selected items are marked used_in_blog
4. Agent activity logs include source mix metadata
"""

import sys
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID, uuid4


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_mock_items(prefix: str, source_type: str, count: int) -> List[Dict[str, Any]]:
    """Create mock items for a given source type."""
    items: List[Dict[str, Any]] = []
    for idx in range(count):
        items.append({
            "id": str(uuid4()),
            "title": f"{prefix} {idx + 1}",
            "summary": f"Summary for {prefix} {idx + 1}",
            "url": f"https://example.com/{prefix.lower()}-{idx + 1}",
            "source_type": source_type,
        })
    return items


class MockRssService:
    """Mock RSS service for mixed-source selection."""

    def __init__(self, items: List[Dict[str, Any]]) -> None:
        self.items = items
        self.marked_ids: List[str] = []

    def fetch_unused_items(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self.items[:limit]

    def fetch_active_sources(self) -> List[Dict[str, Any]]:
        return []

    def fetch_feed_items(self, source_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return []

    def mark_items_as_used(self, item_ids: List[str], blog_id: str) -> int:
        self.marked_ids.extend(item_ids)
        return len(item_ids)


class MockTopicItemService:
    """Mock topic item service for mixed-source selection."""

    def __init__(self, items_by_type: Dict[str, List[Dict[str, Any]]]) -> None:
        self.items_by_type = items_by_type
        self.marked_ids: List[str] = []

    def fetch_unused_items_by_source_type(self, source_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        items = self.items_by_type.get(source_type, [])[:limit]
        for item in items:
            item.setdefault("source_type", source_type)
        return items

    def mark_items_as_used(self, item_ids: List[str], blog_id: str) -> int:
        self.marked_ids.extend(item_ids)
        return len(item_ids)


class MockSupabaseClient:
    """Mock Supabase client update chain."""

    def table(self, _table: str) -> "MockSupabaseClient":
        return self

    def update(self, _data: Dict[str, Any]) -> "MockSupabaseClient":
        return self

    def eq(self, _field: str, _value: str) -> "MockSupabaseClient":
        return self

    def execute(self) -> "MockSupabaseClient":
        return self


class MockSupabaseService:
    """Mock Supabase service to capture logs and drafts."""

    def __init__(self) -> None:
        self.activities: List[Dict[str, Any]] = []

    def create_blog_post(self, title: str, content: str, status: str = "draft") -> UUID:
        return uuid4()

    def save_draft_iteration(
        self,
        blog_post_id: UUID,
        iteration_number: int,
        content: str,
        quality_score: float,
        critique: Dict[str, Any],
        title: str = None,
        api_cost_cents: int = 0,
    ) -> UUID:
        return uuid4()

    def log_agent_activity(
        self,
        agent_name: str,
        activity_type: str,
        success: bool,
        context_id: UUID = None,
        duration_ms: int = None,
        error_message: str = None,
        metadata: Dict[str, Any] = None,
    ) -> UUID:
        self.activities.append({
            "agent_name": agent_name,
            "activity_type": activity_type,
            "success": success,
            "metadata": metadata or {},
        })
        return uuid4()

    def get_supabase_client(self) -> MockSupabaseClient:
        return MockSupabaseClient()


class MockProductMarketingAgent:
    """Mock content agent returning deterministic content."""

    def __init__(self) -> None:
        self.total_input_tokens = 500
        self.total_output_tokens = 2000

    @property
    def agent_name(self) -> str:
        return "mock-product-marketing"

    def generate_content(self, source_items: List[Dict[str, Any]]) -> tuple[str, str]:
        return "Mock Mixed Sources Post", "## Title\n\nMock content."

    def improve_content(self, content: str, critique: Dict[str, Any]) -> str:
        return content

    def get_total_tokens(self) -> tuple[int, int]:
        return (self.total_input_tokens, self.total_output_tokens)


class MockCritiqueAgent:
    """Mock critique agent."""

    @property
    def agent_name(self) -> str:
        return "mock-critique"

    def evaluate_content(self, title: str, content: str, current_score: float) -> Dict[str, Any]:
        return {"quality_score": current_score}

    def get_total_tokens(self) -> tuple[int, int]:
        return (0, 0)


def mock_quality_validator(content: str, title: str) -> Dict[str, Any]:
    """Return a high quality score to avoid iteration loop."""
    return {"overall_score": 0.9}


def verify_mix_004() -> bool:
    """Verify all acceptance criteria for mix-004."""
    print("=" * 60)
    print("VERIFICATION: mix-004 - mixed-source selection in RalphLoop")
    print("=" * 60)

    passed = 0
    total = 4

    from ralph_content.ralph_loop import RalphLoop

    print("\n[1/4] Verifying default source mix is documented and used...")
    default_mix = getattr(RalphLoop, "DEFAULT_SOURCE_MIX", {})
    if isinstance(default_mix, dict) and "rss" in default_mix and "evergreen" in default_mix:
        print(f"✓ Default source mix documented: {default_mix}")
    else:
        print("✗ DEFAULT_SOURCE_MIX missing expected keys")
        return False

    rss_items = create_mock_items("RSS Item", "rss", 4)
    evergreen_items = create_mock_items("Evergreen Topic", "evergreen", 1)
    vendor_items = create_mock_items("Vendor Update", "vendor", 1)

    mock_rss = MockRssService(rss_items)
    mock_topic = MockTopicItemService({
        "evergreen": evergreen_items,
        "vendor": vendor_items,
        "standards": [],
    })
    mock_supabase = MockSupabaseService()

    loop = RalphLoop(
        agent=MockProductMarketingAgent(),
        critique_agent=MockCritiqueAgent(),
        rss_service=mock_rss,
        topic_item_service=mock_topic,
        supabase_service=mock_supabase,
        quality_validator=mock_quality_validator,
        min_items=3,
        max_items=5,
        quality_threshold=0.85,
    )

    result = loop.run()

    total_selected = len(mock_rss.marked_ids) + len(mock_topic.marked_ids)
    if 3 <= total_selected <= 5:
        print(f"✓ Selected {total_selected} items using source mix")
        passed += 1
    else:
        print(f"✗ Selected {total_selected} items, expected 3-5")

    print("\n[2/4] Verifying fallback when a source type is short...")
    if len(mock_rss.marked_ids) >= 3 and len(mock_topic.marked_ids) == 2:
        print("✓ Fallback filled missing standards items with other sources")
        passed += 1
    else:
        print(
            "✗ Fallback did not fill shortages as expected "
            f"(rss={len(mock_rss.marked_ids)}, topic={len(mock_topic.marked_ids)})"
        )

    print("\n[3/4] Verifying selected items are marked used_in_blog...")
    if mock_rss.marked_ids and mock_topic.marked_ids:
        print("✓ RSS and topic items were marked as used")
        passed += 1
    else:
        print("✗ Expected both RSS and topic items to be marked as used")

    print("\n[4/4] Verifying activity logs include source mix metadata...")
    has_mix_metadata = any(
        activity.get("metadata", {}).get("source_mix")
        for activity in mock_supabase.activities
        if activity.get("activity_type") == "content_draft"
    )
    if has_mix_metadata:
        print("✓ Activity log includes source mix metadata")
        passed += 1
    else:
        print("✗ Activity log missing source mix metadata")

    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    if result.status not in ("published", "draft"):
        print("✗ RalphLoop returned unexpected status")
        return False

    return passed == total


if __name__ == "__main__":
    try:
        success = verify_mix_004()
        sys.exit(0 if success else 1)
    except Exception as exc:
        print(f"\n✗ Verification failed with error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
