#!/usr/bin/env python3
"""Verification script for svc-004: log_agent_activity() function.

Acceptance Criteria:
1. Function log_agent_activity(agent, activity_type, success, metadata) exists
2. Function inserts row into blog_agent_activity
3. agent_name matches input parameter
4. activity_type matches input parameter
5. metadata stored as JSONB
"""

import sys
from pathlib import Path
from uuid import UUID
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from services.supabase_service import log_agent_activity, get_supabase_client  # noqa: E402


def verify_svc_004() -> bool:
    """Verify all acceptance criteria for svc-004."""
    print("=" * 60)
    print("VERIFICATION: svc-004 - log_agent_activity() function")
    print("=" * 60)

    passed = 0
    total = 5
    activity_id = None

    # Test 1: Function exists and has correct signature
    print("\n[1/5] Verifying log_agent_activity() function exists...")
    try:
        import inspect
        sig = inspect.signature(log_agent_activity)
        params = list(sig.parameters.keys())

        # Check required parameters exist
        required_params = ["agent_name", "activity_type", "success", "metadata"]
        has_all_params = all(p in params for p in required_params)

        if has_all_params:
            print(f"✓ Function exists with parameters: {params}")
            passed += 1
        else:
            print(f"✗ Missing parameters. Found: {params}, expected: {required_params}")
    except ImportError as e:
        print(f"✗ Failed to import function: {e}")
        return False

    # Test 2: Function inserts row into blog_agent_activity
    print("\n[2/5] Verifying function inserts row into blog_agent_activity...")
    test_agent = "TestAgent"
    test_activity_type = "test_verification"
    test_success = True
    test_metadata = {
        "test_key": "test_value",
        "tokens": 1000,
        "cost_cents": 5
    }

    try:
        activity_id = log_agent_activity(
            agent_name=test_agent,
            activity_type=test_activity_type,
            success=test_success,
            metadata=test_metadata
        )
        if isinstance(activity_id, UUID):
            print(f"✓ Function returned UUID: {activity_id}")
            passed += 1
        else:
            print(f"✗ Function returned {type(activity_id)}, expected UUID")
    except Exception as e:
        print(f"✗ Failed to log agent activity: {e}")
        return False

    # Test 3: agent_name matches input parameter
    print("\n[3/5] Verifying agent_name matches input parameter...")
    try:
        client = get_supabase_client()
        response = client.table("blog_agent_activity").select("*").eq("id", str(activity_id)).execute()

        if not response.data or len(response.data) == 0:
            print("✗ Failed to retrieve created activity log")
        else:
            record = response.data[0]
            if record["agent_name"] == test_agent:
                print(f"✓ agent_name matches: {record['agent_name']}")
                passed += 1
            else:
                print(f"✗ agent_name mismatch: expected {test_agent}, got {record['agent_name']}")
    except Exception as e:
        print(f"✗ Failed to verify agent_name: {e}")

    # Test 4: activity_type matches input parameter
    print("\n[4/5] Verifying activity_type matches input parameter...")
    try:
        if record["activity_type"] == test_activity_type:
            print(f"✓ activity_type matches: {record['activity_type']}")
            passed += 1
        else:
            print(f"✗ activity_type mismatch: expected {test_activity_type}, got {record['activity_type']}")
    except Exception as e:
        print(f"✗ Failed to verify activity_type: {e}")

    # Test 5: metadata stored as JSONB
    print("\n[5/5] Verifying metadata stored as JSONB...")
    try:
        stored_metadata = record["metadata"]
        if stored_metadata == test_metadata:
            print(f"✓ metadata matches: {stored_metadata}")
            passed += 1
        elif isinstance(stored_metadata, dict) and stored_metadata.get("test_key") == "test_value":
            print(f"✓ metadata stored correctly as JSONB: {stored_metadata}")
            passed += 1
        else:
            print(f"✗ metadata mismatch: expected {test_metadata}, got {stored_metadata}")
    except Exception as e:
        print(f"✗ Failed to verify metadata: {e}")

    # Cleanup
    cleanup(activity_id)

    # Summary
    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    return passed == total


def cleanup(activity_id: UUID):
    """Clean up test data."""
    print("\n[CLEANUP] Deleting test data...")
    try:
        client = get_supabase_client()

        if activity_id:
            try:
                client.table("blog_agent_activity").delete().eq("id", str(activity_id)).execute()
                print("✓ Test activity log deleted")
            except Exception as e:
                print(f"⚠ Failed to delete activity log: {e}")

    except Exception as e:
        print(f"⚠ Cleanup failed: {e}")


if __name__ == "__main__":
    try:
        success = verify_svc_004()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
