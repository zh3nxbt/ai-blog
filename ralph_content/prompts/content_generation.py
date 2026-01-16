"""Prompt templates for Ralph content generation."""

INITIAL_DRAFT_PROMPT = """You are writing a blog post for MAS Precision Parts, a machine shop website.

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
  "source_urls": ["only URLs from sources that have them - no fabricated URLs"]
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
  "source_urls": ["only URLs from original sources - no fabricated URLs"]
}}

Do not include any text before or after the JSON object."""
