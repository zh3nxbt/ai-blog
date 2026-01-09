{
  "phase": "Phase 1 - Core Ralph Loop",
  "goal": "Single-agent iterative content generation with quality validation",
  "estimated_duration": "Days 4-14",
  "success_criteria": {
    "published_posts": 5,
    "quality_threshold": 0.85,
    "avg_iterations": "2-4",
    "api_cost_per_post": 0.25,
    "zero_ai_slop": true
  },
  "tasks": [
    {
      "id": "db-001",
      "category": "database",
      "description": "blog_posts table exists with proper schema and constraints",
      "steps": [
        "Query Supabase schema for blog_posts table",
        "Verify columns: id, title, content, status, published_at, created_at, updated_at",
        "Insert a test record with status='draft'",
        "Verify CHECK constraint rejects invalid status values",
        "Confirm test record appears in SELECT query"
      ],
      "passes": false
    },
    {
      "id": "db-002",
      "category": "database",
      "description": "blog_content_drafts table exists with foreign keys and unique constraint",
      "steps": [
        "Query Supabase schema for blog_content_drafts table",
        "Verify all columns exist: id, blog_post_id, iteration_number, content, title, agent_name, critique, quality_score, improvements, token_count, api_cost_cents, created_at",
        "Insert draft with iteration_number=1 for existing blog_post",
        "Attempt to insert duplicate iteration_number for same blog_post_id",
        "Verify UNIQUE constraint prevents duplicate (should fail)"
      ],
      "passes": false
    },
    {
      "id": "db-003",
      "category": "database",
      "description": "blog_agent_activity table exists for logging agent actions",
      "steps": [
        "Query Supabase schema for blog_agent_activity table",
        "Verify columns: id, agent_name, activity_type, context_id, duration_ms, success, error_message, metadata, created_at",
        "Insert activity record with activity_type='content_draft'",
        "Attempt to insert invalid activity_type",
        "Verify CHECK constraint rejects invalid activity types"
      ],
      "passes": false
    },
    {
      "id": "db-004",
      "category": "database",
      "description": "blog_rss_sources table exists for managing RSS feeds",
      "steps": [
        "Query Supabase schema for blog_rss_sources table",
        "Verify columns: id, name, url, category, active, priority, last_fetched_at, created_at, updated_at",
        "Insert RSS source with active=true, priority=5",
        "Attempt to insert duplicate URL",
        "Verify UNIQUE constraint on url prevents duplicate"
      ],
      "passes": false
    },
    {
      "id": "db-005",
      "category": "database",
      "description": "blog_rss_items table exists with foreign keys to sources and posts",
      "steps": [
        "Query Supabase schema for blog_rss_items table",
        "Verify columns: id, source_id, title, url, summary, published_at, relevance_score, used_in_blog, created_at",
        "Insert RSS item linked to valid source_id",
        "Verify foreign key to blog_rss_sources works",
        "Confirm UNIQUE constraint on url column exists"
      ],
      "passes": false
    },
    {
      "id": "db-006",
      "category": "database",
      "description": "Database indexes created for query performance",
      "steps": [
        "Query pg_indexes for blog_content_drafts indexes",
        "Verify index exists on (blog_post_id, iteration_number DESC)",
        "Query pg_indexes for blog_agent_activity indexes",
        "Verify indexes exist on (agent_name, created_at DESC) and (activity_type, created_at DESC)",
        "Verify partial index on blog_rss_items where used_in_blog IS NULL"
      ],
      "passes": false
    },
    {
      "id": "db-007",
      "category": "database",
      "description": "5 manufacturing RSS sources seeded and active",
      "steps": [
        "Query blog_rss_sources table",
        "Verify at least 5 RSS sources exist",
        "Check that all sources have active=true",
        "Verify priority values are set (1-10)",
        "Manually fetch one RSS URL to confirm it's accessible"
      ],
      "passes": false
    },
    {
      "id": "svc-001",
      "category": "services",
      "description": "services package is importable and supabase_service provides client",
      "steps": [
        "Run: python -c 'import services'",
        "Verify import succeeds without errors",
        "Run: python -c 'from services.supabase_service import get_supabase_client; print(get_supabase_client())'",
        "Verify Supabase client object is returned",
        "Check that SUPABASE_URL and SUPABASE_KEY are loaded from environment"
      ],
      "passes": false
    },
    {
      "id": "svc-002",
      "category": "services",
      "description": "supabase_service.create_blog_post() creates blog posts",
      "steps": [
        "Call create_blog_post('Test Title', 'Test Content', 'draft')",
        "Verify function returns a UUID blog_post_id",
        "Query blog_posts table for the created record",
        "Confirm title, content, and status match input",
        "Verify created_at timestamp is set"
      ],
      "passes": false
    },
    {
      "id": "svc-003",
      "category": "services",
      "description": "supabase_service.save_draft_iteration() stores content drafts",
      "steps": [
        "Create a test blog post",
        "Call save_draft_iteration(blog_id, 1, 'content', 0.75, {'notes': 'test'})",
        "Query blog_content_drafts for the iteration",
        "Verify iteration_number, content, and quality_score are correct",
        "Attempt to save duplicate iteration_number and verify it fails"
      ],
      "passes": false
    },
    {
      "id": "svc-004",
      "category": "services",
      "description": "supabase_service.log_agent_activity() logs agent actions",
      "steps": [
        "Call log_agent_activity('ProductMarketing', 'content_draft', True, {'cost': 50})",
        "Verify function returns without error",
        "Query blog_agent_activity table",
        "Confirm agent_name, activity_type, success, and metadata are stored",
        "Verify created_at timestamp is recent"
      ],
      "passes": false
    },
    {
      "id": "svc-005",
      "category": "services",
      "description": "rss_service.fetch_active_feeds() returns active RSS sources",
      "steps": [
        "Call fetch_active_feeds()",
        "Verify function returns a list of RSS sources",
        "Check that all returned sources have active=true",
        "Verify sources are ordered by priority DESC",
        "Confirm at least 5 sources are returned"
      ],
      "passes": false
    },
    {
      "id": "svc-006",
      "category": "services",
      "description": "rss_service.fetch_feed_items() fetches and stores RSS items",
      "steps": [
        "Get a valid RSS source_id from database",
        "Call fetch_feed_items(source_id, limit=10)",
        "Verify function returns list of RSS items",
        "Query blog_rss_items table",
        "Confirm new items are stored with title, url, summary, published_at"
      ],
      "passes": false
    },
    {
      "id": "svc-007",
      "category": "services",
      "description": "rss_service.mark_items_as_used() marks items as consumed",
      "steps": [
        "Get unused RSS item IDs from database",
        "Create a test blog post",
        "Call mark_items_as_used([item_id1, item_id2], blog_id)",
        "Query blog_rss_items for those item IDs",
        "Verify used_in_blog column is set to the blog_id"
      ],
      "passes": false
    },
    {
      "id": "svc-008",
      "category": "services",
      "description": "quality_validator detects AI slop keywords",
      "steps": [
        "Create test content with 'delve' keyword",
        "Call detect_ai_slop(content)",
        "Verify function returns (True, ['delve'])",
        "Create test content with 'leverage' and 'unlock' keywords",
        "Verify function returns (True, ['leverage', 'unlock'])"
      ],
      "passes": false
    },
    {
      "id": "svc-009",
      "category": "services",
      "description": "quality_validator validates content length (1000-2500 words)",
      "steps": [
        "Create content with 500 words",
        "Call validate_length(content)",
        "Verify returns (False, 500, low_score)",
        "Create content with 1500 words",
        "Verify returns (True, 1500, high_score)"
      ],
      "passes": false
    },
    {
      "id": "svc-010",
      "category": "services",
      "description": "quality_validator checks content structure (headings, paragraphs)",
      "steps": [
        "Create content without markdown headings",
        "Call validate_structure(content)",
        "Verify returns (False, issues_list, low_score)",
        "Create content with proper ## and ### headings",
        "Verify returns (True, [], high_score)"
      ],
      "passes": false
    },
    {
      "id": "svc-011",
      "category": "services",
      "description": "quality_validator checks brand voice (not salesy, professional)",
      "steps": [
        "Create content with excessive exclamation marks",
        "Call validate_brand_voice(content)",
        "Verify returns (False, issues_list, low_score)",
        "Create professional, technical content",
        "Verify returns (True, [], high_score)"
      ],
      "passes": false
    },
    {
      "id": "svc-012",
      "category": "services",
      "description": "quality_validator.validate_content() aggregates all checks",
      "steps": [
        "Create high-quality content (1500 words, headings, no slop)",
        "Call validate_content(content, title)",
        "Verify returns quality_score >= 0.85",
        "Create content with AI slop keyword",
        "Verify returns quality_score < 0.50"
      ],
      "passes": false
    },
    {
      "id": "ralph-001",
      "category": "ralph-core",
      "description": "ralph package structure exists and is importable",
      "steps": [
        "Run: python -c 'import ralph'",
        "Run: python -c 'import ralph.core'",
        "Run: python -c 'import ralph.agents'",
        "Run: python -c 'import ralph.prompts'",
        "Verify all imports succeed without errors"
      ],
      "passes": false
    },
    {
      "id": "ralph-002",
      "category": "ralph-core",
      "description": "timeout_manager.TimeoutManager tracks time and cost limits",
      "steps": [
        "Create TimeoutManager(timeout_minutes=30, cost_limit_cents=100)",
        "Call is_timeout_exceeded() immediately",
        "Verify returns False",
        "Call is_cost_limit_exceeded(110)",
        "Verify returns True"
      ],
      "passes": false
    },
    {
      "id": "ralph-003",
      "category": "ralph-core",
      "description": "timeout_manager calculates API costs from tokens",
      "steps": [
        "Call calculate_api_cost(input_tokens=1000, output_tokens=2000, model='claude-sonnet-4-5')",
        "Verify returns cost in cents as integer",
        "Check cost matches Anthropic pricing (approximately)",
        "Call with different token amounts",
        "Verify costs scale proportionally"
      ],
      "passes": false
    },
    {
      "id": "ralph-004",
      "category": "ralph-core",
      "description": "critique.py defines AI slop keywords and critique prompt",
      "steps": [
        "Run: python -c 'from ralph.prompts.critique import AI_SLOP_KEYWORDS; print(len(AI_SLOP_KEYWORDS))'",
        "Verify at least 15 forbidden keywords exist",
        "Run: python -c 'from ralph.prompts.critique import CRITIQUE_PROMPT_TEMPLATE; print(len(CRITIQUE_PROMPT_TEMPLATE))'",
        "Verify critique prompt template is defined and non-empty",
        "Check that AI_SLOP_KEYWORDS matches quality_validator list"
      ],
      "passes": false
    },
    {
      "id": "ralph-005",
      "category": "ralph-core",
      "description": "critique prompt includes JSON output specification with quality score",
      "steps": [
        "Read CRITIQUE_PROMPT_TEMPLATE content",
        "Verify it includes 'quality_score' field specification",
        "Verify it includes 'ai_slop_detected' field",
        "Verify it includes 'improvements' field",
        "Check that example JSON response is provided in prompt"
      ],
      "passes": false
    },
    {
      "id": "ralph-006",
      "category": "ralph-core",
      "description": "content_generation.py provides initial draft and improvement prompts",
      "steps": [
        "Run: python -c 'from ralph.prompts.content_generation import INITIAL_DRAFT_PROMPT; print(len(INITIAL_DRAFT_PROMPT))'",
        "Verify initial draft prompt is defined",
        "Run: python -c 'from ralph.prompts.content_generation import IMPROVEMENT_PROMPT_TEMPLATE; print(len(IMPROVEMENT_PROMPT_TEMPLATE))'",
        "Verify improvement prompt template is defined",
        "Check that both prompts mention manufacturing industry and MAS Precision Parts"
      ],
      "passes": false
    },
    {
      "id": "ralph-007",
      "category": "ralph-core",
      "description": "BaseAgent abstract class provides Claude API integration",
      "steps": [
        "Run: python -c 'from ralph.agents.base_agent import BaseAgent; print(BaseAgent.__bases__)'",
        "Verify BaseAgent is an abstract class",
        "Check that BaseAgent has _call_claude() method",
        "Check that BaseAgent has token tracking attributes",
        "Verify get_total_tokens() method exists"
      ],
      "passes": false
    },
    {
      "id": "ralph-008",
      "category": "ralph-core",
      "description": "BaseAgent tracks input and output tokens across calls",
      "steps": [
        "Create a concrete implementation of BaseAgent for testing",
        "Make 2 Claude API calls via _call_claude()",
        "Call get_total_tokens()",
        "Verify it returns tuple of (input_tokens, output_tokens)",
        "Verify tokens accumulate across multiple calls"
      ],
      "passes": false
    },
    {
      "id": "ralph-009",
      "category": "ralph-core",
      "description": "ProductMarketingAgent generates initial blog content from RSS",
      "steps": [
        "Create ProductMarketingAgent instance",
        "Get RSS items from database (3-5 items)",
        "Call agent.generate_content(rss_items)",
        "Verify returns tuple (title, content)",
        "Check that content is 1000+ words and mentions manufacturing"
      ],
      "passes": false
    },
    {
      "id": "ralph-010",
      "category": "ralph-core",
      "description": "ProductMarketingAgent improves content based on critique",
      "steps": [
        "Create ProductMarketingAgent instance",
        "Create sample content with known issues",
        "Create critique dict with specific improvement suggestions",
        "Call agent.improve_content(current_content, critique)",
        "Verify improved content addresses critique points"
      ],
      "passes": false
    },
    {
      "id": "ralph-011",
      "category": "functional",
      "description": "RalphLoop generates initial draft and creates blog post record",
      "steps": [
        "Create RalphLoop instance",
        "Call loop.generate_initial_draft()",
        "Verify blog_posts record is created with status='draft'",
        "Verify blog_content_drafts has iteration 1 saved",
        "Check that RSS items are marked as used"
      ],
      "passes": false
    },
    {
      "id": "ralph-012",
      "category": "functional",
      "description": "RalphLoop iteratively improves content until quality threshold reached",
      "steps": [
        "Create RalphLoop instance with quality threshold 0.85",
        "Run loop.run()",
        "Monitor blog_content_drafts for multiple iterations",
        "Verify quality_score increases with each iteration",
        "Confirm loop stops when quality >= 0.85"
      ],
      "passes": false
    },
    {
      "id": "ralph-013",
      "category": "functional",
      "description": "RalphLoop publishes blog when quality threshold reached",
      "steps": [
        "Run RalphLoop until quality >= 0.85",
        "Query blog_posts for the blog_post_id",
        "Verify status is 'published'",
        "Verify published_at timestamp is set",
        "Confirm final content matches best iteration"
      ],
      "passes": false
    },
    {
      "id": "ralph-014",
      "category": "functional",
      "description": "RalphLoop saves as draft when timeout reached before quality threshold",
      "steps": [
        "Set RALPH_TIMEOUT_MINUTES=1 in environment",
        "Run RalphLoop (will timeout before reaching 0.85)",
        "Wait for timeout to trigger",
        "Query blog_posts and verify status='draft' (if quality >= 0.70)",
        "Verify alert/log message about timeout"
      ],
      "passes": false
    },
    {
      "id": "ralph-015",
      "category": "functional",
      "description": "RalphLoop saves as draft when cost limit reached before quality threshold",
      "steps": [
        "Set RALPH_COST_LIMIT_CENTS=10 in environment",
        "Run RalphLoop (will hit cost limit quickly)",
        "Monitor cost accumulation in logs",
        "Verify loop stops when cost > limit",
        "Check blog_posts status='draft' (if quality >= 0.70)"
      ],
      "passes": false
    },
    {
      "id": "ralph-016",
      "category": "functional",
      "description": "RalphLoop fails explicitly if quality below 0.70 at limits",
      "steps": [
        "Set very low timeout (RALPH_TIMEOUT_MINUTES=0.5)",
        "Run RalphLoop (will timeout with low quality)",
        "Verify blog_posts status='failed' if quality < 0.70",
        "Check that error log/alert is generated",
        "Confirm all iterations are still saved in database"
      ],
      "passes": false
    },
    {
      "id": "ralph-017",
      "category": "functional",
      "description": "RalphLoop logs all agent activity to blog_agent_activity table",
      "steps": [
        "Run RalphLoop completely",
        "Query blog_agent_activity table",
        "Verify entries exist for 'content_draft' activities",
        "Verify entries exist for 'critique' activities",
        "Verify entry exists for 'publish' activity"
      ],
      "passes": false
    },
    {
      "id": "ralph-018",
      "category": "functional",
      "description": "RalphLoop can be run from command line",
      "steps": [
        "Run: python -m ralph.core.ralph_loop",
        "Verify script executes without import errors",
        "Check that blog post is generated",
        "Verify summary is printed to stdout (status, quality, iterations, cost)",
        "Check exit code is 0 for success"
      ],
      "passes": false
    },
    {
      "id": "test-001",
      "category": "testing",
      "description": "High-quality first draft (quality >= 0.85) publishes immediately",
      "steps": [
        "Run: python -m ralph.core.ralph_loop",
        "Monitor logs for iteration 1 generation",
        "Check quality score for iteration 1",
        "If quality >= 0.85, verify blog_posts status='published'",
        "Confirm only 1 iteration exists in blog_content_drafts"
      ],
      "passes": false
    },
    {
      "id": "test-002",
      "category": "testing",
      "description": "Content improves over 2-3 iterations to reach quality threshold",
      "steps": [
        "Run: python -m ralph.core.ralph_loop",
        "Monitor quality scores: iteration 1, 2, 3",
        "Verify quality increases with each iteration",
        "Check that status='published' after 2-3 iterations",
        "Confirm final quality >= 0.85"
      ],
      "passes": false
    },
    {
      "id": "test-003",
      "category": "testing",
      "description": "AI slop detection forces quality below 0.50",
      "steps": [
        "Manually insert draft with 'delve' or 'leverage' in content",
        "Run quality validation on that content",
        "Verify quality_score < 0.50",
        "Check that critique has ai_slop_detected=true",
        "Verify found_keywords includes the forbidden phrase"
      ],
      "passes": false
    },
    {
      "id": "test-004",
      "category": "testing",
      "description": "System can generate 5 successful posts end-to-end",
      "steps": [
        "Run ralph_loop.py 5 times (manually or scripted)",
        "Verify all 5 posts have status='published'",
        "Calculate average quality score across 5 posts",
        "Verify average quality >= 0.85",
        "Check average iterations is 2-4 per post"
      ],
      "passes": false
    },
    {
      "id": "test-005",
      "category": "testing",
      "description": "No AI slop keywords in any published content",
      "steps": [
        "Query all blog_posts where status='published'",
        "For each post, run AI slop detection on content",
        "Verify no forbidden keywords found in published posts",
        "Document any edge cases (legitimate keyword use)",
        "Confirm zero AI slop in production content"
      ],
      "passes": false
    },
    {
      "id": "test-006",
      "category": "testing",
      "description": "API costs average below $0.25 per post",
      "steps": [
        "Query blog_content_drafts for recent blog posts",
        "Sum api_cost_cents for each blog_post_id",
        "Calculate average cost per post",
        "Verify average is below 25 cents",
        "Check that no single post exceeded $1.00 (cost limit)"
      ],
      "passes": false
    },
    {
      "id": "doc-001",
      "category": "documentation",
      "description": "README includes Phase 1 setup and usage instructions",
      "steps": [
        "Open README.md file",
        "Verify section exists for 'Phase 1 - Core Ralph Loop'",
        "Check that database setup steps are documented",
        "Verify environment variables are listed",
        "Confirm manual run command is provided: python -m ralph.core.ralph_loop"
      ],
      "passes": false
    },
    {
      "id": "doc-002",
      "category": "documentation",
      "description": ".env.example includes all Phase 1 environment variables",
      "steps": [
        "Open .env.example file",
        "Verify SUPABASE_URL and SUPABASE_KEY are present",
        "Verify ANTHROPIC_API_KEY and ANTHROPIC_MODEL are present",
        "Verify Ralph settings: RALPH_TIMEOUT_MINUTES, RALPH_QUALITY_THRESHOLD, RALPH_QUALITY_FLOOR, RALPH_COST_LIMIT_CENTS",
        "Check that placeholder values and comments explain each variable"
      ],
      "passes": false
    }
  ]
}
