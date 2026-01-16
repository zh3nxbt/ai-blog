import sys

from db_utils import apply_migration


def main() -> int:
    return apply_migration(
        sql_filename="010_seed_expanded_rss_sources.sql",
        migration_name="db-008 - Seed expanded manufacturing RSS sources",
    )


if __name__ == "__main__":
    sys.exit(main())
