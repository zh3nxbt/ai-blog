"""Tests for major news screening functionality."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


class TestMajorNewsScreeningResult:
    """Tests for MajorNewsScreeningResult dataclass."""

    def test_dataclass_fields(self):
        """MajorNewsScreeningResult should have all expected fields."""
        from ralph_content.ralph_loop import MajorNewsScreeningResult

        result = MajorNewsScreeningResult(
            items_with_scores=[
                {"id": "1", "title": "Test", "urgency_score": 0.8, "is_major_news": True}
            ],
            highest_scoring_major={"id": "1", "title": "Test", "urgency_score": 0.8},
            cost_cents=1,
        )
        assert len(result.items_with_scores) == 1
        assert result.highest_scoring_major is not None
        assert result.highest_scoring_major["urgency_score"] == 0.8
        assert result.cost_cents == 1


class TestPreScreenRssPool:
    """Tests for _pre_screen_rss_pool method."""

    @pytest.fixture
    def ralph_loop_with_mocked_api(self):
        """Create a RalphLoop with mocked Anthropic client."""
        with patch("ralph_content.ralph_loop.ProductMarketingAgent"):
            with patch("ralph_content.ralph_loop.CritiqueAgent"):
                from ralph_content.ralph_loop import RalphLoop

                # Create mock Anthropic client
                mock_anthropic = MagicMock()
                mock_response = MagicMock()
                mock_response.usage.input_tokens = 200
                mock_response.usage.output_tokens = 50
                mock_response.content = [
                    MagicMock(
                        text='{"screening_results": [{"item_index": 0, "is_major_news": true, "urgency_score": 0.85, "reason": "Trade policy change"}, {"item_index": 1, "is_major_news": false, "urgency_score": 0.3, "reason": "Routine news"}]}'
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
                )
                return loop

    def test_small_pool_skips_screening(self, ralph_loop_with_mocked_api):
        """Pools with 4 or fewer items should skip LLM screening."""
        items = [
            {"id": "1", "title": "Item 1"},
            {"id": "2", "title": "Item 2"},
            {"id": "3", "title": "Item 3"},
        ]
        result = ralph_loop_with_mocked_api._pre_screen_rss_pool(items)

        # Should not call API for small pools
        ralph_loop_with_mocked_api._anthropic_client.messages.create.assert_not_called()
        assert result.cost_cents == 0
        assert result.highest_scoring_major is None
        assert len(result.items_with_scores) == 3
        # All items should have default scores
        for item in result.items_with_scores:
            assert item["urgency_score"] == 0.5
            assert item["is_major_news"] is False

    def test_large_pool_calls_screening(self, ralph_loop_with_mocked_api):
        """Pools with more than 4 items should call LLM for screening."""
        items = [
            {"id": "1", "title": "Major News Item", "summary": "Tariffs announced"},
            {"id": "2", "title": "Routine Item", "summary": "Regular update"},
            {"id": "3", "title": "Item 3", "summary": "Content 3"},
            {"id": "4", "title": "Item 4", "summary": "Content 4"},
            {"id": "5", "title": "Item 5", "summary": "Content 5"},
        ]
        result = ralph_loop_with_mocked_api._pre_screen_rss_pool(items)

        # Should call API for large pools
        ralph_loop_with_mocked_api._anthropic_client.messages.create.assert_called_once()
        assert result.cost_cents > 0

    def test_uses_haiku_model(self, ralph_loop_with_mocked_api):
        """Pre-screening should use the cheap Haiku model."""
        items = [{"id": str(i), "title": f"Item {i}"} for i in range(6)]
        ralph_loop_with_mocked_api._pre_screen_rss_pool(items)

        # Check that Haiku model was specified
        call_args = ralph_loop_with_mocked_api._anthropic_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-haiku-3-5"

    def test_major_news_identified(self, ralph_loop_with_mocked_api):
        """Major news items should be identified and scored correctly."""
        items = [
            {"id": "1", "title": "Major News Item", "summary": "Tariffs announced"},
            {"id": "2", "title": "Routine Item", "summary": "Regular update"},
            {"id": "3", "title": "Item 3", "summary": "Content 3"},
            {"id": "4", "title": "Item 4", "summary": "Content 4"},
            {"id": "5", "title": "Item 5", "summary": "Content 5"},
        ]
        result = ralph_loop_with_mocked_api._pre_screen_rss_pool(items)

        # Should identify highest-scoring major news
        assert result.highest_scoring_major is not None
        assert result.highest_scoring_major["urgency_score"] >= 0.7


class TestSelectRssWithMajorNewsSlot:
    """Tests for _select_rss_with_major_news_slot method."""

    @pytest.fixture
    def ralph_loop_with_mocked_screening(self):
        """Create a RalphLoop with mocked pre-screening."""
        with patch("ralph_content.ralph_loop.ProductMarketingAgent"):
            with patch("ralph_content.ralph_loop.CritiqueAgent"):
                with patch("ralph_content.ralph_loop.Anthropic"):
                    from ralph_content.ralph_loop import RalphLoop

                    mock_rss_service = MagicMock()
                    mock_topic_item_service = MagicMock()
                    mock_supabase_service = MagicMock()

                    loop = RalphLoop(
                        rss_service=mock_rss_service,
                        topic_item_service=mock_topic_item_service,
                        supabase_service=mock_supabase_service,
                    )
                    return loop

    def test_major_news_gets_reserved_slot(self, ralph_loop_with_mocked_screening):
        """High-scoring major news should be guaranteed selection."""
        from ralph_content.ralph_loop import MajorNewsScreeningResult

        # Create pool with major news
        pool = [
            {"id": "1", "title": "Major News"},
            {"id": "2", "title": "Regular 1"},
            {"id": "3", "title": "Regular 2"},
            {"id": "4", "title": "Regular 3"},
            {"id": "5", "title": "Regular 4"},
        ]

        # Mock pre-screening to return major news
        major_item = {"id": "1", "title": "Major News", "urgency_score": 0.9, "is_major_news": True}
        with patch.object(
            ralph_loop_with_mocked_screening,
            "_pre_screen_rss_pool",
            return_value=MajorNewsScreeningResult(
                items_with_scores=[
                    major_item,
                    {"id": "2", "title": "Regular 1", "urgency_score": 0.3, "is_major_news": False},
                    {"id": "3", "title": "Regular 2", "urgency_score": 0.4, "is_major_news": False},
                    {"id": "4", "title": "Regular 3", "urgency_score": 0.35, "is_major_news": False},
                    {"id": "5", "title": "Regular 4", "urgency_score": 0.25, "is_major_news": False},
                ],
                highest_scoring_major=major_item,
                cost_cents=1,
            ),
        ):
            selected = ralph_loop_with_mocked_screening._select_rss_with_major_news_slot(
                pool, count=4, exclude_ids=set()
            )

            # Major news item should always be included
            selected_ids = [item["id"] for item in selected]
            assert "1" in selected_ids
            assert len(selected) == 4

    def test_no_major_news_all_random(self, ralph_loop_with_mocked_screening):
        """When no major news, all items should be randomly selected."""
        from ralph_content.ralph_loop import MajorNewsScreeningResult

        pool = [
            {"id": "1", "title": "Regular 1"},
            {"id": "2", "title": "Regular 2"},
            {"id": "3", "title": "Regular 3"},
            {"id": "4", "title": "Regular 4"},
            {"id": "5", "title": "Regular 5"},
        ]

        # Mock pre-screening to return no major news
        with patch.object(
            ralph_loop_with_mocked_screening,
            "_pre_screen_rss_pool",
            return_value=MajorNewsScreeningResult(
                items_with_scores=[
                    {"id": "1", "title": "Regular 1", "urgency_score": 0.3, "is_major_news": False},
                    {"id": "2", "title": "Regular 2", "urgency_score": 0.4, "is_major_news": False},
                    {"id": "3", "title": "Regular 3", "urgency_score": 0.35, "is_major_news": False},
                    {"id": "4", "title": "Regular 4", "urgency_score": 0.25, "is_major_news": False},
                    {"id": "5", "title": "Regular 5", "urgency_score": 0.5, "is_major_news": False},
                ],
                highest_scoring_major=None,
                cost_cents=1,
            ),
        ):
            selected = ralph_loop_with_mocked_screening._select_rss_with_major_news_slot(
                pool, count=3, exclude_ids=set()
            )

            # Should still select 3 items
            assert len(selected) == 3

    def test_excludes_ids_correctly(self, ralph_loop_with_mocked_screening):
        """Excluded IDs should not appear in selection."""
        from ralph_content.ralph_loop import MajorNewsScreeningResult

        pool = [
            {"id": "1", "title": "Item 1"},
            {"id": "2", "title": "Item 2"},
            {"id": "3", "title": "Item 3"},
            {"id": "4", "title": "Item 4"},
            {"id": "5", "title": "Item 5"},
        ]

        # Mock pre-screening
        with patch.object(
            ralph_loop_with_mocked_screening,
            "_pre_screen_rss_pool",
            return_value=MajorNewsScreeningResult(
                items_with_scores=[
                    {"id": "3", "title": "Item 3", "urgency_score": 0.3, "is_major_news": False},
                    {"id": "4", "title": "Item 4", "urgency_score": 0.4, "is_major_news": False},
                    {"id": "5", "title": "Item 5", "urgency_score": 0.35, "is_major_news": False},
                ],
                highest_scoring_major=None,
                cost_cents=1,
            ),
        ):
            selected = ralph_loop_with_mocked_screening._select_rss_with_major_news_slot(
                pool, count=3, exclude_ids={"1", "2"}
            )

            # Excluded IDs should not be present
            selected_ids = [item["id"] for item in selected]
            assert "1" not in selected_ids
            assert "2" not in selected_ids


class TestRssSourceMixUpdate:
    """Tests for updated RSS source mix configuration."""

    def test_default_rss_count_is_four(self):
        """DEFAULT_SOURCE_MIX should have rss count of 4."""
        with patch("ralph_content.ralph_loop.ProductMarketingAgent"):
            with patch("ralph_content.ralph_loop.CritiqueAgent"):
                with patch("ralph_content.ralph_loop.Anthropic"):
                    from ralph_content.ralph_loop import RalphLoop

                    assert RalphLoop.DEFAULT_SOURCE_MIX["rss"] == 4

    def test_major_news_constants_exist(self):
        """Major news constants should be defined."""
        with patch("ralph_content.ralph_loop.ProductMarketingAgent"):
            with patch("ralph_content.ralph_loop.CritiqueAgent"):
                with patch("ralph_content.ralph_loop.Anthropic"):
                    from ralph_content.ralph_loop import RalphLoop

                    assert RalphLoop.MAJOR_NEWS_THRESHOLD == 0.7
                    assert RalphLoop.MAJOR_NEWS_RESERVED_SLOTS == 1
                    assert RalphLoop.PRE_SCREEN_MODEL == "claude-haiku-3-5"
