"""Prompt templates for Ralph content generation."""

INITIAL_DRAFT_PROMPT = """You are writing a blog post for MAS Precision Parts, a precision machine shop based in Ontario, Canada.

Your task: Write a single blog post that synthesizes insights from the following mixed sources.

**About the sources:**
Sources come from different types: RSS news feeds, evergreen manufacturing topics, industry standards updates, and vendor announcements. Some sources have URLs, others (like evergreen topics) do not. This is intentional.

**Sources:**
{sources_text}

**Requirements:**
1. Write in markdown format
2. Length: 1000-2500 words
3. Include ## and ### headings for structure
4. Sound like a knowledgeable shop veteran, not a marketing bot
5. Be practical and industrial, not corporate or salesy
6. Use concrete examples over abstract concepts
7. Lead with interesting details, not context-setting
8. Short sentences. Active voice. No hedging.
9. Summarize sources; do not copy or quote large blocks
10. Include a short "Sources" section with links (only for sources that have URLs)
11. If sources are unrelated, choose a single coherent theme and ignore unrelated items
12. Only cite sources you actually used

**CRITICAL - Avoid AI slop language:**
- NEVER use: delve, unveil, landscape, realm, unlock, leverage, utilize, robust, streamline, cutting-edge,
  revolutionary, harness, paradigm, synergy
- NEVER use: "in today's fast-paced world", "it's important to note", "let's explore", "dive deep",
  "game-changer", "best practices"
- NEVER use em-dashes (—). Use commas or spaced regular dashes ( - ) instead
- DO NOT use formulaic structure every time
- DO NOT hedge or qualify unnecessarily

**CRITICAL - URL handling:**
- NEVER fabricate or invent URLs
- Only include URLs that are explicitly provided in the sources above
- If a source has no URL (marked as "No URL"), do not invent one
- The source_urls array must ONLY contain URLs that appear in the sources

**Output format:**
Return ONLY a JSON object with these exact keys:
{{
  "title": "Post title (5-10 words, engaging)",
  "excerpt": "Brief summary (2-3 sentences, 150-200 chars)",
  "content_markdown": "Full blog post content in markdown format",
  "source_urls": ["only URLs from sources that have them - no fabricated URLs"],
  "meta_description": "SEO description (1-2 sentences, 150-160 chars max)",
  "meta_keywords": "comma, separated, keywords, for, seo",
  "tags": ["Category Tag 1", "Category Tag 2"]
}}

Tags should be 1-3 relevant categories like: Industry News, Technology, Materials, Machining Tips, Business, Manufacturing Trends, Tooling, Quality Control.

Do not include any text before or after the JSON object."""


# Strategy-specific prompts

ANCHOR_CONTEXT_PROMPT = """You are writing a blog post for MAS Precision Parts, a precision machine shop based in Ontario, Canada.

**STRATEGY: ANCHOR + CONTEXT**
One source is the main story. Other sources provide supporting context.

**ANCHOR SOURCE (main story):**
{anchor_source}

**CONTEXT SOURCES (supporting material):**
{context_sources}

**Your approach:**
1. Lead with the anchor story - it's the headline
2. Use context sources to add depth, background, or related perspectives
3. Don't give equal weight to everything - the anchor dominates
4. Context sources support the main narrative, not compete with it

**Requirements:**
1. Write in markdown format
2. Length: 1000-2500 words
3. Include ## and ### headings for structure
4. Sound like a knowledgeable shop veteran, not a marketing bot
5. Be practical and industrial, not corporate or salesy
6. Short sentences. Active voice. No hedging.
7. Include a "Sources" section with links (only for sources that have URLs)
8. Only cite sources you actually used

**CRITICAL - Avoid AI slop language:**
- NEVER use: delve, unveil, landscape, realm, unlock, leverage, utilize, robust, streamline, cutting-edge,
  revolutionary, harness, paradigm, synergy
- NEVER use: "in today's fast-paced world", "it's important to note", "let's explore", "dive deep"
- NEVER use em-dashes (—). Use commas or spaced regular dashes ( - ) instead

**CRITICAL - URL handling:**
- NEVER fabricate or invent URLs
- Only include URLs explicitly provided in the sources above

**Output format:**
Return ONLY a JSON object with these exact keys:
{{
  "title": "Post title (5-10 words, engaging)",
  "excerpt": "Brief summary (2-3 sentences, 150-200 chars)",
  "content_markdown": "Full blog post content in markdown format",
  "source_urls": ["only URLs from sources that have them"]
}}

Do not include any text before or after the JSON object."""


THEMATIC_PROMPT = """You are writing a blog post for MAS Precision Parts, a precision machine shop based in Ontario, Canada.

**STRATEGY: THEMATIC CLUSTER**
Multiple sources share a common theme. Explore that theme from different angles.

**THEME:** {theme_name}

**RELATED SOURCES:**
{sources_text}

**Your approach:**
1. The theme is your throughline - everything connects to it
2. Each source offers a different angle on the same topic
3. Build a narrative that weaves these perspectives together
4. Find the "so what" - why does this theme matter to a machine shop?

**Requirements:**
1. Write in markdown format
2. Length: 1000-2500 words
3. Include ## and ### headings for structure
4. Sound like a knowledgeable shop veteran, not a marketing bot
5. Be practical and industrial, not corporate or salesy
6. Short sentences. Active voice. No hedging.
7. Include a "Sources" section with links (only for sources that have URLs)
8. Only cite sources you actually used

**CRITICAL - Avoid AI slop language:**
- NEVER use: delve, unveil, landscape, realm, unlock, leverage, utilize, robust, streamline, cutting-edge,
  revolutionary, harness, paradigm, synergy
- NEVER use: "in today's fast-paced world", "it's important to note", "let's explore", "dive deep"
- NEVER use em-dashes (—). Use commas or spaced regular dashes ( - ) instead

**CRITICAL - URL handling:**
- NEVER fabricate or invent URLs
- Only include URLs explicitly provided in the sources above

**Output format:**
Return ONLY a JSON object with these exact keys:
{{
  "title": "Post title (5-10 words, engaging)",
  "excerpt": "Brief summary (2-3 sentences, 150-200 chars)",
  "content_markdown": "Full blog post content in markdown format",
  "source_urls": ["only URLs from sources that have them"]
}}

Do not include any text before or after the JSON object."""


ANALYSIS_PROMPT = """You are writing a blog post for MAS Precision Parts, a precision machine shop based in Ontario, Canada.

**STRATEGY: SHOP FLOOR ANALYSIS**
Sources are varied, but you'll tie them together with practical shop-floor perspective.

**UNIFYING ANGLE:** {unifying_angle}

**SOURCES:**
{sources_text}

**Your approach:**
1. You're the experienced machinist making sense of scattered news
2. The unifying angle is your thesis - what ties this together for shop owners
3. Each source becomes evidence or example supporting your perspective
4. End with actionable takeaways - what should a shop owner do with this info?

**Requirements:**
1. Write in markdown format
2. Length: 1000-2500 words
3. Include ## and ### headings for structure
4. Sound like a knowledgeable shop veteran sharing hard-won wisdom
5. Be opinionated - take a stance, don't just summarize
6. Short sentences. Active voice. No hedging.
7. Include a "Sources" section with links (only for sources that have URLs)
8. Only cite sources you actually used

**CRITICAL - Avoid AI slop language:**
- NEVER use: delve, unveil, landscape, realm, unlock, leverage, utilize, robust, streamline, cutting-edge,
  revolutionary, harness, paradigm, synergy
- NEVER use: "in today's fast-paced world", "it's important to note", "let's explore", "dive deep"
- NEVER use em-dashes (—). Use commas or spaced regular dashes ( - ) instead

**CRITICAL - URL handling:**
- NEVER fabricate or invent URLs
- Only include URLs explicitly provided in the sources above

**Output format:**
Return ONLY a JSON object with these exact keys:
{{
  "title": "Post title (5-10 words, engaging)",
  "excerpt": "Brief summary (2-3 sentences, 150-200 chars)",
  "content_markdown": "Full blog post content in markdown format",
  "source_urls": ["only URLs from sources that have them"]
}}

Do not include any text before or after the JSON object."""


DEEP_DIVE_PROMPT = """You are writing a blog post for MAS Precision Parts, a precision machine shop based in Ontario, Canada.

**STRATEGY: DEEP DIVE**
Focus on one or two sources and explore them thoroughly.

**PRIMARY SOURCE(S):**
{sources_text}

**Your approach:**
1. Go deep, not broad - this is about thorough exploration
2. Extract every useful insight from the source material
3. Add your shop-floor context and practical implications
4. Connect to real-world applications a machinist would care about
5. If technical, explain it clearly without dumbing it down

**Requirements:**
1. Write in markdown format
2. Length: 1000-2500 words
3. Include ## and ### headings for structure
4. Sound like a knowledgeable shop veteran breaking down a topic
5. Be thorough but not padded - every paragraph should add value
6. Short sentences. Active voice. No hedging.
7. Include a "Sources" section with links (only for sources that have URLs)
8. Only cite sources you actually used

**CRITICAL - Avoid AI slop language:**
- NEVER use: delve, unveil, landscape, realm, unlock, leverage, utilize, robust, streamline, cutting-edge,
  revolutionary, harness, paradigm, synergy
- NEVER use: "in today's fast-paced world", "it's important to note", "let's explore", "dive deep"
- NEVER use em-dashes (—). Use commas or spaced regular dashes ( - ) instead

**CRITICAL - URL handling:**
- NEVER fabricate or invent URLs
- Only include URLs explicitly provided in the sources above

**Output format:**
Return ONLY a JSON object with these exact keys:
{{
  "title": "Post title (5-10 words, engaging)",
  "excerpt": "Brief summary (2-3 sentences, 150-200 chars)",
  "content_markdown": "Full blog post content in markdown format",
  "source_urls": ["only URLs from sources that have them"]
}}

Do not include any text before or after the JSON object."""


IMPROVEMENT_PROMPT_TEMPLATE = """You are revising a draft blog post for MAS Precision Parts.

Your task: Improve the draft using the critique below. Address the issues directly while preserving the core topic.

**Critique:**
{critique}

**Draft to Improve:**
{content_markdown}

**Requirements:**
1. Keep the length between 1000-2500 words
2. Keep ## and ### headings for structure
3. Maintain the shop-veteran tone: practical, direct, non-salesy
4. Keep facts grounded in the provided sources
5. Remove any AI slop language
6. Preserve or improve clarity and flow
7. If sources feel unrelated, keep one coherent theme and drop unrelated material
8. Only cite sources you actually used

**CRITICAL - URL handling:**
- NEVER fabricate or invent URLs
- Only include URLs that already appear in the draft's source section
- Do not add new URLs that were not in the original sources

**Output format:**
Return ONLY a JSON object with these exact keys:
{{
  "title": "Improved title (5-10 words, engaging)",
  "excerpt": "Brief summary (2-3 sentences, 150-200 chars)",
  "content_markdown": "Improved blog post content in markdown format",
  "source_urls": ["only URLs from original sources - no fabricated URLs"],
  "meta_description": "SEO description (1-2 sentences, 150-160 chars max)",
  "meta_keywords": "comma, separated, keywords, for, seo",
  "tags": ["Category Tag 1", "Category Tag 2"]
}}

Tags should be 1-3 relevant categories like: Industry News, Technology, Materials, Machining Tips, Business, Manufacturing Trends, Tooling, Quality Control.

Do not include any text before or after the JSON object."""
