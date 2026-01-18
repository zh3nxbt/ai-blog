"""Apply db-012 migration: Seed trade and policy RSS sources."""

import sys
from db_utils import apply_migration


def main():
    """Apply db-012 migration."""
    return apply_migration(
        sql_filename="012_seed_trade_policy_rss_sources.sql",
        migration_name="db-012 - Seed trade and policy RSS sources",
    )


if __name__ == "__main__":
    sys.exit(main())
