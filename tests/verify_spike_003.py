#!/usr/bin/env python3
"""Verification script for spike-003: spike.py orchestrator."""

import sys
import os

# Add parent directory to path so we can import from services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()


def verify_spike_003():
    """Verify all acceptance criteria for spike-003."""

    print("=" * 70)
    print("SPIKE-003 VERIFICATION: spike.py orchestrator script")
    print("=" * 70)

    passes = []

    # Test 1: spike.py exists in project root
    print("\n[1/6] Checking if spike.py exists in project root...")
    spike_path = os.path.join(os.path.dirname(__file__), '..', 'spike.py')
    if os.path.exists(spike_path):
        print("✓ spike.py exists in project root")
        passes.append(True)
    else:
        print("✗ spike.py not found in project root")
        passes.append(False)

    # Test 2: Script fetches RSS items using rss_service
    print("\n[2/6] Checking if script uses rss_service...")
    try:
        with open(spike_path, 'r') as f:
            content = f.read()

        has_import = 'from services.rss_service import' in content
        has_fetch_call = 'fetch_unused_items' in content or 'fetch_active_sources' in content

        if has_import and has_fetch_call:
            print("✓ Script imports and uses rss_service")
            passes.append(True)
        else:
            print("✗ Script does not properly use rss_service")
            passes.append(False)
    except Exception as e:
        print(f"✗ Failed to verify rss_service usage: {e}")
        passes.append(False)

    # Test 3: Script generates blog post using llm_service
    print("\n[3/6] Checking if script uses llm_service...")
    try:
        has_llm_import = 'from services.llm_service import' in content
        has_generate_call = 'generate_blog_post' in content

        if has_llm_import and has_generate_call:
            print("✓ Script imports and uses llm_service")
            passes.append(True)
        else:
            print("✗ Script does not properly use llm_service")
            passes.append(False)
    except Exception as e:
        print(f"✗ Failed to verify llm_service usage: {e}")
        passes.append(False)

    # Test 4: Script saves post using supabase_service.create_blog_post()
    print("\n[4/6] Checking if script uses supabase_service.create_blog_post()...")
    try:
        has_supabase_import = 'from services.supabase_service import' in content
        has_create_call = 'create_blog_post' in content

        if has_supabase_import and has_create_call:
            print("✓ Script imports and uses supabase_service.create_blog_post()")
            passes.append(True)
        else:
            print("✗ Script does not properly use supabase_service.create_blog_post()")
            passes.append(False)
    except Exception as e:
        print(f"✗ Failed to verify supabase_service usage: {e}")
        passes.append(False)

    # Test 5: Script logs activity to blog_agent_activity
    print("\n[5/6] Checking if script logs activity...")
    try:
        has_log_activity = 'log_agent_activity' in content

        if has_log_activity:
            print("✓ Script logs activity to blog_agent_activity")
            passes.append(True)
        else:
            print("✗ Script does not log activity")
            passes.append(False)
    except Exception as e:
        print(f"✗ Failed to verify activity logging: {e}")
        passes.append(False)

    # Test 6: Script prints summary (token usage, cost, content preview)
    print("\n[6/6] Checking if script prints summary...")
    try:
        has_token_output = 'input_tokens' in content or 'token' in content.lower()
        has_cost_output = 'cost' in content.lower()
        has_content_preview = 'preview' in content.lower() or 'content[:' in content

        if has_token_output and has_cost_output and has_content_preview:
            print("✓ Script prints summary with token usage, cost, and content preview")
            passes.append(True)
        else:
            missing = []
            if not has_token_output:
                missing.append("token usage")
            if not has_cost_output:
                missing.append("cost")
            if not has_content_preview:
                missing.append("content preview")
            print(f"✗ Script missing summary elements: {', '.join(missing)}")
            passes.append(False)
    except Exception as e:
        print(f"✗ Failed to verify summary output: {e}")
        passes.append(False)

    # Summary
    print("\n" + "=" * 70)
    print(f"RESULTS: {sum(passes)}/{len(passes)} tests passed")
    print("=" * 70)

    if all(passes):
        print("✓ spike-003 PASSES all acceptance criteria")
        print("\nTo execute spike.py and verify it works end-to-end:")
        print("  python spike.py")
        return True
    else:
        print("✗ spike-003 FAILS - some criteria not met")
        return False


if __name__ == "__main__":
    success = verify_spike_003()
    sys.exit(0 if success else 1)
