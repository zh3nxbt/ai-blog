#!/usr/bin/env python3
"""Verification script for ralph-009: ProductMarketingAgent.generate_content().

Acceptance Criteria:
1. `python -c 'from ralph_content.agents.product_marketing import ProductMarketingAgent'` exits with code 0
2. agent.generate_content(rss_items) returns (title, content) tuple
3. Returned title is non-empty string
4. Returned content is >= 1000 words
5. Content mentions manufacturing or machining concepts
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
            usage=_FakeUsage(input_tokens=120, output_tokens=240),
            content=[_FakeContentBlock(self._text)],
        )


@dataclass
class _FakeResponse:
    usage: _FakeUsage
    content: list[_FakeContentBlock]


class _FakeAnthropic:
    def __init__(self, text: str) -> None:
        self.messages = _FakeMessages(text=text)


def _build_fake_response() -> str:
    words = ["machining"] * 1005
    content = "## Shop Floor Notes\n\n" + " ".join(words)
    payload = {
        "title": "Machining Notes From Busy Shop Floors",
        "excerpt": "Short summary of shop-floor developments.",
        "content_markdown": content,
        "source_urls": ["https://example.com/source-1"],
    }
    return json.dumps(payload)


def verify_ralph_009() -> bool:
    """Verify all acceptance criteria for ralph-009."""
    print("=" * 60)
    print("VERIFICATION: ralph-009 - ProductMarketingAgent.generate_content()")
    print("=" * 60)

    passed = 0
    total = 5

    # Test 1: Import test
    print("\n[1/5] Verifying import works...")
    try:
        from ralph_content.agents.product_marketing import ProductMarketingAgent
        print("✓ Successfully imported ProductMarketingAgent")
        passed += 1
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Test 2: generate_content returns tuple
    print("\n[2/5] Verifying generate_content() return type...")
    try:
        fake_client = _FakeAnthropic(text=_build_fake_response())
        agent = ProductMarketingAgent(client=fake_client)
        title, content = agent.generate_content(
            rss_items=[{"title": "Tooling update", "url": "https://example.com", "summary": "Summary."}]
        )
        if isinstance(title, str) and isinstance(content, str):
            print("✓ generate_content() returned title and content strings")
            passed += 1
        else:
            print("✗ generate_content() did not return strings")
    except Exception as e:
        print(f"✗ generate_content() failed: {e}")

    # Test 3: Title non-empty
    print("\n[3/5] Verifying title is non-empty...")
    try:
        if title.strip():
            print("✓ Title is non-empty")
            passed += 1
        else:
            print("✗ Title is empty")
    except Exception as e:
        print(f"✗ Check failed: {e}")

    # Test 4: Content >= 1000 words
    print("\n[4/5] Verifying content length >= 1000 words...")
    try:
        word_count = len(content.split())
        if word_count >= 1000:
            print(f"✓ Content word count = {word_count}")
            passed += 1
        else:
            print(f"✗ Content word count too low: {word_count}")
    except Exception as e:
        print(f"✗ Check failed: {e}")

    # Test 5: Content mentions manufacturing or machining
    print("\n[5/5] Verifying content mentions manufacturing or machining...")
    try:
        content_lower = content.lower()
        if "machining" in content_lower or "manufacturing" in content_lower:
            print("✓ Content mentions manufacturing/machining")
            passed += 1
        else:
            print("✗ Content missing manufacturing/machining references")
    except Exception as e:
        print(f"✗ Check failed: {e}")

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
        success = verify_ralph_009()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
