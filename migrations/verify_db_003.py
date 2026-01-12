"""Verify db-003: blog_agent_activity table acceptance criteria."""

import uuid
from supabase import create_client
from config import settings


def verify_db_003():
    """Verify all acceptance criteria for db-003."""
    print("🔍 Verifying db-003: blog_agent_activity table\n")

    # Initialize Supabase client
    supabase = create_client(settings.supabase_url, settings.supabase_key)

    results = []
    test_activity_ids = []  # Track all test activities for cleanup

    # 1. Table exists
    print("✓ Checking: Table blog_agent_activity exists...")
    try:
        # Try to query the table
        supabase.table("blog_agent_activity").select("*").limit(0).execute()
        results.append(("Table blog_agent_activity exists", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("Table blog_agent_activity exists", False))
        print(f"  ❌ FAIL: {e}\n")
        # Print summary before exiting
        print("=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print("❌ FAIL: Table blog_agent_activity exists")
        print("=" * 60)
        print("Total: 0/1 criteria passed")
        print("=" * 60)
        return False  # Can't continue if table doesn't exist

    # 2. INSERT with activity_type='content_draft' succeeds
    print("✓ Checking: INSERT with activity_type='content_draft' succeeds...")
    test_activity_id_1 = None
    try:
        activity = (
            supabase.table("blog_agent_activity")
            .insert(
                {
                    "agent_name": "TestAgent",
                    "activity_type": "content_draft",
                    "context_id": str(uuid.uuid4()),
                    "duration_ms": 1500,
                    "success": True,
                    "metadata": {"test": True, "iteration": 1},
                }
            )
            .execute()
        )
        test_activity_id_1 = activity.data[0]["id"]
        test_activity_ids.append(test_activity_id_1)
        results.append(("INSERT with activity_type='content_draft' succeeds", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("INSERT with activity_type='content_draft' succeeds", False))
        print(f"  ❌ FAIL: {e}\n")

    # 3. INSERT with activity_type='critique' succeeds
    print("✓ Checking: INSERT with activity_type='critique' succeeds...")
    test_activity_id_2 = None
    try:
        activity = (
            supabase.table("blog_agent_activity")
            .insert(
                {
                    "agent_name": "CritiqueAgent",
                    "activity_type": "critique",
                    "duration_ms": 800,
                    "success": True,
                }
            )
            .execute()
        )
        test_activity_id_2 = activity.data[0]["id"]
        test_activity_ids.append(test_activity_id_2)
        results.append(("INSERT with activity_type='critique' succeeds", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("INSERT with activity_type='critique' succeeds", False))
        print(f"  ❌ FAIL: {e}\n")

    # 4. INSERT with activity_type='publish' succeeds
    print("✓ Checking: INSERT with activity_type='publish' succeeds...")
    test_activity_id_3 = None
    try:
        activity = (
            supabase.table("blog_agent_activity")
            .insert(
                {
                    "agent_name": "PublishAgent",
                    "activity_type": "publish",
                    "success": False,
                    "error_message": "API rate limit exceeded",
                }
            )
            .execute()
        )
        test_activity_id_3 = activity.data[0]["id"]
        test_activity_ids.append(test_activity_id_3)
        results.append(("INSERT with activity_type='publish' succeeds", True))
        print("  ✅ PASS\n")
    except Exception as e:
        results.append(("INSERT with activity_type='publish' succeeds", False))
        print(f"  ❌ FAIL: {e}\n")

    # 5. Column id is UUID primary key
    print("✓ Checking: Column id is UUID primary key...")
    if test_activity_id_1:
        try:
            # UUID should be valid format
            uuid.UUID(test_activity_id_1)
            results.append(("Column id is UUID primary key", True))
            print("  ✅ PASS\n")
        except ValueError as e:
            results.append(("Column id is UUID primary key", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("Column id is UUID primary key", False))
        print("  ❌ FAIL: No activity created\n")

    # 6. Column agent_name is non-null text
    print("✓ Checking: Column agent_name is non-null text...")
    try:
        # Try to insert without agent_name
        supabase.table("blog_agent_activity").insert(
            {"activity_type": "test"}
        ).execute()
        results.append(("Column agent_name is non-null text", False))
        print("  ❌ FAIL: Should have rejected null agent_name\n")
    except Exception:
        # Expected to fail
        results.append(("Column agent_name is non-null text", True))
        print("  ✅ PASS (correctly rejected null agent_name)\n")

    # 7. Column activity_type is non-null text
    print("✓ Checking: Column activity_type is non-null text...")
    try:
        # Try to insert without activity_type
        supabase.table("blog_agent_activity").insert(
            {"agent_name": "TestAgent"}
        ).execute()
        results.append(("Column activity_type is non-null text", False))
        print("  ❌ FAIL: Should have rejected null activity_type\n")
    except Exception:
        # Expected to fail
        results.append(("Column activity_type is non-null text", True))
        print("  ✅ PASS (correctly rejected null activity_type)\n")

    # 8. Column types verification
    print("✓ Checking: All columns have correct types...")
    if test_activity_id_1:
        try:
            activity = (
                supabase.table("blog_agent_activity")
                .select("*")
                .eq("id", test_activity_id_1)
                .execute()
            )
            data = activity.data[0]

            checks = [
                ("agent_name", str, data.get("agent_name")),
                ("activity_type", str, data.get("activity_type")),
                ("context_id", (str, type(None)), data.get("context_id")),
                ("duration_ms", (int, type(None)), data.get("duration_ms")),
                ("success", (bool, type(None)), data.get("success")),
                ("error_message", (str, type(None)), data.get("error_message")),
                ("metadata", (dict, type(None)), data.get("metadata")),
                ("created_at", str, data.get("created_at")),
            ]

            all_pass = True
            for field, expected_type, value in checks:
                if isinstance(expected_type, tuple):
                    if not isinstance(value, expected_type):
                        print(f"  ❌ Field {field} has wrong type: {type(value)}")
                        all_pass = False
                else:
                    if not isinstance(value, expected_type):
                        print(f"  ❌ Field {field} has wrong type: {type(value)}")
                        all_pass = False

            results.append(("All columns have correct types", all_pass))
            if all_pass:
                print("  ✅ PASS\n")
            else:
                print("  ❌ FAIL\n")
        except Exception as e:
            results.append(("All columns have correct types", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("All columns have correct types", False))
        print("  ❌ FAIL: No activity created\n")

    # 9. Column context_id is nullable UUID
    print("✓ Checking: Column context_id is nullable UUID...")
    if test_activity_id_2:
        try:
            activity = (
                supabase.table("blog_agent_activity")
                .select("context_id")
                .eq("id", test_activity_id_2)
                .execute()
            )
            context_id = activity.data[0].get("context_id")
            # context_id should be None since we didn't provide it
            if context_id is None:
                results.append(("Column context_id is nullable UUID", True))
                print("  ✅ PASS (nullable)\n")
            else:
                results.append(("Column context_id is nullable UUID", False))
                print(f"  ❌ FAIL: Expected None but got {context_id}\n")
        except Exception as e:
            results.append(("Column context_id is nullable UUID", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("Column context_id is nullable UUID", False))
        print("  ❌ FAIL: No activity created\n")

    # 10. Column metadata is JSONB
    print("✓ Checking: Column metadata is JSONB...")
    if test_activity_id_1:
        try:
            activity = (
                supabase.table("blog_agent_activity")
                .select("metadata")
                .eq("id", test_activity_id_1)
                .execute()
            )
            metadata = activity.data[0].get("metadata")
            if isinstance(metadata, dict) and metadata.get("test") is True:
                results.append(("Column metadata is JSONB", True))
                print("  ✅ PASS\n")
            else:
                results.append(("Column metadata is JSONB", False))
                print(f"  ❌ FAIL: Expected dict with test=True but got {metadata}\n")
        except Exception as e:
            results.append(("Column metadata is JSONB", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("Column metadata is JSONB", False))
        print("  ❌ FAIL: No activity created\n")

    # 11. created_at defaults to NOW()
    print("✓ Checking: created_at defaults to NOW()...")
    if test_activity_id_1:
        try:
            activity = (
                supabase.table("blog_agent_activity")
                .select("created_at")
                .eq("id", test_activity_id_1)
                .execute()
            )
            created_at = activity.data[0].get("created_at")
            if created_at:
                results.append(("created_at defaults to NOW()", True))
                print("  ✅ PASS\n")
            else:
                results.append(("created_at defaults to NOW()", False))
                print("  ❌ FAIL: created_at is null\n")
        except Exception as e:
            results.append(("created_at defaults to NOW()", False))
            print(f"  ❌ FAIL: {e}\n")
    else:
        results.append(("created_at defaults to NOW()", False))
        print("  ❌ FAIL: No activity created\n")

    # Cleanup: Delete all test activities
    print("🧹 Cleaning up test data...")
    for activity_id in test_activity_ids:
        try:
            supabase.table("blog_agent_activity").delete().eq("id", activity_id).execute()
            print(f"  ✅ Test activity {activity_id[:8]} deleted")
        except Exception as e:
            print(f"  ⚠️  Could not delete test activity {activity_id[:8]}: {e}")

    print()  # Empty line after cleanup

    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for criterion, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {criterion}")

    print("=" * 60)
    print(f"Total: {passed}/{total} criteria passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    import sys

    success = verify_db_003()
    sys.exit(0 if success else 1)
