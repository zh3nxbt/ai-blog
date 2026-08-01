"""Markdown to HTML rendering helpers."""

from __future__ import annotations

import markdown


def markdown_to_html(content_markdown: str) -> str:
    """Render markdown content to HTML for storage/display."""
    if not isinstance(content_markdown, str) or not content_markdown.strip():
        raise ValueError("content_markdown must be a non-empty string")

    return markdown.markdown(content_markdown, extensions=["extra"])
