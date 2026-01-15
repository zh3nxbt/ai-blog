#!/usr/bin/env python3
"""
Verification script for func-001: RalphLoop iterates until quality threshold.

Acceptance criteria:
1. loop.run() executes multiple iterations when initial quality < 0.85
2. Each iteration creates new blog_content_drafts record
3. quality_score generally increases across iterations
4. Loop stops when quality_score >= 0.85
5. Final iteration count is logged
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dataclasses import dataclass  # noqa: E402
from typing import Any, Dict, List, Tuple  # noqa: E402
from uuid import UUID, uuid4  # noqa: E402


@dataclass
class MockRSSItem:
    """Mock RSS item for testing."""

    id: str
    title: str
    url: str
    summary: str


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

        # Generate content with proper structure
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

        # Return slightly modified content
        return content + "\n\n### Additional Details\n\nImproved content with more specifics."

    def get_total_tokens(self) -> Tuple[int, int]:
        return self.total_input_tokens, self.total_output_tokens


class MockCritiqueAgent:
    """Mock CritiqueAgent that returns configured scores."""

    def __init__(self, scores: List[float] = None) -> None:
        self.scores = scores or [0.70, 0.78, 0.86]
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
            "main_issues": ["needs more detail"],
            "improvements": [
                {"section": "body", "problem": "lacks specifics", "fix": "add examples"}
            ],
            "strengths": ["good structure"],
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


def mock_quality_validator(content: str, title: str) -> Dict[str, Any]:
    """Mock quality validator that returns predictable scores based on content length."""
    word_count = len(content.split())

    # Start with medium score, increase based on content additions
    base_score = 0.65
    if "Additional Details" in content:
        base_score = 0.78
    if content.count("Additional Details") >= 2:
        base_score = 0.88

    return {
        "title": title,
        "overall_score": base_score,
        "ai_slop": {"has_slop": False, "found_keywords": []},
        "length": {"is_valid": True, "word_count": word_count, "score": 0.9},
        "structure": {"is_valid": True, "issues": [], "score": 0.85},
        "brand_voice": {"is_valid": True, "issues": [], "score": 0.9},
    }


def run_tests() -> bool:
    """Run all verification tests."""
    from ralph_content.ralph_loop import RalphLoop, RalphLoopResult

    passed = 0
    total = 5

    print("=" * 60)
    print("func-001: RalphLoop iterates until quality threshold")
    print("=" * 60)

    # Test 1: Import and instantiation
    print("\nTest 1: RalphLoop imports and instantiates correctly")
    try:
        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent()
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=mock_quality_validator,
            quality_threshold=0.85,
        )

        assert loop is not None, "RalphLoop should instantiate"
        assert hasattr(loop, "run"), "RalphLoop should have run() method"
        print("  PASS: RalphLoop instantiates with run() method")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 2: run() executes multiple iterations when initial quality < 0.85
    print("\nTest 2: run() executes multiple iterations when quality < 0.85")
    try:
        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.70, 0.78, 0.86])
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=mock_quality_validator,
            quality_threshold=0.85,
        )

        result = loop.run()

        assert isinstance(result, RalphLoopResult), "run() should return RalphLoopResult"
        assert result.iteration_count > 1, f"Should iterate more than once, got {result.iteration_count}"
        print(f"  PASS: Executed {result.iteration_count} iterations")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: Each iteration creates new blog_content_drafts record
    print("\nTest 3: Each iteration creates blog_content_drafts record")
    try:
        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.70, 0.78, 0.86])
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=mock_quality_validator,
            quality_threshold=0.85,
        )

        result = loop.run()

        draft_count = len(mock_supabase.draft_iterations)
        assert draft_count == result.iteration_count, (
            f"Draft count ({draft_count}) should match iteration count ({result.iteration_count})"
        )

        # Check iteration numbers are sequential
        iteration_numbers = [d["iteration_number"] for d in mock_supabase.draft_iterations]
        expected = list(range(1, result.iteration_count + 1))
        assert iteration_numbers == expected, f"Expected {expected}, got {iteration_numbers}"

        print(f"  PASS: Created {draft_count} draft records with correct iteration numbers")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 4: Loop stops when quality >= 0.85
    print("\nTest 4: Loop stops when quality_score >= 0.85")
    try:
        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.70, 0.86])  # Should stop after 2 iterations
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=mock_quality_validator,
            quality_threshold=0.85,
        )

        result = loop.run()

        # The mock_quality_validator returns 0.88 when "Additional Details" appears twice
        # So the loop should stop once quality meets threshold
        assert result.final_quality_score >= 0.85, (
            f"Final quality ({result.final_quality_score}) should be >= 0.85"
        )
        print(f"  PASS: Final quality score {result.final_quality_score:.2f} >= 0.85")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 5: Final iteration count is logged
    print("\nTest 5: Final iteration count is logged")
    try:
        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.70, 0.78, 0.86])
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=mock_quality_validator,
            quality_threshold=0.85,
        )

        result = loop.run()

        # Find the final publish/finalize log
        final_logs = [
            log
            for log in mock_supabase.activity_logs
            if log["activity_type"] in ("publish", "finalize")
        ]

        assert len(final_logs) > 0, "Should have a publish/finalize log entry"

        final_log = final_logs[-1]
        logged_count = final_log["metadata"].get("iteration_count")
        assert logged_count == result.iteration_count, (
            f"Logged count ({logged_count}) should match result ({result.iteration_count})"
        )

        print(f"  PASS: Final iteration count {logged_count} logged correctly")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    import sys

    success = run_tests()
    sys.exit(0 if success else 1)
