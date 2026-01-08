# Implementation Plan: Blog Backend

**Status:** Ready for approval
**Date:** 2026-01-07

## Executive Summary

Build a Python backend service that generates one daily blog post for MAS Precision Parts by:
1. Fetching recent manufacturing RSS feeds
2. Using Claude 3.5 Sonnet to generate 800-1200 word posts
3. Auto-publishing to existing Supabase blog_posts table
4. Sending email alerts via Resend.com on failures

---

## Database Architecture

### Existing Table: `blog_posts`
Already set up with all required fields. We'll use:
- `title` - Generated post title
- `slug` - Auto-generated from title using python-slugify
- `content` - HTML content (convert from LLM's markdown)
- `excerpt` - Short summary for previews
- `tags` - Array of categories (LLM-generated)
- `status` - Set to `'published'` for auto-publish
- `published_at` - Set to current timestamp
- `author` - Default 'MAS Precision Parts' (already set)
- `meta_description` - Same as excerpt for SEO

**Fields we'll skip for now:**
- `featured_image` - Text-only posts (per requirements)
- `meta_keywords` - Modern SEO doesn't prioritize this

### New Tables to Design

**Note:** All new tables use `blog_*` prefix for consistency.

#### 1. `blog_rss_feeds`
Manage RSS sources dynamically without code changes.

```sql
CREATE TABLE blog_rss_feeds (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  url text NOT NULL UNIQUE,
  name text NOT NULL,
  category text,
  active boolean DEFAULT true,
  last_fetched_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now()
);
```

**Usage:** Worker fetches all active feeds daily.

#### 2. `evergreen_topics`
Fallback content when RSS feeds are stale.

```sql
CREATE TABLE evergreen_topics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  description text,
  keywords text[],
  used_count integer DEFAULT 0,
  last_used_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now()
);
```

**Usage:** Sequential rotation - pick topic with oldest `last_used_at`.

#### 3. `used_feed_items`
Track which RSS items we've already covered to avoid duplication.

```sql
CREATE TABLE used_feed_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  feed_url text NOT NULL,
  item_url text NOT NULL UNIQUE,
  item_title text,
  used_at timestamp with time zone DEFAULT now(),
  post_id uuid REFERENCES blog_posts(id)
);
```

**Usage:** Before using RSS item, check if `item_url` exists in this table.

#### 4. `generation_log`
Audit trail for debugging and monitoring.

```sql
CREATE TABLE generation_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  status text NOT NULL, -- 'success', 'failed', 'skipped'
  post_id uuid REFERENCES blog_posts(id),
  source_type text, -- 'rss', 'evergreen'
  sources_used jsonb,
  error_message text,
  quality_score integer, -- 0-100
  generation_time_seconds integer,
  created_at timestamp with time zone DEFAULT now()
);
```

**Usage:** Log every worker run for troubleshooting.

---

## Service Architecture

### Module Structure

```
services/
├── rss_service.py          # Fetch & parse RSS feeds
├── content_service.py      # LLM generation & validation
├── supabase_service.py     # Database operations
├── email_service.py        # Resend.com alerts
└── quality_validator.py    # Post quality checks
```

### Service Responsibilities

#### 1. `rss_service.py`
```python
def fetch_active_feeds() -> list[dict]:
    """Get all active RSS feeds from Supabase."""

def fetch_feed_items(feed_url: str, limit: int = 15) -> list[dict]:
    """Parse RSS feed, return recent items."""

def get_unused_items(items: list[dict]) -> list[dict]:
    """Filter out items already in used_feed_items table."""

def mark_items_as_used(items: list[dict], post_id: str):
    """Record items in used_feed_items table."""
```

**Key logic:**
- Fetch all feeds where `active = true`
- Get latest 10-15 items per feed
- Cross-check against `used_feed_items` table
- Return only fresh, unused content

#### 2. `content_service.py`
```python
def generate_post(source_items: list[dict]) -> dict:
    """
    Use Claude 3.5 Sonnet to generate blog post.

    Returns:
        {
            "title": str,
            "content_markdown": str,
            "excerpt": str,
            "tags": list[str],
            "source_urls": list[str]
        }
    """

def build_prompt(items: list[dict], topic: dict = None) -> str:
    """Construct LLM prompt with voice guidelines from claude.md."""

def convert_markdown_to_html(markdown: str) -> str:
    """Convert LLM's markdown output to HTML for blog_posts.content."""
```

**LLM prompt structure:**
```
SYSTEM:
You are a blog writer for MAS Precision Parts, a machine shop.
Write practical, industrial content for machinists and engineers.

[Insert full voice guidelines from claude.md here]

USER:
Generate a blog post based on these manufacturing news items:
[RSS items with titles, excerpts, URLs]

Requirements:
- 800-1200 words
- Use concrete examples and specific numbers
- Suggest 3-5 relevant tags (e.g., "CNC Machining", "Materials", "Quality Control")
- Write in markdown format
- Avoid AI slop language (no "delve", "landscape", "robust", etc.)

Return JSON:
{
  "title": "...",
  "content_markdown": "...",
  "excerpt": "...",
  "tags": ["...", "..."]
}
```

#### 3. `quality_validator.py`
```python
AI_SLOP_KEYWORDS = [
    "delve", "unveil", "landscape", "realm", "unlock", "leverage",
    "in today's fast-paced", "it's important to note",
    "streamline", "cutting-edge", "revolutionize"
]

def validate_post(post_data: dict) -> tuple[bool, int, str]:
    """
    Check post quality before publishing.

    Returns:
        (is_valid, quality_score, failure_reason)
    """

def check_for_ai_slop(content: str) -> list[str]:
    """Return list of banned phrases found in content."""

def check_length(content: str, min_words: int = 800, max_words: int = 1200) -> bool:
    """Ensure word count is in target range."""

def check_structure(content: str) -> bool:
    """Verify post has headings, paragraphs, not just wall of text."""
```

**Quality scoring (0-100):**
- -50 points if contains AI slop keywords
- -20 points if too short/long
- -10 points if poor structure (no headings, huge paragraphs)
- -10 points if tags are generic ("Blog", "Update")
- Pass threshold: 70+

**Retry logic:** If score < 70, regenerate up to 3 times.

#### 4. `supabase_service.py`
```python
def get_supabase_client():
    """Initialize Supabase client with service role key."""

def check_post_exists_today() -> bool:
    """Query blog_posts for published_at = today."""

def save_post(post_data: dict) -> str:
    """
    Insert into blog_posts table.

    Sets:
    - status = 'published'
    - published_at = now()
    - slug = slugify(title)
    - content = markdown_to_html(content_markdown)
    """

def get_next_evergreen_topic() -> dict:
    """Get topic with oldest last_used_at (sequential rotation)."""

def update_evergreen_usage(topic_id: str):
    """Increment used_count, set last_used_at = now()."""

def log_generation(status: str, post_id: str, metadata: dict):
    """Insert into generation_log table."""
```

#### 5. `email_service.py`
```python
def send_failure_alert(error: str, context: dict):
    """
    Send email via Resend.com when generation fails.

    Email includes:
    - Error message
    - Last successful generation date
    - Feed status summary
    - Link to generation_log
    """
```

**Resend.com integration:**
- Use `resend` Python package
- API key in `.env` as `RESEND_API_KEY`
- Recipient in `.env` as `ALERT_EMAIL`

---

## Worker Flow

### Main Execution Path

```python
def run_worker():
    """Daily blog post generation."""

    # 1. Pre-flight checks
    if check_post_exists_today():
        log_generation('skipped', None, {'reason': 'already_generated'})
        return

    # 2. Fetch RSS content
    feeds = rss_service.fetch_active_feeds()
    all_items = []
    for feed in feeds:
        items = rss_service.fetch_feed_items(feed['url'], limit=15)
        unused = rss_service.get_unused_items(items)
        all_items.extend(unused)

    # 3. Fallback to evergreen if no RSS content
    source_type = 'rss'
    source_data = all_items

    if not all_items:
        topic = supabase_service.get_next_evergreen_topic()
        source_type = 'evergreen'
        source_data = topic

    # 4. Generate post with retries
    max_attempts = 3
    for attempt in range(max_attempts):
        post_data = content_service.generate_post(source_data)

        is_valid, score, reason = quality_validator.validate_post(post_data)

        if is_valid:
            break

        if attempt == max_attempts - 1:
            email_service.send_failure_alert(
                f"Quality validation failed after {max_attempts} attempts",
                {'last_score': score, 'reason': reason}
            )
            log_generation('failed', None, {'reason': 'quality_check'})
            return

    # 5. Save to Supabase
    post_id = supabase_service.save_post(post_data)

    # 6. Update tracking
    if source_type == 'rss':
        rss_service.mark_items_as_used(source_data, post_id)
    else:
        supabase_service.update_evergreen_usage(source_data['id'])

    # 7. Log success
    log_generation('success', post_id, {
        'source_type': source_type,
        'quality_score': score,
        'sources_count': len(source_data)
    })
```

---

## Configuration Updates

### `.env` additions
```bash
# Email Alerts
RESEND_API_KEY=re_your_key_here
ALERT_EMAIL=you@example.com

# Content Settings
MIN_WORDS=800
MAX_WORDS=1200
QUALITY_THRESHOLD=70
MAX_GENERATION_RETRIES=3

# Anthropic
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### `config.py` updates
```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Email
    resend_api_key: str
    alert_email: str

    # Content
    min_words: int = 800
    max_words: int = 1200
    quality_threshold: int = 70
    max_generation_retries: int = 3
    anthropic_model: str = "claude-3-5-sonnet-20241022"
```

---

## RSS Feed Research

I'll research and provide 10-15 quality RSS feeds covering:
- **Manufacturing news:** Modern Machine Shop, Production Machining
- **Tooling vendors:** Sandvik, Kennametal, Harvey Tool
- **Standards bodies:** NIST Manufacturing Updates
- **Industry associations:** NTMA, AMT

This will be a separate deliverable after plan approval.

---

## Testing Strategy

### Unit Tests
```
tests/
├── test_rss_service.py        # Mock feedparser responses
├── test_quality_validator.py  # Test slop detection
├── test_content_service.py    # Mock Anthropic API
└── test_supabase_service.py   # Mock Supabase client
```

### Integration Tests
- Full worker run with test Supabase project
- Mock LLM responses with pre-generated content
- Verify database state after generation

### Manual Testing Checklist
- [ ] RSS feeds parse correctly
- [ ] Deduplication works (run twice, verify no duplicate)
- [ ] Evergreen fallback activates when no RSS items
- [ ] Quality validator rejects AI slop
- [ ] Email alerts send on failure
- [ ] Posts appear in Supabase with correct fields
- [ ] HTML conversion preserves formatting

---

## Deployment

### Production Setup (DigitalOcean)

#### 1. systemd Service
```ini
[Unit]
Description=Blog Backend API
After=network.target

[Service]
Type=simple
User=bloguser
WorkingDirectory=/home/bloguser/blog-backend
Environment="PATH=/home/bloguser/blog-backend/.venv/bin"
ExecStart=/home/bloguser/blog-backend/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 2. systemd Timer (Daily 7 AM)
```ini
[Unit]
Description=Daily Blog Post Generation
Requires=blog-worker.service

[Timer]
OnCalendar=*-*-* 07:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

#### 3. Worker Service
```ini
[Unit]
Description=Blog Post Worker
After=network.target

[Service]
Type=oneshot
User=bloguser
WorkingDirectory=/home/bloguser/blog-backend
Environment="PATH=/home/bloguser/blog-backend/.venv/bin"
ExecStart=/home/bloguser/blog-backend/.venv/bin/python worker.py --run-once
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Day 1-2)
1. Create database tables in Supabase
2. Implement `supabase_service.py` with CRUD operations
3. Add markdown-to-HTML conversion
4. Test database connectivity

### Phase 2: RSS Pipeline (Day 2-3)
1. Implement `rss_service.py`
2. Research and populate initial RSS feeds
3. Test feed parsing and deduplication
4. Seed evergreen topics table

### Phase 3: Content Generation (Day 3-4)
1. Implement `content_service.py` with Claude integration
2. Build LLM prompt with voice guidelines
3. Test generation with mock RSS data
4. Implement `quality_validator.py`

### Phase 4: Alerts & Polish (Day 4-5)
1. Implement `email_service.py` with Resend.com
2. Add generation_log tracking
3. Complete worker.py with full flow
4. End-to-end testing

### Phase 5: Production Deploy (Day 5)
1. Set up systemd service and timer
2. Configure environment variables
3. Test production run
4. Monitor first automated generation

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| RSS feeds go down | Evergreen fallback + multiple feed sources |
| LLM generates poor quality | Quality validator with retry logic |
| API rate limits | Exponential backoff, single daily run |
| Duplicate content | Track used items in database |
| Email delivery fails | Log errors, check Resend.com dashboard |
| Worker crashes | systemd auto-restart, detailed logging |

---

## Success Metrics

- ✅ Post generated every day at 7 AM
- ✅ Quality score average > 80
- ✅ < 5% duplicate content rate
- ✅ < 1% generation failures per month
- ✅ Zero AI slop keywords in published posts
- ✅ Email alerts delivered within 5 minutes of failure

---

## Next Steps After Approval

1. **You create database tables** using SQL above
2. **I implement Phase 1** (Supabase integration)
3. **I research RSS feeds** and provide curated list
4. **We iterate** on LLM prompt until voice is perfect
5. **Deploy to production** and monitor

---

## Open Questions

1. ✅ Database schema - ANSWERED (you'll create tables from plan)
2. ✅ RSS feeds - ANSWERED (I'll research manufacturing sources)
3. ✅ Voice/tone - ANSWERED (use claude.md guidelines)
4. ✅ Failure handling - ANSWERED (alert via email, skip day)
5. ✅ Content selection - ANSWERED (random from recent, track used items)

---

**Ready to proceed?** This plan provides:
- Clear technical architecture
- Defined database schema
- Concrete implementation phases
- Quality safeguards
- Production deployment strategy

Let me know if you want to adjust any aspect before implementation begins.
