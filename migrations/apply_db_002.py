"""Apply db-002 migration: Create blog_content_drafts table."""

import sys
from db_utils import apply_migration


def main():
    """Apply db-002 migration."""
    return apply_migration(
        sql_filename="002_create_blog_content_drafts.sql",
        migration_name="db-002 - Create blog_content_drafts table",
    )


if __name__ == "__main__":
    sys.exit(main())
