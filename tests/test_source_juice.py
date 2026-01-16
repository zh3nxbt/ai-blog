"""Tests for source juice evaluation."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestSourcesFreshnessCheck:
    """Tests for _check_sources_freshness method."""

    @pytest.fixture
    def ralph_loop(self):
        """Create a RalphLoop instance with mocked dependencies."""
        with patch("ralph_content.ralph_loop.ProductMarketingAgent"):
            with patch("ralph_content.ralph_loop.CritiqueAgent"):
                with patch("ralph_content.ralph_loop.Anthropic"):
                    from ralph_content.ralph_loop import RalphLoop

                    # Create mock services
                    mock_rss_service = MagicMock()
                    mock_topic_item_service = MagicMock()
                    mock_supabase_service = MagicMock()

                    loop = RalphLoop(
                        rss_service=mock_rss_service,
                        topic_item_service=mock_topic_item_service,
                        supabase_service=mock_supabase_service,
                        juice_threshold=0.6,
                    )
                    return loop

    def test_empty_sources_fails_freshness(self, ralph_loop):
        """Empty source items should fail freshness check."""
        is_fresh, reason = ralph_loop._check_sources_freshness([])
        assert is_fresh is False
        assert "No source items available" in reason

    def test_fresh_sources_pass(self, ralph_loop):
        """Sources published within 48 hours should pass."""
        now = datetime.now(timezone.utc)
        sources = [
            {"title": "Fresh Item", "published_at": now.isoformat()},
            {
                "title": "Recent Item",
                "published_at": (now - timedelta(hours=24)).isoformat(),
            },
        ]
        is_fresh, reason = ralph_loop._check_sources_freshness(sources)
        assert is_fresh is True
        assert "2/2 sources are fresh" in reason

    def test_stale_sources_fail(self, ralph_loop):
        """Sources older than 48 hours should fail."""
        now = datetime.now(timezone.utc)
        sources = [
            {
                "title": "Stale Item",
                "published_at": (now - timedelta(hours=72)).isoformat(),
            },
            {
                "title": "Old Item",
                "published_at": (now - timedelta(hours=100)).isoformat(),
            },
        ]
        is_fresh, reason = ralph_loop._check_sources_freshness(sources)
        assert is_fresh is False
        assert "older than 48 hours" in reason

    def test_mixed_freshness_passes(self, ralph_loop):
        """At least one fresh source should pass."""
        now = datetime.now(timezone.utc)
        sources = [
            {
                "title": "Stale Item",
                "published_at": (now - timedelta(hours=72)).isoformat(),
            },
            {"title": "Fresh Item", "published_at": now.isoformat()},
        ]
        is_fresh, reason = ralph_loop._check_sources_freshness(sources)
        assert is_fresh is True
        assert "1/2 sources are fresh" in reason

    def test_sources_without_dates_pass(self, ralph_loop):
        """Sources without published_at should be given benefit of the doubt."""
        sources = [
            {"title": "No Date Item"},
            {"title": "Also No Date"},
        ]
        is_fresh, reason = ralph_loop._check_sources_freshness(sources)
        assert is_fresh is True
        assert "No published dates available" in reason

    def test_iso_z_format_parsed(self, ralph_loop):
        """ISO format with Z suffix should be parsed correctly."""
        now = datetime.now(timezone.utc)
        sources = [{"title": "Z Format", "published_at": now.strftime("%Y-%m-%dT%H:%M:%SZ")}]
        is_fresh, reason = ralph_loop._check_sources_freshness(sources)
        assert is_fresh is True


class TestJuiceEvaluationResult:
    """Tests for JuiceEvaluationResult dataclass."""

    def test_dataclass_fields(self):
        """JuiceEvaluationResult should have all expected fields."""
        from ralph_content.ralph_loop import JuiceEvaluationResult

        result = JuiceEvaluationResult(
            should_proceed=True,
            reason="Good sources",
            juice_score=0.8,
            best_source="Top Article",
            potential_angle="Focus on cost savings",
            cost_cents=5,
        )
        assert result.should_proceed is True
        assert result.reason == "Good sources"
        assert result.juice_score == 0.8
        assert result.best_source == "Top Article"
        assert result.potential_angle == "Focus on cost savings"
        assert result.cost_cents == 5


class TestRalphLoopResultStatus:
    """Tests for RalphLoopResult status handling."""

    def test_skipped_no_juice_status(self):
        """RalphLoopResult should support skipped_no_juice status."""
        from uuid import uuid4

        from ralph_content.ralph_loop import RalphLoopResult

        result = RalphLoopResult(
            blog_post_id=uuid4(),
            final_quality_score=0.0,
            iteration_count=0,
            total_cost_cents=5,
            status="skipped_no_juice",
        )
        assert result.status == "skipped_no_juice"


class TestEvaluateSourceJuice:
    """Tests for _evaluate_source_juice method."""

    @pytest.fixture
    def ralph_loop_with_mocked_api(self):
        """Create a RalphLoop with mocked Anthropic client."""
        with patch("ralph_content.ralph_loop.ProductMarketingAgent"):
            with patch("ralph_content.ralph_loop.CritiqueAgent"):
                from ralph_content.ralph_loop import RalphLoop

                # Create mock Anthropic client
                mock_anthropic = MagicMock()
                mock_response = MagicMock()
                mock_response.usage.input_tokens = 500
                mock_response.usage.output_tokens = 100
                mock_response.content = [
                    MagicMock(
                        text='{"juice_score": 0.75, "should_proceed": true, "reason": "Good sources", "best_source": "Top Article", "potential_angle": "Focus on costs"}'
                    )
                ]
                mock_anthropic.messages.create.return_value = mock_response

                # Create mock services
                mock_rss_service = MagicMock()
                mock_topic_item_service = MagicMock()
                mock_supabase_service = MagicMock()

                loop = RalphLoop(
                    rss_service=mock_rss_service,
                    topic_item_service=mock_topic_item_service,
                    supabase_service=mock_supabase_service,
                    anthropic_client=mock_anthropic,
                    juice_threshold=0.6,
                )
                return loop

    def test_stale_sources_auto_fail(self, ralph_loop_with_mocked_api):
        """Sources older than 48 hours should auto-fail without API call."""
        now = datetime.now(timezone.utc)
        sources = [
            {
                "id": "1",
                "title": "Stale Item",
                "published_at": (now - timedelta(hours=72)).isoformat(),
                "source_type": "rss",
            },
        ]
        result = ralph_loop_with_mocked_api._evaluate_source_juice(sources)

        assert result.should_proceed is False
        assert result.juice_score == 0.0
        assert "Auto-skip" in result.reason
        assert result.cost_cents == 0  # No API call made

    def test_fresh_sources_call_api(self, ralph_loop_with_mocked_api):
        """Fresh sources should call the API for evaluation."""
        now = datetime.now(timezone.utc)
        sources = [
            {
                "id": "1",
                "title": "Fresh Item",
                "summary": "Interesting news about manufacturing",
                "published_at": now.isoformat(),
                "source_type": "rss",
                "url": "https://example.com/article",
            },
        ]
        result = ralph_loop_with_mocked_api._evaluate_source_juice(sources)

        assert result.should_proceed is True
        assert result.juice_score == 0.75
        assert result.reason == "Good sources"
        assert result.best_source == "Top Article"
        assert result.cost_cents > 0  # API call made

    def test_low_juice_score_fails(self):
        """Low juice score should cause should_proceed to be False."""
        with patch("ralph_content.ralph_loop.ProductMarketingAgent"):
            with patch("ralph_content.ralph_loop.CritiqueAgent"):
                from ralph_content.ralph_loop import RalphLoop

                # Create mock Anthropic client that returns low score
                mock_anthropic = MagicMock()
                mock_response = MagicMock()
                mock_response.usage.input_tokens = 500
                mock_response.usage.output_tokens = 100
                mock_response.content = [
                    MagicMock(
                        text='{"juice_score": 0.4, "should_proceed": true, "reason": "Weak sources", "best_source": null, "potential_angle": null}'
                    )
                ]
                mock_anthropic.messages.create.return_value = mock_response

                mock_rss_service = MagicMock()
                mock_topic_item_service = MagicMock()
                mock_supabase_service = MagicMock()

                loop = RalphLoop(
                    rss_service=mock_rss_service,
                    topic_item_service=mock_topic_item_service,
                    supabase_service=mock_supabase_service,
                    anthropic_client=mock_anthropic,
                    juice_threshold=0.6,
                )

                now = datetime.now(timezone.utc)
                sources = [
                    {
                        "id": "1",
                        "title": "Weak Item",
                        "published_at": now.isoformat(),
                        "source_type": "rss",
                    },
                ]
                result = loop._evaluate_source_juice(sources)

                # Should fail because juice_score (0.4) < threshold (0.6)
                assert result.should_proceed is False
                assert result.juice_score == 0.4
                assert "below threshold" in result.reason.lower() or "0.40" in result.reason
