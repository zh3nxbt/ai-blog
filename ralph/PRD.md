# Product Requirements Document: Ralph Content Generator

**Product:** Autonomous Blog Content Generation System
**Client:** MAS Precision Parts (machine shop website)
**Phase:** 1 - Core Ralph Loop
**Last Updated:** 2026-01-12

---

## 1. Problem Statement

MAS Precision Parts needs consistent, high-quality blog content to establish industry expertise and improve SEO. Manual content creation is time-consuming and inconsistent. Generic AI-generated content sounds robotic and damages credibility.

**The solution:** An autonomous system that generates one blog post per day using manufacturing industry sources, iteratively refining content until it meets quality standards - without sounding like AI wrote it.

---

## 2. Goals

### Primary Goal
Generate exactly **one high-quality blog post per day** that:
- Sounds like a knowledgeable shop veteran wrote it
- Contains zero "AI slop" language
- References real, current industry sources
- Publishes automatically when quality threshold is met

### Phase 1 Success Criteria

| Metric | Target |
|--------|--------|
| Published posts | 5 |
| Quality score threshold | >= 0.85 |
| Average iterations per post | 2-4 |
| API cost per post | <= $0.50 |
| AI slop in published content | Zero tolerance |

---

## 3. User Stories

### Website Visitor
> As a visitor to the MAS Precision Parts website, I want to read relevant, practical content about manufacturing so I can learn something useful and trust this shop knows their craft.

### Shop Owner
> As the machine shop owner, I want automated content generation that reflects our expertise without requiring my daily involvement, so the website stays fresh while I focus on running the shop.

### Content System
> As the content generation system, I want to iteratively improve drafts until quality is achieved or limits are reached, so every published post meets our standards.

---

## 4. Functional Requirements

### 4.1 Content Sourcing
- Fetch articles from manufacturing industry RSS feeds
- Store and deduplicate RSS items in database
- Track which items have been used in posts
- Support 5+ active feed sources at launch

### 4.2 Content Generation
- Generate initial draft from 3-5 RSS source items
- Use Claude API for content generation
- Output structured JSON with title, excerpt, content_markdown, source_urls
- Iteratively improve content based on critique feedback

### 4.3 Quality Validation
- Score content on 0.0-1.0 scale
- Detect AI slop keywords (delve, leverage, unlock, landscape, etc.)
- Validate content length (1000-2500 words)
- Check structure (headings, paragraphs, flow)
- Verify brand voice compliance

### 4.4 Publishing Workflow
| Quality Score | Action |
|---------------|--------|
| >= 0.85 | Publish immediately |
| 0.70 - 0.84 | Save as draft (manual review) |
| < 0.70 | Mark as failed |

### 4.5 Safety Limits
- 30-minute timeout per generation run
- $1.00 cost limit per generation
- Graceful degradation: publish > draft > fail
- All iterations saved for debugging

---

## 5. Non-Functional Requirements

### Reliability
- Fail loudly, never silently
- Idempotent execution (safe to re-run)
- Clear error messages with actionable context

### Observability
- Log all agent activity to database
- Track token usage and API costs per iteration
- Record quality scores and critique feedback

### Cost Control
- Calculate costs from token usage
- Stop iteration loop when budget exceeded
- Alert on unusual cost patterns

---

## 6. Technical Constraints

| Constraint | Decision |
|------------|----------|
| Database | Supabase (PostgreSQL) - integrates with existing website |
| Deployment | DigitalOcean Ubuntu with systemd (no containers) |
| LLM | External Claude API only (no local models) |
| Scheduling | systemd timer, daily at 7 AM UTC |
| API Framework | FastAPI (stateless, minimal surface) |

---

## 7. Out of Scope (Phase 1)

These features are explicitly **not** part of Phase 1:

- Multi-agent coordination (Phase 3+)
- Real-time content updates
- User-facing admin UI
- Social media distribution
- Multiple posts per day
- Image generation or handling
- Content categories/tagging
- A/B testing of content

---

## 8. Brand Voice Requirements

Content must sound like a **knowledgeable shop veteran**, not a marketing bot.

### Do
- Use concrete examples over abstract concepts
- Lead with interesting details, not context-setting
- Be opinionated when backed by facts
- Write short sentences in active voice
- Use specific numbers and real examples

### Don't
- Use AI slop language (delve, leverage, unlock, landscape, realm, utilize)
- Start with "In today's fast-paced world..." or similar
- Use formulaic structure every time
- Hedge or qualify unnecessarily
- Sound corporate or salesy

### Examples

```
BAD:  "In the ever-evolving landscape of manufacturing..."
GOOD: "Carbide tooling costs dropped 15% last quarter."

BAD:  "Let's delve into the intricacies of tolerance stacking..."
GOOD: "Tolerance stacking breaks projects. Here's why."

BAD:  "It's important to note that surface finish impacts..."
GOOD: "Surface finish isn't cosmetic—it changes how parts fail."
```

See `claude.md` for complete content guidelines.

---

## 9. Data Model

### blog_posts
Primary content storage for generated posts. **Note:** This table pre-existed and contains additional columns for the existing website.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| title | String | Post title |
| slug | String | URL-safe identifier |
| excerpt | String | Short summary |
| content | Text | Full post content (markdown) |
| featured_image | String | URL to featured image (optional) |
| author | String | Post author (optional) |
| status | Enum | draft, published, failed |
| meta_description | String | SEO meta description (optional) |
| meta_keywords | String | SEO keywords (optional) |
| tags | Array | Post tags (optional) |
| published_at | Timestamp | When published |
| created_at | Timestamp | When created |
| updated_at | Timestamp | When last updated |

### blog_content_drafts
Iteration history for each post.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| blog_post_id | UUID | Foreign key to blog_posts |
| iteration_number | Integer | 1, 2, 3... |
| content | Text | Draft content |
| quality_score | Float | 0.0-1.0 |
| critique | JSON | Feedback from quality check |
| api_cost_cents | Integer | Cost of this iteration |

### blog_rss_sources
RSS feed configuration.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String | Feed name |
| url | String | Feed URL (unique) |
| active | Boolean | Is feed enabled |
| priority | Integer | 1-10, higher = preferred |

### blog_rss_items
Individual articles from feeds.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| source_id | UUID | Foreign key to sources |
| title | String | Article title |
| url | String | Article URL (unique) |
| summary | Text | Article excerpt |
| used_in_blog | UUID | Foreign key to blog_posts (nullable) |

### blog_agent_activity
Observability and debugging.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| agent_name | String | Which agent acted |
| activity_type | String | content_draft, critique, publish |
| success | Boolean | Did it succeed |
| metadata | JSON | Additional context |

---

## 10. References

| Document | Purpose |
|----------|---------|
| `PRD.json` | Implementation task list (45 tasks) |
| `progress.txt` | Completed work tracking |
| `claude.md` | Coding principles and content guidelines |
| `docs/RALPH_OVERALL_PLAN.md` | Multi-phase roadmap |

---

## 11. Implementation Learnings

### Migration Tooling Simplification (2026-01-13)

**Context:** During Phase 0 database setup, we created 6 migrations (db-002 through db-007) with separate apply and verify scripts. Over time, this grew to 17 Python files with significant code duplication.

**Problem:**
- 40% of codebase was duplicated migration application logic
- Each `apply_db_XXX.py` script had identical 165-line connection code
- Bug fixes required updating 6+ files
- New migrations required copying 165 lines of boilerplate
- Dead/experimental code added confusion

**Solution:**
- Created `migrations/db_utils.py` with shared connection and application logic
- Refactored all apply scripts from ~165 lines to ~16 lines each
- Deleted 4 dead/experimental scripts
- Added comprehensive `migrations/README.md` documentation

**Impact:**
- Reduced codebase from ~2,877 lines to ~1,200 lines (42% reduction)
- Eliminated code duplication
- Future migrations now trivial to add (just 16 lines per migration)
- Clear developer experience with single approach

**Principles Reinforced:**
- **DRY applies to everything:** Scripts, tests, and tools deserve the same refactoring attention as application code
- **Boring correctness requires active maintenance:** Simplicity doesn't happen by accident - it requires deliberate effort
- **Documentation prevents debt:** Clear README prevents future confusion about "which script do I run?"

### Spike-Driven Development Pattern

**Pattern:** Build minimal proof-of-concept before full production system

**Rationale:**
- Test integration points early (RSS, Claude API, Supabase)
- Measure actual costs and performance vs estimates
- Reveal unknown unknowns before investing in full system
- Generate real data for quality threshold calibration

**spike.py Approach:**
- Single-pass end-to-end flow (no iterative refinement)
- Basic error handling (fail loud, don't retry)
- Manual review of generated content
- Logs token usage, costs, and content preview
- Success criteria: 3 successful runs producing 3 drafts

**Benefits:**
- De-risks Phase 1 implementation
- Informs architecture decisions with real data
- Validates assumptions about RSS feeds and content quality
- Builds confidence in integration points

**Phase 0 Exit Criteria:**
- Database schema complete ✅
- Migration tooling simplified ✅
- spike.py runs 3 times successfully ⏳
- 3 blog drafts created in Supabase ⏳
- RSS feeds return valid, parseable content ⏳
- Claude API generates readable blog posts ⏳
- Token costs measured and within budget ⏳

---

## 12. spike.py Specification

### Purpose
Minimal end-to-end proof-of-concept to validate Claude + Supabase + RSS integration before building the full production system.

### Scope

**In scope:**
1. Fetch 3-5 RSS items from seeded sources (`blog_rss_sources` table)
2. Store fetched items in `blog_rss_items` (skip duplicates based on URL)
3. Generate blog post using Claude API (single iteration, no refinement loop)
4. Save generated post to `blog_posts` with `status='draft'`
5. Log activity to `blog_agent_activity` table
6. Print token usage, estimated cost, and content preview

**Out of scope:**
- Quality validation/scoring (no critique loop)
- Iterative refinement (single-pass generation only)
- Error retry logic (fail loud on errors)
- Cost guards and timeouts (basic implementation)
- Idempotency checks (manual execution only)
- Scheduling/automation (run manually 3 times)

### Implementation Tasks

See `PRD.json` for detailed task breakdown:
- `svc-003`: RSS feed fetching service
- `svc-004`: Claude API integration service
- `spike-001`: Build spike.py orchestrator
- `spike-002`: Execute spike.py 3 times and verify results

### Success Criteria

**Per-run criteria:**
- Executes without fatal errors
- Creates valid blog post in Supabase (`blog_posts` table)
- Content is readable and relevant (manual review)
- Token usage logged accurately
- Estimated cost < $0.50 per run

**Phase 0 completion criteria:**
- 3 successful spike.py executions
- 3 blog drafts visible in Supabase dashboard
- RSS feeds demonstrated as reliable
- Claude API demonstrated as generating acceptable content
- Token costs measured and documented in `progress.txt`

### Deliverable
Confidence that the full system CAN work, with real data to inform Phase 1 architecture decisions.

---

## Appendix: Forbidden AI Slop Keywords

Content containing these terms will be penalized heavily in quality scoring:

```
delve, unveil, landscape, realm, unlock, leverage, utilize, robust,
streamline, cutting-edge, revolutionary, harness, paradigm, synergy,
"in today's fast-paced world", "it's important to note",
"let's explore", "dive deep", "game-changer", "best practices"
```
