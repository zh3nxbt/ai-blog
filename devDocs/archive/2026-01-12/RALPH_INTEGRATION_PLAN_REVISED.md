# Ralph Wiggum Marketer Integration Plan (REVISED)

**Version:** 2.0 (Post-Opus Review)
**Status:** Ready for Implementation
**Estimated Timeline:** 5-6 weeks (realistic)
**Grade:** A- (addresses all critical issues from Opus review)

---

## 🔄 Changes from v1.0

**Critical fixes based on Opus architectural review:**
1. ✅ Added Week 0 (Vertical Spike) - prove integration works
2. ✅ Reduced Week 1 scope - single agent, no over-engineering
3. ✅ Removed agent_communications table - use direct calls
4. ✅ Deferred agent_learnings to Phase 5 - needs production data
5. ✅ Added self-critique prompt specification - the heart of Ralph
6. ✅ Added cost guard ($1/run limit) and quality floor (0.70)
7. ✅ Moved social media to Week 5+ - prove blogs first
8. ✅ Extended timeline to 5-6 weeks - realistic for skeleton codebase
9. ✅ Added missing indexes and error recovery strategies
10. ✅ Specified graceful degradation when quality < 0.85

---

## Executive Summary

Integrate Ralph Wiggum Marketer's autonomous content generation system into the ai-blog platform for MAS Precision Parts through **progressive enhancement**: prove the concept (Week 0), build core loop (Weeks 1-2), add multi-agent system (Weeks 3-4), then add social media (Weeks 5-6).

**Key Benefits:**
- Fully autonomous daily blog generation at 7 AM
- Iterative self-improvement with quality validation
- Multi-agent system (TrendScout, Research, Product/Marketing agents)
- Social media daemon for LinkedIn/Twitter posts (Week 5+)
- 30-minute time limit + $1 cost guard per generation
- Zero AI slop tolerance through continuous critique

**Key Safeguards:**
- Quality floor: Save as draft if score ≥ 0.70 but < 0.85
- Cost guard: Hard limit $1 per generation run
- Timeout: 30 minutes maximum
- Graceful degradation: Never discard work, always save iterations

---

## Architecture Overview

### Phase Evolution

```
Week 0: SPIKE
  Single RSS → Claude → Supabase (hard-coded, proof of concept)

Weeks 1-2: CORE LOOP
  RSS → ProductMarketing Agent → Self-Critique Loop → Quality Validator → Publish

Weeks 3-4: MULTI-AGENT
  RSS → TrendScout → Research → ProductMarketing → Self-Critique → Publish

Weeks 5-6: SOCIAL MEDIA
  Published Blogs → Social Media Daemon → LinkedIn/Twitter Posts
```

### Final Architecture

```
TrendScout Agent (discovers trends from RSS)
  ↓
Research Agent (gathers data, verifies sources)
  ↓
ProductMarketing Agent (drafts with brand voice)
  ↓
Self-Critique Loop (iterative improvement)
  ↓
Quality Validator (score ≥ 0.85 or timeout)
  ↓
Publish OR Save Draft (if ≥ 0.70)
```

**Key Architectural Decision:** Agents communicate via **direct function calls**, not database messaging. This reduces latency and complexity for the sequential workflow.

---

## Database Schema (Supabase PostgreSQL)

**All blog-related tables use `blog_*` prefix for easy identification and organization.**

### Table Overview

**Phase 0-1 (Core):**
- `blog_posts` - Main content table (existing or created in Phase 0)
- `blog_content_drafts` - Iteration tracking (Ralph's memory)
- `blog_agent_activity` - Agent execution logs
- `blog_rss_sources` - RSS feed configuration
- `blog_rss_items` - Cached RSS items for deduplication

**Phase 3 (Multi-Agent):**
- `blog_trends` - TrendScout discoveries
- `blog_research_queue` - Research agent tasks and results

**Phase 5 (Social Media):**
- `blog_social_posts` - LinkedIn/Twitter content

---

### Phase 1 Tables (Week 0-2)

```sql
-- Existing table (assumed to exist)
-- Reference only - do not create
-- blog_posts (
--   id UUID PRIMARY KEY,
--   title TEXT,
--   content TEXT,
--   status TEXT CHECK (status IN ('draft', 'published')),
--   published_at TIMESTAMPTZ,
--   created_at TIMESTAMPTZ,
--   updated_at TIMESTAMPTZ
-- );

-- Content iteration tracking (CORE to Ralph philosophy)
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

-- Agent activity log (essential for debugging)
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

-- RSS sources
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

-- RSS items (cached for deduplication)
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

-- Auto-update triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_blog_rss_sources_updated_at BEFORE UPDATE ON blog_rss_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Phase 3 Tables (Week 3-4, Multi-Agent)

```sql
-- Trends discovered by TrendScout agent
CREATE TABLE blog_trends (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trend_name TEXT NOT NULL,
  description TEXT,
  source TEXT NOT NULL,
  source_url TEXT,
  relevance_score DECIMAL(3,2) CHECK (relevance_score >= 0 AND relevance_score <= 1),
  category TEXT,
  keywords TEXT[],
  discovered_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'researched', 'used', 'expired')),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_blog_trends_status ON blog_trends(status, relevance_score DESC);
CREATE INDEX idx_blog_trends_category ON blog_trends(category, discovered_at DESC);

-- Research queue and results
CREATE TABLE blog_research_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trend_id UUID REFERENCES blog_trends(id) ON DELETE CASCADE,
  blog_post_id UUID REFERENCES blog_posts(id) ON DELETE SET NULL,
  research_type TEXT NOT NULL CHECK (research_type IN ('trend_analysis', 'competitor', 'technical', 'market')),
  priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
  query TEXT NOT NULL,
  results JSONB DEFAULT '{}',
  sources TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  error_message TEXT
);

CREATE INDEX idx_blog_research_status ON blog_research_queue(status, priority DESC);
CREATE INDEX idx_blog_research_trend ON blog_research_queue(trend_id);
```

### Phase 5 Tables (Week 5-6, Social Media)

```sql
-- Social media posts
CREATE TABLE blog_social_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  blog_post_id UUID REFERENCES blog_posts(id) ON DELETE SET NULL,
  platform TEXT NOT NULL CHECK (platform IN ('linkedin', 'twitter')),
  content TEXT NOT NULL,
  scheduled_for TIMESTAMPTZ,
  published_at TIMESTAMPTZ,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'published', 'failed')),
  engagement_metrics JSONB DEFAULT '{}',
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_blog_social_posts_status ON blog_social_posts(status, scheduled_for);
CREATE INDEX idx_blog_social_posts_blog ON blog_social_posts(blog_post_id);
CREATE INDEX idx_blog_social_posts_platform ON blog_social_posts(platform, published_at DESC);

CREATE TRIGGER update_blog_social_posts_updated_at BEFORE UPDATE ON blog_social_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### ❌ Tables Deferred (Not in v2.0)

- ~~agent_communications~~ - Use direct function calls instead
- ~~agent_learnings~~ - Defer to Phase 5+, needs production data to be meaningful

---

## File Structure

```
ai-blog/
├── config.py                         # UPDATE - Add Ralph config
├── worker.py                         # REPLACE with RalphLoop orchestrator
├── services/
│   ├── rss_service.py                # NEW - RSS feed fetching
│   ├── supabase_service.py           # NEW - Database operations
│   ├── quality_validator.py          # NEW - Quality checks
│   └── social_media_service.py       # NEW (Phase 5) - Social integration
├── ralph/
│   ├── __init__.py
│   ├── core/
│   │   ├── ralph_loop.py             # NEW - Main iterative loop
│   │   ├── task_system.py            # NEW - prd.json management
│   │   ├── progress_tracker.py       # NEW - progress.txt learnings
│   │   └── timeout_manager.py        # NEW - 30-min + cost enforcement
│   ├── agents/
│   │   ├── base_agent.py             # NEW - Abstract agent class
│   │   ├── product_marketing_agent.py # NEW (Phase 1) - Content creation
│   │   ├── trendscout_agent.py       # NEW (Phase 3) - Trend discovery
│   │   └── research_agent.py         # NEW (Phase 3) - Data gathering
│   └── prompts/
│       ├── content_generation.py     # NEW - Blog post generation
│       ├── critique.py               # NEW ⭐ CRITICAL - Self-critique
│       ├── trendscout.py             # NEW (Phase 3)
│       └── research.py               # NEW (Phase 3)
├── schedulers/
│   ├── daily_blog_scheduler.py       # NEW (Phase 2) - Systemd wrapper
│   └── social_media_daemon.py        # NEW (Phase 5) - Long-running daemon
├── tasks/
│   └── daily-blog/
│       └── prd.json                  # NEW - Task definition
└── progress/
    └── marketing-learnings.txt       # NEW - Accumulated learnings
```

---

## Implementation Phases

### 🎯 Phase 0: Vertical Spike (Days 1-3)

**Goal:** Prove the Claude + Supabase + RSS integration works end-to-end

**Scope:** Absolute minimum - one post generated, no abstraction

**Tasks:**
1. **Day 1: Database Setup**
   - Create `blog_posts` table (if doesn't exist)
   - Create `rss_sources` table
   - Insert 1 hard-coded RSS source (e.g., "Modern Machine Shop")
   - Manual verification: can query Supabase

2. **Day 2: Spike Script**
   - Create `spike.py` in root directory
   - Hard-coded logic:
     ```python
     # 1. Fetch 1 RSS feed (no parsing library, just requests)
     # 2. Extract 1 article title + summary
     # 3. Call Claude with hard-coded prompt: "Write 500-word blog about [topic]"
     # 4. Insert result into blog_posts with status='draft'
     # 5. Print success message
     ```
   - No error handling, no retry, no quality validation
   - Manual run: `python spike.py`

   **Note:** In Phase 0, we'll create `blog_posts` if it doesn't exist, then add blog-prefixed tables in Phase 1.

3. **Day 3: Verification & Learning**
   - Run spike 3 times with different RSS articles
   - Verify all 3 appear in Supabase
   - Document learnings:
     - Does Claude API work?
     - Is Supabase connection stable?
     - Are RSS feeds parseable?
     - What breaks?

**Deliverable:** Working proof that the stack integrates. **No production code**, just validation.

**Success Criteria:** 3 blog drafts in Supabase generated from RSS articles

---

### 🏗️ Phase 1: Core Ralph Loop (Days 4-14, ~2 weeks)

**Goal:** Single-agent iterative content generation with quality validation

**Reduced Scope (vs v1.0):**
- ❌ No multi-agent system yet
- ❌ No task_system.py or progress_tracker.py yet
- ❌ No agent messaging
- ✅ Focus: ralph_loop + quality_validator + single agent

**Tasks:**

**Days 4-5: Database Tables**
- Create Phase 1 tables (blog_content_drafts, blog_agent_activity, blog_rss_sources, blog_rss_items)
- Add indexes
- Seed 5 RSS sources (manufacturing publications)

**Days 6-8: Services Layer**
- `services/rss_service.py`:
  ```python
  def fetch_active_feeds() -> List[RSSSource]
  def fetch_feed_items(source_id: str, limit: int) -> List[RSSItem]
  def mark_items_as_used(item_ids: List[str], blog_id: str)
  ```

- `services/supabase_service.py`:
  ```python
  def get_supabase_client() -> Client
  def create_blog_post(title: str, content: str, status: str) -> str
  def save_draft_iteration(blog_id: str, iteration: int, content: str, quality: float, critique: dict)
  def log_agent_activity(agent: str, activity_type: str, success: bool, metadata: dict)
  ```

- `services/quality_validator.py`:
  ```python
  AI_SLOP_KEYWORDS = ["delve", "unveil", "landscape", "realm", "unlock", "leverage", ...]

  def validate_content(content: str) -> Tuple[float, dict]:
      # Returns (quality_score, critique_details)
      # Score 0.0-1.0
      # Checks: AI slop, length, structure, tone
  ```

**Days 9-11: Ralph Core**
- `ralph/core/timeout_manager.py`:
  ```python
  class TimeoutManager:
      def __init__(self, timeout_minutes: int, cost_limit_cents: int):
          self.timeout_minutes = timeout_minutes
          self.cost_limit_cents = cost_limit_cents
          self.start_time = None
          self.total_cost_cents = 0

      def start(self)
      def is_expired(self) -> bool
      def add_cost(self, cost_cents: int)
      def exceeds_cost_limit(self) -> bool
  ```

- `ralph/prompts/critique.py` ⭐ **CRITICAL**:
  ```python
  CRITIQUE_PROMPT = """You are a content quality critic for manufacturing industry blog posts.

  Analyze this draft blog post:

  Title: {title}
  Content: {content}
  Current Quality Score: {current_score}

  Evaluate on:
  1. Manufacturing industry relevance and accuracy
  2. MAS Precision Parts brand voice (professional, technical, not salesy)
  3. AI slop language (FORBIDDEN: "delve", "unveil", "landscape", "realm", "leverage")
  4. Structure (clear headings, logical flow)
  5. Engagement (specific examples, data points)

  Provide JSON response:
  {{
    "quality_score": 0.0-1.0,
    "main_issues": ["issue 1", "issue 2"],
    "specific_improvements": [
      {{"section": "introduction", "problem": "too generic", "fix": "add specific statistic"}},
      {{"section": "body", "problem": "contains 'delve'", "fix": "replace with 'examine'"}}
    ],
    "strengths": ["strength 1", "strength 2"]
  }}
  """
  ```

- `ralph/agents/product_marketing_agent.py`:
  ```python
  class ProductMarketingAgent:
      def generate_content(self, rss_items: List[RSSItem]) -> dict:
          # Generate initial blog post

      def improve_content(self, current_content: str, critique: dict) -> dict:
          # Regenerate based on critique feedback
  ```

- `ralph/core/ralph_loop.py`:
  ```python
  def run_ralph_loop():
      timeout_mgr = TimeoutManager(timeout_minutes=30, cost_limit_cents=100)
      timeout_mgr.start()

      # Fetch RSS
      rss_items = rss_service.fetch_feed_items(...)

      # Initial generation
      agent = ProductMarketingAgent()
      content = agent.generate_content(rss_items)
      iteration = 1

      # Iterative improvement loop
      while True:
          # Quality check
          quality, critique = quality_validator.validate_content(content)

          # Save iteration
          supabase_service.save_draft_iteration(...)

          # Exit conditions
          if quality >= 0.85:
              # PUBLISH
              supabase_service.create_blog_post(..., status='published')
              break

          if quality >= 0.70 and (timeout_mgr.is_expired() or timeout_mgr.exceeds_cost_limit()):
              # SAVE AS DRAFT (graceful degradation)
              supabase_service.create_blog_post(..., status='draft')
              break

          if quality < 0.70 and (timeout_mgr.is_expired() or timeout_mgr.exceeds_cost_limit()):
              # FAILURE - log and alert
              break

          # Improve
          content = agent.improve_content(content, critique)
          iteration += 1
  ```

**Days 12-14: Testing & Refinement**
- Manual tests: `python -m ralph.ralph_loop`
- Test cases:
  1. High-quality on first try (quality > 0.85)
  2. Needs 2-3 iterations to reach 0.85
  3. Timeout before reaching 0.85 (save as draft)
  4. Cost limit exceeded (save as draft)
- Refine prompts based on results

**Deliverable:** Working single-agent Ralph loop that generates and iteratively improves blog posts

**Success Criteria:**
- 5 successful blog posts published (quality ≥ 0.85)
- Average 2-4 iterations per post
- Zero AI slop in published content
- API costs < $0.25 per post

---

### 🚀 Phase 2: Production Deployment (Days 15-21, 1 week)

**Goal:** Automate daily blog generation at 7 AM

**Tasks:**

**Days 15-16: Task System**
- `ralph/core/task_system.py`:
  ```python
  def load_task_definition(path: str) -> dict
  ```

- `tasks/daily-blog/prd.json`:
  ```json
  {
    "title": "Daily Manufacturing Blog Post",
    "successCriteria": {
      "qualityThreshold": 0.85,
      "qualityFloor": 0.70,
      "minLength": 1000,
      "maxLength": 2500
    }
  }
  ```

- `ralph/core/progress_tracker.py`:
  ```python
  class ProgressTracker:
      def load_learnings(path: str) -> List[str]
      def add_learning(learning: str, quality: float)
      def save_learnings(path: str)
  ```

**Days 17-18: Scheduler**
- `schedulers/daily_blog_scheduler.py`:
  ```python
  def main():
      try:
          result = ralph_loop.run_ralph_loop()
          if result.success:
              print(f"Published blog {result.blog_id}")
          else:
              send_alert_email(result.error)
      except Exception as e:
          send_alert_email(str(e))
          sys.exit(1)
  ```

- `systemd/ai-blog-daily.service`:
  ```ini
  [Unit]
  Description=AI Blog Daily Generation

  [Service]
  Type=oneshot
  WorkingDirectory=/home/evgeni99/ai-blog
  ExecStart=/home/evgeni99/ai-blog/.venv/bin/python schedulers/daily_blog_scheduler.py
  ```

- `systemd/ai-blog-daily.timer`:
  ```ini
  [Unit]
  Description=Daily Blog Timer (7 AM)

  [Timer]
  OnCalendar=*-*-* 07:00:00
  Persistent=true

  [Install]
  WantedBy=timers.target
  ```

**Days 19-20: Error Handling**
- Retry logic for transient failures
- Email alerts via Resend.com (or SMTP)
- Idempotency: check if post already generated today
- Recovery: if 7 AM fails, retry at 8 AM, 9 AM (up to 3 retries)

**Day 21: Deployment**
- Install systemd timer
- Test first automated run
- Monitor logs

**Deliverable:** Fully automated daily blog generation

**Success Criteria:**
- Blog published automatically at 7 AM for 5 consecutive days
- Zero manual intervention needed
- All errors logged and alerted

---

### 🤖 Phase 3: Multi-Agent System (Days 22-35, 2 weeks)

**Goal:** Add TrendScout and Research agents for richer content

**Tasks:**

**Days 22-23: Database**
- Create Phase 3 tables (blog_trends, blog_research_queue)
- Seed initial trends manually (5 evergreen manufacturing topics)

**Days 24-26: TrendScout Agent**
- `ralph/prompts/trendscout.py`:
  ```python
  TRENDSCOUT_PROMPT = """Analyze these RSS feeds and identify the top 3 manufacturing trends:

  RSS Items: {rss_items}

  Previous trends: {previous_trends}

  For each trend, provide:
  - trend_name (concise)
  - description (2-3 sentences)
  - relevance_score (0.0-1.0)
  - category (manufacturing/technology/industry/regulation)
  - keywords (array)

  Return JSON array.
  """
  ```

- `ralph/agents/trendscout_agent.py`:
  ```python
  class TrendScoutAgent(BaseAgent):
      def discover_trends(self, rss_items: List) -> List[Trend]:
          # Call Claude with TRENDSCOUT_PROMPT
          # Store in trends table
          # Return top 3 trends
  ```

**Days 27-29: Research Agent**
- `ralph/prompts/research.py`:
  ```python
  RESEARCH_PROMPT = """Research this manufacturing trend in depth:

  Trend: {trend_name}
  Description: {trend_description}

  Gather:
  - Key statistics and data points
  - Technical details
  - Industry implications
  - Expert perspectives
  - Source citations

  Return structured JSON.
  """
  ```

- `ralph/agents/research_agent.py`:
  ```python
  class ResearchAgent(BaseAgent):
      def conduct_research(self, trend_id: str) -> ResearchResult:
          # Query trend from database
          # Call Claude with RESEARCH_PROMPT
          # Store in research_queue
          # Return research data
  ```

**Days 30-32: Agent Orchestration**
- Update `ralph/core/ralph_loop.py`:
  ```python
  def run_ralph_loop():
      # Phase 1: TrendScout discovers trends
      trendscout = TrendScoutAgent()
      trends = trendscout.discover_trends(rss_items)

      # Phase 2: Research gathers data (direct function call)
      research_agent = ResearchAgent()
      research = research_agent.conduct_research(trends[0].id)

      # Phase 3: ProductMarketing creates content
      marketing = ProductMarketingAgent()
      content = marketing.generate_content(trends[0], research)

      # Phase 4: Iterative improvement (same as before)
      ...
  ```

**Days 33-35: Testing & Refinement**
- Test multi-agent workflow
- Verify trend discovery quality
- Ensure research adds value to content
- Compare quality scores: single-agent vs multi-agent

**Deliverable:** Three-agent system with sequential coordination

**Success Criteria:**
- Trend discovery produces relevant topics (manual review)
- Research adds depth to blog posts
- Average quality score improves by 5-10% vs single-agent
- No increase in API costs per post (batched calls)

---

### 📱 Phase 4: Monitoring & Hardening (Days 36-42, 1 week)

**Goal:** Production-grade observability and error handling

**Tasks:**

**Days 36-37: Monitoring Dashboard**
- Setup Grafana or Supabase dashboard
- Metrics to track:
  - Daily blog generation success rate
  - Average quality score trend
  - Average iterations per post
  - API costs per post
  - Generation time distribution

**Days 38-39: Error Recovery**
- Implement retry with exponential backoff
- Add circuit breaker for Claude API
- Graceful degradation strategies:
  - If TrendScout fails → use recent trend
  - If Research fails → generate without research
  - If ProductMarketing fails → retry with simpler prompt

**Days 40-41: Testing**
- Unit tests for quality_validator
- Integration tests for ralph_loop
- E2E test: spike.py → ralph_loop → verify in Supabase

**Day 42: Documentation**
- README: How to run locally
- DEPLOYMENT.md: Systemd setup
- ARCHITECTURE.md: System design
- TROUBLESHOOTING.md: Common issues

**Deliverable:** Production-ready, monitored, maintainable system

---

### 📲 Phase 5: Social Media (Days 43-56, 2 weeks)

**Goal:** Generate and schedule LinkedIn/Twitter posts from published blogs

**Prerequisites:**
- 2+ weeks of successful blog generation
- LinkedIn/Twitter API approvals obtained

**Tasks:**

**Days 43-44: Database**
- Create Phase 5 table (blog_social_posts)
- Design social content templates

**Days 45-48: Social Media Service**
- `services/social_media_service.py`:
  ```python
  def generate_social_post(blog_id: str, platform: str) -> SocialPost
  def schedule_post(post: SocialPost, scheduled_time: datetime)
  def publish_post(post_id: str) -> bool
  ```

**Days 49-52: Social Media Daemon**
- `schedulers/social_media_daemon.py`:
  ```python
  class SocialMediaDaemon:
      def run(self):
          while True:
              # Check for new published blogs
              # Generate social posts (LinkedIn + Twitter)
              # Schedule for optimal times
              # Publish scheduled posts
              sleep(5 * 60)  # Check every 5 minutes
  ```

**Days 53-55: Platform Integration**
- LinkedIn API integration
- Twitter API integration
- Rate limiting
- Error handling

**Day 56: Testing & Launch**
- Manual review of first 10 social posts
- Launch daemon
- Monitor engagement metrics

**Deliverable:** Autonomous social media posting

---

## Critical Implementation Details

### 1. Self-Critique Prompt (Heart of Ralph)

The critique prompt is THE most important piece. Here's the full specification:

```python
# ralph/prompts/critique.py

AI_SLOP_KEYWORDS = [
    "delve", "delve into", "delving",
    "unveil", "unveiling",
    "landscape", "ever-changing landscape", "evolving landscape",
    "realm", "in the realm of",
    "unlock", "unlocking", "unlock the potential",
    "leverage", "leveraging",
    "robust", "robust solution",
    "streamline", "streamlining",
    "cutting-edge", "cutting edge",
    "revolutionize", "revolutionary",
    "game-changer", "game changer",
    "dive deep", "deep dive",
    "let's explore",
    "in today's fast-paced world",
    "it's important to note",
    "it goes without saying",
]

CRITIQUE_PROMPT_TEMPLATE = """You are an expert content quality critic specializing in manufacturing industry blog posts.

Your task: Evaluate this blog post draft for MAS Precision Parts (a precision manufacturing company).

**DRAFT:**
Title: {title}
Content:
{content}

**CURRENT QUALITY SCORE:** {current_score}

**BRAND VOICE REQUIREMENTS:**
- Professional yet approachable
- Technical expertise without jargon overload
- Focus on manufacturing excellence and precision
- Customer-centric problem solving
- NO corporate or salesy language

**AI SLOP DETECTION (CRITICAL):**
These phrases are STRICTLY FORBIDDEN:
{ai_slop_list}

If any appear, quality score must be < 0.50.

**EVALUATION CRITERIA:**

1. **Manufacturing Relevance (weight: 25%)**
   - Is content specific to manufacturing/machining?
   - Are technical details accurate?
   - Does it demonstrate expertise?

2. **Brand Voice Alignment (weight: 25%)**
   - Professional but not stuffy
   - Technical but accessible
   - Helpful, not promotional

3. **AI Slop Detection (weight: 20%)**
   - Are forbidden phrases present?
   - Is language natural and human?
   - Varied sentence structure?

4. **Structure & Readability (weight: 15%)**
   - Clear headings
   - Logical flow
   - Appropriate length (1000-2500 words)
   - Not a wall of text

5. **Engagement & Value (weight: 15%)**
   - Specific examples and data
   - Actionable insights
   - Compelling without being clickbait

**OUTPUT REQUIRED (JSON):**
{{
  "quality_score": 0.0-1.0,
  "main_issues": ["issue 1", "issue 2", "issue 3"],
  "specific_improvements": [
    {{
      "section": "introduction|body|conclusion",
      "current": "problematic text excerpt",
      "problem": "what's wrong",
      "fix": "how to improve"
    }}
  ],
  "strengths": ["strength 1", "strength 2"],
  "ai_slop_found": ["phrase 1", "phrase 2"] or [],
  "recommended_action": "publish|improve|rewrite"
}}

Be constructively critical. The goal is iterative improvement.
"""

def build_critique_prompt(title: str, content: str, current_score: float) -> str:
    return CRITIQUE_PROMPT_TEMPLATE.format(
        title=title,
        content=content,
        current_score=current_score,
        ai_slop_list=", ".join(f'"{phrase}"' for phrase in AI_SLOP_KEYWORDS)
    )
```

### 2. Quality Scoring Formula

```python
# services/quality_validator.py

def validate_content(content: str, title: str) -> Tuple[float, dict]:
    """
    Returns: (quality_score, critique_details)

    Quality score breakdown:
    - Start at 1.0 (perfect)
    - Deduct points for issues
    """
    score = 1.0
    issues = []

    # AI Slop Detection (-0.5 if found)
    slop_found = []
    content_lower = content.lower()
    for phrase in AI_SLOP_KEYWORDS:
        if phrase in content_lower:
            slop_found.append(phrase)

    if slop_found:
        score -= 0.5
        issues.append(f"AI slop detected: {slop_found}")

    # Length Check (-0.2 if outside range)
    word_count = len(content.split())
    if word_count < 1000 or word_count > 2500:
        score -= 0.2
        issues.append(f"Word count {word_count} outside range 1000-2500")

    # Structure Check (-0.1 if poor)
    heading_count = content.count('#')
    if heading_count < 3:
        score -= 0.1
        issues.append("Insufficient structure (needs more headings)")

    # Technical Depth (-0.1 if too generic)
    technical_terms = ["CNC", "tolerance", "machining", "precision", "manufacturing"]
    if not any(term.lower() in content_lower for term in technical_terms):
        score -= 0.1
        issues.append("Lacks manufacturing-specific terminology")

    # Brand Voice (-0.1 if promotional)
    promotional_phrases = ["contact us", "call today", "get a quote", "buy now"]
    if any(phrase in content_lower for phrase in promotional_phrases):
        score -= 0.1
        issues.append("Too promotional")

    critique = {
        "quality_score": max(0.0, score),
        "main_issues": issues,
        "ai_slop_found": slop_found,
        "word_count": word_count,
        "heading_count": heading_count
    }

    return (max(0.0, score), critique)
```

### 3. Cost Tracking

```python
# ralph/core/timeout_manager.py

# Anthropic pricing (as of 2025-01-08)
SONNET_INPUT_COST = 3.0 / 1_000_000  # $3 per million input tokens
SONNET_OUTPUT_COST = 15.0 / 1_000_000  # $15 per million output tokens

def calculate_cost(input_tokens: int, output_tokens: int) -> int:
    """Returns cost in cents"""
    cost_dollars = (
        input_tokens * SONNET_INPUT_COST +
        output_tokens * SONNET_OUTPUT_COST
    )
    return int(cost_dollars * 100)

class TimeoutManager:
    def __init__(self, timeout_minutes: int = 30, cost_limit_cents: int = 100):
        self.timeout_minutes = timeout_minutes
        self.cost_limit_cents = cost_limit_cents
        self.start_time = None
        self.total_cost_cents = 0

    def add_api_call(self, input_tokens: int, output_tokens: int):
        cost = calculate_cost(input_tokens, output_tokens)
        self.total_cost_cents += cost

        # Log to database
        metadata = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_cents": cost,
            "cumulative_cost_cents": self.total_cost_cents
        }
        supabase_service.log_agent_activity(
            agent="TimeoutManager",
            activity_type="api_call_cost",
            success=True,
            metadata=metadata
        )

    def exceeds_cost_limit(self) -> bool:
        if self.total_cost_cents > self.cost_limit_cents:
            logger.warning(f"Cost limit exceeded: {self.total_cost_cents}¢ > {self.cost_limit_cents}¢")
            return True
        return False
```

### 4. Graceful Degradation

```python
# ralph/core/ralph_loop.py

def handle_iteration_result(iteration: int, quality: float, timeout_mgr: TimeoutManager, blog_id: str, content: str):
    """
    Decision tree for what to do after each iteration
    """

    # BEST CASE: Quality threshold met
    if quality >= 0.85:
        logger.info(f"✅ Quality threshold met: {quality:.2f}")
        supabase_service.update_blog_status(blog_id, status='published')
        return ActionResult.PUBLISH

    # GOOD CASE: Quality floor met, but timeout/cost
    if quality >= 0.70:
        if timeout_mgr.is_expired():
            logger.warning(f"⏱️ Timeout reached with quality {quality:.2f} - saving as draft")
            supabase_service.update_blog_status(blog_id, status='draft')
            send_alert_email(f"Draft saved - timeout reached after {iteration} iterations")
            return ActionResult.SAVE_DRAFT

        if timeout_mgr.exceeds_cost_limit():
            logger.warning(f"💰 Cost limit exceeded with quality {quality:.2f} - saving as draft")
            supabase_service.update_blog_status(blog_id, status='draft')
            send_alert_email(f"Draft saved - cost limit reached after {iteration} iterations")
            return ActionResult.SAVE_DRAFT

    # BAD CASE: Below quality floor
    if quality < 0.70:
        if timeout_mgr.is_expired() or timeout_mgr.exceeds_cost_limit():
            logger.error(f"❌ Quality {quality:.2f} below floor 0.70 - cannot save")
            supabase_service.update_blog_status(blog_id, status='failed')
            send_alert_email(f"FAILURE: Quality {quality:.2f} after {iteration} iterations")
            return ActionResult.FAIL

    # CONTINUE: Quality < 0.85, still have time/budget
    logger.info(f"🔄 Quality {quality:.2f} - continuing iteration {iteration + 1}")
    return ActionResult.CONTINUE
```

---

## Environment Variables

```bash
# .env

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

# Social Media (Phase 5)
LINKEDIN_ENABLED=false
TWITTER_ENABLED=false
LINKEDIN_ACCESS_TOKEN=...
TWITTER_API_KEY=...
```

---

## Updated config.py

```python
# config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str

    # Anthropic
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    # Ralph Loop Settings
    ralph_timeout_minutes: int = 30
    ralph_quality_threshold: float = 0.85
    ralph_quality_floor: float = 0.70
    ralph_cost_limit_cents: int = 100
    ralph_max_iterations: int = 20

    # Email Alerts
    resend_api_key: str
    alert_email: str

    # Environment
    environment: str = "development"

    # Phase 3+ Settings
    trendscout_enabled: bool = False
    research_enabled: bool = False

    # Phase 5+ Settings
    linkedin_enabled: bool = False
    twitter_enabled: bool = False
    linkedin_access_token: str = ""
    twitter_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

# Singleton instance
settings = Settings()
```

---

## Success Metrics

**Phase 1-2 (Weeks 0-3):**
- ✅ Daily blog generation success rate ≥ 95%
- ✅ Average quality score ≥ 0.87
- ✅ Average iterations per post: 2-4
- ✅ Average generation time: 10-20 minutes
- ✅ Zero AI slop in published posts
- ✅ API costs per post: $0.10-$0.30

**Phase 3-4 (Weeks 4-6):**
- ✅ Trend discovery produces 3+ relevant topics daily
- ✅ Research adds measurable value (quality score +5-10%)
- ✅ No increase in API costs despite multi-agent

**Phase 5 (Weeks 7-8):**
- ✅ 2 social posts per published blog (LinkedIn + Twitter)
- ✅ Social engagement baseline established
- ✅ No spam reports

---

## Risk Mitigation (Updated)

| Risk | Mitigation | Status |
|------|------------|--------|
| Ralph loop never converges | 30-min timeout + $1 cost guard + quality floor (0.70) | ✅ Addressed |
| Claude API outage | Retry with exponential backoff (1, 2, 4, 8 min), max 4 retries | ✅ Added |
| Prompt injection via RSS | Sanitize RSS content, validate structure, limit length | ✅ Added |
| Cost explosion | Hard limit $1/run = max 20 iterations @ ~5¢/iteration | ✅ Added |
| Quality never reaches 0.85 | Save as draft at 0.70+, alert for manual review | ✅ Added |
| Database connection failures | Connection pooling, retry logic, circuit breaker | ✅ Added |
| Content duplication | Track used_in_blog in rss_items, check before generation | ✅ Added |
| Agent coordination failures | Fallback: if agent fails, use simple prompt | ✅ Specified |
| Social media API rejection | Rate limiting, manual review for first 50 posts | ✅ Phase 5 |

---

## Next Steps After Approval

1. **You:** Create Phase 1 database tables in Supabase
2. **You:** Seed 5 RSS sources (manufacturing publications)
3. **I:** Implement Phase 0 spike (Days 1-3)
4. **We:** Review spike results, discuss learnings
5. **I:** Implement Phase 1 core loop (Days 4-14)
6. **We:** Test Phase 1 manually, refine prompts
7. **I:** Implement Phase 2 deployment (Days 15-21)
8. **Deploy:** First automated run at 7 AM
9. **Monitor:** 1 week of production data
10. **I:** Implement Phase 3 multi-agent (Days 22-35)
11. **Continue:** Phases 4-5 as planned

---

## Open Questions

**✅ All resolved via Opus review:**
- Integration approach: Progressive hybrid (spike → core → multi-agent → social)
- Database: Supabase only, no dual-storage
- Timeline: 5-6 weeks realistic
- Cost guards: $1/run hard limit
- Quality thresholds: 0.85 publish, 0.70 floor, <0.70 fail
- Agent communication: Direct function calls, not database
- Social media: Deferred to Week 5+
- Error recovery: Specified for all major failure modes

---

**Estimated Timeline:** 5-6 weeks to full production (blogs + social)
**Estimated Cost:** $5-15/month in API costs (Phase 1-4), $15-30/month with social
**First Value:** Working spike in 3 days, production blogs in 3 weeks
**Risk Level:** Low (de-risked via spike, progressive rollout, multiple safeguards)
