"""Topic item selection service for mixed-source content."""

from typing import Any, Dict, List

from services.supabase_service import get_supabase_client


def fetch_active_topic_sources(source_type: str) -> List[Dict[str, Any]]:
    """
    Fetch active topic sources for a given source type.

    Args:
        source_type: Topic source type (rss, evergreen, standards, vendor, internal)

    Returns:
        List[Dict]: Active topic source records
    """
    if not source_type:
        raise ValueError("source_type is required")

    client = get_supabase_client()
    response = (
        client.table("blog_topic_sources")
        .select("*")
        .eq("source_type", source_type)
        .eq("active", True)
        .order("priority", desc=True)
        .execute()
    )

    return response.data or []


def fetch_unused_items_by_source_type(
    source_type: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Fetch unused topic items for a given source type.

    Args:
        source_type: Topic source type (rss, evergreen, standards, vendor, internal)
        limit: Maximum number of items to fetch

    Returns:
        List[Dict]: Unused topic items with source_type attached
    """
    if not source_type:
        raise ValueError("source_type is required")

    if limit < 1:
        return []

    client = get_supabase_client()
    sources = fetch_active_topic_sources(source_type)
    if not sources:
        return []

    source_ids = [source["id"] for source in sources]
    response = (
        client.table("blog_topic_items")
        .select("*")
        .in_("source_id", source_ids)
        .is_("used_in_blog", "null")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    items = response.data or []
    for item in items:
        item.setdefault("source_type", source_type)

    return items


def mark_items_as_used(item_ids: List[str], blog_id: str) -> int:
    """
    Mark topic items as used in a blog post.

    Args:
        item_ids: List of topic item UUIDs to mark as used
        blog_id: UUID of the blog post that used these items

    Returns:
        int: Number of items successfully updated
    """
    if not item_ids:
        raise ValueError("item_ids cannot be empty")

    if not blog_id:
        raise ValueError("blog_id cannot be empty")

    client = get_supabase_client()
    response = (
        client.table("blog_topic_items")
        .update({"used_in_blog": blog_id})
        .in_("id", item_ids)
        .is_("used_in_blog", "null")
        .execute()
    )

    return len(response.data) if response.data else 0
