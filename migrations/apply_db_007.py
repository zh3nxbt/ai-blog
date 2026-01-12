"""Apply db-007 migration: Seed 5 manufacturing RSS sources."""

import os
import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)


def read_migration_sql() -> str:
    """Read the migration SQL file."""
    migration_path = Path(__file__).parent / "007_seed_manufacturing_rss_sources.sql"
    with open(migration_path) as f:
        return f.read()


def get_db_connection_string() -> str:
    """Get PostgreSQL connection string from environment."""
    # Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    # Try to construct from Supabase URL and password
    supabase_url = os.getenv("SUPABASE_URL", "")
    db_password = os.getenv("SUPABASE_DB_PASSWORD", "")

    if not db_password:
        print()
        print("=" * 70)
        print("❌ DATABASE CONNECTION STRING NOT FOUND")
        print("=" * 70)
        print()
        print("To apply this migration automatically, you need to provide one of:")
        print()
        print("Option 1: Set DATABASE_URL environment variable")
        print("  DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres")
        print()
        print("Option 2: Set SUPABASE_DB_PASSWORD")
        print("  SUPABASE_DB_PASSWORD=your_database_password")
        print()
        print("Or execute the SQL manually in the Supabase SQL Editor.")
        print()
        sys.exit(1)

    # Extract project ref from URL
    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")

    # Check for preferred pooler region from env var
    preferred_pooler = os.getenv("SUPABASE_POOLER_HOST")

    # Build list of connection attempts
    connection_attempts = []

    # If user specified a pooler, try it first
    if preferred_pooler:
        connection_attempts.append((preferred_pooler, True))

    # Try direct connection
    connection_attempts.append((f"db.{project_ref}.supabase.co", False))

    # Try common pooler regions
    pooler_regions = [
        "aws-0-us-east-1.pooler.supabase.com",
        "aws-0-us-west-1.pooler.supabase.com",
        "aws-0-eu-west-1.pooler.supabase.com",
        "aws-0-ap-southeast-1.pooler.supabase.com",
    ]
    connection_attempts.extend((region, True) for region in pooler_regions)

    for host, is_pooler in connection_attempts:
        # Use postgres.{project_ref} for poolers, just postgres for direct
        username = f"postgres.{project_ref}" if is_pooler else "postgres"
        conn_string = f"postgresql://{username}:{db_password}@{host}:5432/postgres"

        try:
            conn = psycopg2.connect(conn_string, connect_timeout=5)
            conn.close()
            print(f"✅ Connected successfully via: {host}")
            return conn_string
        except Exception as e:
            print(f"⚠️  Failed to connect via {host}: {str(e)[:80]}")
            continue

    print()
    print("❌ Could not connect to database via any available host")
    sys.exit(1)


def main():
    """Apply migration."""
    print("=" * 70)
    print("APPLYING MIGRATION: db-007 - Seed 5 manufacturing RSS sources")
    print("=" * 70)
    print()

    # Get connection string
    conn_string = get_db_connection_string()

    # Read migration SQL
    sql = read_migration_sql()

    # Connect and execute
    print("🔗 Connecting to database...")
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        print("📝 Executing migration SQL...")
        cur.execute(sql)

        conn.commit()
        cur.close()
        conn.close()

        print("✅ Migration applied successfully!")
        print("✅ 5 manufacturing RSS sources seeded")
        print()
        print("Next step: Run verification")
        print("  python migrations/verify_db_007.py")
        print()
        return 0

    except Exception as e:
        # Clean up connections on failure
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass

        print(f"❌ Migration failed: {e}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
