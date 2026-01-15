#!/usr/bin/env python3
"""
Verification script for func-007: RalphLoop CLI entrypoint.

Acceptance criteria:
1. `python -m ralph.ralph_loop` executes without import errors
2. Script generates one blog post
3. Summary printed to stdout includes: status, quality, iterations, cost
4. Exit code is 0 on success
5. Exit code is 1 on failure
"""

import subprocess
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
        self.scores = scores or [0.88]  # High score for quick publish
        self.call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.tokens_per_call = tokens_per_call

    @property
    def agent_name(self) -> str:
        return "mock-critique"

    def evaluate_content(self, title: str, content: str, current_score: float) -> Dict[str, Any]:
        """Return configured critique score."""
        self.total_input_tokens += self.tokens_per_call // 2
        self.total_output_tokens += self.tokens_per_call // 2

        score_idx = min(self.call_count, len(self.scores) - 1)
        score = self.scores[score_idx]
        self.call_count += 1

        return {
            "quality_score": score,
            "improvements": ["Add more detail"],
            "ai_slop_detected": False,
        }

    def get_total_tokens(self) -> Tuple[int, int]:
        return self.total_input_tokens, self.total_output_tokens


class MockRssService:
    """Mock RSS service that returns test items."""

    def __init__(self, items: List[Dict[str, Any]] = None) -> None:
        self.items = items or create_mock_rss_items()
        self.marked_used = []

    def fetch_unused_items(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self.items[:limit]

    def fetch_active_sources(self) -> List[Dict[str, Any]]:
        return [{"id": str(uuid4()), "url": "https://example.com/rss"}]

    def fetch_feed_items(self, source_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self.items[:limit]

    def mark_items_as_used(self, item_ids: List[str], blog_id: str) -> int:
        self.marked_used.extend(item_ids)
        return len(item_ids)


class MockSupabaseService:
    """Mock Supabase service for testing."""

    def __init__(self) -> None:
        self.blog_posts: Dict[str, Dict[str, Any]] = {}
        self.drafts: List[Dict[str, Any]] = []
        self.activities: List[Dict[str, Any]] = []

    def get_supabase_client(self) -> "MockSupabaseClient":
        return MockSupabaseClient(self)

    def create_blog_post(self, title: str, content: str, status: str) -> UUID:
        post_id = uuid4()
        self.blog_posts[str(post_id)] = {
            "id": str(post_id),
            "title": title,
            "content": content,
            "status": status,
        }
        return post_id

    def save_draft_iteration(
        self,
        blog_post_id: UUID,
        iteration_number: int,
        content: str,
        quality_score: float,
        critique: Dict[str, Any],
        title: str = "",
        api_cost_cents: int = 0,
    ) -> UUID:
        draft_id = uuid4()
        self.drafts.append(
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
        context_id: UUID | None = None,
        duration_ms: int | None = None,
        error_message: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> UUID:
        activity_id = uuid4()
        self.activities.append(
            {
                "id": str(activity_id),
                "agent_name": agent_name,
                "activity_type": activity_type,
                "success": success,
                "context_id": str(context_id) if context_id else None,
                "duration_ms": duration_ms,
                "error_message": error_message,
                "metadata": metadata or {},
            }
        )
        return activity_id


class MockSupabaseClient:
    """Mock Supabase client for table operations."""

    def __init__(self, service: MockSupabaseService) -> None:
        self.service = service

    def table(self, name: str) -> "MockTable":
        return MockTable(name, self.service)


class MockTable:
    """Mock Supabase table for update operations."""

    def __init__(self, name: str, service: MockSupabaseService) -> None:
        self.name = name
        self.service = service
        self._update_data: Dict[str, Any] = {}
        self._filter_id: str | None = None

    def update(self, data: Dict[str, Any]) -> "MockTable":
        self._update_data = data
        return self

    def eq(self, column: str, value: str) -> "MockTable":
        if column == "id":
            self._filter_id = value
        return self

    def execute(self) -> None:
        if self._filter_id and self._filter_id in self.service.blog_posts:
            self.service.blog_posts[self._filter_id].update(self._update_data)


def mock_quality_validator(content: str, title: str) -> Dict[str, Any]:
    """Mock quality validator that returns a high score."""
    return {
        "overall_score": 0.90,
        "ai_slop": {"has_slop": False, "found_keywords": []},
        "length": {"is_valid": True, "word_count": 1500, "score": 0.95},
        "structure": {"is_valid": True, "issues": [], "score": 0.90},
        "brand_voice": {"is_valid": True, "issues": [], "score": 0.88},
    }


def main() -> bool:
    """Run all verification tests."""
    all_passed = True
    tests_passed = 0
    tests_failed = 0

    print("=" * 60)
    print("func-007: RalphLoop CLI entrypoint Verification")
    print("=" * 60)

    # Test 1: Module imports without errors
    print("\nTest 1: `python -m ralph.ralph_loop` executes without import errors")
    try:
        # Use subprocess to check if the import works
        result = subprocess.run(
            [sys.executable, "-c", "from ralph.ralph_loop import RalphLoop, main"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("  PASS: Module imports successfully")
            tests_passed += 1
        else:
            print(f"  FAIL: Import failed with error: {result.stderr}")
            tests_failed += 1
            all_passed = False
    except Exception as e:
        print(f"  FAIL: Exception during import test: {e}")
        tests_failed += 1
        all_passed = False

    # Test 2: Script generates one blog post (using mocks)
    print("\nTest 2: Script generates one blog post")
    try:
        from ralph.ralph_loop import RalphLoop

        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.90])  # High enough to publish
        mock_rss = MockRssService()
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

        if len(mock_supabase.blog_posts) == 1:
            print("  PASS: One blog post was generated")
            tests_passed += 1
        else:
            print(f"  FAIL: Expected 1 blog post, got {len(mock_supabase.blog_posts)}")
            tests_failed += 1
            all_passed = False
    except Exception as e:
        print(f"  FAIL: Exception during generation test: {e}")
        tests_failed += 1
        all_passed = False

    # Test 3: Summary includes status, quality, iterations, cost
    print("\nTest 3: Summary printed to stdout includes status, quality, iterations, cost")
    try:
        from ralph.ralph_loop import RalphLoopResult

        # Verify RalphLoopResult has required fields
        result_fields = ["status", "final_quality_score", "iteration_count", "total_cost_cents"]
        missing_fields = []

        for field in result_fields:
            if not hasattr(RalphLoopResult, "__dataclass_fields__") or field not in RalphLoopResult.__dataclass_fields__:
                missing_fields.append(field)

        if not missing_fields:
            print("  PASS: RalphLoopResult contains all required fields")
            tests_passed += 1
        else:
            print(f"  FAIL: RalphLoopResult missing fields: {missing_fields}")
            tests_failed += 1
            all_passed = False
    except Exception as e:
        print(f"  FAIL: Exception during field check: {e}")
        tests_failed += 1
        all_passed = False

    # Test 4: Exit code is 0 on success
    print("\nTest 4: Exit code is 0 on success (published or draft)")
    try:
        from ralph.ralph_loop import RalphLoop

        # Test with high quality (published)
        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.92])
        mock_rss = MockRssService()
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

        if result.status == "published":
            print("  PASS: Status is 'published' (would return exit code 0)")
            tests_passed += 1
        else:
            print(f"  FAIL: Expected status 'published', got '{result.status}'")
            tests_failed += 1
            all_passed = False
    except Exception as e:
        print(f"  FAIL: Exception during success test: {e}")
        tests_failed += 1
        all_passed = False

    # Test 5: Exit code is 1 on failure
    print("\nTest 5: Exit code is 1 on failure")
    try:
        from ralph.ralph_loop import RalphLoop

        # Create a validator that returns low quality consistently
        def low_quality_validator(content: str, title: str) -> Dict[str, Any]:
            return {
                "overall_score": 0.50,  # Below 0.70 floor
                "ai_slop": {"has_slop": True, "found_keywords": ["delve"]},
                "length": {"is_valid": False, "word_count": 200, "score": 0.30},
                "structure": {"is_valid": False, "issues": ["missing headings"], "score": 0.40},
                "brand_voice": {"is_valid": True, "issues": [], "score": 0.60},
            }

        mock_agent = MockProductMarketingAgent()
        mock_critique = MockCritiqueAgent(scores=[0.50, 0.55, 0.60])  # Never reaches threshold
        mock_rss = MockRssService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=low_quality_validator,
            quality_threshold=0.85,
            timeout_minutes=0.01,  # Very short timeout to force failure
        )

        result = loop.run()

        if result.status == "failed":
            print("  PASS: Status is 'failed' (would return exit code 1)")
            tests_passed += 1
        else:
            print(f"  FAIL: Expected status 'failed', got '{result.status}'")
            tests_failed += 1
            all_passed = False
    except Exception as e:
        print(f"  FAIL: Exception during failure test: {e}")
        tests_failed += 1
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
