#!/usr/bin/env python3
"""Quick script to view juice evaluation logs with full source details.

Usage:
    python check_all_logs.py           # Show latest evaluation summary
    python check_all_logs.py --sources # Include full source summaries
"""

from supabase import create_client
import os
from dotenv import load_dotenv
import json
import sys

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET")
)

# Check for --sources flag to show full source details
show_sources = "--sources" in sys.argv

# Get the most recent juice evaluation with input_data
print("Checking latest juice evaluation...")
result = supabase.table("blog_agent_activity").select("*").eq(
    "activity_type", "juice_evaluation"
).order("created_at", desc=True).limit(1).execute()

if not result.data:
    print("No juice evaluation found")
else:
    activity = result.data[0]
    print(f"\n{'='*60}")
    print(f"Time: {activity['created_at']}")

    metadata = activity.get('metadata', {})
    print(f"\nJuice Score: {metadata.get('juice_score', 'N/A')} (threshold: 0.6)")
    print(f"Source Count: {metadata.get('source_count', 'N/A')}")
    print(f"Should Proceed: {metadata.get('should_proceed', 'N/A')}")
    print(f"Best Source: {metadata.get('best_source', 'N/A')}")
    print(f"Potential Angle: {metadata.get('potential_angle', 'N/A')}")
    print(f"Cost: {metadata.get('cost_cents', 0)} cents")
    print(f"\nLLM Reasoning:\n  {metadata.get('reason', 'N/A')}")

    # Show source details from input_data
    input_data = activity.get('input_data', {})
    source_items = input_data.get('source_items', [])

    if source_items:
        print(f"\n{'='*60}")
        print(f"SOURCE ITEMS EVALUATED ({len(source_items)} items):")
        print("="*60)

        for i, item in enumerate(source_items, 1):
            print(f"\n[{i}] {item.get('title', 'Untitled')}")
            print(f"    Type: {item.get('source_type', 'unknown')}")
            print(f"    Source: {item.get('source_name', 'N/A')}")
            print(f"    Published: {item.get('published_at', 'N/A')}")
            print(f"    URL: {item.get('url', 'N/A')}")
            if show_sources:
                summary = item.get('summary', 'No summary')
                if len(summary) > 300:
                    print(f"    Summary: {summary[:300]}...")
                else:
                    print(f"    Summary: {summary}")
    else:
        print("\nNo source items in input_data (older log format)")

print(f"\n{'='*60}")
if not show_sources:
    print("Tip: Run with --sources to see full summaries")
print("="*60)
