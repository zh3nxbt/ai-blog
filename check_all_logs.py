#!/usr/bin/env python3
"""Quick script to view all recent logs"""

from supabase import create_client
import os
from dotenv import load_dotenv
import json

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET")
)

# Get the most recent activity
print("Checking blog_agent_activity...")
result = supabase.table("blog_agent_activity").select("*").order("created_at", desc=True).limit(10).execute()

if not result.data:
    print("No data found in blog_agent_activity")
else:
    print(f"Found {len(result.data)} records\n")
    for activity in result.data:
        print(f"\n{'='*60}")
        print(f"Agent: {activity.get('agent_name', 'N/A')}")
        print(f"Activity: {activity['activity_type']}")
        print(f"Time: {activity['created_at']}")
        print(f"Status: {activity.get('status', 'N/A')}")
        if activity.get('metadata'):
            print(f"\nMetadata:")
            metadata = json.dumps(activity['metadata'], indent=2)
            if len(metadata) > 1500:
                print(metadata[:1500] + "\n... (truncated)")
            else:
                print(metadata)
        if activity.get('input_data'):
            print(f"\nInput Data:")
            input_str = json.dumps(activity['input_data'], indent=2)
            if len(input_str) > 2000:
                print(input_str[:2000] + "\n... (truncated)")
            else:
                print(input_str)
        if activity.get('output_data'):
            print(f"\nOutput Data (first 500 chars):")
            output_str = json.dumps(activity['output_data'], indent=2)
            print(output_str[:500])
            if len(output_str) > 500:
                print("... (truncated)")

# Also check blog_posts for the skipped entry
print("\n\n" + "="*60)
print("Checking blog_posts for recent entries...")
posts = supabase.table("blog_posts").select("id, title, status, created_at").order("created_at", desc=True).limit(5).execute()

for post in posts.data:
    print(f"\nPost ID: {post['id']}")
    print(f"Title: {post.get('title', 'N/A')}")
    print(f"Status: {post['status']}")
    print(f"Created: {post['created_at']}")
