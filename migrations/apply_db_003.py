"""Apply db-003 migration: Create blog_agent_activity table."""

import sys
from db_utils import apply_migration


def main():
    """Apply db-003 migration."""
    return apply_migration(
        sql_filename="003_create_blog_agent_activity.sql",
        migration_name="db-003 - Create blog_agent_activity table",
    )


if __name__ == "__main__":
    sys.exit(main())
