"""Apply db-006 migration: Create database indexes."""

import sys
from db_utils import apply_migration


def main():
    """Apply db-006 migration."""
    return apply_migration(
        sql_filename="006_create_database_indexes.sql",
        migration_name="db-006 - Create database indexes",
    )


if __name__ == "__main__":
    sys.exit(main())
