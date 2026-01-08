"""
Daily blog post generation worker.

This script is designed to run once per day via systemd timer or cron.
It fetches content from RSS feeds, generates a blog post using an LLM,
and stores the result in Supabase.

This worker is idempotent and safe to re-run.
"""

import argparse
import sys
from datetime import datetime

from config import settings


def check_already_generated_today() -> bool:
    """
    Check if a post has already been generated today.

    Returns:
        bool: True if post exists for today, False otherwise
    """
    # TODO: Query Supabase for posts with today's date
    return False


def fetch_rss_feeds() -> list[dict]:
    """
    Fetch and parse RSS feeds from configured sources.

    Returns:
        list[dict]: List of feed items with metadata
    """
    # TODO: Implement RSS feed fetching
    # - Read feed URLs from configuration or database
    # - Parse feeds using feedparser
    # - Deduplicate items
    # - Return structured data
    return []


def generate_blog_post(feed_items: list[dict]) -> dict:
    """
    Generate blog post using LLM based on feed items.

    Args:
        feed_items: List of RSS feed items to use as source material

    Returns:
        dict: Structured blog post with title, excerpt, content, sources
    """
    # TODO: Implement LLM generation
    # - Format feed items into prompt
    # - Call Anthropic API with structured output
    # - Validate response fields
    # - Return parsed result
    return {
        "title": "",
        "excerpt": "",
        "content_markdown": "",
        "source_urls": [],
    }


def save_to_supabase(post_data: dict) -> str:
    """
    Save generated post to Supabase.

    Args:
        post_data: Blog post data to save

    Returns:
        str: Post ID from Supabase
    """
    # TODO: Implement Supabase save
    # - Generate slug from title
    # - Set publish_date to today
    # - Set status to 'draft' or 'published'
    # - Insert into posts table
    # - Return created post ID
    return ""


def run_worker():
    """Main worker execution logic."""
    print(f"[{datetime.now().isoformat()}] Worker started")

    if not settings.worker_enabled:
        print("Worker is disabled via configuration. Exiting.")
        return

    # Check if already generated today
    if check_already_generated_today():
        print("Post already generated for today. Exiting.")
        return

    # Fetch RSS feeds
    print("Fetching RSS feeds...")
    feed_items = fetch_rss_feeds()

    if not feed_items:
        print("No feed items found. Cannot generate post.")
        sys.exit(1)

    # Generate blog post
    print(f"Generating blog post from {len(feed_items)} feed items...")
    post_data = generate_blog_post(feed_items)

    # Validate post data
    required_fields = ["title", "excerpt", "content_markdown", "source_urls"]
    missing_fields = [f for f in required_fields if not post_data.get(f)]

    if missing_fields:
        print(f"Generated post missing required fields: {missing_fields}")
        sys.exit(1)

    # Save to Supabase
    print("Saving to Supabase...")
    post_id = save_to_supabase(post_data)

    print(f"Post generated successfully. ID: {post_id}")
    print(f"[{datetime.now().isoformat()}] Worker completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blog post generation worker")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run worker once and exit (for testing)",
    )

    args = parser.parse_args()

    try:
        run_worker()
    except Exception as e:
        print(f"Worker failed: {e}")
        sys.exit(1)
