# blog-backend

Backend service that generates one daily blog post for a machine shop website and stores it in Supabase.

## Core Principles

**This project optimizes for boring correctness.**

- Stable, legal, reproducible content sources only
- Explicit over clever
- Reliability over elegance
- Fail loudly, never silently

## Project Goals

1. Generate exactly **one high-quality blog post per day**
2. Use only stable, legal content sources (no scraping, no fragile platforms)
3. Maintain reliability and maintainability over novelty
4. Store results in Supabase for consumption by existing website

## Architecture

**Stack:**
- Python + FastAPI
- Supabase (external PostgreSQL)
- External LLM API (no local models)
- No containers

**Components:**

### 1. API (FastAPI)
- Health checks
- Manual generation trigger
- Draft/post listing (optional)
- Future admin hooks
- **Stateless, minimal surface area, no business logic duplication**

### 2. Worker (Python Script)
- Runs once per day via systemd timer or cron
- Fetches content from RSS feeds
- Deduplicates sources
- Generates post via LLM
- Validates output structure
- Stores in Supabase
- **Must be idempotent and safe to re-run**

## Environment Constraints

### Development (WSL2 Ubuntu on Windows)

**Valid paths:**
```
/home/<user>/projects/blog-backend
```

**Invalid paths:**
```
/mnt/c/Users/...
Any Windows-native directory
```

**Critical rules:**
- All project files MUST live inside Linux filesystem
- NEVER develop inside `/mnt/c`
- Always use Python virtual environments
- Watch for Windows/Linux permission and line ending differences

### Production (DigitalOcean Ubuntu)
- systemd service for API
- systemd timer or cron for worker
- Environment variables for secrets only

## Local Workflow

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Development
uvicorn api.main:app --reload          # API server
python worker.py --run-once            # Test worker
```

## Content Strategy

### Allowed Sources
- RSS feeds from manufacturing publications
- Vendor and tooling company feeds
- Government and standards body updates
- Evergreen topic bank (materials, tolerances, DFM, finishes)

### Explicitly Disallowed
- Facebook scraping
- Fragile HTML scraping
- ToS-restricted platforms
- Unstable or unreliable sources

### Content Rules
1. Summarize, never copy
2. Always include source links
3. No rehosted images (unless explicitly permitted)
4. No hallucinated facts or speculation

## LLM Guidelines

**Output format:** Structured JSON only

**Required fields:**
- `title`
- `excerpt`
- `content_markdown`
- `source_urls`

**Tone & Voice:**
- Practical and industrial, not corporate or salesy
- Direct communication, skip the fluff
- **Avoid AI slop language at all costs:**
  - No "delve into", "unveil", "landscape", "realm", "unlock", "leverage"
  - No "in today's fast-paced world" or "it's important to note"
  - No overuse of "robust", "streamline", "utilize", "cutting-edge"
  - Skip transitions like "let's explore" or "dive deep"
- **Develop personality without being cringe:**
  - Write like a knowledgeable shop veteran, not a marketing bot
  - Use concrete examples over abstract concepts
  - Casual but competent (think "here's what matters" not "revolutionize your workflow")
  - Okay to be opinionated when backed by facts
  - Short sentences. Active voice. No hedging.
- **Unique across AI-generated content:**
  - Vary sentence structure (not every paragraph needs 3 bullet points)
  - Lead with the interesting detail, not context-setting
  - Use specific numbers and examples
  - No formulaic "Introduction → 3 points → Conclusion" structure every time

**Anti-patterns to reject:**
```
❌ "In the ever-evolving landscape of manufacturing..."
✅ "Carbide tooling costs dropped 15% last quarter."

❌ "Let's delve into the intricacies of tolerance stacking..."
✅ "Tolerance stacking breaks projects. Here's why."

❌ "It's important to note that surface finish impacts..."
✅ "Surface finish isn't cosmetic—it changes how parts fail."
```

**Safety:**
- Validate all fields before persistence
- Retry safely on transient errors
- Clear error messages

## Data Model

### Post
```
id              UUID
title           String
slug            String
excerpt         String
content_markdown Text
source_urls     Array<String>
status          Enum(draft, published)
created_at      Timestamp
publish_date    Date
```

## Code Style

### Principles
- Small functions with clear intent
- Readable over abstract
- Reliability over elegance

### Rules
- No magic globals
- Type hints where useful
- Explicit error handling
- No silent failures

## Security

- **NEVER commit Supabase credentials**
- Secrets via environment variables only
- Validate external inputs
- No user-generated code execution

## Future Extensions (Non-blocking)

- Admin approval UI
- Multiple posts per day
- Category-based generation
- Internal shop data augmentation (CAD specs, equipment manuals)

---

**Last updated:** 2026-01-07
