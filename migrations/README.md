# Database Migrations

This directory contains SQL migrations and utilities for the ai-blog database schema.

## Quick Start

### Apply a Migration

```bash
cd /workspace/ai-blog
python migrations/apply_db_002.py
```

### Verify a Migration

```bash
PYTHONPATH=/workspace/ai-blog python migrations/verify_db_002.py
```

## Migration Files

### SQL Migrations
- `002_create_blog_content_drafts.sql` - Draft iterations table
- `003_create_blog_agent_activity.sql` - Agent activity logging
- `004_create_blog_rss_sources.sql` - RSS feed sources
- `005_create_blog_rss_items.sql` - RSS items storage
- `006_create_database_indexes.sql` - Performance indexes
- `007_seed_manufacturing_rss_sources.sql` - Initial RSS feed data
- `008_create_blog_topic_sources_items.sql` - Unified topic source tables
- `009_seed_evergreen_topics.sql` - Evergreen topic bank seed data

### Application Scripts
- `apply_db_002.py` through `apply_db_009.py` - Apply migrations automatically
- `db_utils.py` - Shared connection and migration utilities

### Verification Scripts
- `verify_db_002.py` through `verify_db_009.py` - Comprehensive acceptance tests

## How Migrations Work

### Automatic Application

Each `apply_db_XXX.py` script:
1. Reads connection credentials from environment variables
2. Tries multiple connection methods (direct + pooler fallback)
3. Executes the corresponding SQL file
4. Reports success/failure

**Environment Variables:**

**Option 1: Direct DATABASE_URL**
```bash
export DATABASE_URL="postgresql://postgres:[password]@[host]:5432/postgres"
python migrations/apply_db_002.py
```

**Option 2: Supabase credentials**
```bash
export SUPABASE_URL="https://[project-ref].supabase.co"
export SUPABASE_DB_PASSWORD="your_database_password"
python migrations/apply_db_002.py
```

The script will automatically:
- Try direct connection first
- Fall back to connection pooler (multiple regions)
- Report which connection method worked

### Manual Application

If automatic application fails, use the Supabase SQL Editor:

1. Open the migration SQL file (e.g., `002_create_blog_content_drafts.sql`)
2. Copy the entire SQL content
3. Go to https://app.supabase.com/
4. Navigate to: SQL Editor
5. Paste and run the SQL

## Connection Troubleshooting

### IPv6 Issues

If you see "cannot connect to server" errors, try using the connection pooler:

```bash
export SUPABASE_POOLER_HOST="aws-0-us-east-1.pooler.supabase.com"
python migrations/apply_db_XXX.py
```

Available pooler regions:
- `aws-0-us-east-1.pooler.supabase.com`
- `aws-0-us-west-1.pooler.supabase.com`
- `aws-0-eu-west-1.pooler.supabase.com`
- `aws-0-ap-southeast-1.pooler.supabase.com`

### Finding Your Database Password

1. Go to https://app.supabase.com/
2. Select your project
3. Navigate to: Settings > Database
4. Look for "Connection string" or "Database password"
5. Copy the password (NOT the anon/service keys)

## Verification

After applying a migration, always run the verification script:

```bash
PYTHONPATH=/workspace/ai-blog python migrations/verify_db_002.py
```

Verification scripts test:
- Table exists
- Can insert/update/delete records
- Column types are correct
- Constraints work (foreign keys, unique, check)
- Indexes exist
- Default values work

**Expected output:**
```
✅ All acceptance criteria passed!

Summary:
  Tests passed: 7/7
  Tests failed: 0
```

## Adding New Migrations

1. **Create SQL file**: `migrations/XXX_description.sql`

2. **Create apply script**: `migrations/apply_db_XXX.py`
   ```python
   import sys
   from db_utils import apply_migration

   def main():
       return apply_migration(
           sql_filename="XXX_description.sql",
           migration_name="db-XXX - Description",
       )

   if __name__ == "__main__":
       sys.exit(main())
   ```

3. **Create verification script**: `migrations/verify_db_XXX.py`
   - Test table existence
   - Test insertions
   - Test constraints
   - Test indexes
   - Return exit code 0 for success, 1 for failure

## Architecture

### Why This Design?

**Shared utilities (`db_utils.py`):**
- Eliminates code duplication (previously 40% of codebase)
- Centralized connection logic
- Easy to maintain and update
- Consistent error messages

**Pure SQL migrations:**
- No ORM complexity
- Direct database control
- Easy to review and understand
- Works with any database tool

**Comprehensive verification:**
- Catch regressions early
- Document expected behavior
- CI/CD integration via exit codes

## Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `db_utils.py` | Shared connection + migration logic | ~200 |
| `apply_db_XXX.py` (×6) | Apply specific migration | ~16 each |
| `verify_db_XXX.py` (×6) | Test migration acceptance criteria | ~100 each |
| `*.sql` (×7) | Pure SQL migration definitions | Varies |
| `execute_sql.py` | Helper to print SQL for manual execution | ~50 |

**Total:** ~1,200 lines (down from ~2,900 before consolidation)

## Philosophy

This migration system follows the project's "boring correctness" principle:

- **Explicit over clever** - Pure SQL, no magic
- **Fail loudly** - Clear error messages with actionable guidance
- **Multiple fallbacks** - Auto pooler discovery, manual execution option
- **Comprehensive testing** - Every migration has verification

The goal is maintainability and reliability, not novelty.
