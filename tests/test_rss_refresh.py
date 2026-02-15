"""Tests for RSS refresh ingestion utilities."""

from services import rss_service


def test_refresh_active_sources_aggregates_results(monkeypatch):
    sources = [
        {"id": "1", "name": "Feed A"},
        {"id": "2", "name": "Feed B"},
        {"id": "3", "name": "Feed C"},
    ]

    monkeypatch.setattr(rss_service, "fetch_active_sources", lambda: sources)

    def fake_fetch_feed_items(source_id, limit):
        if source_id == "2":
            raise ValueError("feed unavailable")
        return [{"id": f"{source_id}-1"}]

    monkeypatch.setattr(rss_service, "fetch_feed_items", fake_fetch_feed_items)

    result = rss_service.refresh_active_sources(per_source_limit=10, max_sources=3)

    assert result["sources_total"] == 3
    assert result["sources_refreshed"] == 2
    assert result["sources_failed"] == 1
    assert result["new_items_total"] == 2
    assert len(result["results"]) == 3


def test_refresh_active_sources_validates_arguments():
    try:
        rss_service.refresh_active_sources(per_source_limit=0)
        assert False, "Expected ValueError for per_source_limit=0"
    except ValueError as exc:
        assert "per_source_limit" in str(exc)

    try:
        rss_service.refresh_active_sources(per_source_limit=5, max_sources=0)
        assert False, "Expected ValueError for max_sources=0"
    except ValueError as exc:
        assert "max_sources" in str(exc)


def test_refresh_active_sources_retries_before_success(monkeypatch):
    monkeypatch.setenv("RALPH_RSS_FETCH_RETRIES", "2")
    monkeypatch.setattr(
        rss_service, "fetch_active_sources", lambda: [{"id": "1", "name": "Feed A"}]
    )

    call_count = {"count": 0}

    def fake_fetch_feed_items(source_id, limit):
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise ValueError("temporary network error")
        return [{"id": "1-1"}]

    monkeypatch.setattr(rss_service, "fetch_feed_items", fake_fetch_feed_items)
    monkeypatch.setattr(
        rss_service,
        "_mark_source_fetch_failure",
        lambda source, error, failure_threshold: {
            "consecutive_failures": 1,
            "auto_disabled": False,
        },
    )

    result = rss_service.refresh_active_sources(per_source_limit=5, max_sources=1)

    assert result["sources_refreshed"] == 1
    assert result["sources_failed"] == 0
    assert result["results"][0]["attempts"] == 2


def test_refresh_active_sources_reports_auto_disabled(monkeypatch):
    monkeypatch.setenv("RALPH_RSS_FETCH_RETRIES", "1")
    monkeypatch.setenv("RALPH_RSS_FAILURE_THRESHOLD", "3")
    monkeypatch.setattr(
        rss_service,
        "fetch_active_sources",
        lambda: [{"id": "1", "name": "Feed A", "consecutive_failures": 2}],
    )
    monkeypatch.setattr(
        rss_service,
        "fetch_feed_items",
        lambda source_id, limit: (_ for _ in ()).throw(ValueError("permanent parse error")),
    )
    monkeypatch.setattr(
        rss_service,
        "_mark_source_fetch_failure",
        lambda source, error, failure_threshold: {
            "consecutive_failures": 3,
            "auto_disabled": True,
        },
    )

    result = rss_service.refresh_active_sources(per_source_limit=5, max_sources=1)

    assert result["sources_refreshed"] == 0
    assert result["sources_failed"] == 1
    assert result["results"][0]["auto_disabled"] is True
