"""Apply db-014 migration: Seed machinist/manufacturing resources."""

import sys

from db_utils import apply_migration


def main():
    """Apply db-014 migration."""
    return apply_migration(
        sql_filename="014_seed_machinist_resources.sql",
        migration_name="db-014 - Seed machinist/manufacturing resources",
    )


if __name__ == "__main__":
    sys.exit(main())
