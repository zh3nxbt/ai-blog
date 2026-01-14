"""Product marketing agent for Ralph content generation."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from ralph_content.agents.base_agent import BaseAgent
from ralph_content.prompts.content_generation import INITIAL_DRAFT_PROMPT


class ProductMarketingAgent(BaseAgent):
    """Generates manufacturing blog content from RSS items."""

    @property
    def agent_name(self) -> str:
        return "product-marketing"

    def generate_content(self, rss_items: List[Dict[str, Any]]) -> Tuple[str, str]:
        """Generate a blog post title and content from RSS items."""
        if not rss_items:
            raise ValueError("rss_items cannot be empty")

        sources_text = "\n\n".join(
            [
                f"**Source {i + 1}:** {item.get('title', 'No title')}\n"
                f"URL: {item.get('url', 'No URL')}\n"
                f"Summary: {item.get('summary', 'No summary')}"
                for i, item in enumerate(rss_items)
            ]
        )

        prompt = INITIAL_DRAFT_PROMPT.format(sources_text=sources_text)
        response_text = self._call_claude(messages=[{"role": "user", "content": prompt}])
        post_data = _parse_json_response(response_text)

        title = _get_required_string(post_data, "title")
        content = post_data.get("content_markdown")
        if content is None:
            content = post_data.get("content")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("content_markdown must be a non-empty string")

        return title, content


def _parse_json_response(response_text: str) -> Dict[str, Any]:
    """Parse Claude JSON response, handling optional code fences."""
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse JSON response: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object, got {type(payload).__name__}")

    return payload


def _get_required_string(payload: Dict[str, Any], key: str) -> str:
    """Return required string value or raise a clear error."""
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value
