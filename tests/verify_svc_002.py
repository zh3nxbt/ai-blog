#!/usr/bin/env python3
"""Verification script for svc-002: create_blog_post() function.

Acceptance Criteria:
1. Function create_blog_post(title, content, status) exists
2. Function returns UUID of created blog post
3. Created record has matching title, content, status
4. created_at timestamp is set automatically
5. slug is generated from title
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

from services.supabase_service import create_blog_post, get_supabase_client


def verify_svc_002() -> bool:
    """Verify all acceptance criteria for svc-002."""
    print("=" * 60)
    print("VERIFICATION: svc-002 - create_blog_post() function")
    print("=" * 60)

    passed = 0
    total = 5

    # Test 1: Function exists and is callable
    print("\n[1/5] Verifying create_blog_post() function exists...")
    try:
        from services.supabase_service import create_blog_post
        print("✓ Function exists and is importable")
        passed += 1
    except ImportError as e:
        print(f"✗ Failed to import function: {e}")
        return False

    # Test 2: Function returns UUID
    print("\n[2/5] Verifying function returns UUID...")
    test_title = "Test Blog Post for svc-002 Verification"
    test_content = "This is test content for verification purposes."
    test_status = "draft"

    try:
        blog_id = create_blog_post(test_title, test_content, test_status)
        if isinstance(blog_id, UUID):
            print(f"✓ Function returned UUID: {blog_id}")
            passed += 1
        else:
            print(f"✗ Function returned {type(blog_id)}, expected UUID")
    except Exception as e:
        print(f"✗ Failed to create blog post: {e}")
        return False

    # Test 3: Created record has matching fields
    print("\n[3/5] Verifying created record has matching title, content, status...")
    try:
        client = get_supabase_client()
        response = client.table("blog_posts").select("*").eq("id", str(blog_id)).execute()

        if not response.data or len(response.data) == 0:
            print("✗ Failed to retrieve created blog post")
        else:
            record = response.data[0]
            matches = []
            if record["title"] == test_title:
                matches.append("title")
            else:
                print(f"  ✗ Title mismatch: expected '{test_title}', got '{record['title']}'")

            if record["content"] == test_content:
                matches.append("content")
            else:
                print(f"  ✗ Content mismatch: expected '{test_content}', got '{record.get('content')}'")

            if record["status"] == test_status:
                matches.append("status")
            else:
                print(f"  ✗ Status mismatch: expected '{test_status}', got '{record['status']}'")

            if len(matches) == 3:
                print(f"✓ All fields match: {', '.join(matches)}")
                passed += 1
    except Exception as e:
        print(f"✗ Failed to verify record: {e}")

    # Test 4: created_at timestamp is set automatically
    print("\n[4/5] Verifying created_at timestamp is set automatically...")
    try:
        if "created_at" in record and record["created_at"]:
            print(f"✓ created_at timestamp: {record['created_at']}")
            passed += 1
        else:
            print("✗ created_at timestamp is missing or null")
    except Exception as e:
        print(f"✗ Failed to verify created_at: {e}")

    # Test 5: slug is generated from title
    print("\n[5/5] Verifying slug is generated from title...")
    try:
        expected_slug = "test-blog-post-for-svc-002-verification"
        if "slug" in record and record["slug"] == expected_slug:
            print(f"✓ Slug correctly generated: {record['slug']}")
            passed += 1
        else:
            print(f"✗ Slug mismatch: expected '{expected_slug}', got '{record.get('slug')}'")
    except Exception as e:
        print(f"✗ Failed to verify slug: {e}")

    # Cleanup: Delete test blog post
    print("\n[CLEANUP] Deleting test blog post...")
    try:
        client.table("blog_posts").delete().eq("id", str(blog_id)).execute()
        print("✓ Test blog post deleted")
    except Exception as e:
        print(f"⚠ Failed to delete test blog post: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    try:
        success = verify_svc_002()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
