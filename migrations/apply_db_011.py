"""Apply db-011 migration: Add input_data and output_data to blog_agent_activity."""

import sys
from db_utils import apply_migration


def main():
    """Apply db-011 migration."""
    return apply_migration(
        sql_filename="011_add_input_output_data_to_blog_agent_activity.sql",
        migration_name="db-011 - Add input_data and output_data to blog_agent_activity",
    )


if __name__ == "__main__":
    sys.exit(main())
