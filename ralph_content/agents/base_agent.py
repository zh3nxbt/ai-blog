"""Base agent abstractions for Claude-driven workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from anthropic import Anthropic

from config import settings


class BaseAgent(ABC):
    """Abstract base class for Claude-backed agents with token tracking."""

    def __init__(self, model: str | None = None, client: Anthropic | None = None) -> None:
        self.model = model or settings.anthropic_model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self._client = client or Anthropic(api_key=settings.anthropic_api_key)

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Human-readable agent name for logging."""

    def _call_claude(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> str:
        """Call Claude API and track token usage."""
        if not messages:
            raise ValueError("messages cannot be empty")

        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system is not None:
            if isinstance(system, str):
                payload["system"] = [{"type": "text", "text": system}]
            elif isinstance(system, list):
                payload["system"] = system
            else:
                raise ValueError("system must be a string, list, or None")

        response = self._client.messages.create(**payload)

        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens

        content = response.content[0].text
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Claude response content was empty")

        return content

    def get_total_tokens(self) -> Tuple[int, int]:
        """Return cumulative input and output token usage."""
        return self.total_input_tokens, self.total_output_tokens
