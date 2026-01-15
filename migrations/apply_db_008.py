import sys

from db_utils import apply_migration


def main() -> int:
    return apply_migration(
        sql_filename="008_create_blog_topic_sources_items.sql",
        migration_name="mix-001 - Unified topic source tables",
    )


if __name__ == "__main__":
    sys.exit(main())
