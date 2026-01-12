"""Supabase client service for database operations."""

import os
import re
from uuid import UUID
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """
    Create and return a Supabase client for backend operations.

    Uses SUPABASE_SECRET (service role key) which bypasses RLS policies.
    Falls back to SUPABASE_KEY if SUPABASE_SECRET is not set.

    Returns:
        Client: Configured Supabase client instance

    Raises:
        ValueError: If required environment variables are missing
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET") or os.getenv("SUPABASE_KEY")

    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable is required")

    if not supabase_key:
        raise ValueError("SUPABASE_SECRET or SUPABASE_KEY environment variable is required")

    return create_client(supabase_url, supabase_key)


def _generate_slug(title: str) -> str:
    """
    Generate a URL-safe slug from a title.

    Args:
        title: The title to convert to a slug

    Returns:
        str: URL-safe slug
    """
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def create_blog_post(title: str, content: str, status: str = "draft") -> UUID:
    """
    Create a new blog post in the database.

    Args:
        title: The title of the blog post
        content: The content of the blog post (markdown)
        status: The status of the post (draft, published, failed)

    Returns:
        UUID: The ID of the created blog post

    Raises:
        ValueError: If required parameters are missing or invalid
        Exception: If the database operation fails
    """
    if not title:
        raise ValueError("title is required")

    if not content:
        raise ValueError("content is required")

    if status not in ["draft", "published", "failed"]:
        raise ValueError(f"status must be one of: draft, published, failed. Got: {status}")

    client = get_supabase_client()
    slug = _generate_slug(title)

    response = client.table("blog_posts").insert({
        "title": title,
        "content": content,
        "slug": slug,
        "status": status
    }).execute()

    if not response.data or len(response.data) == 0:
        raise Exception("Failed to create blog post: no data returned")

    return UUID(response.data[0]["id"])
