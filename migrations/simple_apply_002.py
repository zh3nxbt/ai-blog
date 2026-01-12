"""Simple script to apply migration 002 via raw SQL execution."""

import sys
from pathlib import Path

# Add parent directory to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


def read_sql():
    """Read migration SQL."""
    sql_file = Path(__file__).parent / "002_create_blog_content_drafts.sql"
    return sql_file.read_text()


def main():
    """Apply migration."""
    sql = read_sql()

    print("=" * 70)
    print("Applying Migration: 002_create_blog_content_drafts")
    print("=" * 70)
    print()
    print("SQL to execute:")
    print("-" * 70)
    print(sql)
    print("-" * 70)
    print()
    print("Supabase Project: " + settings.supabase_url)
    print()
    print("MANUAL EXECUTION STEPS:")
    print("1. Go to: https://app.supabase.com/")
    print("2. Select your project")
    print("3. Navigate to: SQL Editor")
    print("4. Create new query")
    print("5. Paste the SQL above")
    print("6. Click 'Run'")
    print()
    print("After execution, run verification:")
    print(
        '  python -c \'import sys; sys.path.insert(0, "/workspace/ai-blog"); exec(open("migrations/verify_db_002.py").read())\''
    )
    print()


if __name__ == "__main__":
    main()
