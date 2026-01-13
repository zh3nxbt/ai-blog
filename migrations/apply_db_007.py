"""Apply db-007 migration: Seed manufacturing RSS sources."""

import sys
from db_utils import apply_migration


def main():
    """Apply db-007 migration."""
    return apply_migration(
        sql_filename="007_seed_manufacturing_rss_sources.sql",
        migration_name="db-007 - Seed manufacturing RSS sources",
    )


if __name__ == "__main__":
    sys.exit(main())
