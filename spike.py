#!/usr/bin/env python3
"""
spike.py - Proof-of-concept orchestrator for Phase 0

This script demonstrates end-to-end blog post generation:
1. Fetches unused RSS items from the database
2. Generates blog post using Claude API
3. Saves post to blog_posts table
4. Logs activity for debugging
5. Prints summary with token usage and costs

Usage:
    python spike.py
"""

import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.rss_service import fetch_unused_items, fetch_active_sources, fetch_feed, store_rss_items  # noqa: E402
from services.llm_service import generate_blog_post, calculate_api_cost  # noqa: E402
from services.supabase_service import create_blog_post, log_agent_activity, get_supabase_client  # noqa: E402


def main():
    """Run the spike proof-of-concept."""
    print("=" * 80)
    print("SPIKE.PY - End-to-End Blog Generation Proof-of-Concept")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    start_time = time.time()
    blog_post_id = None

    try:
        # Step 1: Fetch unused RSS items
        print("[1/5] Fetching unused RSS items...")
        unused_items = fetch_unused_items(limit=5)

        if len(unused_items) < 3:
            print(f"  WARNING: Only {len(unused_items)} unused items found")
            print("  Fetching fresh RSS items from sources...")

            # Fetch fresh items from active sources
            sources = fetch_active_sources()
            if not sources:
                raise Exception("No active RSS sources found in database")

            for source in sources[:2]:  # Fetch from first 2 sources
                print(f"  Fetching from: {source['name']}")
                feed = fetch_feed(source['url'])
                stored = store_rss_items(source['id'], feed, limit=10)
                print(f"    Stored {len(stored)} new items")

            # Try fetching unused items again
            unused_items = fetch_unused_items(limit=5)

        if len(unused_items) < 3:
            raise Exception(f"Insufficient RSS items: need at least 3, found {len(unused_items)}")

        print(f"✓ Found {len(unused_items)} unused RSS items")
        for i, item in enumerate(unused_items[:3], 1):
            print(f"  {i}. {item['title'][:60]}...")

        # Step 2: Generate blog post using Claude API
        print("\n[2/5] Generating blog post with Claude API...")
        rss_items_for_generation = unused_items[:5]  # Use up to 5 items

        post_data, input_tokens, output_tokens = generate_blog_post(rss_items_for_generation)

        print("✓ Generated blog post")
        print(f"  Title: {post_data['title']}")
        print(f"  Excerpt: {post_data['excerpt'][:80]}...")
        print(f"  Content length: {len(post_data['content'])} characters")
        print(f"  Token usage: {input_tokens} input + {output_tokens} output = {input_tokens + output_tokens} total")

        # Step 3: Calculate cost
        cost_cents = calculate_api_cost(input_tokens, output_tokens)
        cost_dollars = cost_cents / 100

        print(f"  Estimated cost: ${cost_dollars:.4f} ({cost_cents} cents)")

        # Step 4: Save blog post to database
        print("\n[3/5] Saving blog post to database...")
        blog_post_id = create_blog_post(
            title=post_data['title'],
            content=post_data['content'],
            status='draft'
        )

        print(f"✓ Saved blog post with ID: {blog_post_id}")

        # Step 5: Mark RSS items as used
        print("\n[4/5] Marking RSS items as used...")
        client = get_supabase_client()
        item_ids = [item['id'] for item in rss_items_for_generation]

        for item_id in item_ids:
            client.table("blog_rss_items").update({
                "used_in_blog": str(blog_post_id)
            }).eq("id", item_id).execute()

        print(f"✓ Marked {len(item_ids)} RSS items as used")

        # Step 6: Log activity
        print("\n[5/5] Logging activity to database...")
        duration_ms = int((time.time() - start_time) * 1000)

        log_agent_activity(
            agent_name="spike.py",
            activity_type="content_generation",
            success=True,
            context_id=blog_post_id,
            duration_ms=duration_ms,
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_cents": cost_cents,
                "rss_items_used": len(item_ids)
            }
        )

        print("✓ Activity logged")

        # Summary
        print("\n" + "=" * 80)
        print("EXECUTION SUMMARY")
        print("=" * 80)
        print("Status: SUCCESS")
        print(f"Blog Post ID: {blog_post_id}")
        print(f"Title: {post_data['title']}")
        print("Status: draft (ready for manual review)")
        print(f"Content length: {len(post_data['content'])} characters")
        print(f"RSS items used: {len(item_ids)}")
        print(f"Token usage: {input_tokens} input + {output_tokens} output")
        print(f"Cost: ${cost_dollars:.4f}")
        print(f"Duration: {duration_ms/1000:.2f} seconds")
        print("=" * 80)

        # Print content preview
        print("\nCONTENT PREVIEW (first 500 characters):")
        print("-" * 80)
        print(post_data['content'][:500] + "...")
        print("-" * 80)

        return 0

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)

        print(f"\n✗ FAILED: {e}")

        # Log failure
        try:
            log_agent_activity(
                agent_name="spike.py",
                activity_type="content_generation",
                success=False,
                context_id=blog_post_id,
                duration_ms=duration_ms,
                error_message=str(e)
            )
        except Exception as log_error:
            print(f"  (Failed to log error: {log_error})")

        print("\n" + "=" * 80)
        print("EXECUTION SUMMARY")
        print("=" * 80)
        print("Status: FAILED")
        print(f"Error: {e}")
        print(f"Duration: {duration_ms/1000:.2f} seconds")
        print("=" * 80)

        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
