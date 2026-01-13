#!/usr/bin/env python3
"""Verification script for spike-002: Claude API integration."""

import sys
import os

# Add parent directory to path so we can import from services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()


def verify_spike_002():
    """Verify all acceptance criteria for spike-002."""

    print("=" * 70)
    print("SPIKE-002 VERIFICATION: Claude API Integration")
    print("=" * 70)

    passes = []

    # Test 1: services/llm_service.py exists
    print("\n[1/6] Checking if services/llm_service.py exists...")
    try:
        import services.llm_service  # noqa: F401
        print("✓ services/llm_service.py exists")
        passes.append(True)
    except ImportError as e:
        print(f"✗ Failed to import services.llm_service: {e}")
        passes.append(False)

    # Test 2: Function generate_blog_post(rss_items) accepts list of RSS items
    print("\n[2/6] Checking if generate_blog_post() accepts list of RSS items...")
    try:
        from services.llm_service import generate_blog_post

        # Test with sample RSS items
        sample_items = [
            {
                "title": "New CNC Technology Improves Precision",
                "url": "https://example.com/cnc-tech",
                "summary": "A new CNC technology has been developed that improves precision by 15%."
            },
            {
                "title": "Understanding Surface Finishes",
                "url": "https://example.com/surface-finish",
                "summary": "Surface finish requirements vary by application. Here's what you need to know."
            },
            {
                "title": "Material Selection for Machine Parts",
                "url": "https://example.com/materials",
                "summary": "Choosing the right material is critical for part performance and longevity."
            }
        ]

        # Make actual API call
        result, input_tokens, output_tokens = generate_blog_post(sample_items)

        print("✓ generate_blog_post() accepts list of RSS items")
        print(f"  Input tokens: {input_tokens}")
        print(f"  Output tokens: {output_tokens}")
        passes.append(True)

    except Exception as e:
        print(f"✗ Failed to call generate_blog_post(): {e}")
        passes.append(False)
        result = None
        input_tokens = 0
        output_tokens = 0

    # Test 3: Function calls Claude API using Anthropic SDK
    print("\n[3/6] Checking if function calls Claude API...")
    if result is not None:
        print("✓ Function successfully called Claude API (confirmed by receiving response)")
        passes.append(True)
    else:
        print("✗ Function did not return a valid response from Claude API")
        passes.append(False)

    # Test 4: Function returns dict with keys: title, excerpt, content
    print("\n[4/6] Checking if function returns dict with required keys...")
    if result is not None:
        required_keys = ["title", "excerpt", "content"]
        has_all_keys = all(key in result for key in required_keys)

        if has_all_keys:
            print(f"✓ Function returns dict with all required keys: {required_keys}")
            print(f"  Title: {result['title'][:60]}...")
            print(f"  Excerpt: {result['excerpt'][:80]}...")
            print(f"  Content length: {len(result['content'])} characters")
            passes.append(True)
        else:
            missing = [key for key in required_keys if key not in result]
            print(f"✗ Function missing required keys: {missing}")
            passes.append(False)
    else:
        print("✗ Cannot verify keys (no result from previous test)")
        passes.append(False)

    # Test 5: Token usage tracked (input_tokens + output_tokens)
    print("\n[5/6] Checking if token usage is tracked...")
    if input_tokens > 0 and output_tokens > 0:
        print(f"✓ Token usage tracked: {input_tokens} input + {output_tokens} output = {input_tokens + output_tokens} total")
        passes.append(True)
    else:
        print(f"✗ Token usage not tracked properly: input={input_tokens}, output={output_tokens}")
        passes.append(False)

    # Test 6: Cost calculated based on token pricing
    print("\n[6/6] Checking if cost calculation works...")
    try:
        from services.llm_service import calculate_api_cost  # noqa: E402
        cost_cents = calculate_api_cost(input_tokens, output_tokens)
        cost_dollars = cost_cents / 100

        # Verify cost is reasonable (should be a few cents for typical usage)
        if 0 < cost_cents < 500:  # Between $0.01 and $5.00
            print(f"✓ Cost calculated: {cost_cents} cents (${cost_dollars:.2f})")
            passes.append(True)
        else:
            print(f"✗ Cost seems unreasonable: {cost_cents} cents")
            passes.append(False)
    except Exception as e:
        print(f"✗ Failed to calculate cost: {e}")
        passes.append(False)

    # Summary
    print("\n" + "=" * 70)
    print(f"RESULTS: {sum(passes)}/{len(passes)} tests passed")
    print("=" * 70)

    if all(passes):
        print("✓ spike-002 PASSES all acceptance criteria")
        return True
    else:
        print("✗ spike-002 FAILS - some criteria not met")
        return False


if __name__ == "__main__":
    success = verify_spike_002()
    sys.exit(0 if success else 1)
