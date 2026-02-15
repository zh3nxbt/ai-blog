"""Apply db-015 migration: Add RSS source health tracking columns."""

import sys

from db_utils import apply_migration


def main():
    """Apply db-015 migration."""
    return apply_migration(
        sql_filename="015_add_rss_source_health_columns.sql",
        migration_name="db-015 - Add RSS source health tracking columns",
    )


if __name__ == "__main__":
    sys.exit(main())
