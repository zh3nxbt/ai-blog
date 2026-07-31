"""Hourly RSS refresh entrypoint (ingestion only, no LLM calls).

Usage:
    python -m ralph.refresh_sources
    python -m ralph.refresh_sources --max-sources 20 --per-source-limit 15
"""

from __future__ import annotations

import argparse
import os
import sys

from services import rss_service, supabase_service
from utils.env import load_local_env_if_available


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh active RSS sources and store new items",
    )
    parser.add_argument(
        "--per-source-limit",
        type=int,
        default=int(os.environ.get("RALPH_REFRESH_LIMIT_PER_SOURCE", "20")),
        help="Maximum items fetched per source",
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        default=(
            int(os.environ["RALPH_REFRESH_MAX_SOURCES"])
            if os.environ.get("RALPH_REFRESH_MAX_SOURCES")
            else None
        ),
        help="Optional cap on number of active sources to refresh",
    )
    return parser.parse_args()


def main() -> int:
    load_local_env_if_available()
    args = _parse_args()

    required_vars = ["SUPABASE_URL", "SUPABASE_SECRET"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        return 1

    print("Starting RSS refresh (ingestion only)...")
    print(f"  Per-source limit: {args.per_source_limit}")
    print(f"  Max sources:      {args.max_sources if args.max_sources is not None else 'all'}")
    print()

    try:
        result = rss_service.refresh_active_sources(
            per_source_limit=args.per_source_limit,
            max_sources=args.max_sources,
        )
        all_failed = (
            result["sources_total"] > 0 and result["sources_refreshed"] == 0
        )

        supabase_service.log_agent_activity(
            agent_name="rss-refresh",
            activity_type="refresh_sources",
            success=not all_failed,
            metadata={
                "sources_total": result["sources_total"],
                "sources_refreshed": result["sources_refreshed"],
                "sources_failed": result["sources_failed"],
                "new_items_total": result["new_items_total"],
                "fetch_retries": result.get("fetch_retries"),
                "failure_threshold": result.get("failure_threshold"),
                "degraded": result["sources_failed"] > 0,
            },
            input_data={
                "per_source_limit": args.per_source_limit,
                "max_sources": args.max_sources,
            },
            output_data={
                "results": result["results"],
            },
        )

        print("=" * 50)
        print("RSS Refresh Complete")
        print("=" * 50)
        print(f"Sources total:     {result['sources_total']}")
        print(f"Sources refreshed: {result['sources_refreshed']}")
        print(f"Sources failed:    {result['sources_failed']}")
        print(f"New items stored:  {result['new_items_total']}")
        if result["sources_failed"] > 0:
            print("Mode:             degraded (partial source failures)")
        print("=" * 50)

        # Don't fail the hourly timer for partial source failures.
        # Return non-zero only when every source failed (or nothing could refresh).
        return 1 if all_failed else 0

    except Exception as exc:
        try:
            supabase_service.log_agent_activity(
                agent_name="rss-refresh",
                activity_type="refresh_sources",
                success=False,
                error_message=str(exc),
                input_data={
                    "per_source_limit": args.per_source_limit,
                    "max_sources": args.max_sources,
                },
            )
        except Exception:
            # Avoid masking the root failure if logging itself fails.
            pass

        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
