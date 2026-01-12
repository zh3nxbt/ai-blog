"""Apply database migrations to Supabase."""

import sys
from pathlib import Path
from supabase import create_client
from config import settings


def apply_migration(migration_file: str):
    """Apply a SQL migration file to Supabase."""
    # Initialize Supabase client
    supabase = create_client(settings.supabase_url, settings.supabase_key)

    # Read migration file
    migration_path = Path(__file__).parent / migration_file
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    with open(migration_path, "r") as f:
        sql = f.read()

    print(f"📄 Applying migration: {migration_file}")

    try:
        # Execute SQL via Supabase RPC or direct SQL execution
        # Note: Supabase Python client doesn't have direct SQL execution
        # We'll use the PostgREST API to execute via a custom function or rpc

        # For now, we'll use the raw SQL execution via the underlying connection
        # This requires using the postgrest client's rpc method
        supabase.rpc("exec_sql", {"sql": sql}).execute()

        print(f"✅ Migration applied successfully: {migration_file}")
        return True
    except Exception as e:
        # If exec_sql doesn't exist, print SQL for manual execution
        print(
            "⚠️  Cannot auto-apply migration. Please execute manually in Supabase SQL Editor:"
        )
        print(f"\n{sql}\n")
        print(f"Error: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python apply_migration.py <migration_file>")
        print("Example: python apply_migration.py 002_create_blog_content_drafts.sql")
        sys.exit(1)

    migration_file = sys.argv[1]
    success = apply_migration(migration_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
