"""Execute SQL via Supabase Management API."""

import os
import sys
from pathlib import Path
import httpx


def read_migration_sql() -> str:
    """Read the migration SQL file."""
    migration_path = Path(__file__).parent / "002_create_blog_content_drafts.sql"
    with open(migration_path, "r") as f:
        return f.read()


def execute_sql_via_api(sql: str) -> bool:
    """Execute SQL using Supabase Management API."""
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SECRET") or os.getenv("SUPABASE_KEY", "")

    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL or SUPABASE_KEY not found in environment")
        return False

    # Try to execute via REST API using RPC
    api_url = f"{supabase_url}/rest/v1/rpc/exec_sql"

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
    }

    payload = {"query": sql}

    try:
        with httpx.Client() as client:
            response = client.post(api_url, headers=headers, json=payload, timeout=30.0)

            if response.status_code == 200:
                return True
            else:
                print(f"❌ API returned {response.status_code}: {response.text}")
                return False

    except Exception as e:
        print(f"❌ API request failed: {e}")
        return False


def main():
    """Main entry point."""
    print("=" * 70)
    print("EXECUTING SQL VIA SUPABASE API")
    print("=" * 70)
    print()

    sql = read_migration_sql()

    print("📝 Attempting to execute SQL via Supabase REST API...")
    print()

    if execute_sql_via_api(sql):
        print("✅ SQL executed successfully!")
        print()
        print("Run verification:")
        print("  PYTHONPATH=/workspace/ai-blog python migrations/verify_db_002.py")
        print()
        return 0
    else:
        print()
        print("⚠️  API execution failed. This is expected - Supabase REST API")
        print("    doesn't support arbitrary SQL execution for security reasons.")
        print()
        print("MANUAL EXECUTION REQUIRED:")
        print("-" * 70)
        print(sql)
        print("-" * 70)
        print()
        print("To apply manually:")
        print("  1. Copy the SQL above")
        print("  2. Go to: https://app.supabase.com/")
        print("  3. Navigate to: SQL Editor")
        print("  4. Paste and execute")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
