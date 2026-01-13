"""RSS feed fetching and storage service."""

import feedparser
from typing import List, Dict, Any
from datetime import datetime

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
    feed = feedparser.parse(url)

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
            published_at = datetime(*entry.published_parsed[:6]).isoformat()
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published_at = datetime(*entry.updated_parsed[:6]).isoformat()

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

    return response.data
