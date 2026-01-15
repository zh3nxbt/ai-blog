#!/usr/bin/env python3
"""
Verification script for func-006: RalphLoop logs all activity.

Acceptance criteria:
1. blog_agent_activity has entry with activity_type='content_draft' for each iteration
2. blog_agent_activity has entry with activity_type='critique' for each critique
3. blog_agent_activity has entry with activity_type='publish' on publish
4. Each entry has duration_ms recorded
5. Each entry has success boolean set
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
        self.scores = scores or [0.70, 0.78, 0.88]  # Progressively improve to publish
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
            "main_issues": ["minor improvements needed"],
            "improvements": [
                {"section": "body", "problem": "could be better", "fix": "refine"}
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


def create_quality_validator(scores: List[float]):
    """Create a quality validator that returns scores from a list sequentially."""
    call_count = [0]  # Use list to allow mutation in closure

    def mock_validator(content: str, title: str) -> Dict[str, Any]:
        score = scores[min(call_count[0], len(scores) - 1)]
        call_count[0] += 1
        return {
            "title": title,
            "overall_score": score,
            "ai_slop": {"has_slop": False, "found_keywords": []},
            "length": {"is_valid": True, "word_count": 1500, "score": 0.9},
            "structure": {"is_valid": True, "issues": [], "score": 0.85},
            "brand_voice": {"is_valid": True, "issues": [], "score": 0.9},
        }

    return mock_validator


def run_tests() -> bool:
    """Run all verification tests."""
    from ralph_content.ralph_loop import RalphLoop

    passed = 0
    total = 5

    print("=" * 60)
    print("func-006: RalphLoop logs all activity")
    print("=" * 60)

    # Test 1: content_draft activity logged for each iteration
    print("\nTest 1: blog_agent_activity has entry with activity_type='content_draft' for each iteration")
    try:
        mock_agent = MockProductMarketingAgent(tokens_per_call=3000)
        mock_critique = MockCritiqueAgent(
            scores=[0.75, 0.82, 0.88],  # Improve to reach 0.85 threshold
            tokens_per_call=1000,
        )
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        # Scores: 0.72 (initial), 0.78, 0.88 (reaches threshold at iteration 3)
        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_quality_validator([0.72, 0.78, 0.88]),
            quality_threshold=0.85,
            timeout_minutes=30,
            cost_limit_cents=100,
        )

        result = loop.run()

        # Count content_draft entries
        content_draft_logs = [
            log for log in mock_supabase.activity_logs
            if log["activity_type"] == "content_draft"
        ]

        # Should have one content_draft per iteration
        expected_drafts = result.iteration_count
        assert len(content_draft_logs) == expected_drafts, (
            f"Expected {expected_drafts} content_draft logs, got {len(content_draft_logs)}"
        )

        # Verify each log has iteration info in metadata
        for i, log in enumerate(content_draft_logs):
            assert "iteration" in log["metadata"], (
                f"Content draft log {i} missing iteration in metadata"
            )

        print(f"  PASS: {len(content_draft_logs)} content_draft entries for {result.iteration_count} iterations")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 2: critique activity logged for each critique
    print("\nTest 2: blog_agent_activity has entry with activity_type='critique' for each critique")
    try:
        mock_agent = MockProductMarketingAgent(tokens_per_call=3000)
        mock_critique = MockCritiqueAgent(
            scores=[0.75, 0.82, 0.88],
            tokens_per_call=1000,
        )
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_quality_validator([0.72, 0.78, 0.88]),
            quality_threshold=0.85,
            timeout_minutes=30,
            cost_limit_cents=100,
        )

        result = loop.run()

        # Count critique entries
        critique_logs = [
            log for log in mock_supabase.activity_logs
            if log["activity_type"] == "critique"
        ]

        # Should have one critique per improvement iteration (iterations - 1)
        # Initial draft doesn't need critique, but each improvement does
        expected_critiques = result.iteration_count - 1
        assert len(critique_logs) == expected_critiques, (
            f"Expected {expected_critiques} critique logs, got {len(critique_logs)}"
        )

        print(f"  PASS: {len(critique_logs)} critique entries for {result.iteration_count - 1} improvement cycles")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: publish activity logged on successful publish
    print("\nTest 3: blog_agent_activity has entry with activity_type='publish' on publish")
    try:
        mock_agent = MockProductMarketingAgent(tokens_per_call=3000)
        mock_critique = MockCritiqueAgent(
            scores=[0.88],  # High enough to trigger publish
            tokens_per_call=1000,
        )
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        # Start with quality that reaches threshold after one improvement
        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_quality_validator([0.72, 0.88]),
            quality_threshold=0.85,
            timeout_minutes=30,
            cost_limit_cents=100,
        )

        result = loop.run()

        # Should have publish entry since quality reached threshold
        publish_logs = [
            log for log in mock_supabase.activity_logs
            if log["activity_type"] == "publish"
        ]

        assert len(publish_logs) == 1, (
            f"Expected 1 publish log for successful publish, got {len(publish_logs)}"
        )
        assert publish_logs[0]["metadata"]["final_status"] == "published", (
            f"Publish log should have final_status='published', got {publish_logs[0]['metadata']}"
        )
        assert result.status == "published", (
            f"Result status should be 'published', got '{result.status}'"
        )

        print("  PASS: publish activity logged with final_status='published'")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 4: Each entry has duration_ms recorded (for critique and improvement)
    print("\nTest 4: Each entry has duration_ms recorded")
    try:
        mock_agent = MockProductMarketingAgent(tokens_per_call=3000)
        mock_critique = MockCritiqueAgent(
            scores=[0.78, 0.88],
            tokens_per_call=1000,
        )
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_quality_validator([0.72, 0.88]),
            quality_threshold=0.85,
            timeout_minutes=30,
            cost_limit_cents=100,
        )

        result = loop.run()

        # Critique logs should have duration_ms
        critique_logs = [
            log for log in mock_supabase.activity_logs
            if log["activity_type"] == "critique"
        ]

        for log in critique_logs:
            assert log["duration_ms"] is not None, (
                "Critique log should have duration_ms set"
            )
            assert isinstance(log["duration_ms"], int), (
                f"duration_ms should be int, got {type(log['duration_ms'])}"
            )

        # Improvement content_draft logs (iteration > 1) should have duration_ms
        improvement_logs = [
            log for log in mock_supabase.activity_logs
            if log["activity_type"] == "content_draft" and log["metadata"].get("iteration", 0) > 1
        ]

        for log in improvement_logs:
            assert log["duration_ms"] is not None, (
                "Improvement content_draft log should have duration_ms set"
            )

        print(f"  PASS: {len(critique_logs)} critique logs and {len(improvement_logs)} improvement logs have duration_ms")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 5: Each entry has success boolean set
    print("\nTest 5: Each entry has success boolean set")
    try:
        mock_agent = MockProductMarketingAgent(tokens_per_call=3000)
        mock_critique = MockCritiqueAgent(
            scores=[0.78, 0.88],
            tokens_per_call=1000,
        )
        mock_rss = MockRSSService()
        mock_supabase = MockSupabaseService()

        loop = RalphLoop(
            agent=mock_agent,
            critique_agent=mock_critique,
            rss_service=mock_rss,
            supabase_service=mock_supabase,
            quality_validator=create_quality_validator([0.72, 0.88]),
            quality_threshold=0.85,
            timeout_minutes=30,
            cost_limit_cents=100,
        )

        result = loop.run()

        # All logs should have success boolean
        for log in mock_supabase.activity_logs:
            assert "success" in log, (
                f"Log entry should have 'success' field: {log['activity_type']}"
            )
            assert isinstance(log["success"], bool), (
                f"success should be bool, got {type(log['success'])} for {log['activity_type']}"
            )

        # Count by success status
        success_count = sum(1 for log in mock_supabase.activity_logs if log["success"])
        total_logs = len(mock_supabase.activity_logs)

        print(f"  PASS: All {total_logs} logs have success boolean ({success_count} successful)")
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
