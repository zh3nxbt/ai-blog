#!/usr/bin/env python3
"""Verification script for ralph-010: ProductMarketingAgent.improve_content().

Acceptance Criteria:
1. agent.improve_content(content, critique) returns improved content string
2. Improved content differs from input content
3. Improved content addresses at least one critique point
4. Improved content length is within 20% of original
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class _FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class _FakeContentBlock:
    text: str


class _FakeMessages:
    def __init__(self, text: str) -> None:
        self._text = text

    def create(self, model: str, max_tokens: int, system: str | None, messages: list[dict[str, str]]):
        del model, max_tokens, system, messages
        return _FakeResponse(
            usage=_FakeUsage(input_tokens=90, output_tokens=180),
            content=[_FakeContentBlock(self._text)],
        )


@dataclass
class _FakeResponse:
    usage: _FakeUsage
    content: list[_FakeContentBlock]


class _FakeAnthropic:
    def __init__(self, text: str) -> None:
        self.messages = _FakeMessages(text=text)


def _build_original_content() -> str:
    words = ["machining"] * 1000
    return "## Draft\n\n" + " ".join(words)


def _build_fake_response() -> str:
    words = ["machining"] * 1000
    words.append("tooling")
    content = "## Improved Draft\n\n" + " ".join(words)
    payload = {
        "title": "Machining Changes Worth Watching",
        "excerpt": "Summary of updated machining insights.",
        "content_markdown": content,
        "source_urls": ["https://example.com/source-1"],
    }
    return json.dumps(payload)


def verify_ralph_010() -> bool:
    """Verify all acceptance criteria for ralph-010."""
    print("=" * 60)
    print("VERIFICATION: ralph-010 - ProductMarketingAgent.improve_content()")
    print("=" * 60)

    passed = 0
    total = 4

    from ralph_content.agents.product_marketing import ProductMarketingAgent

    original_content = _build_original_content()
    critique = "Add a tooling example and tighten the opening."

    fake_client = _FakeAnthropic(text=_build_fake_response())
    agent = ProductMarketingAgent(client=fake_client)

    # Test 1: improve_content returns string
    print("\n[1/4] Verifying improve_content() return type...")
    try:
        improved = agent.improve_content(original_content, critique)
        if isinstance(improved, str):
            print("✓ improve_content() returned a string")
            passed += 1
        else:
            print("✗ improve_content() did not return a string")
    except Exception as e:
        print(f"✗ improve_content() failed: {e}")
        return False

    # Test 2: improved content differs from input
    print("\n[2/4] Verifying improved content differs from input...")
    if improved != original_content:
        print("✓ Improved content differs from original")
        passed += 1
    else:
        print("✗ Improved content matches original")

    # Test 3: improved content addresses critique
    print("\n[3/4] Verifying improved content addresses critique...")
    if "tooling" in improved.lower():
        print("✓ Improved content references tooling")
        passed += 1
    else:
        print("✗ Improved content does not address critique")

    # Test 4: length within 20% of original
    print("\n[4/4] Verifying improved content length within 20%...")
    original_words = len(original_content.split())
    improved_words = len(improved.split())
    lower_bound = int(original_words * 0.8)
    upper_bound = int(original_words * 1.2)
    if lower_bound <= improved_words <= upper_bound:
        print(f"✓ Length within 20% ({improved_words} words)")
        passed += 1
    else:
        print(f"✗ Length out of range: {improved_words} words")

    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    if passed == total:
        print("\n✓ All acceptance criteria PASSED")
    else:
        print(f"\n✗ {total - passed} acceptance criteria FAILED")

    return passed == total


if __name__ == "__main__":
    try:
        success = verify_ralph_010()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
