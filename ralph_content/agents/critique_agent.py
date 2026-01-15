"""Critique agent for evaluating blog post quality."""

from __future__ import annotations

import json
from typing import Any, Dict

from ralph_content.agents.base_agent import BaseAgent
from ralph_content.prompts.critique import AI_SLOP_KEYWORDS, CRITIQUE_PROMPT_TEMPLATE


class CritiqueAgent(BaseAgent):
    """Evaluates blog post quality and provides improvement feedback."""

    @property
    def agent_name(self) -> str:
        return "critique"

    def evaluate_content(
        self, title: str, content: str, current_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Evaluate a blog post draft and return structured critique.

        Args:
            title: Blog post title
            content: Blog post content in markdown
            current_score: Previous quality score (for context)

        Returns:
            Dict containing quality_score, ai_slop_detected, main_issues,
            improvements, and strengths
        """
        if not title or not isinstance(title, str):
            raise ValueError("title must be a non-empty string")
        if not content or not isinstance(content, str):
            raise ValueError("content must be a non-empty string")

        ai_slop_list = "\n".join(f"- {kw}" for kw in AI_SLOP_KEYWORDS)

        prompt = CRITIQUE_PROMPT_TEMPLATE.format(
            title=title,
            content=content,
            current_score=current_score,
            ai_slop_list=ai_slop_list,
        )

        response_text = self._call_claude(messages=[{"role": "user", "content": prompt}])
        critique = _parse_critique_response(response_text)

        return critique


def _parse_critique_response(response_text: str) -> Dict[str, Any]:
    """Parse Claude critique response, handling optional code fences."""
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
        raise ValueError(f"Failed to parse critique JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object, got {type(payload).__name__}")

    # Validate required fields
    required_fields = ["quality_score", "ai_slop_detected"]
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    # Ensure quality_score is a valid float
    score = payload.get("quality_score")
    if not isinstance(score, (int, float)) or score < 0 or score > 1:
        raise ValueError(f"quality_score must be between 0.0 and 1.0, got {score}")

    return payload
