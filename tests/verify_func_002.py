#!/usr/bin/env python3
"""
Verification script for func-002: RalphLoop publishes on quality threshold.

Acceptance criteria:
1. When quality >= 0.85, blog_posts.status becomes 'published'
2. published_at timestamp is set to current time
3. Final content_markdown matches best iteration content
4. loop.run() returns success status
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Any, Dict, List, Tuple  # noqa: E402
from uuid import UUID, uuid4  # noqa: E402


def create_mock_rss_items(count: int = 3) -> List[Dict[str, Any]]:
    """Create mock RSS items for testing."""
    return [
        {
            "id": str(uuid4()),
            "title": f"Manufacturing News {i}",
            "url": f"https://example.com/article-{i}",
            "summary": f"Summary of manufacturing article {i} about CNC machining.",
        }
        for i in range(count)
    ]


class MockProductMarketingAgent:
    """Mock ProductMarketingAgent that simulates content generation."""

    def __init__(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.generate_count = 0
        self.improve_count = 0

    @property
    def agent_name(self) -> str:
        return "mock-product-marketing"

    def generate_content(self, rss_items: List[Dict[str, Any]]) -> Tuple[str, str]:
        """Generate mock content."""
        self.generate_count += 1
        self.total_input_tokens += 500
        self.total_output_tokens += 2000

        content = """## Introduction

This is the introduction paragraph about manufacturing trends.

## Main Section

Here we discuss the details of CNC machining and precision parts.

### Subsection A

Details about tolerances and specifications.

### Subsection B

Information about material selection.

## Conclusion

Summary of the key points discussed.

## Sources

- https://example.com/source-1
- https://example.com/source-2
"""
        return "Mock Manufacturing Article", content

    def improve_content(self, content: str, critique: Any) -> str:
        """Simulate content improvement."""
        self.improve_count += 1
        self.total_input_tokens += 800
        self.total_output_tokens += 2500
        return content + "\n\n### Additional Details\n\nImproved content with more specifics."

    def get_total_tokens(self) -> Tuple[int, int]:
        return self.total_input_tokens, self.total_output_tokens


class MockCritiqueAgent:
    """Mock CritiqueAgent that returns configured scores."""

    def __init__(self, scores: List[float] = None) -> None:
        self.scores = scores or [0.86]  # Default to high score
        self.call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    @property
    def agent_name(self) -> str:
        return "mock-critique"

    def evaluate_content(
        self, title: str, content: str, current_score: float = 0.0
    ) -> Dict[str, Any]:
        """Return mock critique with configured score progression."""
        score = self.scores[min(self.call_count, len(self.scores) - 1)]
        self.call_count += 1
        self.total_input_tokens += 300
        self.total_output_tokens += 500

        return {
            "quality_score": score,
            "ai_slop_detected": False,
            "ai_slop_found": [],
            "main_issues": [],
            "improvements": [],
            "strengths": ["good structure", "clear writing"],
        }

    def get_total_tokens(self) -> Tuple[int, int]:
        return self.total_input_tokens, self.total_output_tokens


class MockRSSService:
    """Mock RSS service for testing."""

    def __init__(self) -> None:
        self.items = create_mock_rss_items(5)
        self.marked_items: List[str] = []

    def fetch_unused_items(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self.items[:limit]

    def fetch_active_sources(self) -> List[Dict[str, Any]]:
        return [{"id": str(uuid4()), "name": "Test Source", "url": "https://example.com/rss"}]

    def fetch_feed_items(self, source_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self.items

    def mark_items_as_used(self, item_ids: List[str], blog_id: str) -> int:
        self.marked_items.extend(item_ids)
        return len(item_ids)


class MockSupabaseService:
    """Mock Supabase service for testing."""

    def __init__(self) -> None:
        self.blog_posts: Dict[str, Dict[str, Any]] = {}
        self.draft_iterations: List[Dict[str, Any]] = []
        self.activity_logs: List[Dict[str, Any]] = []

    def create_blog_post(self, title: str, content: str, status: str = "draft") -> UUID:
        blog_id = uuid4()
        self.blog_posts[str(blog_id)] = {
            "id": str(blog_id),
            "title": title,
            "content": content,
            "status": status,
            "published_at": None,
        }
        return blog_id

    def save_draft_iteration(
        self,
        blog_post_id: UUID,
        iteration_number: int,
        content: str,
        quality_score: float,
        critique: dict,
        title: str = None,
        api_cost_cents: int = 0,
    ) -> UUID:
        draft_id = uuid4()
        self.draft_iterations.append(
            {
                "id": str(draft_id),
                "blog_post_id": str(blog_post_id),
                "iteration_number": iteration_number,
                "content": content,
                "quality_score": quality_score,
                "critique": critique,
                "title": title,
                "api_cost_cents": api_cost_cents,
            }
        )
        return draft_id

    def log_agent_activity(
        self,
        agent_name: str,
        activity_type: str,
        success: bool,
        context_id: UUID = None,
        duration_ms: int = None,
        error_message: str = None,
        metadata: dict = None,
    ) -> UUID:
        log_id = uuid4()
        self.activity_logs.append(
            {
                "id": str(log_id),
                "agent_name": agent_name,
                "activity_type": activity_type,
                "success": success,
                "context_id": str(context_id) if context_id else None,
                "duration_ms": duration_ms,
                "error_message": error_message,
                "metadata": metadata,
            }
        )
        return log_id

    def get_supabase_client(self) -> "MockSupabaseClient":
        return MockSupabaseClient(self)


class MockSupabaseClient:
    """Mock Supabase client for update operations."""

    def __init__(self, service: MockSupabaseService) -> None:
        self._service = service
        self._table_name = None
        self._update_data = None
        self._filter_column = None
        self._filter_value = None

    def table(self, name: str) -> "MockSupabaseClient":
        self._table_name = name
        return self

    def update(self, data: Dict[str, Any]) -> "MockSupabaseClient":
        self._update_data = data
        return self

    def eq(self, column: str, value: str) -> "MockSupabaseClient":
        self._filter_column = column
        self._filter_value = value
        return self

    def execute(self) -> Any:
        if self._table_name == "blog_posts" and self._update_data:
            blog_id = self._filter_value
            if blog_id in self._service.blog_posts:
                self._service.blog_posts[blog_id].update(self._update_data)
        return type("Response", (), {"data": [{"id": self._filter_value}]})()


def create_high_quality_validator(target_score: float = 0.88):
    """Create a quality validator that returns a specified score."""

    def validator(content: str, title: str) -> Dict[str, Any]:
        word_count = len(content.split())
        return {
            "title": title,
            "overall_score": target_score,
            "ai_slop": {"has_slop": False, "found_keywords": []},
            "length": {"is_valid": True, "word_count": word_count, "score": 0.9},
            "structure": {"is_valid": True, "issues": [], "score": 0.95},
            "brand_voice": {"is_valid": True, "issues": [], "score": 0.92},
        }

    return validator


def run_tests() -> bool:
    """Run all verification tests."""
    from ralph_content.ralph_loop import RalphLoop, RalphLoopResult

    passed = 0
    total = 4

    print("=" * 60)
    print("func-002: RalphLoop publishes on quality threshold")
    print("=" * 60)

    # Test 1: When quality >= 0.85, blog_posts.status becomes 'published'
    print("\nTest 1: When quality >= 0.85, blog_posts.status becomes 'published'")
    try:
        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.90])
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_high_quality_validator(0.88),
            quality_threshold=0.85,
        )

        result = loop.run()

        # Check that the blog post status is 'published'
        blog_post = mock_supabase.blog_posts[str(result.blog_post_id)]
        assert blog_post["status"] == "published", (
            f"Expected status 'published', got '{blog_post['status']}'"
        )

        print(f"  PASS: Status is 'published' (quality: {result.final_quality_score:.2f})")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 2: published_at timestamp is set to current time
    print("\nTest 2: published_at timestamp is set to current time")
    try:
        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.90])
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        before_run = datetime.now(timezone.utc)

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_high_quality_validator(0.88),
            quality_threshold=0.85,
        )

        result = loop.run()

        after_run = datetime.now(timezone.utc)

        blog_post = mock_supabase.blog_posts[str(result.blog_post_id)]
        published_at_str = blog_post.get("published_at")

        assert published_at_str is not None, "published_at should be set"

        # Parse the ISO timestamp
        published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))

        assert before_run <= published_at <= after_run, (
            f"published_at ({published_at}) should be between {before_run} and {after_run}"
        )

        print(f"  PASS: published_at is set ({published_at_str})")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: Final content matches best iteration content
    print("\nTest 3: Final content matches best iteration content")
    try:
        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.90])
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_high_quality_validator(0.88),
            quality_threshold=0.85,
        )

        result = loop.run()

        blog_post = mock_supabase.blog_posts[str(result.blog_post_id)]

        # Find the last iteration (best content)
        iterations_for_post = [
            d for d in mock_supabase.draft_iterations
            if d["blog_post_id"] == str(result.blog_post_id)
        ]
        iterations_for_post.sort(key=lambda x: x["iteration_number"])
        last_iteration = iterations_for_post[-1]

        # Content in blog_posts should match the last iteration's content
        assert blog_post["content"] == last_iteration["content"], (
            "Blog post content should match last iteration content"
        )

        print(f"  PASS: Final content matches iteration {last_iteration['iteration_number']} content")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 4: loop.run() returns success status
    print("\nTest 4: loop.run() returns success status")
    try:
        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.90])
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_high_quality_validator(0.88),
            quality_threshold=0.85,
        )

        result = loop.run()

        assert isinstance(result, RalphLoopResult), "run() should return RalphLoopResult"
        assert result.status == "published", f"Expected status 'published', got '{result.status}'"
        assert result.final_quality_score >= 0.85, (
            f"Final quality score ({result.final_quality_score}) should be >= 0.85"
        )
        assert result.blog_post_id is not None, "blog_post_id should not be None"
        assert result.iteration_count >= 1, "iteration_count should be >= 1"

        print("  PASS: Returns RalphLoopResult with status='published'")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
