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
| API cost per post | <= $0.25 |
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
Primary content storage for generated posts.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| title | String | Post title |
| slug | String | URL-safe identifier |
| excerpt | String | Short summary |
| content_markdown | Text | Full post content |
| source_urls | Array | RSS sources used |
| status | Enum | draft, published, failed |
| published_at | Timestamp | When published |
| created_at | Timestamp | When created |

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

## Appendix: Forbidden AI Slop Keywords

Content containing these terms will be penalized heavily in quality scoring:

```
delve, unveil, landscape, realm, unlock, leverage, utilize, robust,
streamline, cutting-edge, revolutionary, harness, paradigm, synergy,
"in today's fast-paced world", "it's important to note",
"let's explore", "dive deep", "game-changer", "best practices"
```
