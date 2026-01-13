"""Apply db-004 migration: Create blog_rss_sources table."""

import sys
from db_utils import apply_migration


def main():
    """Apply db-004 migration."""
    return apply_migration(
        sql_filename="004_create_blog_rss_sources.sql",
        migration_name="db-004 - Create blog_rss_sources table",
    )


if __name__ == "__main__":
    sys.exit(main())
