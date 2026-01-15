#!/usr/bin/env python3
"""
Verification script for test-002: Content improves over iterations.

Acceptance criteria:
1. Iteration 2 quality_score > Iteration 1 quality_score (typical case)
2. Iteration 3 quality_score > Iteration 2 quality_score (typical case)
3. Final published post has quality >= 0.85
4. Average iterations to publish is 2-4
"""

import sys
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
    """Mock ProductMarketingAgent that simulates content generation with improvements."""

    def __init__(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.generate_count = 0
        self.improve_count = 0

    @property
    def agent_name(self) -> str:
        return "mock-product-marketing"

    def generate_content(self, rss_items: List[Dict[str, Any]]) -> Tuple[str, str]:
        """Generate mock content with initial quality issues."""
        self.generate_count += 1
        self.total_input_tokens += 500
        self.total_output_tokens += 2000

        # Initial content has some structure issues (missing H3)
        content = """## Introduction

This is the introduction paragraph about manufacturing trends.

## Main Section

Here we discuss the details of CNC machining and precision parts.

Some additional information about the manufacturing process.

## Conclusion

Summary of the key points discussed.

## Sources

- https://example.com/source-1
- https://example.com/source-2
"""
        return "Mock Manufacturing Article", content

    def improve_content(self, content: str, critique: Any) -> str:
        """Simulate content improvement based on critique feedback."""
        self.improve_count += 1
        self.total_input_tokens += 800
        self.total_output_tokens += 2500

        # Each improvement adds more structure
        if self.improve_count == 1:
            # First improvement: add subsections
            return content.replace(
                "## Main Section\n\nHere we discuss",
                "## Main Section\n\n### Technical Details\n\nHere we discuss"
            ) + "\n### Additional Considerations\n\nMore detailed analysis."

        elif self.improve_count == 2:
            # Second improvement: add more depth and detail
            return content + "\n\n### Industry Applications\n\nReal-world examples and use cases."

        else:
            # Further improvements: minor refinements
            return content + f"\n\n### Update {self.improve_count}\n\nFurther refinements."

    def get_total_tokens(self) -> Tuple[int, int]:
        return self.total_input_tokens, self.total_output_tokens


class MockCritiqueAgentProgressive:
    """Mock CritiqueAgent that returns progressively improving scores."""

    def __init__(self, score_sequence: List[float]) -> None:
        """
        Initialize with a sequence of scores to return.

        Args:
            score_sequence: List of scores to return for each evaluation.
                           For example [0.65, 0.78, 0.88] would return
                           0.65 on first call, 0.78 on second, 0.88 on third.
        """
        self.score_sequence = score_sequence
        self.call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    @property
    def agent_name(self) -> str:
        return "mock-critique"

    def evaluate_content(
        self, title: str, content: str, current_score: float = 0.0
    ) -> Dict[str, Any]:
        """Return mock critique with progressively improving scores."""
        self.call_count += 1
        self.total_input_tokens += 300
        self.total_output_tokens += 500

        # Get the score for this call (use last score if we exceed sequence length)
        idx = min(self.call_count - 1, len(self.score_sequence) - 1)
        score = self.score_sequence[idx]

        # Simulate critique based on score
        if score < 0.70:
            return {
                "quality_score": score,
                "ai_slop_detected": False,
                "ai_slop_found": [],
                "main_issues": ["lacks depth", "needs more subsections", "structure could improve"],
                "improvements": ["add H3 subsections", "include specific examples", "expand analysis"],
                "strengths": ["clear topic focus"],
            }
        elif score < 0.85:
            return {
                "quality_score": score,
                "ai_slop_detected": False,
                "ai_slop_found": [],
                "main_issues": ["could use more detail"],
                "improvements": ["add real-world examples"],
                "strengths": ["good structure", "clear writing"],
            }
        else:
            return {
                "quality_score": score,
                "ai_slop_detected": False,
                "ai_slop_found": [],
                "main_issues": [],
                "improvements": [],
                "strengths": ["excellent structure", "clear writing", "practical examples"],
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


def create_progressive_validator(score_sequence: List[float]):
    """Create a quality validator that returns progressively improving scores."""
    call_count = [0]  # Use list to allow modification in closure

    def validator(content: str, title: str) -> Dict[str, Any]:
        idx = min(call_count[0], len(score_sequence) - 1)
        score = score_sequence[idx]
        call_count[0] += 1

        word_count = len(content.split())
        return {
            "title": title,
            "overall_score": score,
            "ai_slop": {"has_slop": False, "found_keywords": []},
            "length": {"is_valid": True, "word_count": word_count, "score": 0.85 + (score - 0.65) * 0.5},
            "structure": {"is_valid": score >= 0.70, "issues": [] if score >= 0.70 else ["needs more structure"], "score": score},
            "brand_voice": {"is_valid": True, "issues": [], "score": 0.90},
        }

    return validator


def run_tests() -> bool:
    """Run all verification tests."""
    from ralph_content.ralph_loop import RalphLoop

    passed = 0
    total = 4

    print("=" * 60)
    print("test-002: Content improves over iterations")
    print("=" * 60)

    # Test 1: Iteration 2 quality_score > Iteration 1 quality_score
    print("\nTest 1: Iteration 2 quality_score > Iteration 1 quality_score")
    try:
        # Score sequence: 0.65 -> 0.78 -> 0.88 (improves each iteration)
        score_sequence = [0.65, 0.78, 0.88]

        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgentProgressive(score_sequence)
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_progressive_validator(score_sequence),
            quality_threshold=0.85,
        )

        result = loop.run()

        # Get iterations sorted by iteration_number
        iterations = sorted(
            [d for d in mock_supabase.draft_iterations if d["blog_post_id"] == str(result.blog_post_id)],
            key=lambda x: x["iteration_number"]
        )

        assert len(iterations) >= 2, f"Expected at least 2 iterations, found {len(iterations)}"

        iter1_score = iterations[0]["quality_score"]
        iter2_score = iterations[1]["quality_score"]

        assert iter2_score > iter1_score, (
            f"Expected iter2 ({iter2_score}) > iter1 ({iter1_score})"
        )

        print(f"  PASS: Iteration 2 ({iter2_score:.2f}) > Iteration 1 ({iter1_score:.2f})")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 2: Iteration 3 quality_score > Iteration 2 quality_score
    print("\nTest 2: Iteration 3 quality_score > Iteration 2 quality_score")
    try:
        # Score sequence: 0.60 -> 0.72 -> 0.82 -> 0.90 (needs 4 iterations)
        score_sequence = [0.60, 0.72, 0.82, 0.90]

        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgentProgressive(score_sequence)
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_progressive_validator(score_sequence),
            quality_threshold=0.85,
        )

        result = loop.run()

        # Get iterations sorted by iteration_number
        iterations = sorted(
            [d for d in mock_supabase.draft_iterations if d["blog_post_id"] == str(result.blog_post_id)],
            key=lambda x: x["iteration_number"]
        )

        assert len(iterations) >= 3, f"Expected at least 3 iterations, found {len(iterations)}"

        iter2_score = iterations[1]["quality_score"]
        iter3_score = iterations[2]["quality_score"]

        assert iter3_score > iter2_score, (
            f"Expected iter3 ({iter3_score}) > iter2 ({iter2_score})"
        )

        print(f"  PASS: Iteration 3 ({iter3_score:.2f}) > Iteration 2 ({iter2_score:.2f})")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: Final published post has quality >= 0.85
    print("\nTest 3: Final published post has quality >= 0.85")
    try:
        # Score sequence that ends above 0.85 threshold
        score_sequence = [0.65, 0.78, 0.88]

        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgentProgressive(score_sequence)
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_progressive_validator(score_sequence),
            quality_threshold=0.85,
        )

        result = loop.run()

        assert result.status == "published", (
            f"Expected status 'published', got '{result.status}'"
        )
        assert result.final_quality_score >= 0.85, (
            f"Expected final quality >= 0.85, got {result.final_quality_score}"
        )

        blog_post = mock_supabase.blog_posts[str(result.blog_post_id)]
        assert blog_post["status"] == "published", (
            f"Expected blog_post status 'published', got '{blog_post['status']}'"
        )

        print(f"  PASS: Final published post has quality {result.final_quality_score:.2f} >= 0.85")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 4: Average iterations to publish is 2-4
    print("\nTest 4: Average iterations to publish is 2-4")
    try:
        # Run multiple simulations with different score progressions
        total_iterations = 0
        num_runs = 5

        test_sequences = [
            [0.65, 0.78, 0.88],        # 3 iterations
            [0.72, 0.86],               # 2 iterations
            [0.60, 0.70, 0.80, 0.87],  # 4 iterations
            [0.70, 0.85],               # 2 iterations
            [0.62, 0.75, 0.88],        # 3 iterations
        ]

        for score_sequence in test_sequences:
            mock_agent = MockProductMarketingAgent()
            mock_critique = MockCritiqueAgentProgressive(score_sequence)
            mock_rss = MockRSSService()
            mock_supabase = MockSupabaseService()

            loop = RalphLoop(
                agent=mock_agent,
                critique_agent=mock_critique,
                rss_service=mock_rss,
                supabase_service=mock_supabase,
                quality_validator=create_progressive_validator(score_sequence),
                quality_threshold=0.85,
            )

            result = loop.run()
            total_iterations += result.iteration_count

        avg_iterations = total_iterations / num_runs

        assert 2 <= avg_iterations <= 4, (
            f"Expected average iterations 2-4, got {avg_iterations:.1f}"
        )

        print(f"  PASS: Average iterations to publish is {avg_iterations:.1f} (target: 2-4)")
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
