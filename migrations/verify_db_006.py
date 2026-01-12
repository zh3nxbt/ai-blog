"""Verify db-006: database indexes acceptance criteria."""

import os
import sys

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)


def get_db_connection_string() -> str:
    """Get PostgreSQL connection string from environment."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    supabase_url = os.getenv("SUPABASE_URL", "")
    db_password = os.getenv("SUPABASE_DB_PASSWORD", "")

    if not db_password:
        print("❌ Database credentials not found in environment")
        sys.exit(1)

    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
    preferred_pooler = os.getenv("SUPABASE_POOLER_HOST")

    connection_attempts = [
        (f"db.{project_ref}.supabase.co", False),
    ]

    if preferred_pooler:
        connection_attempts.append((preferred_pooler, True))

    pooler_regions = [
        "aws-0-us-east-1.pooler.supabase.com",
        "aws-0-us-west-1.pooler.supabase.com",
        "aws-0-eu-west-1.pooler.supabase.com",
        "aws-0-ap-southeast-1.pooler.supabase.com",
    ]
    connection_attempts.extend((region, True) for region in pooler_regions)

    for host, is_pooler in connection_attempts:
        username = f"postgres.{project_ref}" if is_pooler else "postgres"
        conn_string = f"postgresql://{username}:{db_password}@{host}:5432/postgres"

        try:
            conn = psycopg2.connect(conn_string, connect_timeout=5)
            conn.close()
            return conn_string
        except Exception:
            continue

    print("❌ Could not connect to database")
    sys.exit(1)


def verify_index_exists(cur, index_name: str) -> bool:
    """Check if an index exists in the database."""
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE indexname = %s
        );
        """,
        (index_name,),
    )
    result = cur.fetchone()
    return result[0] if result else False


def verify_partial_index_condition(cur, index_name: str, expected_condition: str) -> bool:
    """Verify that a partial index has the expected WHERE condition."""
    cur.execute(
        """
        SELECT pg_get_expr(indpred, indrelid) AS condition
        FROM pg_index
        JOIN pg_class ON pg_class.oid = pg_index.indexrelid
        WHERE pg_class.relname = %s;
        """,
        (index_name,),
    )
    result = cur.fetchone()
    if not result or result[0] is None:
        return False

    condition = result[0].strip()
    # Normalize for comparison (partial index format varies, may have parentheses)
    condition_normalized = condition.upper().replace("(", "").replace(")", "")
    return "USED_IN_BLOG IS NULL" in condition_normalized


def verify_index_usage_for_unused_items(cur) -> bool:
    """Verify that the query for unused RSS items uses the partial index."""
    # Use EXPLAIN to see query plan
    cur.execute(
        """
        EXPLAIN (FORMAT JSON)
        SELECT * FROM blog_rss_items WHERE used_in_blog IS NULL;
        """
    )
    result = cur.fetchone()
    if not result:
        return False

    explain_output = str(result[0])
    # Check if the index scan mentions our partial index
    return "idx_blog_rss_items_unused" in explain_output


def verify_db_006():
    """Verify all acceptance criteria for db-006."""
    print("🔍 Verifying db-006: database indexes\n")

    # Get database connection
    conn_string = get_db_connection_string()

    conn = None
    cur = None
    results = []

    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        # 1. Index exists on blog_content_drafts(blog_post_id, iteration_number DESC)
        print("✓ Checking: Index idx_blog_content_drafts_post_iteration exists...")
        if verify_index_exists(cur, "idx_blog_content_drafts_post_iteration"):
            results.append(
                ("Index on blog_content_drafts(blog_post_id, iteration_number DESC)", True)
            )
            print("  ✅ PASS\n")
        else:
            results.append(
                ("Index on blog_content_drafts(blog_post_id, iteration_number DESC)", False)
            )
            print("  ❌ FAIL: Index not found\n")

        # 2. Index exists on blog_agent_activity(agent_name, created_at DESC)
        print("✓ Checking: Index idx_blog_agent_activity_agent_time exists...")
        if verify_index_exists(cur, "idx_blog_agent_activity_agent_time"):
            results.append(("Index on blog_agent_activity(agent_name, created_at DESC)", True))
            print("  ✅ PASS\n")
        else:
            results.append(("Index on blog_agent_activity(agent_name, created_at DESC)", False))
            print("  ❌ FAIL: Index not found\n")

        # 3. Index exists on blog_agent_activity(activity_type, created_at DESC)
        print("✓ Checking: Index idx_blog_agent_activity_type_time exists...")
        if verify_index_exists(cur, "idx_blog_agent_activity_type_time"):
            results.append(
                ("Index on blog_agent_activity(activity_type, created_at DESC)", True)
            )
            print("  ✅ PASS\n")
        else:
            results.append(
                ("Index on blog_agent_activity(activity_type, created_at DESC)", False)
            )
            print("  ❌ FAIL: Index not found\n")

        # 4. Partial index exists on blog_rss_items WHERE used_in_blog IS NULL
        print("✓ Checking: Partial index idx_blog_rss_items_unused exists...")
        if verify_index_exists(cur, "idx_blog_rss_items_unused"):
            results.append(("Partial index on blog_rss_items WHERE used_in_blog IS NULL", True))
            print("  ✅ PASS\n")

            # 4a. Verify the partial index has the correct WHERE condition
            print("✓ Checking: Partial index has WHERE used_in_blog IS NULL condition...")
            if verify_partial_index_condition(cur, "idx_blog_rss_items_unused", "used_in_blog IS NULL"):
                results.append(("Partial index has correct WHERE condition", True))
                print("  ✅ PASS\n")
            else:
                results.append(("Partial index has correct WHERE condition", False))
                print("  ❌ FAIL: Partial index condition incorrect\n")
        else:
            results.append(("Partial index on blog_rss_items WHERE used_in_blog IS NULL", False))
            print("  ❌ FAIL: Index not found\n")

        # 5. Query for unused RSS items uses the partial index
        print("✓ Checking: Query for unused items uses partial index...")
        if verify_index_usage_for_unused_items(cur):
            results.append(("Query uses index for unused RSS items", True))
            print("  ✅ PASS\n")
        else:
            results.append(("Query uses index for unused RSS items", False))
            print("  ❌ FAIL: Query does not use the partial index\n")

    except Exception as e:
        print(f"❌ Verification error: {e}\n")
        results.append(("Verification completed without errors", False))

    finally:
        # Clean up connection
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # Print summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for criterion, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {criterion}")

    print("=" * 60)
    print(f"Total: {passed}/{total} criteria passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = verify_db_006()
    sys.exit(0 if success else 1)
