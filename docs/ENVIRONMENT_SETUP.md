# Environment Variables Setup Guide

## Required API Keys

### 1. Supabase (Database)

**Variables:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon or service role key

**Where to get:**
1. Go to your Supabase project dashboard
2. Click "Settings" → "API"
3. Copy the Project URL
4. Copy the `anon` key (for basic use) or `service_role` key (for full access)

**Required for:**
- Storing blog posts and drafts
- RSS feed management
- Agent activity logging
- All database operations

---

### 2. Anthropic API (Claude AI)

**Variables:**
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `ANTHROPIC_MODEL` - Model to use (default: `claude-sonnet-4-5`)

**Where to get:**
1. Go to https://console.anthropic.com/
2. Navigate to "API Keys"
3. Create a new API key
4. Copy the key (starts with `sk-ant-api03-...`)

**Important:** This is separate from Claude Code CLI! Your application needs its own API key to:
- Generate blog content via ProductMarketingAgent
- Critique content for quality validation
- Iterate on drafts until quality threshold is reached

**Cost management:**
- Set `RALPH_COST_LIMIT_CENTS` to control spending per generation run
- Default: $1.00 per run (100 cents)
- Average expected cost: $0.25 per published post

---

## Ralph Configuration

**Variables:**
- `RALPH_TIMEOUT_MINUTES` - Max time per generation run (default: 30)
- `RALPH_QUALITY_THRESHOLD` - Quality score to publish (default: 0.85)
- `RALPH_QUALITY_FLOOR` - Minimum quality to save as draft (default: 0.70)
- `RALPH_COST_LIMIT_CENTS` - Max API cost per run in cents (default: 100 = $1.00)

**How it works:**
1. Ralph generates initial draft
2. Critiques and iterates until quality ≥ 0.85 → publishes
3. If timeout/cost limit hit and quality ≥ 0.70 → saves as draft
4. If quality < 0.70 at limits → fails explicitly

---

## Setup Steps

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Get your Supabase credentials and add them to `.env`

3. Get your Anthropic API key and add it to `.env`

4. Adjust Ralph configuration values if needed (defaults are good)

5. Verify configuration:
   ```bash
   python -c "from config import *; print('Config loaded successfully')"
   ```

---

## Security Notes

- **NEVER commit `.env` to git** (already in `.gitignore`)
- Use environment variables only, never hardcode secrets
- Rotate API keys periodically
- Use Supabase `service_role` key only if you need full admin access
- Monitor API usage to avoid unexpected charges

---

## Cost Estimates

**Anthropic API (Claude Sonnet 4.5):**
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens
- Average blog post: 2-4 iterations
- Expected cost: $0.15-$0.25 per published post

**Supabase:**
- Free tier includes 500MB database + 1GB file storage
- Plenty for storing blog posts and metadata

**Total monthly cost estimate (30 posts):**
- Anthropic API: ~$7.50/month
- Supabase: $0 (within free tier)
- **Total: ~$7.50/month**
