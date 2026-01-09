# Phase 1 - Core Ralph Loop

**Goal:** Single-agent iterative content generation with quality validation

**Duration:** Days 4-14

## Success Criteria

| Metric | Target |
|--------|--------|
| Published Posts | 5 |
| Quality Threshold | ≥ 0.85 |
| Avg Iterations per Post | 2-4 |
| API Cost per Post | ≤ $0.25 |
| Zero AI Slop | ✓ Required |

---

## Tasks

### Database (7 tasks)

#### db-001: blog_posts table exists with proper schema and constraints
**Status:** ❌ Not Complete

**Steps:**
1. Query Supabase schema for blog_posts table
2. Verify columns: id, title, content, status, published_at, created_at, updated_at
3. Insert a test record with status='draft'
4. Verify CHECK constraint rejects invalid status values
5. Confirm test record appears in SELECT query

---

#### db-002: blog_content_drafts table exists with foreign keys and unique constraint
**Status:** ❌ Not Complete

**Steps:**
1. Query Supabase schema for blog_content_drafts table
2. Verify all columns exist: id, blog_post_id, iteration_number, content, title, agent_name, critique, quality_score, improvements, token_count, api_cost_cents, created_at
3. Insert draft with iteration_number=1 for existing blog_post
4. Attempt to insert duplicate iteration_number for same blog_post_id
5. Verify UNIQUE constraint prevents duplicate (should fail)

---

#### db-003: blog_agent_activity table exists for logging agent actions
**Status:** ❌ Not Complete

**Steps:**
1. Query Supabase schema for blog_agent_activity table
2. Verify columns: id, agent_name, activity_type, context_id, duration_ms, success, error_message, metadata, created_at
3. Insert activity record with activity_type='content_draft'
4. Attempt to insert invalid activity_type
5. Verify CHECK constraint rejects invalid activity types

---

#### db-004: blog_rss_sources table exists for managing RSS feeds
**Status:** ❌ Not Complete

**Steps:**
1. Query Supabase schema for blog_rss_sources table
2. Verify columns: id, name, url, category, active, priority, last_fetched_at, created_at, updated_at
3. Insert RSS source with active=true, priority=5
4. Attempt to insert duplicate URL
5. Verify UNIQUE constraint on url prevents duplicate

---

#### db-005: blog_rss_items table exists with foreign keys to sources and posts
**Status:** ❌ Not Complete

**Steps:**
1. Query Supabase schema for blog_rss_items table
2. Verify columns: id, source_id, title, url, summary, published_at, relevance_score, used_in_blog, created_at
3. Insert RSS item linked to valid source_id
4. Verify foreign key to blog_rss_sources works
5. Confirm UNIQUE constraint on url column exists

---

#### db-006: Database indexes created for query performance
**Status:** ❌ Not Complete

**Steps:**
1. Query pg_indexes for blog_content_drafts indexes
2. Verify index exists on (blog_post_id, iteration_number DESC)
3. Query pg_indexes for blog_agent_activity indexes
4. Verify indexes exist on (agent_name, created_at DESC) and (activity_type, created_at DESC)
5. Verify partial index on blog_rss_items where used_in_blog IS NULL

---

#### db-007: 5 manufacturing RSS sources seeded and active
**Status:** ❌ Not Complete

**Steps:**
1. Query blog_rss_sources table
2. Verify at least 5 RSS sources exist
3. Check that all sources have active=true
4. Verify priority values are set (1-10)
5. Manually fetch one RSS URL to confirm it's accessible

---

### Services (12 tasks)

#### svc-001: services package is importable and supabase_service provides client
**Status:** ❌ Not Complete

**Steps:**
1. Run: `python -c 'import services'`
2. Verify import succeeds without errors
3. Run: `python -c 'from services.supabase_service import get_supabase_client; print(get_supabase_client())'`
4. Verify Supabase client object is returned
5. Check that SUPABASE_URL and SUPABASE_KEY are loaded from environment

---

#### svc-002: supabase_service.create_blog_post() creates blog posts
**Status:** ❌ Not Complete

**Steps:**
1. Call `create_blog_post('Test Title', 'Test Content', 'draft')`
2. Verify function returns a UUID blog_post_id
3. Query blog_posts table for the created record
4. Confirm title, content, and status match input
5. Verify created_at timestamp is set

---

#### svc-003: supabase_service.save_draft_iteration() stores content drafts
**Status:** ❌ Not Complete

**Steps:**
1. Create a test blog post
2. Call `save_draft_iteration(blog_id, 1, 'content', 0.75, {'notes': 'test'})`
3. Query blog_content_drafts for the iteration
4. Verify iteration_number, content, and quality_score are correct
5. Attempt to save duplicate iteration_number and verify it fails

---

#### svc-004: supabase_service.log_agent_activity() logs agent actions
**Status:** ❌ Not Complete

**Steps:**
1. Call `log_agent_activity('ProductMarketing', 'content_draft', True, {'cost': 50})`
2. Verify function returns without error
3. Query blog_agent_activity table
4. Confirm agent_name, activity_type, success, and metadata are stored
5. Verify created_at timestamp is recent

---

#### svc-005: rss_service.fetch_active_feeds() returns active RSS sources
**Status:** ❌ Not Complete

**Steps:**
1. Call `fetch_active_feeds()`
2. Verify function returns a list of RSS sources
3. Check that all returned sources have active=true
4. Verify sources are ordered by priority DESC
5. Confirm at least 5 sources are returned

---

#### svc-006: rss_service.fetch_feed_items() fetches and stores RSS items
**Status:** ❌ Not Complete

**Steps:**
1. Get a valid RSS source_id from database
2. Call `fetch_feed_items(source_id, limit=10)`
3. Verify function returns list of RSS items
4. Query blog_rss_items table
5. Confirm new items are stored with title, url, summary, published_at

---

#### svc-007: rss_service.mark_items_as_used() marks items as consumed
**Status:** ❌ Not Complete

**Steps:**
1. Get unused RSS item IDs from database
2. Create a test blog post
3. Call `mark_items_as_used([item_id1, item_id2], blog_id)`
4. Query blog_rss_items for those item IDs
5. Verify used_in_blog column is set to the blog_id

---

#### svc-008: quality_validator detects AI slop keywords
**Status:** ❌ Not Complete

**Steps:**
1. Create test content with 'delve' keyword
2. Call `detect_ai_slop(content)`
3. Verify function returns `(True, ['delve'])`
4. Create test content with 'leverage' and 'unlock' keywords
5. Verify function returns `(True, ['leverage', 'unlock'])`

---

#### svc-009: quality_validator validates content length (1000-2500 words)
**Status:** ❌ Not Complete

**Steps:**
1. Create content with 500 words
2. Call `validate_length(content)`
3. Verify returns `(False, 500, low_score)`
4. Create content with 1500 words
5. Verify returns `(True, 1500, high_score)`

---

#### svc-010: quality_validator checks content structure (headings, paragraphs)
**Status:** ❌ Not Complete

**Steps:**
1. Create content without markdown headings
2. Call `validate_structure(content)`
3. Verify returns `(False, issues_list, low_score)`
4. Create content with proper ## and ### headings
5. Verify returns `(True, [], high_score)`

---

#### svc-011: quality_validator checks brand voice (not salesy, professional)
**Status:** ❌ Not Complete

**Steps:**
1. Create content with excessive exclamation marks
2. Call `validate_brand_voice(content)`
3. Verify returns `(False, issues_list, low_score)`
4. Create professional, technical content
5. Verify returns `(True, [], high_score)`

---

#### svc-012: quality_validator.validate_content() aggregates all checks
**Status:** ❌ Not Complete

**Steps:**
1. Create high-quality content (1500 words, headings, no slop)
2. Call `validate_content(content, title)`
3. Verify returns quality_score >= 0.85
4. Create content with AI slop keyword
5. Verify returns quality_score < 0.50

---

### Ralph Core (11 tasks)

#### ralph-001: ralph package structure exists and is importable
**Status:** ❌ Not Complete

**Steps:**
1. Run: `python -c 'import ralph'`
2. Run: `python -c 'import ralph.core'`
3. Run: `python -c 'import ralph.agents'`
4. Run: `python -c 'import ralph.prompts'`
5. Verify all imports succeed without errors

---

#### ralph-002: timeout_manager.TimeoutManager tracks time and cost limits
**Status:** ❌ Not Complete

**Steps:**
1. Create `TimeoutManager(timeout_minutes=30, cost_limit_cents=100)`
2. Call `is_timeout_exceeded()` immediately
3. Verify returns False
4. Call `is_cost_limit_exceeded(110)`
5. Verify returns True

---

#### ralph-003: timeout_manager calculates API costs from tokens
**Status:** ❌ Not Complete

**Steps:**
1. Call `calculate_api_cost(input_tokens=1000, output_tokens=2000, model='claude-sonnet-4-5')`
2. Verify returns cost in cents as integer
3. Check cost matches Anthropic pricing (approximately)
4. Call with different token amounts
5. Verify costs scale proportionally

---

#### ralph-004: critique.py defines AI slop keywords and critique prompt
**Status:** ❌ Not Complete

**Steps:**
1. Run: `python -c 'from ralph.prompts.critique import AI_SLOP_KEYWORDS; print(len(AI_SLOP_KEYWORDS))'`
2. Verify at least 15 forbidden keywords exist
3. Run: `python -c 'from ralph.prompts.critique import CRITIQUE_PROMPT_TEMPLATE; print(len(CRITIQUE_PROMPT_TEMPLATE))'`
4. Verify critique prompt template is defined and non-empty
5. Check that AI_SLOP_KEYWORDS matches quality_validator list

---

#### ralph-005: critique prompt includes JSON output specification with quality score
**Status:** ❌ Not Complete

**Steps:**
1. Read CRITIQUE_PROMPT_TEMPLATE content
2. Verify it includes 'quality_score' field specification
3. Verify it includes 'ai_slop_detected' field
4. Verify it includes 'improvements' field
5. Check that example JSON response is provided in prompt

---

#### ralph-006: content_generation.py provides initial draft and improvement prompts
**Status:** ❌ Not Complete

**Steps:**
1. Run: `python -c 'from ralph.prompts.content_generation import INITIAL_DRAFT_PROMPT; print(len(INITIAL_DRAFT_PROMPT))'`
2. Verify initial draft prompt is defined
3. Run: `python -c 'from ralph.prompts.content_generation import IMPROVEMENT_PROMPT_TEMPLATE; print(len(IMPROVEMENT_PROMPT_TEMPLATE))'`
4. Verify improvement prompt template is defined
5. Check that both prompts mention manufacturing industry and MAS Precision Parts

---

#### ralph-007: BaseAgent abstract class provides Claude API integration
**Status:** ❌ Not Complete

**Steps:**
1. Run: `python -c 'from ralph.agents.base_agent import BaseAgent; print(BaseAgent.__bases__)'`
2. Verify BaseAgent is an abstract class
3. Check that BaseAgent has `_call_claude()` method
4. Check that BaseAgent has token tracking attributes
5. Verify `get_total_tokens()` method exists

---

#### ralph-008: BaseAgent tracks input and output tokens across calls
**Status:** ❌ Not Complete

**Steps:**
1. Create a concrete implementation of BaseAgent for testing
2. Make 2 Claude API calls via `_call_claude()`
3. Call `get_total_tokens()`
4. Verify it returns tuple of (input_tokens, output_tokens)
5. Verify tokens accumulate across multiple calls

---

#### ralph-009: ProductMarketingAgent generates initial blog content from RSS
**Status:** ❌ Not Complete

**Steps:**
1. Create ProductMarketingAgent instance
2. Get RSS items from database (3-5 items)
3. Call `agent.generate_content(rss_items)`
4. Verify returns tuple (title, content)
5. Check that content is 1000+ words and mentions manufacturing

---

#### ralph-010: ProductMarketingAgent improves content based on critique
**Status:** ❌ Not Complete

**Steps:**
1. Create ProductMarketingAgent instance
2. Create sample content with known issues
3. Create critique dict with specific improvement suggestions
4. Call `agent.improve_content(current_content, critique)`
5. Verify improved content addresses critique points

---

#### ralph-011: RalphLoop generates initial draft and creates blog post record
**Status:** ❌ Not Complete

**Steps:**
1. Create RalphLoop instance
2. Call `loop.generate_initial_draft()`
3. Verify blog_posts record is created with status='draft'
4. Verify blog_content_drafts has iteration 1 saved
5. Check that RSS items are marked as used

---

### Functional (7 tasks)

#### ralph-012: RalphLoop iteratively improves content until quality threshold reached
**Status:** ❌ Not Complete

**Steps:**
1. Create RalphLoop instance with quality threshold 0.85
2. Run `loop.run()`
3. Monitor blog_content_drafts for multiple iterations
4. Verify quality_score increases with each iteration
5. Confirm loop stops when quality >= 0.85

---

#### ralph-013: RalphLoop publishes blog when quality threshold reached
**Status:** ❌ Not Complete

**Steps:**
1. Run RalphLoop until quality >= 0.85
2. Query blog_posts for the blog_post_id
3. Verify status is 'published'
4. Verify published_at timestamp is set
5. Confirm final content matches best iteration

---

#### ralph-014: RalphLoop saves as draft when timeout reached before quality threshold
**Status:** ❌ Not Complete

**Steps:**
1. Set RALPH_TIMEOUT_MINUTES=1 in environment
2. Run RalphLoop (will timeout before reaching 0.85)
3. Wait for timeout to trigger
4. Query blog_posts and verify status='draft' (if quality >= 0.70)
5. Verify alert/log message about timeout

---

#### ralph-015: RalphLoop saves as draft when cost limit reached before quality threshold
**Status:** ❌ Not Complete

**Steps:**
1. Set RALPH_COST_LIMIT_CENTS=10 in environment
2. Run RalphLoop (will hit cost limit quickly)
3. Monitor cost accumulation in logs
4. Verify loop stops when cost > limit
5. Check blog_posts status='draft' (if quality >= 0.70)

---

#### ralph-016: RalphLoop fails explicitly if quality below 0.70 at limits
**Status:** ❌ Not Complete

**Steps:**
1. Set very low timeout (RALPH_TIMEOUT_MINUTES=0.5)
2. Run RalphLoop (will timeout with low quality)
3. Verify blog_posts status='failed' if quality < 0.70
4. Check that error log/alert is generated
5. Confirm all iterations are still saved in database

---

#### ralph-017: RalphLoop logs all agent activity to blog_agent_activity table
**Status:** ❌ Not Complete

**Steps:**
1. Run RalphLoop completely
2. Query blog_agent_activity table
3. Verify entries exist for 'content_draft' activities
4. Verify entries exist for 'critique' activities
5. Verify entry exists for 'publish' activity

---

#### ralph-018: RalphLoop can be run from command line
**Status:** ❌ Not Complete

**Steps:**
1. Run: `python -m ralph.core.ralph_loop`
2. Verify script executes without import errors
3. Check that blog post is generated
4. Verify summary is printed to stdout (status, quality, iterations, cost)
5. Check exit code is 0 for success

---

### Testing (6 tasks)

#### test-001: High-quality first draft (quality >= 0.85) publishes immediately
**Status:** ❌ Not Complete

**Steps:**
1. Run: `python -m ralph.core.ralph_loop`
2. Monitor logs for iteration 1 generation
3. Check quality score for iteration 1
4. If quality >= 0.85, verify blog_posts status='published'
5. Confirm only 1 iteration exists in blog_content_drafts

---

#### test-002: Content improves over 2-3 iterations to reach quality threshold
**Status:** ❌ Not Complete

**Steps:**
1. Run: `python -m ralph.core.ralph_loop`
2. Monitor quality scores: iteration 1, 2, 3
3. Verify quality increases with each iteration
4. Check that status='published' after 2-3 iterations
5. Confirm final quality >= 0.85

---

#### test-003: AI slop detection forces quality below 0.50
**Status:** ❌ Not Complete

**Steps:**
1. Manually insert draft with 'delve' or 'leverage' in content
2. Run quality validation on that content
3. Verify quality_score < 0.50
4. Check that critique has ai_slop_detected=true
5. Verify found_keywords includes the forbidden phrase

---

#### test-004: System can generate 5 successful posts end-to-end
**Status:** ❌ Not Complete

**Steps:**
1. Run ralph_loop.py 5 times (manually or scripted)
2. Verify all 5 posts have status='published'
3. Calculate average quality score across 5 posts
4. Verify average quality >= 0.85
5. Check average iterations is 2-4 per post

---

#### test-005: No AI slop keywords in any published content
**Status:** ❌ Not Complete

**Steps:**
1. Query all blog_posts where status='published'
2. For each post, run AI slop detection on content
3. Verify no forbidden keywords found in published posts
4. Document any edge cases (legitimate keyword use)
5. Confirm zero AI slop in production content

---

#### test-006: API costs average below $0.25 per post
**Status:** ❌ Not Complete

**Steps:**
1. Query blog_content_drafts for recent blog posts
2. Sum api_cost_cents for each blog_post_id
3. Calculate average cost per post
4. Verify average is below 25 cents
5. Check that no single post exceeded $1.00 (cost limit)

---

### Documentation (2 tasks)

#### doc-001: README includes Phase 1 setup and usage instructions
**Status:** ❌ Not Complete

**Steps:**
1. Open README.md file
2. Verify section exists for 'Phase 1 - Core Ralph Loop'
3. Check that database setup steps are documented
4. Verify environment variables are listed
5. Confirm manual run command is provided: `python -m ralph.core.ralph_loop`

---

#### doc-002: .env.example includes all Phase 1 environment variables
**Status:** ❌ Not Complete

**Steps:**
1. Open .env.example file
2. Verify SUPABASE_URL and SUPABASE_KEY are present
3. Verify ANTHROPIC_API_KEY and ANTHROPIC_MODEL are present
4. Verify Ralph settings: RALPH_TIMEOUT_MINUTES, RALPH_QUALITY_THRESHOLD, RALPH_QUALITY_FLOOR, RALPH_COST_LIMIT_CENTS
5. Check that placeholder values and comments explain each variable

---

## Summary

**Total Tasks:** 45
- Database: 7
- Services: 12
- Ralph Core: 11
- Functional: 7
- Testing: 6
- Documentation: 2

**Completed:** 0/45
**Progress:** 0%
