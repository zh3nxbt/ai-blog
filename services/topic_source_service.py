"""Non-RSS source registration and ingestion service."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from services.rss_service import fetch_feed
from services.supabase_service import get_supabase_client


DEFAULT_NON_RSS_SOURCES: List[Dict[str, Any]] = [
    {
        "name": "USPTO News",
        "source_type": "standards",
        "category": "Government",
        "priority": 7,
        "active": True,
        "notes": "Official RSS feed: https://www.uspto.gov/rss.xml",
        "feed_url": "https://www.uspto.gov/rss.xml",
    },
    {
        "name": "American Wood Council News",
        "source_type": "standards",
        "category": "Standards",
        "priority": 6,
        "active": True,
        "notes": "Official RSS feed: https://www.awc.org/rss",
        "feed_url": "https://www.awc.org/rss",
    },
    {
        "name": "Autodesk News",
        "source_type": "vendor",
        "category": "Vendor",
        "priority": 6,
        "active": True,
        "notes": "Official RSS feed: https://adsknews.autodesk.com/rss",
        "feed_url": "https://adsknews.autodesk.com/rss",
    },
]


def register_non_rss_sources() -> List[Dict[str, Any]]:
    """
    Ensure baseline non-RSS sources are registered.

    Returns:
        List[Dict]: Registered source records with feed_url attached
    """
    client = get_supabase_client()
    registered_sources: List[Dict[str, Any]] = []

    for source in DEFAULT_NON_RSS_SOURCES:
        response = (
            client.table("blog_topic_sources")
            .select("*")
            .eq("name", source["name"])
            .eq("source_type", source["source_type"])
            .limit(1)
            .execute()
        )

        if response.data:
            record = response.data[0]
        else:
            insert_data = {
                "name": source["name"],
                "source_type": source["source_type"],
                "category": source["category"],
                "priority": source["priority"],
                "active": source["active"],
                "notes": source["notes"],
            }
            insert_response = client.table("blog_topic_sources").insert(insert_data).execute()
            if not insert_response.data:
                raise Exception(f"Failed to insert source: {source['name']}")
            record = insert_response.data[0]

        record_with_feed = dict(record)
        record_with_feed["feed_url"] = source["feed_url"]
        registered_sources.append(record_with_feed)

    return registered_sources


def store_topic_items(
    source_id: str,
    feed: Any,
    limit: int = 10,
    feed_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Store topic items from a feed into blog_topic_items, skipping duplicates.

    Args:
        source_id: UUID of the topic source
        feed: Parsed feed data
        limit: Maximum items to store
        feed_url: Feed URL to include in metadata

    Returns:
        List[Dict]: Newly stored items
    """
    client = get_supabase_client()
    stored_items: List[Dict[str, Any]] = []

    for entry in feed.entries[:limit]:
        title = entry.get("title", "No title")
        url = entry.get("link", "")
        summary = entry.get("summary", entry.get("description", ""))

        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_at = datetime(*entry.published_parsed[:6]).isoformat()
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            published_at = datetime(*entry.updated_parsed[:6]).isoformat()

        if not url:
            continue

        metadata = {}
        if feed_url:
            metadata["feed_url"] = feed_url
        feed_title = feed.feed.get("title") if hasattr(feed, "feed") else None
        if feed_title:
            metadata["feed_title"] = feed_title

        try:
            response = client.table("blog_topic_items").insert({
                "source_id": source_id,
                "title": title,
                "summary": summary,
                "url": url,
                "content": None,
                "published_at": published_at,
                "metadata": metadata or None,
            }).execute()

            if response.data:
                stored_items.append(response.data[0])
        except Exception as exc:
            error_msg = str(exc).lower()
            if "duplicate" not in error_msg and "unique" not in error_msg:
                raise
            continue

    return stored_items


def ingest_non_rss_sources(
    limit_per_source: int = 10,
    sources: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Ingest items from registered non-RSS sources.

    Args:
        limit_per_source: Max items per source
        sources: Optional list of source records (for testing)

    Returns:
        Dict with success and failure details
    """
    sources_to_ingest = sources if sources is not None else register_non_rss_sources()
    successes: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    for source in sources_to_ingest:
        feed_url = source.get("feed_url")
        try:
            if not feed_url:
                raise ValueError(f"Missing feed_url for source {source.get('name')}")

            feed = fetch_feed(feed_url)
            stored_items = store_topic_items(
                source_id=source["id"],
                feed=feed,
                limit=limit_per_source,
                feed_url=feed_url,
            )

            successes.append({
                "source_id": source["id"],
                "source_name": source.get("name"),
                "stored_count": len(stored_items),
            })
        except Exception as exc:
            failures.append({
                "source_id": source.get("id"),
                "source_name": source.get("name"),
                "error": str(exc),
            })
            continue

    return {
        "successes": successes,
        "failures": failures,
    }
