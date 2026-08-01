"""CLI helpers for Claude Code blog generation.

Thin wrappers around existing services, exposed as argparse subcommands.
All output is JSON to stdout. Designed to be called via:

    python -m blog.generate_helpers <subcommand> [args]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from uuid import UUID

from utils.env import load_local_env_if_available


# Manual and native-Windows runs do not have systemd injecting /etc/blog-backend/env.
# python-dotenv keeps existing process variables authoritative by default.
load_local_env_if_available()


def _json_out(data: dict) -> None:
    """Print JSON to stdout and exit 0."""
    print(json.dumps(data, default=str))


def _error_out(message: str) -> None:
    """Print JSON error to stdout and exit 1."""
    print(json.dumps({"error": message}))
    sys.exit(1)


def cmd_check_today(args: argparse.Namespace) -> None:
    """Check if a blog post already exists for today."""
    from services.supabase_service import get_supabase_client

    client = get_supabase_client()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    response = (
        client.table("blog_posts")
        .select("id, title, status")
        .gte("created_at", f"{today}T00:00:00Z")
        .lte("created_at", f"{today}T23:59:59Z")
        .execute()
    )

    if response.data and len(response.data) > 0:
        post = response.data[0]
        _json_out({
            "exists": True,
            "post_id": post["id"],
            "title": post.get("title"),
            "status": post.get("status"),
        })
    else:
        _json_out({"exists": False})


def cmd_fetch_sources(args: argparse.Namespace) -> None:
    """Fetch unused RSS items and topic items for blog generation."""
    from services.rss_service import fetch_unused_items
    from services.topic_item_service import fetch_unused_items_by_source_type

    rss_limit = args.rss_limit
    items = []

    # Fetch RSS items
    rss_items = fetch_unused_items(limit=rss_limit)
    for item in rss_items:
        item["_source_type"] = "rss"
    items.extend(rss_items)

    # Fetch topic items (evergreen, standards, vendor)
    for source_type in ["evergreen", "standards", "vendor"]:
        topic_items = fetch_unused_items_by_source_type(source_type, limit=args.topic_limit)
        for item in topic_items:
            item["_source_type"] = source_type
        items.extend(topic_items)

    _json_out({"items": items, "count": len(items)})


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate blog post content quality."""
    from services.quality_validator import validate_content

    content_file = args.content_file
    title = args.title

    try:
        with open(content_file, "r") as f:
            content = f.read()
    except FileNotFoundError:
        _error_out(f"Content file not found: {content_file}")
        return

    result = validate_content(content, title)
    _json_out(result)


def cmd_save_post(args: argparse.Namespace) -> None:
    """Save a blog post to Supabase."""
    from blog.markdown_renderer import markdown_to_html
    from services.supabase_service import create_blog_post

    try:
        with open(args.content_file, "r") as f:
            content_markdown = f.read()
    except FileNotFoundError:
        _error_out(f"Content file not found: {args.content_file}")
        return

    content_html = markdown_to_html(content_markdown)

    tags = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    blog_post_id = create_blog_post(
        title=args.title,
        content=content_html,
        status=args.status,
        meta_description=args.meta_description,
        meta_keywords=args.meta_keywords,
        tags=tags,
    )

    _json_out({"blog_post_id": str(blog_post_id)})


def cmd_mark_used(args: argparse.Namespace) -> None:
    """Mark source items as used in a blog post."""
    from services.rss_service import mark_items_as_used as mark_rss_used
    from services.topic_item_service import mark_items_as_used as mark_topic_used

    blog_post_id = args.blog_post_id
    rss_ids = [i.strip() for i in (args.rss_ids or "").split(",") if i.strip()]
    topic_ids = [i.strip() for i in (args.topic_ids or "").split(",") if i.strip()]

    marked = 0
    if rss_ids:
        marked += mark_rss_used(rss_ids, blog_post_id)
    if topic_ids:
        marked += mark_topic_used(topic_ids, blog_post_id)

    _json_out({"marked": marked})


def cmd_log_activity(args: argparse.Namespace) -> None:
    """Log agent activity to the database."""
    from services.supabase_service import log_agent_activity

    metadata = None
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            _error_out(f"Invalid JSON for --metadata: {args.metadata}")
            return

    context_id = None
    if args.context_id:
        context_id = UUID(args.context_id)

    activity_id = log_agent_activity(
        agent_name=args.agent,
        activity_type=args.type,
        success=args.success,
        context_id=context_id,
        error_message=args.error,
        metadata=metadata,
    )

    _json_out({"activity_id": str(activity_id)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blog.generate_helpers",
        description="CLI helpers for Claude Code blog generation",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check-today
    subparsers.add_parser("check-today", help="Check if a post exists for today")

    # fetch-sources
    fetch = subparsers.add_parser("fetch-sources", help="Fetch unused source items")
    fetch.add_argument("--rss-limit", type=int, default=10, help="Max RSS items")
    fetch.add_argument("--topic-limit", type=int, default=2, help="Max items per topic type")

    # validate
    validate = subparsers.add_parser("validate", help="Validate blog content quality")
    validate.add_argument("--title", required=True, help="Blog post title")
    validate.add_argument("--content-file", required=True, help="Path to markdown content file")

    # save-post
    save = subparsers.add_parser("save-post", help="Save a blog post to Supabase")
    save.add_argument("--title", required=True, help="Blog post title")
    save.add_argument("--content-file", required=True, help="Path to markdown content file")
    save.add_argument("--excerpt", default=None, help="Blog post excerpt")
    save.add_argument("--meta-description", default=None, help="SEO meta description")
    save.add_argument("--meta-keywords", default=None, help="SEO meta keywords")
    save.add_argument("--tags", default=None, help="Comma-separated tags")
    save.add_argument("--status", default="draft", choices=["draft", "published", "failed"],
                       help="Post status")

    # mark-used
    mark = subparsers.add_parser("mark-used", help="Mark source items as used")
    mark.add_argument("--rss-ids", default=None, help="Comma-separated RSS item IDs")
    mark.add_argument("--topic-ids", default=None, help="Comma-separated topic item IDs")
    mark.add_argument("--blog-post-id", required=True, help="Blog post UUID")

    # log-activity
    log = subparsers.add_parser("log-activity", help="Log agent activity")
    log.add_argument("--agent", required=True, help="Agent name")
    log.add_argument("--type", required=True, help="Activity type")
    success_group = log.add_mutually_exclusive_group(required=True)
    success_group.add_argument("--success", action="store_true", dest="success",
                                help="Activity succeeded")
    success_group.add_argument("--failure", action="store_false", dest="success",
                                help="Activity failed")
    log.add_argument("--context-id", default=None, help="Context UUID")
    log.add_argument("--metadata", default=None, help="JSON metadata string")
    log.add_argument("--error", default=None, help="Error message")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "check-today": cmd_check_today,
        "fetch-sources": cmd_fetch_sources,
        "validate": cmd_validate,
        "save-post": cmd_save_post,
        "mark-used": cmd_mark_used,
        "log-activity": cmd_log_activity,
    }

    try:
        commands[args.command](args)
    except Exception as e:
        _error_out(str(e))


if __name__ == "__main__":
    main()
