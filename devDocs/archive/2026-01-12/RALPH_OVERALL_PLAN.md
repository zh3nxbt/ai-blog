# Product Requirements Document: Ralph Wiggum Content Generation System

**Version:** 1.0
**Date:** 2026-01-09
**Status:** Ready for Implementation
**Meta-Context:** This PRD is the task definition for a Ralph Wiggum iterative implementation process

---

## Executive Summary

Build an autonomous blog content generation system (Ralph Wiggum) that produces one high-quality manufacturing industry blog post daily at 7 AM, using iterative self-improvement with Claude AI, RSS feeds, and quality validation.

**Key Innovation:** Iterative self-critique loop ensures zero AI slop and high-quality content through continuous refinement.

---

## Success Criteria

### Quantitative Metrics
- Daily blog generation success rate ≥ 95%
- Average quality score ≥ 0.87 (scale: 0.0-1.0)
- Average iterations per post: 2-4
- Zero AI slop in published posts (forbidden phrases detected)
- API costs per post: $0.10-$0.30
- Generation time: 10-20 minutes per post
- Timeout enforcement: 30 minutes maximum
- Cost guard: $1.00 per generation run (hard limit)

### Qualitative Criteria
- Content demonstrates manufacturing expertise
- Brand voice aligns with MAS Precision Parts (professional, technical, helpful)
- Posts provide actionable value to manufacturing audience
- No promotional/salesy language
- Natural human-like writing (not AI-generated feel)

---

## Core Requirements

### Functional Requirements

#### FR-1: RSS Feed Management
- System MUST fetch content from approved RSS sources only
- MUST support multiple RSS sources (minimum 5)
- MUST cache RSS items to prevent duplication
- MUST track which items have been used in blog posts
- MUST support priority weighting for sources

#### FR-2: Content Generation (Core Ralph Loop)
- MUST generate initial blog post draft from RSS content
- MUST iteratively improve content based on self-critique
- MUST continue iterations until quality ≥ 0.85 OR timeout/cost limits reached
- MUST support multiple agents: ProductMarketing (Phase 1), TrendScout (Phase 3), Research (Phase 3)
- MUST maintain iteration history in database

#### FR-3: Quality Validation
- MUST score content quality on 0.0-1.0 scale
- MUST detect AI slop keywords (forbidden phrases list)
- MUST validate manufacturing industry relevance
- MUST check brand voice alignment
- MUST verify structure and readability
- MUST provide specific, actionable critique for improvements

#### FR-4: Graceful Degradation
- MUST publish if quality ≥ 0.85
- MUST save as draft if 0.70 ≤ quality < 0.85 when timeout/cost limit reached
- MUST fail explicitly if quality < 0.70 when limits reached
- MUST never silently discard work
- MUST log all iterations regardless of outcome

#### FR-5: Safety Guards
- MUST enforce 30-minute timeout per generation
- MUST enforce $1.00 cost limit per generation
- MUST track API costs accurately (input + output tokens)
- MUST stop immediately when limits exceeded
- MUST alert on failures or draft-only outcomes

#### FR-6: Data Persistence
- MUST store all blog posts in Supabase
- MUST store all draft iterations with quality scores
- MUST log all agent activity for debugging
- MUST track RSS sources and items
- MUST record trends and research (Phase 3+)

#### FR-7: Scheduling & Automation
- MUST run automatically daily at 7 AM UTC
- MUST use systemd timer (no Docker/containers)
- MUST support manual trigger via API endpoint
- MUST implement idempotency (check if already generated today)
- MUST retry on transient failures (max 3 retries)

#### FR-8: Monitoring & Alerts
- MUST send email alerts on failures
- MUST send alerts when draft saved (quality < 0.85)
- MUST log all errors with full context
- MUST provide health check endpoint
- MUST track metrics (success rate, quality trends, costs)

---

### Non-Functional Requirements

#### NFR-1: Reliability
- System uptime ≥ 99% (excluding planned maintenance)
- No data loss under any failure scenario
- Idempotent operations (safe to retry)
- Explicit error handling (fail loudly, never silently)

#### NFR-2: Performance
- Generation completes within 30 minutes (hard timeout)
- API response time < 5 seconds for health checks
- Database queries optimized with indexes
- Efficient token usage (no unnecessary context)

#### NFR-3: Security
- All secrets in environment variables (never in code)
- No secrets in version control
- No user-generated code execution
- Validate and sanitize all external inputs (RSS feeds)
- Use Supabase RLS policies for data access

#### NFR-4: Maintainability
- Code follows "boring correctness" philosophy
- Explicit over clever
- Readable over abstract
- Comprehensive error messages
- Self-documenting code with clear naming
- No magic globals or hidden state

#### NFR-5: Cost Efficiency
- Hard limit $1 per generation (enforced)
- Target average $0.20 per post
- No unnecessary API calls
- Batch operations where possible

---

## AI Slop Detection (Critical)

### Forbidden Phrases (Must Detect & Penalize)
```
"delve", "delve into", "delving"
"unveil", "unveiling"
"landscape", "ever-changing landscape", "evolving landscape"
"realm", "in the realm of"
"unlock", "unlocking", "unlock the potential"
"leverage", "leveraging"
"robust", "robust solution"
"streamline", "streamlining"
"cutting-edge", "cutting edge"
"revolutionize", "revolutionary"
"game-changer", "game changer"
"dive deep", "deep dive"
"let's explore"
"in today's fast-paced world"
"it's important to note"
"it goes without saying"
```

**Rule:** Any forbidden phrase detected MUST result in quality score < 0.50

---

## Implementation Phases

### Phase 0: Vertical Spike (Days 1-3)
**Goal:** Prove Claude + Supabase + RSS integration works end-to-end

**Tasks:**
1. Create `blog_posts` table in Supabase (if doesn't exist)
2. Create `blog_rss_sources` table
3. Insert 1 hard-coded RSS source
4. Create `spike.py` with minimal logic:
   - Fetch 1 RSS feed
   - Extract 1 article
   - Call Claude with basic prompt
   - Insert result into `blog_posts`
5. Run 3 times, verify 3 drafts in database

**Deliverable:** Working proof that stack integrates (no production code)

**Success Criteria:** 3 blog drafts in Supabase from RSS articles

---

### Phase 1: Core Ralph Loop (Days 4-14)
**Goal:** Single-agent iterative content generation with quality validation

**Database Tasks:**
- Create `blog_content_drafts` table
- Create `blog_agent_activity` table
- Create `blog_rss_sources` table
- Create `blog_rss_items` table
- Add indexes for performance
- Seed 5 RSS sources (manufacturing publications)

**Services Layer:**
- Implement `services/rss_service.py`
  - `fetch_active_feeds()`
  - `fetch_feed_items(source_id, limit)`
  - `mark_items_as_used(item_ids, blog_id)`
- Implement `services/supabase_service.py`
  - `get_supabase_client()`
  - `create_blog_post(title, content, status)`
  - `save_draft_iteration(blog_id, iteration, content, quality, critique)`
  - `log_agent_activity(agent, activity_type, success, metadata)`
- Implement `services/quality_validator.py`
  - `validate_content(content, title)` → (quality_score, critique_details)
  - AI slop detection
  - Length validation (1000-2500 words)
  - Structure validation (headings)
  - Brand voice validation

**Ralph Core:**
- Implement `ralph/core/timeout_manager.py`
  - 30-minute timeout enforcement
  - $1 cost limit enforcement
  - Token cost calculation (Anthropic pricing)
- Implement `ralph/prompts/critique.py` (CRITICAL)
  - Self-critique prompt template
  - AI slop keyword list
  - Evaluation criteria (5 dimensions)
  - JSON output specification
- Implement `ralph/agents/base_agent.py`
  - Abstract agent class
  - Claude API integration
  - Token tracking
- Implement `ralph/agents/product_marketing_agent.py`
  - `generate_content(rss_items)` → initial draft
  - `improve_content(current_content, critique)` → improved draft
- Implement `ralph/core/ralph_loop.py`
  - Main orchestration logic
  - Iterative improvement loop
  - Exit conditions (quality, timeout, cost)
  - Graceful degradation

**Testing:**
- Manual runs: `python -m ralph.ralph_loop`
- Test high-quality first draft (quality > 0.85)
- Test 2-3 iterations to reach 0.85
- Test timeout before 0.85 (save as draft)
- Test cost limit exceeded (save as draft)

**Deliverable:** Working single-agent Ralph loop

**Success Criteria:**
- 5 successful blog posts published (quality ≥ 0.85)
- Average 2-4 iterations per post
- Zero AI slop in published content
- API costs < $0.25 per post

---

### Phase 2: Production Deployment (Days 15-21)
**Goal:** Automate daily blog generation at 7 AM

**Task System:**
- Implement `ralph/core/task_system.py`
  - `load_task_definition(path)` → task config
- Create `tasks/daily-blog/prd.json`
  - Quality thresholds
  - Length requirements
  - Success criteria
- Implement `ralph/core/progress_tracker.py`
  - `load_learnings(path)` → past learnings
  - `add_learning(learning, quality)`
  - `save_learnings(path)`

**Scheduler:**
- Implement `schedulers/daily_blog_scheduler.py`
  - Main entry point for daily run
  - Error handling and alerting
  - Success/failure logging
- Create `systemd/ai-blog-daily.service`
  - Oneshot service definition
  - Working directory and ExecStart
- Create `systemd/ai-blog-daily.timer`
  - Daily trigger at 7 AM UTC
  - Persistent flag for missed runs

**Error Handling:**
- Retry logic with exponential backoff
- Email alerts via Resend.com
- Idempotency check (already generated today?)
- Recovery: retry at 8 AM, 9 AM (max 3 attempts)

**Deployment:**
- Install systemd timer on production server
- Test first automated run
- Monitor logs for 5 consecutive days

**Deliverable:** Fully automated daily blog generation

**Success Criteria:**
- Blog published automatically at 7 AM for 5 consecutive days
- Zero manual intervention needed
- All errors logged and alerted

---

### Phase 3: Multi-Agent System (Days 22-35)
**Goal:** Add TrendScout and Research agents for richer content

**Database:**
- Create `blog_trends` table
- Create `blog_research_queue` table
- Seed 5 initial evergreen trends

**TrendScout Agent:**
- Implement `ralph/prompts/trendscout.py`
  - Trend discovery prompt
  - JSON output specification
- Implement `ralph/agents/trendscout_agent.py`
  - `discover_trends(rss_items)` → List[Trend]
  - Store top 3 trends in database

**Research Agent:**
- Implement `ralph/prompts/research.py`
  - In-depth research prompt
  - Data gathering specification
- Implement `ralph/agents/research_agent.py`
  - `conduct_research(trend_id)` → ResearchResult
  - Store research in database

**Agent Orchestration:**
- Update `ralph/core/ralph_loop.py`
  - Phase 1: TrendScout discovers trends
  - Phase 2: Research gathers data (direct function call)
  - Phase 3: ProductMarketing creates content
  - Phase 4: Iterative improvement (unchanged)

**Testing:**
- Test multi-agent workflow end-to-end
- Verify trend discovery produces relevant topics
- Ensure research adds value to content
- Compare quality: single-agent vs multi-agent

**Deliverable:** Three-agent sequential coordination

**Success Criteria:**
- Trend discovery produces relevant topics (manual review)
- Research adds depth to blog posts
- Average quality score improves 5-10% vs single-agent
- No increase in API costs per post

---

### Phase 4: Monitoring & Hardening (Days 36-42)
**Goal:** Production-grade observability and error handling

**Monitoring:**
- Setup Grafana or Supabase dashboard
- Track metrics:
  - Daily generation success rate
  - Average quality score trend
  - Average iterations per post
  - API costs per post
  - Generation time distribution

**Error Recovery:**
- Retry with exponential backoff
- Circuit breaker for Claude API
- Graceful degradation strategies:
  - TrendScout fails → use recent trend
  - Research fails → generate without research
  - ProductMarketing fails → retry with simpler prompt

**Testing:**
- Unit tests for `quality_validator`
- Integration tests for `ralph_loop`
- E2E test: spike → ralph_loop → verify Supabase

**Documentation:**
- README: Local setup and development
- DEPLOYMENT.md: Systemd configuration
- ARCHITECTURE.md: System design
- TROUBLESHOOTING.md: Common issues

**Deliverable:** Production-ready, monitored, maintainable system

---

### Phase 5: Social Media (Days 43-56) [OPTIONAL]
**Goal:** Generate and schedule LinkedIn/Twitter posts from published blogs

**Prerequisites:**
- 2+ weeks of successful blog generation
- LinkedIn/Twitter API approvals obtained

**Database:**
- Create `blog_social_posts` table

**Social Media Service:**
- Implement `services/social_media_service.py`
  - `generate_social_post(blog_id, platform)` → SocialPost
  - `schedule_post(post, scheduled_time)`
  - `publish_post(post_id)` → success/failure

**Social Media Daemon:**
- Implement `schedulers/social_media_daemon.py`
  - Long-running daemon (checks every 5 minutes)
  - Generate social posts for new published blogs
  - Schedule at optimal times
  - Publish scheduled posts

**Platform Integration:**
- LinkedIn API integration
- Twitter API integration
- Rate limiting enforcement
- Error handling and retries

**Deliverable:** Autonomous social media posting

**Success Criteria:**
- 2 social posts per published blog (LinkedIn + Twitter)
- Social engagement baseline established
- No spam reports

---

## Database Schema

### Core Tables (Phase 0-1)

#### blog_posts
```sql
CREATE TABLE blog_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  status TEXT CHECK (status IN ('draft', 'published', 'failed')),
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### blog_content_drafts
```sql
CREATE TABLE blog_content_drafts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  blog_post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE,
  iteration_number INTEGER NOT NULL DEFAULT 1,
  content TEXT NOT NULL,
  title TEXT,
  agent_name TEXT NOT NULL DEFAULT 'ProductMarketing',
  critique JSONB DEFAULT '{}',
  quality_score DECIMAL(3,2),
  improvements TEXT[],
  token_count INTEGER,
  api_cost_cents INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(blog_post_id, iteration_number)
);

CREATE INDEX idx_blog_content_drafts_blog ON blog_content_drafts(blog_post_id, iteration_number DESC);
```

#### blog_agent_activity
```sql
CREATE TABLE blog_agent_activity (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name TEXT NOT NULL,
  activity_type TEXT NOT NULL CHECK (activity_type IN ('content_draft', 'critique', 'publish')),
  context_id UUID,
  duration_ms INTEGER,
  success BOOLEAN DEFAULT TRUE,
  error_message TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_blog_agent_activity_agent ON blog_agent_activity(agent_name, created_at DESC);
CREATE INDEX idx_blog_agent_activity_type ON blog_agent_activity(activity_type, created_at DESC);
```

#### blog_rss_sources
```sql
CREATE TABLE blog_rss_sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  category TEXT,
  active BOOLEAN DEFAULT TRUE,
  priority INTEGER DEFAULT 5,
  last_fetched_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_blog_rss_sources_active ON blog_rss_sources(active, priority DESC);
```

#### blog_rss_items
```sql
CREATE TABLE blog_rss_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id UUID REFERENCES blog_rss_sources(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  summary TEXT,
  published_at TIMESTAMPTZ,
  relevance_score DECIMAL(3,2),
  used_in_blog UUID REFERENCES blog_posts(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_blog_rss_items_source ON blog_rss_items(source_id, published_at DESC);
CREATE INDEX idx_blog_rss_items_unused ON blog_rss_items(used_in_blog) WHERE used_in_blog IS NULL;
CREATE INDEX idx_blog_rss_items_relevance ON blog_rss_items(relevance_score DESC);
```

### Multi-Agent Tables (Phase 3)

#### blog_trends
```sql
CREATE TABLE blog_trends (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trend_name TEXT NOT NULL,
  description TEXT,
  source TEXT NOT NULL,
  source_url TEXT,
  relevance_score DECIMAL(3,2),
  category TEXT,
  keywords TEXT[],
  discovered_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'researched', 'used', 'expired')),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_blog_trends_status ON blog_trends(status, relevance_score DESC);
```

#### blog_research_queue
```sql
CREATE TABLE blog_research_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trend_id UUID REFERENCES blog_trends(id) ON DELETE CASCADE,
  blog_post_id UUID REFERENCES blog_posts(id) ON DELETE SET NULL,
  research_type TEXT NOT NULL CHECK (research_type IN ('trend_analysis', 'competitor', 'technical', 'market')),
  priority INTEGER DEFAULT 5,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
  query TEXT NOT NULL,
  results JSONB DEFAULT '{}',
  sources TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE INDEX idx_blog_research_status ON blog_research_queue(status, priority DESC);
```

### Social Media Tables (Phase 5)

#### blog_social_posts
```sql
CREATE TABLE blog_social_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  blog_post_id UUID REFERENCES blog_posts(id) ON DELETE SET NULL,
  platform TEXT NOT NULL CHECK (platform IN ('linkedin', 'twitter')),
  content TEXT NOT NULL,
  scheduled_for TIMESTAMPTZ,
  published_at TIMESTAMPTZ,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'published', 'failed')),
  engagement_metrics JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_blog_social_posts_status ON blog_social_posts(status, scheduled_for);
```

---

## Environment Variables

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# Ralph Settings
RALPH_TIMEOUT_MINUTES=30
RALPH_QUALITY_THRESHOLD=0.85
RALPH_QUALITY_FLOOR=0.70
RALPH_COST_LIMIT_CENTS=100
RALPH_MAX_ITERATIONS=20

# Email Alerts (Resend.com)
RESEND_API_KEY=re_...
ALERT_EMAIL=you@example.com

# Environment
ENVIRONMENT=development

# Phase 3+ Settings
TRENDSCOUT_ENABLED=false
RESEARCH_ENABLED=false

# Phase 5+ Settings (Optional)
LINKEDIN_ENABLED=false
TWITTER_ENABLED=false
LINKEDIN_ACCESS_TOKEN=...
TWITTER_API_KEY=...
```

---

## File Structure

```
ai-blog/
├── PRD.md                           # THIS FILE - Task definition
├── config.py                        # UPDATE - Add Ralph config
├── worker.py                        # REPLACE with RalphLoop orchestrator
├── spike.py                         # NEW (Phase 0) - Proof of concept
├── requirements.txt                 # UPDATE - Add dependencies
├── .env.example                     # UPDATE - Add Ralph variables
├── services/
│   ├── __init__.py
│   ├── rss_service.py               # NEW - RSS feed operations
│   ├── supabase_service.py          # NEW - Database operations
│   ├── quality_validator.py         # NEW - Content quality checks
│   └── social_media_service.py      # NEW (Phase 5) - Social integration
├── ralph/
│   ├── __init__.py                  # NEW
│   ├── core/
│   │   ├── __init__.py              # NEW
│   │   ├── ralph_loop.py            # NEW - Main iterative loop
│   │   ├── task_system.py           # NEW (Phase 2) - prd.json management
│   │   ├── progress_tracker.py      # NEW (Phase 2) - learnings tracker
│   │   └── timeout_manager.py       # NEW - Time/cost enforcement
│   ├── agents/
│   │   ├── __init__.py              # NEW
│   │   ├── base_agent.py            # NEW - Abstract agent class
│   │   ├── product_marketing_agent.py  # NEW (Phase 1)
│   │   ├── trendscout_agent.py      # NEW (Phase 3)
│   │   └── research_agent.py        # NEW (Phase 3)
│   └── prompts/
│       ├── __init__.py              # NEW
│       ├── content_generation.py    # NEW - Blog generation prompts
│       ├── critique.py              # NEW ⭐ CRITICAL - Self-critique
│       ├── trendscout.py            # NEW (Phase 3)
│       └── research.py              # NEW (Phase 3)
├── schedulers/
│   ├── __init__.py                  # NEW
│   ├── daily_blog_scheduler.py      # NEW (Phase 2) - Systemd wrapper
│   └── social_media_daemon.py       # NEW (Phase 5) - Long-running daemon
├── systemd/
│   ├── ai-blog-daily.service        # NEW (Phase 2)
│   └── ai-blog-daily.timer          # NEW (Phase 2)
├── tasks/
│   └── daily-blog/
│       └── prd.json                 # NEW (Phase 2) - Task config
├── progress/
│   └── marketing-learnings.txt      # NEW (Phase 2) - Accumulated learnings
├── tests/                           # NEW (Phase 4)
│   ├── test_quality_validator.py
│   ├── test_ralph_loop.py
│   └── test_e2e.py
└── docs/
    ├── ARCHITECTURE.md              # NEW (Phase 4)
    ├── DEPLOYMENT.md                # NEW (Phase 4)
    └── TROUBLESHOOTING.md           # NEW (Phase 4)
```

---

## Risk Mitigation

| Risk | Mitigation | Priority |
|------|------------|----------|
| Ralph loop never converges | 30-min timeout + $1 cost guard + quality floor (0.70) | HIGH |
| Claude API outage | Retry with exponential backoff (1, 2, 4, 8 min), max 4 retries | HIGH |
| Prompt injection via RSS | Sanitize RSS content, validate structure, limit length | HIGH |
| Cost explosion | Hard limit $1/run = max 20 iterations @ ~5¢/iteration | HIGH |
| Quality never reaches 0.85 | Save as draft at 0.70+, alert for manual review | MEDIUM |
| Database connection failures | Connection pooling, retry logic, circuit breaker | MEDIUM |
| Content duplication | Track used_in_blog in rss_items, check before generation | MEDIUM |
| Agent coordination failures | Fallback: if agent fails, use simple prompt | MEDIUM |
| Social media API rejection | Rate limiting, manual review for first 50 posts | LOW |

---

## Dependencies

### Python Packages (requirements.txt)
```
# Existing
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.0
pydantic-settings==2.5.2
supabase==2.9.0
anthropic==0.39.0
feedparser==6.0.11
httpx==0.27.2
python-dotenv==1.0.1
python-slugify==8.0.4
pytest==8.3.3
pytest-asyncio==0.24.0
black==24.10.0
ruff==0.7.0

# New (if needed)
resend==0.8.0  # Email alerts
tenacity==8.2.3  # Retry logic
```

### External Services
- Supabase (PostgreSQL database)
- Anthropic Claude API (claude-sonnet-4-5)
- Resend.com (email alerts)
- RSS feeds (manufacturing publications)
- LinkedIn API (Phase 5, optional)
- Twitter API (Phase 5, optional)

---

## Quality Gates

### Phase 0 Gate
- [ ] 3 blog drafts successfully inserted into Supabase
- [ ] Claude API responds correctly
- [ ] RSS feeds parseable
- [ ] Supabase connection stable

### Phase 1 Gate
- [ ] 5 successful blog posts published (quality ≥ 0.85)
- [ ] Average 2-4 iterations per post
- [ ] Zero AI slop in published content
- [ ] API costs < $0.25 per post
- [ ] Timeout enforcement works (tested)
- [ ] Cost limit enforcement works (tested)
- [ ] Draft save works when quality 0.70-0.84 at timeout

### Phase 2 Gate
- [ ] Blog published automatically at 7 AM for 5 consecutive days
- [ ] Zero manual intervention needed
- [ ] All errors logged and alerted
- [ ] Idempotency verified (no duplicate posts)
- [ ] Retry logic tested (simulate failures)

### Phase 3 Gate
- [ ] Trend discovery produces 3+ relevant topics daily
- [ ] Research adds measurable depth to content
- [ ] Average quality score improves 5-10% vs single-agent
- [ ] No increase in API costs per post
- [ ] Multi-agent workflow reliable for 5 consecutive days

### Phase 4 Gate
- [ ] Monitoring dashboard operational
- [ ] All metrics tracked accurately
- [ ] Unit tests pass (≥80% coverage for core modules)
- [ ] Integration tests pass
- [ ] E2E test passes
- [ ] Documentation complete and accurate

### Phase 5 Gate (Optional)
- [ ] 2 social posts per published blog (LinkedIn + Twitter)
- [ ] Social engagement baseline established
- [ ] No spam reports for 2 weeks
- [ ] Rate limits respected
- [ ] Publishing errors handled gracefully

---

## Acceptance Criteria

### Overall System Acceptance
System is ACCEPTED when ALL of the following are true:

1. **Functional Completeness (Phases 0-2 minimum)**
   - [ ] Daily blog generation runs automatically at 7 AM
   - [ ] Quality threshold enforcement works (≥0.85 to publish)
   - [ ] Quality floor enforcement works (≥0.70 to draft)
   - [ ] Timeout enforcement works (30 minutes)
   - [ ] Cost guard enforcement works ($1.00 limit)
   - [ ] AI slop detection works (all forbidden phrases caught)
   - [ ] Graceful degradation works (draft save on timeout)
   - [ ] Error alerting works (email on failures)

2. **Quality Metrics Met**
   - [ ] Daily success rate ≥ 95% over 2 weeks
   - [ ] Average quality score ≥ 0.87 over 20 posts
   - [ ] Zero AI slop in published posts (manual review)
   - [ ] Average iterations 2-4 per post

3. **Cost & Performance**
   - [ ] API costs average $0.10-$0.30 per post
   - [ ] Generation time 10-20 minutes average
   - [ ] No timeout hits when quality reached early
   - [ ] No cost limit hits (except in testing)

4. **Reliability & Maintainability**
   - [ ] System recovers from transient failures automatically
   - [ ] All errors logged with actionable context
   - [ ] Code follows "boring correctness" principles
   - [ ] Documentation complete and accurate

5. **Security & Safety**
   - [ ] No secrets in version control
   - [ ] All external inputs sanitized
   - [ ] Database queries use parameterization
   - [ ] Cost explosion impossible (hard guards)

---

## Out of Scope (Explicitly NOT Included)

- Web scraping (RSS feeds only)
- User authentication system
- Frontend/UI for content management
- Multi-language support (English only)
- Real-time content generation (daily batch only)
- SEO optimization beyond basic quality
- Image generation or multimedia
- Comments system
- Analytics dashboard (basic Supabase metrics only)
- A/B testing of content variants
- Custom LLM fine-tuning

---

## Open Questions (To Be Resolved During Implementation)

1. **RSS Sources:** Which 5 manufacturing publications for initial seed?
2. **Email Provider:** Resend.com vs SMTP vs other?
3. **Brand Voice:** Provide 2-3 example blog posts for reference?
4. **Quality Weights:** Fine-tune the 5 evaluation criteria weights based on results?
5. **Monitoring:** Grafana vs Supabase dashboard vs custom?
6. **Phase 3 Timing:** Proceed to multi-agent after 2 weeks or wait longer?
7. **Social Media:** Skip Phase 5 or implement?

---

## Definition of Done

A task/phase is DONE when:
1. ✅ Code implemented and committed
2. ✅ Tests pass (if applicable)
3. ✅ Manual testing completed successfully
4. ✅ Documentation updated
5. ✅ Quality gate criteria met
6. ✅ Code reviewed (self-review minimum)
7. ✅ Deployed to production (for Phase 2+)
8. ✅ Monitored for 24-48 hours (no errors)

---

## Iterative Implementation Approach (Meta-Ralph)

This PRD serves as the task definition for a **meta-Ralph implementation process**:

1. **Iteration Planning:** Break PRD into discrete, testable tasks
2. **Implementation:** Write code for one task
3. **Self-Critique:** Evaluate implementation quality
   - Code quality (readability, correctness, maintainability)
   - Test coverage
   - Documentation completeness
   - Alignment with "boring correctness" philosophy
4. **Improvement:** Refine based on critique
5. **Verification:** Run tests, manual verification
6. **Progress Tracking:** Update progress.txt with learnings
7. **Repeat:** Next task until phase complete
8. **Phase Gate:** Verify all phase acceptance criteria met

**Quality Score for Code (0.0-1.0):**
- 1.0: Perfect - production-ready, well-tested, documented
- 0.85: Good - publishable, minor improvements possible
- 0.70: Acceptable - works but needs refinement
- < 0.70: Needs significant rework

---

## Contact & Escalation

**Product Owner:** User (evgeni99)
**Technical Lead:** Claude Code (this assistant)
**Escalation:** Open questions resolved via AskUserQuestion tool

---

**Document Version History:**
- v1.0 (2026-01-09): Initial PRD created for meta-Ralph implementation
