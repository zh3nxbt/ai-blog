"""Run migration 002: Create blog_content_drafts table.

This script attempts to apply the migration using the Supabase client.
If that fails, it provides instructions for manual execution.
"""

import sys
from pathlib import Path
from supabase import create_client
from config import settings


def check_table_exists(supabase) -> bool:
    """Check if blog_content_drafts table already exists."""
    try:
        supabase.table("blog_content_drafts").select("id").limit(0).execute()
        return True
    except Exception:
        return False


def read_migration_sql() -> str:
    """Read the migration SQL file."""
    migration_path = Path(__file__).parent / "002_create_blog_content_drafts.sql"
    with open(migration_path, "r") as f:
        return f.read()


def main():
    """Main entry point."""
    print("=" * 70)
    print("MIGRATION: db-002 - Create blog_content_drafts table")
    print("=" * 70)
    print()

    # Initialize Supabase client
    supabase = create_client(settings.supabase_url, settings.supabase_key)

    # Check if table already exists
    print("🔍 Checking if table already exists...")
    if check_table_exists(supabase):
        print("✅ Table blog_content_drafts already exists!")
        print()
        print("Run verification: python migrations/verify_db_002.py")
        return 0

    print("❌ Table does not exist yet.")
    print()

    # Read migration SQL
    sql = read_migration_sql()

    # Print SQL for manual execution
    print("📋 MIGRATION SQL:")
    print("-" * 70)
    print(sql)
    print("-" * 70)
    print()

    print("📝 TO APPLY THIS MIGRATION:")
    print("1. Go to your Supabase dashboard: https://app.supabase.com/")
    print("2. Select your project")
    print("3. Navigate to: SQL Editor")
    print("4. Create a new query")
    print("5. Copy and paste the SQL above")
    print("6. Click 'Run' to execute")
    print()
    print("After applying the migration, run verification:")
    print("  python migrations/verify_db_002.py")
    print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
