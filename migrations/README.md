# Database Migrations

This directory contains SQL migrations for the ai-blog database.

## How to Apply Migrations

### Option 1: Manual Execution (Recommended)

1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Select your project
3. Navigate to **SQL Editor**
4. Create a new query
5. Copy and paste the contents of the migration file (e.g., `002_create_blog_content_drafts.sql`)
6. Click **Run**

### Option 2: Using psycopg2 (Requires Database Password)

**Automatic (tries multiple regions):**
```bash
# Set your database password
export SUPABASE_DB_PASSWORD="your_password"

# Optionally specify preferred pooler region
export SUPABASE_POOLER_HOST="aws-0-us-east-1.pooler.supabase.com"

# Run the migration script (will try multiple regions automatically)
python migrations/apply_db_002.py
```

**Manual connection string:**
```bash
# Set your database connection string directly
export DATABASE_URL="postgresql://postgres:[YOUR_PASSWORD]@[YOUR_HOST]:5432/postgres"

# Run the migration script
python migrations/apply_db_002.py
```

**Pooler regions:**
The script automatically tries:
- Direct connection: `db.{project_ref}.supabase.co`
- US East: `aws-0-us-east-1.pooler.supabase.com`
- US West: `aws-0-us-west-1.pooler.supabase.com`
- EU West: `aws-0-eu-west-1.pooler.supabase.com`
- Asia Pacific: `aws-0-ap-southeast-1.pooler.supabase.com`

### Option 3: Using Supabase CLI (If Installed)

```bash
# Initialize Supabase in your project
supabase init

# Link to your project
supabase link --project-ref [YOUR_PROJECT_REF]

# Apply migrations
supabase db push
```

## Verifying Migrations

After applying a migration, run the verification script:

```bash
PYTHONPATH=/workspace/ai-blog python migrations/verify_db_002.py
```

## Migration Files

- `002_create_blog_content_drafts.sql` - Creates blog_content_drafts table for storing draft iterations

## Troubleshooting

**Error: "relation does not exist"**
- The table hasn't been created yet. Apply the migration manually using Option 1 above.

**Error: "duplicate key value violates unique constraint"**
- You're trying to insert a draft with a duplicate (blog_post_id, iteration_number). This is expected behavior.

**Connection issues:**
- Verify your `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- For direct PostgreSQL access, you need the database password from Supabase Settings > Database
