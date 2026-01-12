"""Verify db-007: 5 manufacturing RSS sources seeded."""

import os
import sys

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ requests not installed. Install with: pip install requests")
    sys.exit(1)


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
        print("❌ DATABASE CONNECTION STRING NOT FOUND")
        print("Set DATABASE_URL or SUPABASE_DB_PASSWORD environment variable")
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

    # Try common pooler regions
    pooler_regions = [
        "aws-0-us-east-1.pooler.supabase.com",
        "aws-0-us-west-1.pooler.supabase.com",
        "aws-0-eu-west-1.pooler.supabase.com",
        "aws-0-ap-southeast-1.pooler.supabase.com",
    ]
    connection_attempts.extend((region, True) for region in pooler_regions)

    for host, is_pooler in connection_attempts:
        # Use postgres.{project_ref} for poolers
        username = f"postgres.{project_ref}"
        conn_string = f"postgresql://{username}:{db_password}@{host}:5432/postgres"

        try:
            conn = psycopg2.connect(conn_string, connect_timeout=5)
            conn.close()
            print(f"✅ Connected via: {host}")
            return conn_string
        except Exception:
            continue

    print("❌ Could not connect to database")
    sys.exit(1)


def main():
    """Verify all acceptance criteria for db-007."""
    print("=" * 70)
    print("VERIFYING: db-007 - 5 manufacturing RSS sources seeded")
    print("=" * 70)
    print()

    conn_string = get_db_connection_string()
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor = conn.cursor()

    passed = 0
    total = 6

    # 1. At least 5 rows exist in blog_rss_sources
    try:
        cursor.execute("SELECT COUNT(*) FROM blog_rss_sources")
        count = cursor.fetchone()[0]
        if count >= 5:
            print(f"✓ [1/6] At least 5 rows exist ({count} rows)")
            passed += 1
        else:
            print(f"✗ [1/6] Expected >= 5 rows, found {count}")
    except Exception as e:
        print(f"✗ [1/6] Error checking row count: {e}")

    # 2. All seeded sources have active=true
    try:
        cursor.execute("SELECT COUNT(*) FROM blog_rss_sources WHERE active = false")
        inactive_count = cursor.fetchone()[0]
        if inactive_count == 0:
            print("✓ [2/6] All sources have active=true")
            passed += 1
        else:
            print(f"✗ [2/6] Found {inactive_count} inactive sources")
    except Exception as e:
        print(f"✗ [2/6] Error checking active status: {e}")

    # 3. All seeded sources have priority between 1-10
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM blog_rss_sources WHERE priority < 1 OR priority > 10"
        )
        invalid_priority = cursor.fetchone()[0]
        if invalid_priority == 0:
            print("✓ [3/6] All sources have priority between 1-10")
            passed += 1
        else:
            print(f"✗ [3/6] Found {invalid_priority} sources with invalid priority")
    except Exception as e:
        print(f"✗ [3/6] Error checking priority: {e}")

    # 4. At least one source URL returns valid RSS/XML when fetched
    try:
        cursor.execute("SELECT url FROM blog_rss_sources LIMIT 5")
        urls = [row[0] for row in cursor.fetchall()]
        valid_rss = False

        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                content = response.text.lower()
                if response.status_code == 200 and ("<?xml" in content or "<rss" in content):
                    print(f"✓ [4/6] Valid RSS/XML feed found: {url}")
                    valid_rss = True
                    passed += 1
                    break
            except Exception:
                continue

        if not valid_rss:
            print(f"✗ [4/6] No valid RSS/XML feed found among {len(urls)} sources")
    except Exception as e:
        print(f"✗ [4/6] Error checking RSS feeds: {e}")

    # 5. Sources include manufacturing industry publications
    try:
        cursor.execute("SELECT name, category FROM blog_rss_sources")
        sources = cursor.fetchall()
        manufacturing_keywords = ["manufacturing", "machining", "fabrication", "assembly"]
        has_manufacturing = False

        for name, category in sources:
            name_lower = name.lower() if name else ""
            category_lower = category.lower() if category else ""
            if any(kw in name_lower or kw in category_lower for kw in manufacturing_keywords):
                has_manufacturing = True
                break

        if has_manufacturing:
            print("✓ [5/6] Sources include manufacturing industry publications")
            passed += 1
        else:
            print("✗ [5/6] No manufacturing industry publications found")
    except Exception as e:
        print(f"✗ [5/6] Error checking manufacturing sources: {e}")

    # 6. Verify specific seed data exists
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM blog_rss_sources WHERE name IN "
            "('Assembly Magazine', 'Manufacturing Dive', 'Modern Machine Shop', "
            "'The Fabricator', 'American Machinist')"
        )
        seeded_count = cursor.fetchone()[0]
        if seeded_count >= 5:
            print("✓ [6/6] All 5 seed sources exist in database")
            passed += 1
        else:
            print(f"✗ [6/6] Expected 5 seed sources, found {seeded_count}")
    except Exception as e:
        print(f"✗ [6/6] Error checking seed data: {e}")

    cursor.close()
    conn.close()

    # Summary
    print()
    print(f"=== Summary: {passed}/{total} checks passed ===")
    print()

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
