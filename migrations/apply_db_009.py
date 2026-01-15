import sys

from db_utils import apply_migration


def main() -> int:
    return apply_migration(
        sql_filename="009_seed_evergreen_topics.sql",
        migration_name="mix-002 - Seed evergreen topic bank",
    )


if __name__ == "__main__":
    sys.exit(main())
