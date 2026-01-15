#!/usr/bin/env python3
"""
Verification script for func-005: RalphLoop fails explicitly below quality floor.

Acceptance criteria:
1. blog_posts.status is 'failed' when quality < 0.70 at limit
2. Error log entry is created in blog_agent_activity
3. All iterations are still saved in blog_content_drafts
4. loop.run() returns failure status
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
from uuid import UUID, uuid4

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


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

    def __init__(self, tokens_per_call: int = 3000) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.generate_count = 0
        self.improve_count = 0
        self.tokens_per_call = tokens_per_call

    @property
    def agent_name(self) -> str:
        return "mock-product-marketing"

    def generate_content(self, rss_items: List[Dict[str, Any]]) -> Tuple[str, str]:
        """Generate mock content with token usage."""
        self.generate_count += 1
        self.total_input_tokens += self.tokens_per_call // 3
        self.total_output_tokens += self.tokens_per_call * 2 // 3

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
"""
        return "Mock Manufacturing Article", content

    def improve_content(self, content: str, critique: Any) -> str:
        """Simulate content improvement with token usage."""
        self.improve_count += 1
        self.total_input_tokens += self.tokens_per_call // 2
        self.total_output_tokens += self.tokens_per_call

        return content + f"\n\n### Improvement {self.improve_count}\n\nAdditional content."

    def get_total_tokens(self) -> Tuple[int, int]:
        return self.total_input_tokens, self.total_output_tokens


class MockCritiqueAgent:
    """Mock CritiqueAgent that returns configured scores."""

    def __init__(self, scores: List[float] = None, tokens_per_call: int = 1000) -> None:
        self.scores = scores or [0.50, 0.52, 0.55, 0.58, 0.60]  # All below 0.70
        self.call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.tokens_per_call = tokens_per_call

    @property
    def agent_name(self) -> str:
        return "mock-critique"

    def evaluate_content(
        self, title: str, content: str, current_score: float = 0.0
    ) -> Dict[str, Any]:
        """Return mock critique with configured score progression."""
        score = self.scores[min(self.call_count, len(self.scores) - 1)]
        self.call_count += 1
        self.total_input_tokens += self.tokens_per_call // 2
        self.total_output_tokens += self.tokens_per_call // 2

        return {
            "quality_score": score,
            "ai_slop_detected": False,
            "ai_slop_found": [],
            "main_issues": ["content quality too low"],
            "improvements": [
                {"section": "body", "problem": "poor quality", "fix": "rewrite"}
            ],
            "strengths": [],
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
                "metadata": metadata or {},
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


def create_low_quality_validator(base_score: float):
    """Create a quality validator that returns a low score (< 0.70)."""

    def mock_validator(content: str, title: str) -> Dict[str, Any]:
        return {
            "title": title,
            "overall_score": base_score,
            "ai_slop": {"has_slop": False, "found_keywords": []},
            "length": {"is_valid": False, "word_count": 200, "score": 0.3},
            "structure": {"is_valid": False, "issues": ["poor structure"], "score": 0.4},
            "brand_voice": {"is_valid": False, "issues": ["weak voice"], "score": 0.5},
        }

    return mock_validator


def run_tests() -> bool:
    """Run all verification tests."""
    from ralph_content.ralph_loop import RalphLoop

    passed = 0
    total = 4

    print("=" * 60)
    print("func-005: RalphLoop fails explicitly below quality floor")
    print("=" * 60)

    # Test 1: blog_posts.status is 'failed' when quality < 0.70 at limit
    print("\nTest 1: blog_posts.status is 'failed' when quality < 0.70 at limit")
    try:
        mock_agent = MockProductMarketingAgent(tokens_per_call=5000)
        mock_critique = MockCritiqueAgent(
            scores=[0.50, 0.55, 0.60, 0.65],  # All below 0.70
            tokens_per_call=2000,
        )
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_low_quality_validator(0.55),  # < 0.70
            quality_threshold=0.85,
            timeout_minutes=30,
            cost_limit_cents=10,  # Very low cost limit to trigger early stop
        )

        result = loop.run()

        # Check final status in blog_posts
        blog_post = mock_supabase.blog_posts[str(result.blog_post_id)]
        assert blog_post["status"] == "failed", (
            f"Status should be 'failed' for quality < 0.70, got '{blog_post['status']}'"
        )

        print(f"  PASS: blog_posts.status is 'failed' with quality {result.final_quality_score:.2f}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 2: Error log entry is created in blog_agent_activity
    print("\nTest 2: Error log entry is created in blog_agent_activity")
    try:
        mock_agent = MockProductMarketingAgent(tokens_per_call=5000)
        mock_critique = MockCritiqueAgent(
            scores=[0.45, 0.48, 0.50],  # All well below 0.70
            tokens_per_call=2000,
        )
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_low_quality_validator(0.45),  # < 0.70
            quality_threshold=0.85,
            timeout_minutes=30,
            cost_limit_cents=10,  # Low limit to trigger early stop
        )

        result = loop.run()

        # Look for finalize log with success=False
        finalize_logs = [
            log
            for log in mock_supabase.activity_logs
            if log["activity_type"] == "finalize" and log["success"] is False
        ]

        assert len(finalize_logs) > 0, "Should have a finalize log with success=False"

        finalize_log = finalize_logs[0]
        assert finalize_log["metadata"]["final_status"] == "failed", (
            f"Finalize log should have final_status='failed', got {finalize_log['metadata']}"
        )

        print("  PASS: Error log entry created with success=False and final_status='failed'")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: All iterations are still saved in blog_content_drafts
    print("\nTest 3: All iterations are still saved in blog_content_drafts")
    try:
        mock_agent = MockProductMarketingAgent(tokens_per_call=2000)
        mock_critique = MockCritiqueAgent(
            scores=[0.50, 0.55, 0.60, 0.65],  # Never reaches 0.70
            tokens_per_call=1000,
        )
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        # Use higher cost limit to allow multiple iterations before stopping
        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_low_quality_validator(0.55),
            quality_threshold=0.85,
            timeout_minutes=30,
            cost_limit_cents=50,  # Allow a few iterations
        )

        result = loop.run()

        # Verify iterations are preserved
        draft_count = len(mock_supabase.draft_iterations)
        assert draft_count >= 1, f"Should have at least 1 draft iteration, got {draft_count}"
        assert draft_count == result.iteration_count, (
            f"Draft count ({draft_count}) should match iteration count ({result.iteration_count})"
        )

        # Check all iterations have correct blog_post_id
        for draft in mock_supabase.draft_iterations:
            assert draft["blog_post_id"] == str(result.blog_post_id), (
                "All drafts should reference the same blog_post_id"
            )

        # Verify final status is still 'failed' despite saved iterations
        blog_post = mock_supabase.blog_posts[str(result.blog_post_id)]
        assert blog_post["status"] == "failed", (
            f"Status should be 'failed', got '{blog_post['status']}'"
        )

        print(f"  PASS: {draft_count} iterations preserved despite failure status")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 4: loop.run() returns failure status
    print("\nTest 4: loop.run() returns failure status")
    try:
        mock_agent = MockProductMarketingAgent(tokens_per_call=5000)
        mock_critique = MockCritiqueAgent(
            scores=[0.40, 0.45, 0.50],  # All below 0.70
            tokens_per_call=2000,
        )
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_low_quality_validator(0.40),  # Very low quality
            quality_threshold=0.85,
            timeout_minutes=30,
            cost_limit_cents=10,
        )

        result = loop.run()

        # Verify result status
        assert result.status == "failed", (
            f"Result status should be 'failed', got '{result.status}'"
        )
        assert result.final_quality_score < 0.70, (
            f"Final quality score should be < 0.70, got {result.final_quality_score}"
        )
        assert result.iteration_count >= 1, (
            f"Should have at least 1 iteration, got {result.iteration_count}"
        )

        print(f"  PASS: loop.run() returns failure status with quality {result.final_quality_score:.2f}")
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
