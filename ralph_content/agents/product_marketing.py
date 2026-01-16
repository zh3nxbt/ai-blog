"""Product marketing agent for Ralph content generation."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from ralph_content.agents.base_agent import BaseAgent
from ralph_content.prompts.content_generation import (
    IMPROVEMENT_PROMPT_TEMPLATE,
    INITIAL_DRAFT_PROMPT,
)


class ProductMarketingAgent(BaseAgent):
    """Generates manufacturing blog content from RSS items."""

    @property
    def agent_name(self) -> str:
        return "product-marketing"

    def generate_content(self, rss_items: List[Dict[str, Any]]) -> Tuple[str, str]:
        """Generate a blog post title and content from source items (RSS, evergreen, etc.)."""
        if not rss_items:
            raise ValueError("rss_items cannot be empty")

        sources_text = "\n\n".join(
            [_format_source_item(i + 1, item) for i, item in enumerate(rss_items)]
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

    def improve_content(self, content: str, critique: str | Dict[str, Any]) -> str:
        """Improve a draft blog post using critique feedback."""
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be a non-empty string")

        critique_text = _format_critique(critique)
        prompt = IMPROVEMENT_PROMPT_TEMPLATE.format(
            critique=critique_text,
            content_markdown=content,
        )
        response_text = self._call_claude(messages=[{"role": "user", "content": prompt}])
        post_data = _parse_json_response(response_text)

        improved = post_data.get("content_markdown")
        if improved is None:
            improved = post_data.get("content")

        if not isinstance(improved, str) or not improved.strip():
            raise ValueError("content_markdown must be a non-empty string")

        return improved


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


def _format_critique(critique: str | Dict[str, Any]) -> str:
    """Normalize critique input for prompt injection."""
    if isinstance(critique, str):
        if not critique.strip():
            raise ValueError("critique must be a non-empty string")
        return critique.strip()
    if isinstance(critique, dict):
        if not critique:
            raise ValueError("critique cannot be empty")
        return json.dumps(critique, indent=2, sort_keys=True)
    raise ValueError("critique must be a string or dict")


def _format_source_item(index: int, item: Dict[str, Any]) -> str:
    """Format a source item for prompt injection, handling mixed source types."""
    source_type = item.get("source_type", "rss")
    title = item.get("title", "No title")
    summary = item.get("summary", "No summary")
    url = item.get("url")

    # Format source type label for clarity
    type_labels = {
        "rss": "RSS Feed",
        "evergreen": "Evergreen Topic",
        "standards": "Standards/Gov",
        "vendor": "Vendor Update",
        "internal": "Internal",
    }
    type_label = type_labels.get(source_type, source_type.capitalize())

    lines = [f"**Source {index} ({type_label}):** {title}"]

    # Only include URL line if URL exists and is not empty
    if url and url.strip() and url.lower() != "no url":
        lines.append(f"URL: {url}")
    else:
        lines.append("URL: No URL available (do not fabricate)")

    lines.append(f"Summary: {summary}")

    return "\n".join(lines)
