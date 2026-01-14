"""Claude API integration for blog post generation."""

import json
from typing import Dict, Any, List, Tuple
from anthropic import Anthropic

from config import settings
from ralph.core.api_cost import calculate_api_cost


def generate_blog_post(rss_items: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], int, int]:
    """
    Generate a blog post from RSS items using Claude API.

    This is a minimal single-pass implementation for spike.py.
    Does not include iterative refinement or quality validation.

    Args:
        rss_items: List of RSS item dictionaries with title, url, summary fields

    Returns:
        Tuple of (post_data, input_tokens, output_tokens) where:
            - post_data: Dict with keys: title, excerpt, content
            - input_tokens: Number of input tokens used
            - output_tokens: Number of output tokens used

    Raises:
        ValueError: If API call fails or response format is invalid
        Exception: If RSS items list is empty
    """
    if not rss_items:
        raise Exception("RSS items list cannot be empty")

    # Initialize Anthropic client
    client = Anthropic(api_key=settings.anthropic_api_key)

    # Build context from RSS items
    sources_text = "\n\n".join([
        f"**Source {i+1}:** {item.get('title', 'No title')}\n"
        f"URL: {item.get('url', 'No URL')}\n"
        f"Summary: {item.get('summary', 'No summary')}"
        for i, item in enumerate(rss_items)
    ])

    # Prompt for blog post generation
    prompt = f"""You are writing a blog post for MAS Precision Parts, a machine shop website.

Your task: Write a single blog post that synthesizes insights from the following manufacturing industry sources.

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

**CRITICAL - Avoid AI slop language:**
- NEVER use: delve, unveil, landscape, realm, unlock, leverage, utilize, robust, streamline, cutting-edge, revolutionary, harness, paradigm, synergy
- NEVER use: "in today's fast-paced world", "it's important to note", "let's explore", "dive deep", "game-changer"
- DO NOT use formulaic structure every time
- DO NOT hedge or qualify unnecessarily

**Output format:**
Return ONLY a JSON object with these exact keys:
{{
  "title": "Post title (5-10 words, engaging)",
  "excerpt": "Brief summary (2-3 sentences, 150-200 chars)",
  "content": "Full blog post content in markdown format"
}}

Do not include any text before or after the JSON object."""

    # Call Claude API
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Extract token usage
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    # Parse response
    response_text = response.content[0].text.strip()

    # Try to extract JSON if wrapped in markdown code block
    if response_text.startswith("```"):
        # Remove code block markers
        lines = response_text.split("\n")
        # Remove first line (```json or ```)
        lines = lines[1:]
        # Remove last line (```) if present and non-empty
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response_text = "\n".join(lines)

    try:
        post_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response from Claude API: {e}\nResponse: {response_text[:500]}")

    # Validate response is a dict (json.loads can return list, string, number, bool, or null)
    if not isinstance(post_data, dict):
        raise ValueError(f"Expected JSON object, got {type(post_data).__name__}: {str(post_data)[:200]}")

    # Validate required keys
    required_keys = ["title", "excerpt", "content"]
    missing_keys = [key for key in required_keys if key not in post_data]
    if missing_keys:
        raise ValueError(f"Response missing required keys: {missing_keys}")

    # Validate non-empty values
    for key in required_keys:
        if not post_data[key] or not isinstance(post_data[key], str):
            raise ValueError(f"Key '{key}' must be a non-empty string")

    return post_data, input_tokens, output_tokens

