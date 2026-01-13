#!/usr/bin/env python3
"""Verification script for svc-003: save_draft_iteration() function.

Acceptance Criteria:
1. Function save_draft_iteration(blog_id, iteration, content, score, critique) exists
2. Function inserts row into blog_content_drafts
3. iteration_number matches input parameter
4. quality_score matches input parameter
5. Duplicate iteration_number for same blog_id raises error
"""

import os
import sys
from pathlib import Path
from uuid import UUID
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from services.supabase_service import (
    create_blog_post,
    save_draft_iteration,
    get_supabase_client
)


def verify_svc_003() -> bool:
    """Verify all acceptance criteria for svc-003."""
    print("=" * 60)
    print("VERIFICATION: svc-003 - save_draft_iteration() function")
    print("=" * 60)

    passed = 0
    total = 5

    # Create a test blog post first
    print("\n[SETUP] Creating test blog post...")
    test_blog_id = None
    draft_id = None

    try:
        test_blog_id = create_blog_post(
            title="Test Post for svc-003",
            content="Test content",
            status="draft"
        )
        print(f"✓ Test blog post created: {test_blog_id}")
    except Exception as e:
        print(f"✗ Failed to create test blog post: {e}")
        return False

    # Test 1: Function exists and is callable
    print("\n[1/5] Verifying save_draft_iteration() function exists...")
    try:
        from services.supabase_service import save_draft_iteration
        print("✓ Function exists and is importable")
        passed += 1
    except ImportError as e:
        print(f"✗ Failed to import function: {e}")
        return False

    # Test 2: Function inserts row into blog_content_drafts
    print("\n[2/5] Verifying function inserts row into blog_content_drafts...")
    test_iteration = 1
    test_title = "Test Draft Title"
    test_content = "This is test draft content for iteration 1."
    test_score = 0.75
    test_critique = {
        "quality_score": 0.75,
        "ai_slop_detected": False,
        "improvements": ["Add more technical details"]
    }
    test_cost = 15

    try:
        draft_id = save_draft_iteration(
            blog_post_id=test_blog_id,
            iteration_number=test_iteration,
            title=test_title,
            content=test_content,
            quality_score=test_score,
            critique=test_critique,
            api_cost_cents=test_cost
        )
        if isinstance(draft_id, UUID):
            print(f"✓ Function returned UUID: {draft_id}")
            passed += 1
        else:
            print(f"✗ Function returned {type(draft_id)}, expected UUID")
    except Exception as e:
        print(f"✗ Failed to save draft iteration: {e}")
        # Cleanup before returning
        cleanup(test_blog_id, None)
        return False

    # Test 3: iteration_number matches input parameter
    print("\n[3/5] Verifying iteration_number matches input parameter...")
    try:
        client = get_supabase_client()
        response = client.table("blog_content_drafts").select("*").eq("id", str(draft_id)).execute()

        if not response.data or len(response.data) == 0:
            print("✗ Failed to retrieve created draft iteration")
        else:
            record = response.data[0]
            if record["iteration_number"] == test_iteration:
                print(f"✓ iteration_number matches: {record['iteration_number']}")
                passed += 1
            else:
                print(f"✗ iteration_number mismatch: expected {test_iteration}, got {record['iteration_number']}")
    except Exception as e:
        print(f"✗ Failed to verify iteration_number: {e}")

    # Test 4: quality_score matches input parameter
    print("\n[4/5] Verifying quality_score matches input parameter...")
    try:
        if abs(float(record["quality_score"]) - test_score) < 0.01:
            print(f"✓ quality_score matches: {record['quality_score']}")
            passed += 1
        else:
            print(f"✗ quality_score mismatch: expected {test_score}, got {record['quality_score']}")
    except Exception as e:
        print(f"✗ Failed to verify quality_score: {e}")

    # Test 5: Duplicate iteration_number for same blog_id raises error
    print("\n[5/5] Verifying duplicate iteration_number raises error...")
    try:
        # Try to insert the same iteration_number again
        save_draft_iteration(
            blog_post_id=test_blog_id,
            iteration_number=test_iteration,
            title="Duplicate Draft",
            content="This should fail",
            quality_score=0.80,
            critique={"test": "duplicate"},
            api_cost_cents=10
        )
        print("✗ Function allowed duplicate iteration_number (should have raised error)")
    except Exception as e:
        # We expect a constraint violation error here
        error_str = str(e).lower()
        if "duplicate" in error_str or "unique" in error_str or "constraint" in error_str or "23505" in str(e):
            print(f"✓ Duplicate correctly rejected: {e}")
            passed += 1
        else:
            # Unrelated error (network, auth, etc.) - doesn't verify the constraint
            print(f"✗ Unexpected error (not a constraint violation): {e}")
            # Do NOT increment passed - this doesn't prove the UNIQUE constraint exists

    # Cleanup
    cleanup(test_blog_id, draft_id)

    # Summary
    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    return passed == total


def cleanup(blog_id: UUID, draft_id: UUID):
    """Clean up test data."""
    print("\n[CLEANUP] Deleting test data...")
    try:
        client = get_supabase_client()

        # Delete draft iterations (will cascade due to foreign key)
        if draft_id:
            try:
                client.table("blog_content_drafts").delete().eq("id", str(draft_id)).execute()
                print("✓ Test draft iteration deleted")
            except Exception as e:
                print(f"⚠ Failed to delete draft iteration: {e}")

        # Delete test blog post
        if blog_id:
            try:
                client.table("blog_posts").delete().eq("id", str(blog_id)).execute()
                print("✓ Test blog post deleted")
            except Exception as e:
                print(f"⚠ Failed to delete test blog post: {e}")

    except Exception as e:
        print(f"⚠ Cleanup failed: {e}")


if __name__ == "__main__":
    try:
        success = verify_svc_003()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
