#!/usr/bin/env python3
"""Verification script for ralph-008: BaseAgent token tracking.

Acceptance Criteria:
1. Concrete BaseAgent subclass can make Claude API call
2. After call, total_input_tokens > 0
3. After call, total_output_tokens > 0
4. get_total_tokens() returns (input_tokens, output_tokens) tuple
5. Multiple calls accumulate token counts
"""

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
    def __init__(self, input_tokens: int, output_tokens: int, text: str) -> None:
        self._input_tokens = input_tokens
        self._output_tokens = output_tokens
        self._text = text

    def create(self, model: str, max_tokens: int, system: str | None, messages: list[dict[str, str]]):
        del model, max_tokens, system, messages
        return _FakeResponse(
            usage=_FakeUsage(self._input_tokens, self._output_tokens),
            content=[_FakeContentBlock(self._text)],
        )


@dataclass
class _FakeResponse:
    usage: _FakeUsage
    content: list[_FakeContentBlock]


class _FakeAnthropic:
    def __init__(self, input_tokens: int, output_tokens: int, text: str) -> None:
        self.messages = _FakeMessages(input_tokens, output_tokens, text)


def verify_ralph_008() -> bool:
    """Verify all acceptance criteria for ralph-008."""
    print("=" * 60)
    print("VERIFICATION: ralph-008 - BaseAgent token tracking")
    print("=" * 60)

    passed = 0
    total = 5

    try:
        from ralph_content.agents.base_agent import BaseAgent
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    class _TestAgent(BaseAgent):
        @property
        def agent_name(self) -> str:
            return "test-agent"

    print("\n[1/5] Verifying concrete subclass can call Claude API...")
    try:
        fake_client = _FakeAnthropic(input_tokens=120, output_tokens=340, text="ok")
        agent = _TestAgent(client=fake_client)
        result = agent._call_claude(messages=[{"role": "user", "content": "ping"}])
        if result == "ok":
            print("✓ _call_claude() returned content")
            passed += 1
        else:
            print("✗ _call_claude() returned unexpected content")
    except Exception as e:
        print(f"✗ Call failed: {e}")

    print("\n[2/5] Verifying total_input_tokens > 0 after call...")
    try:
        if agent.total_input_tokens > 0:
            print(f"✓ total_input_tokens = {agent.total_input_tokens}")
            passed += 1
        else:
            print("✗ total_input_tokens not updated")
    except Exception as e:
        print(f"✗ Check failed: {e}")

    print("\n[3/5] Verifying total_output_tokens > 0 after call...")
    try:
        if agent.total_output_tokens > 0:
            print(f"✓ total_output_tokens = {agent.total_output_tokens}")
            passed += 1
        else:
            print("✗ total_output_tokens not updated")
    except Exception as e:
        print(f"✗ Check failed: {e}")

    print("\n[4/5] Verifying get_total_tokens() return type...")
    try:
        tokens = agent.get_total_tokens()
        if isinstance(tokens, tuple) and len(tokens) == 2:
            print(f"✓ get_total_tokens() returned tuple {tokens}")
            passed += 1
        else:
            print("✗ get_total_tokens() did not return tuple of length 2")
    except Exception as e:
        print(f"✗ Check failed: {e}")

    print("\n[5/5] Verifying multiple calls accumulate token counts...")
    try:
        fake_client.messages = _FakeMessages(input_tokens=10, output_tokens=20, text="ok")
        agent._call_claude(messages=[{"role": "user", "content": "ping again"}])
        if agent.total_input_tokens == 130 and agent.total_output_tokens == 360:
            print("✓ token counts accumulated across calls")
            passed += 1
        else:
            print(
                "✗ token counts did not accumulate correctly "
                f"(input={agent.total_input_tokens}, output={agent.total_output_tokens})"
            )
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
        success = verify_ralph_008()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
