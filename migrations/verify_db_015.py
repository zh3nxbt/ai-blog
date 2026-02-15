"""Verify db-015: RSS source health tracking columns."""

from datetime import datetime, timezone
from uuid import uuid4

from supabase import create_client

from config import settings


def verify_db_015() -> bool:
    """Verify acceptance criteria for db-015 migration."""
    print("Verifying db-015...")

    supabase_key = settings.supabase_secret or settings.supabase_key
    supabase = create_client(settings.supabase_url, supabase_key)
    all_passed = True

    temp_id = None
    try:
        print("Checking health columns are selectable...")
        probe = (
            supabase.table("blog_rss_sources")
            .select("id, consecutive_failures, last_failed_at, last_error")
            .limit(1)
            .execute()
        )
        ok = probe.data is not None
        print(f"  {'PASS' if ok else 'FAIL'}: columns query")
        all_passed = all_passed and ok

        print("Checking defaults + updates on new source row...")
        temp_url = f"https://example.com/test-feed-{uuid4()}.xml"
        inserted = (
            supabase.table("blog_rss_sources")
            .insert(
                {
                    "name": "db-015 health test source",
                    "url": temp_url,
                    "category": "Test",
                    "active": True,
                    "priority": 1,
                }
            )
            .execute()
        )
        row = (inserted.data or [None])[0]
        temp_id = row["id"] if row else None

        defaults_ok = bool(row and int(row.get("consecutive_failures") or 0) == 0)
        print(f"  {'PASS' if defaults_ok else 'FAIL'}: consecutive_failures default")
        all_passed = all_passed and defaults_ok

        failure_time = datetime.now(timezone.utc).isoformat()
        supabase.table("blog_rss_sources").update(
            {
                "consecutive_failures": 3,
                "last_failed_at": failure_time,
                "last_error": "test failure",
            }
        ).eq("id", temp_id).execute()

        updated = (
            supabase.table("blog_rss_sources")
            .select("consecutive_failures, last_failed_at, last_error")
            .eq("id", temp_id)
            .single()
            .execute()
            .data
        )

        update_ok = bool(
            int(updated.get("consecutive_failures") or 0) == 3
            and bool(updated.get("last_failed_at"))
            and updated.get("last_error") == "test failure"
        )
        print(f"  {'PASS' if update_ok else 'FAIL'}: health column updates")
        all_passed = all_passed and update_ok

    except Exception as exc:
        print(f"  FAIL: verification error: {exc}")
        all_passed = False
    finally:
        if temp_id:
            try:
                supabase.table("blog_rss_sources").delete().eq("id", temp_id).execute()
            except Exception:
                pass

    print(f"db-015 verification {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


if __name__ == "__main__":
    raise SystemExit(0 if verify_db_015() else 1)
