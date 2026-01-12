"""Helper script to execute raw SQL using Supabase client."""

import sys
from pathlib import Path


def execute_sql_file(sql_file_path: str):
    """Execute SQL from a file."""
    # Read the SQL file
    sql_path = Path(sql_file_path)
    if not sql_path.exists():
        print(f"❌ SQL file not found: {sql_file_path}")
        return False

    with open(sql_path, "r") as f:
        sql = f.read()

    print(f"📝 Executing SQL from: {sql_file_path}")
    print()

    try:
        # Use the REST API to execute SQL
        # Note: This requires the SQL to be sent via RPC or we need to use postgREST
        # For migrations, it's better to use Supabase SQL editor or direct psql
        print("⚠️  Note: Supabase Python client doesn't support raw SQL execution.")
        print("Please use one of these methods:")
        print()
        print("1. Supabase SQL Editor:")
        print("   - Go to https://app.supabase.com/")
        print("   - Select your project")
        print("   - Go to SQL Editor")
        print("   - Paste and run the SQL")
        print()
        print("2. Direct PostgreSQL connection:")
        print("   - Set SUPABASE_DB_PASSWORD in .env")
        print("   - Run: python migrations/apply_db_004.py")
        print()
        print("SQL to execute:")
        print("=" * 70)
        print(sql)
        print("=" * 70)
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python execute_sql.py <sql_file_path>")
        sys.exit(1)

    sql_file = sys.argv[1]
    success = execute_sql_file(sql_file)
    sys.exit(0 if success else 1)
