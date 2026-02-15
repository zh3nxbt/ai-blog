"""Apply db-013 migration: Seed authoritative RSS sources and disable fragile feeds."""

import sys

from db_utils import apply_migration


def main():
    """Apply db-013 migration."""
    return apply_migration(
        sql_filename="013_seed_authoritative_rss_sources.sql",
        migration_name="db-013 - Seed authoritative RSS sources",
    )


if __name__ == "__main__":
    sys.exit(main())
