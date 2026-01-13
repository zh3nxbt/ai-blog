"""Apply db-005 migration: Create blog_rss_items table."""

import sys
from db_utils import apply_migration


def main():
    """Apply db-005 migration."""
    return apply_migration(
        sql_filename="005_create_blog_rss_items.sql",
        migration_name="db-005 - Create blog_rss_items table",
    )


if __name__ == "__main__":
    sys.exit(main())
