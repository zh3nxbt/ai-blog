#!/usr/bin/env python3
"""Backfill draft api_cost_cents to match publish total_cost_cents."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from services.supabase_service import get_supabase_client  # noqa: E402


def _latest_publish_activity(blog_ids: List[str]) -> Dict[str, dict]:
    client = get_supabase_client()
    response = (
        client.table("blog_agent_activity")
        .select("id,context_id,activity_type,metadata,created_at")
        .in_("context_id", blog_ids)
        .in_("activity_type", ["publish", "finalize"])
        .execute()
    )

    latest: Dict[str, dict] = {}
    for row in response.data or []:
        post_id = row.get("context_id")
        if not post_id:
            continue
        current = latest.get(post_id)
        if current is None or row.get("created_at", "") > current.get("created_at", ""):
            latest[post_id] = row
    return latest


def _fetch_latest_drafts(blog_ids: List[str]) -> Dict[str, dict]:
    client = get_supabase_client()
    response = (
        client.table("blog_content_drafts")
        .select("id,blog_post_id,iteration_number,api_cost_cents")
        .in_("blog_post_id", blog_ids)
        .execute()
    )

    latest: Dict[str, dict] = {}
    for row in response.data or []:
        post_id = row.get("blog_post_id")
        if not post_id:
            continue
        iteration = int(row.get("iteration_number") or 0)
        current = latest.get(post_id)
        if current is None or iteration > int(current.get("iteration_number") or 0):
            latest[post_id] = row
    return latest


def _extract_total_cost(activity: dict) -> Optional[int]:
    metadata = activity.get("metadata") or {}
    total_cost = metadata.get("total_cost_cents")
    if total_cost is None:
        return None
    try:
        return int(total_cost)
    except (TypeError, ValueError):
        return None


def main() -> int:
    client = get_supabase_client()
    posts = (
        client.table("blog_posts")
        .select("id,status")
        .eq("status", "published")
        .execute()
    ).data or []

    blog_ids = [post["id"] for post in posts]
    if not blog_ids:
        print("No published posts found. Nothing to backfill.")
        return 0

    activities = _latest_publish_activity(blog_ids)
    drafts = _fetch_latest_drafts(blog_ids)

    updated = 0
    skipped = 0
    missing = 0

    for post_id in blog_ids:
        activity = activities.get(post_id)
        draft = drafts.get(post_id)
        if not activity or not draft:
            missing += 1
            continue

        total_cost = _extract_total_cost(activity)
        if total_cost is None:
            missing += 1
            continue

        draft_cost = draft.get("api_cost_cents")
        if draft_cost is not None and int(draft_cost) == total_cost:
            skipped += 1
            continue

        update = (
            client.table("blog_content_drafts")
            .update({"api_cost_cents": total_cost})
            .eq("id", draft["id"])
            .execute()
        )
        if update.data:
            updated += 1

    print(
        f"Backfill complete. Updated {updated}, skipped {skipped}, missing {missing}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
