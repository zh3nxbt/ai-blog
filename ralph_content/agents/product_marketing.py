"""Product marketing agent for Ralph content generation."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from ralph_content.agents.base_agent import BaseAgent
from ralph_content.prompts.content_generation import (
    ANCHOR_CONTEXT_PROMPT,
    ANALYSIS_PROMPT,
    DEEP_DIVE_PROMPT,
    IMPROVEMENT_PROMPT_TEMPLATE,
    INITIAL_DRAFT_PROMPT,
    THEMATIC_PROMPT,
)
from ralph_content.prompts.content_strategy import ContentStrategy


class ProductMarketingAgent(BaseAgent):
    """Generates manufacturing blog content from RSS items."""

    @property
    def agent_name(self) -> str:
        return "product-marketing"

    def generate_content(
        self,
        rss_items: List[Dict[str, Any]],
        strategy: Optional[ContentStrategy] = None,
        strategy_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a blog post from source items.

        Args:
            rss_items: Source items (RSS, evergreen, etc.)
            strategy: Content strategy to use (if None, uses default prompt)
            strategy_context: Additional context for strategy-specific prompts:
                - anchor_index: int (for ANCHOR_CONTEXT)
                - theme_name: str (for THEMATIC)
                - unifying_angle: str (for ANALYSIS)

        Returns:
            Dict with keys: title, content_markdown, meta_description, meta_keywords, tags
        """
        if not rss_items:
            raise ValueError("rss_items cannot be empty")

        strategy_context = strategy_context or {}
        prompt = self._build_strategy_prompt(rss_items, strategy, strategy_context)

        response_text = self._call_claude(messages=[{"role": "user", "content": prompt}])
        post_data = _parse_json_response(response_text)

        title = _get_required_string(post_data, "title")
        content = post_data.get("content_markdown")
        if content is None:
            content = post_data.get("content")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("content_markdown must be a non-empty string")

        return {
            "title": title,
            "content_markdown": content,
            "meta_description": post_data.get("meta_description", ""),
            "meta_keywords": post_data.get("meta_keywords", ""),
            "tags": post_data.get("tags", []),
        }

    def _build_strategy_prompt(
        self,
        items: List[Dict[str, Any]],
        strategy: Optional[ContentStrategy],
        context: Dict[str, Any],
    ) -> str:
        """Build the appropriate prompt based on content strategy."""
        if strategy is None:
            # Default behavior - use original prompt
            sources_text = "\n\n".join(
                [_format_source_item(i + 1, item) for i, item in enumerate(items)]
            )
            return INITIAL_DRAFT_PROMPT.format(sources_text=sources_text)

        if strategy == ContentStrategy.ANCHOR_CONTEXT:
            anchor_index = context.get("anchor_index", 0)
            anchor_item = items[anchor_index] if anchor_index < len(items) else items[0]
            context_items = [item for i, item in enumerate(items) if i != anchor_index]

            anchor_source = _format_source_item(1, anchor_item)
            context_sources = "\n\n".join(
                [_format_source_item(i + 2, item) for i, item in enumerate(context_items)]
            ) or "No additional context sources."

            return ANCHOR_CONTEXT_PROMPT.format(
                anchor_source=anchor_source,
                context_sources=context_sources,
            )

        elif strategy == ContentStrategy.THEMATIC:
            theme_name = context.get("theme_name", "Manufacturing")
            sources_text = "\n\n".join(
                [_format_source_item(i + 1, item) for i, item in enumerate(items)]
            )
            return THEMATIC_PROMPT.format(
                theme_name=theme_name,
                sources_text=sources_text,
            )

        elif strategy == ContentStrategy.ANALYSIS:
            unifying_angle = context.get(
                "unifying_angle",
                "What these developments mean for machine shop operations"
            )
            sources_text = "\n\n".join(
                [_format_source_item(i + 1, item) for i, item in enumerate(items)]
            )
            return ANALYSIS_PROMPT.format(
                unifying_angle=unifying_angle,
                sources_text=sources_text,
            )

        elif strategy == ContentStrategy.DEEP_DIVE:
            sources_text = "\n\n".join(
                [_format_source_item(i + 1, item) for i, item in enumerate(items)]
            )
            return DEEP_DIVE_PROMPT.format(sources_text=sources_text)

        else:
            # Fallback to default
            sources_text = "\n\n".join(
                [_format_source_item(i + 1, item) for i, item in enumerate(items)]
            )
            return INITIAL_DRAFT_PROMPT.format(sources_text=sources_text)

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
