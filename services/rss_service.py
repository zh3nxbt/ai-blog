"""RSS feed fetching and storage service."""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import feedparser

from services.supabase_service import get_supabase_client


def fetch_active_sources() -> List[Dict[str, Any]]:
    """
    Fetch all active RSS sources from the database.

    Returns:
        List[Dict]: List of RSS source records ordered by priority (highest first)

    Raises:
        Exception: If the database query fails
    """
    client = get_supabase_client()

    response = client.table("blog_rss_sources")\
        .select("*")\
        .eq("active", True)\
        .order("priority", desc=True)\
        .execute()

    if not response.data:
        return []

    return response.data


# Alias for svc-005 compatibility
fetch_active_feeds = fetch_active_sources


def _get_fetch_retries() -> int:
    """Return max fetch attempts per source for refresh jobs."""
    raw_value = os.getenv("BLOG_RSS_FETCH_RETRIES", "2")
    try:
        retries = int(raw_value)
    except ValueError:
        retries = 2
    return max(1, retries)


def _get_failure_threshold() -> int:
    """Return consecutive failure threshold before auto-disabling a source."""
    raw_value = os.getenv("BLOG_RSS_FAILURE_THRESHOLD", "5")
    try:
        threshold = int(raw_value)
    except ValueError:
        threshold = 5
    return max(1, threshold)


def _truncate_error(error: str, max_len: int = 500) -> str:
    """Clamp long feed errors so activity records stay readable."""
    if len(error) <= max_len:
        return error
    return f"{error[:max_len - 3]}..."


def _safe_update_source(source_id: str, payload: Dict[str, Any]) -> bool:
    """
    Best-effort source update helper.

    Returns:
        bool: True when update succeeded, False when schema/env constraints blocked it.
    """
    try:
        client = get_supabase_client()
        client.table("blog_rss_sources").update(payload).eq("id", source_id).execute()
        return True
    except Exception:
        return False


def _mark_source_fetch_success(source_id: str) -> None:
    """Reset failure counters and update fetch timestamp after a successful poll."""
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "last_fetched_at": now_iso,
        "consecutive_failures": 0,
        "last_failed_at": None,
        "last_error": None,
    }
    if _safe_update_source(source_id, payload):
        return

    # Fallback for environments that have not applied health-tracking migration yet.
    _safe_update_source(source_id, {"last_fetched_at": now_iso})


def _mark_source_fetch_failure(
    source: Dict[str, Any],
    error: str,
    failure_threshold: int,
) -> Dict[str, Any]:
    """
    Record a failed poll and optionally auto-disable noisy sources.

    Returns:
        Dict with updated failure count and disable flag for logging.
    """
    source_id = str(source.get("id"))
    current_failures = int(source.get("consecutive_failures") or 0)
    consecutive_failures = current_failures + 1
    auto_disabled = consecutive_failures >= failure_threshold

    payload: Dict[str, Any] = {
        "consecutive_failures": consecutive_failures,
        "last_failed_at": datetime.now(timezone.utc).isoformat(),
        "last_error": _truncate_error(error),
    }
    if auto_disabled:
        payload["active"] = False

    updated = _safe_update_source(source_id, payload)
    return {
        "consecutive_failures": consecutive_failures,
        "auto_disabled": auto_disabled and updated,
    }


def fetch_feed(url: str) -> feedparser.FeedParserDict:
    """
    Fetch and parse an RSS/Atom feed from a URL.

    Args:
        url: The URL of the RSS feed

    Returns:
        FeedParserDict: Parsed feed data

    Raises:
        ValueError: If the feed cannot be parsed or is invalid
    """
    feed = feedparser.parse(
        url,
        request_headers={"User-Agent": "blog-bot/1.0 (+https://masprecisionparts.com)"},
    )

    if feed.bozo and not feed.entries:
        # bozo=1 means malformed feed, but sometimes still has entries
        raise ValueError(f"Failed to parse feed from {url}: {feed.get('bozo_exception', 'Unknown error')}")

    return feed


def store_rss_items(source_id: str, feed: feedparser.FeedParserDict, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Store RSS feed items in the database, skipping duplicates.

    Args:
        source_id: UUID of the RSS source
        feed: Parsed feed data from feedparser
        limit: Maximum number of items to store (default 10)

    Returns:
        List[Dict]: List of stored RSS items (new items only)

    Raises:
        Exception: If database operations fail
    """
    client = get_supabase_client()
    stored_items = []

    for entry in feed.entries[:limit]:
        # Extract item data
        title = entry.get('title', 'No title')
        url = entry.get('link', '')
        summary = entry.get('summary', entry.get('description', ''))

        # Parse published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).isoformat()

        if not url:
            continue  # Skip entries without URL

        try:
            # Try to insert, skip if URL already exists (UNIQUE constraint)
            response = client.table("blog_rss_items").insert({
                "source_id": source_id,
                "title": title,
                "url": url,
                "summary": summary,
                "published_at": published_at
            }).execute()

            if response.data and len(response.data) > 0:
                stored_items.append(response.data[0])
        except Exception as e:
            # Likely a duplicate URL (UNIQUE constraint violation)
            # Skip this item and continue
            error_msg = str(e).lower()
            if 'duplicate' not in error_msg and 'unique' not in error_msg:
                # Re-raise if it's not a duplicate error
                raise
            continue

    return stored_items


def fetch_feed_items(source_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch and store RSS items from a specific source.

    Combines feed fetching and item storage into a single operation.
    Gets the source URL from the database, fetches the RSS feed,
    parses items, and stores new items (skipping duplicates by URL).

    Args:
        source_id: UUID of the RSS source
        limit: Maximum number of items to fetch and store (default 10)

    Returns:
        List[Dict]: List of newly stored RSS items

    Raises:
        ValueError: If source_id does not exist or feed cannot be parsed
        Exception: If database operations fail
    """
    client = get_supabase_client()

    # Get the source URL from the database
    response = client.table("blog_rss_sources")\
        .select("url, name")\
        .eq("id", source_id)\
        .execute()

    if not response.data or len(response.data) == 0:
        raise ValueError(f"Source with id {source_id} not found")

    source = response.data[0]
    url = source["url"]

    # Fetch and parse the RSS feed
    feed = fetch_feed(url)

    # Store the items (duplicates are skipped automatically)
    stored_items = store_rss_items(source_id, feed, limit)

    # Track successful fetch timing and reset failure counters.
    _mark_source_fetch_success(str(source_id))

    return stored_items


def fetch_unused_items(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch RSS items that haven't been used in a blog post yet.

    Args:
        limit: Maximum number of items to fetch (default 5)

    Returns:
        List[Dict]: List of unused RSS items, ordered by published_at DESC

    Raises:
        Exception: If database query fails
    """
    client = get_supabase_client()

    response = client.table("blog_rss_items")\
        .select("*")\
        .is_("used_in_blog", "null")\
        .order("published_at", desc=True)\
        .limit(limit)\
        .execute()

    if not response.data:
        return []

    items = response.data
    source_ids = list({item["source_id"] for item in items if item.get("source_id")})
    if not source_ids:
        return items

    source_response = (
        client.table("blog_rss_sources")
        .select("id, name, priority, category")
        .in_("id", source_ids)
        .execute()
    )

    source_by_id = {row["id"]: row for row in (source_response.data or [])}
    for item in items:
        source_meta = source_by_id.get(item.get("source_id"))
        if not source_meta:
            continue
        item["source_name"] = source_meta.get("name")
        item["source_priority"] = source_meta.get("priority")
        item["source_category"] = source_meta.get("category")

    return items


def mark_items_as_used(item_ids: List[str], blog_id: str) -> int:
    """
    Mark RSS items as used in a blog post.

    Updates the used_in_blog column for the specified items to reference
    the blog post that used them. Only updates items that are not already
    used (used_in_blog IS NULL) to prevent race conditions where multiple
    workers could overwrite each other's associations.

    Args:
        item_ids: List of RSS item UUIDs to mark as used
        blog_id: UUID of the blog post that used these items

    Returns:
        int: Number of items successfully updated (may be less than
             len(item_ids) if some items were already used)

    Raises:
        ValueError: If item_ids is empty or blog_id is invalid
        Exception: If database operations fail
    """
    if not item_ids:
        raise ValueError("item_ids cannot be empty")

    if not blog_id:
        raise ValueError("blog_id cannot be empty")

    client = get_supabase_client()

    # Update only unused items to prevent race conditions
    # Items already marked as used by another blog post are left untouched
    response = client.table("blog_rss_items")\
        .update({"used_in_blog": blog_id})\
        .in_("id", item_ids)\
        .is_("used_in_blog", "null")\
        .execute()

    # Return count of updated items
    return len(response.data) if response.data else 0


def refresh_active_sources(
    per_source_limit: int = 20,
    max_sources: int | None = None,
) -> Dict[str, Any]:
    """
    Refresh active RSS sources by fetching their latest items.

    This is ingestion-only and does not call any LLM APIs.

    Args:
        per_source_limit: Max number of items fetched per source.
        max_sources: Optional cap on number of active sources to refresh.

    Returns:
        Dict with counts and per-source results.
    """
    if per_source_limit < 1:
        raise ValueError("per_source_limit must be >= 1")
    if max_sources is not None and max_sources < 1:
        raise ValueError("max_sources must be >= 1 when provided")

    active_sources = fetch_active_sources()
    if max_sources is not None:
        active_sources = active_sources[:max_sources]

    fetch_retries = _get_fetch_retries()
    failure_threshold = _get_failure_threshold()

    total_new_items = 0
    refreshed_sources = 0
    failed_sources = 0
    source_results: List[Dict[str, Any]] = []

    for source in active_sources:
        source_id = source.get("id")
        source_name = source.get("name", "Unknown source")
        last_error = ""
        new_items: List[Dict[str, Any]] = []
        succeeded = False
        attempts_used = 0

        for attempt in range(1, fetch_retries + 1):
            attempts_used = attempt
            try:
                new_items = fetch_feed_items(str(source_id), limit=per_source_limit)
                succeeded = True
                break
            except Exception as exc:
                last_error = str(exc)

        if succeeded:
            refreshed_sources += 1
            total_new_items += len(new_items)
            source_results.append(
                {
                    "source_id": source_id,
                    "source_name": source_name,
                    "success": True,
                    "new_items": len(new_items),
                    "attempts": attempts_used,
                }
            )
            continue

        failed_sources += 1
        health = _mark_source_fetch_failure(
            source=source,
            error=last_error,
            failure_threshold=failure_threshold,
        )
        source_results.append(
            {
                "source_id": source_id,
                "source_name": source_name,
                "success": False,
                "new_items": 0,
                "error": _truncate_error(last_error),
                "attempts": attempts_used,
                "consecutive_failures": health["consecutive_failures"],
                "auto_disabled": health["auto_disabled"],
            }
        )

    return {
        "sources_total": len(active_sources),
        "sources_refreshed": refreshed_sources,
        "sources_failed": failed_sources,
        "new_items_total": total_new_items,
        "fetch_retries": fetch_retries,
        "failure_threshold": failure_threshold,
        "results": source_results,
    }
