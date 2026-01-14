"""Critique prompt constants."""

AI_SLOP_KEYWORDS = [
    # Single words
    "delve",
    "unveil",
    "landscape",
    "realm",
    "unlock",
    "leverage",
    "utilize",
    "robust",
    "streamline",
    "cutting-edge",
    "revolutionary",
    "harness",
    "paradigm",
    "synergy",
    "game-changer",
    # Phrases (matched with flexible whitespace)
    "in today's fast-paced world",
    "it's important to note",
    "let's explore",
    "dive deep",
    "best practices",
]

CRITIQUE_PROMPT_TEMPLATE = """You are an expert content quality critic specializing in manufacturing industry blog posts.

Your task: Evaluate this blog post draft for MAS Precision Parts (a precision manufacturing company).

**DRAFT:**
Title: {title}
Content:
{content}

**CURRENT QUALITY SCORE:** {current_score}

**BRAND VOICE REQUIREMENTS:**
- Practical, direct, and technical (not salesy)
- Write like a shop veteran, not a marketing bot
- Use specific details and examples, avoid fluff

**AI SLOP DETECTION (CRITICAL):**
These phrases are strictly forbidden:
{ai_slop_list}

If any appear, quality score must be < 0.50.

**EVALUATION CRITERIA:**
1. Manufacturing relevance and technical accuracy
2. Brand voice alignment
3. AI slop detection
4. Structure and readability (headings, flow, length)
5. Practical value for shop owners and engineers

**OUTPUT REQUIRED (JSON ONLY):**
{{
  "quality_score": 0.0-1.0,
  "ai_slop_detected": true|false,
  "ai_slop_found": ["phrase 1", "phrase 2"] or [],
  "main_issues": ["issue 1", "issue 2"],
  "improvements": [
    {{
      "section": "introduction|body|conclusion",
      "problem": "what's wrong",
      "fix": "how to improve"
    }}
  ],
  "strengths": ["strength 1", "strength 2"]
}}

Be constructively critical. The goal is iterative improvement.
"""
