"""Verify db-013: authoritative RSS feed seed + fragile feed deactivation."""

from supabase import create_client

from config import settings


EXPECTED_ACTIVE_URLS = [
    "https://www150.statcan.gc.ca/n1/rss/dai-quo/16-eng.atom",
    "https://www150.statcan.gc.ca/n1/rss/dai-quo/12-eng.atom",
    "https://www.gazette.gc.ca/rss/p2-eng.xml",
    "https://www.gazette.gc.ca/rss/p1-eng.xml",
    "https://www.bls.gov/feed/prod2.rss",
    "https://www.bls.gov/feed/prin.rss",
]

EXPECTED_INACTIVE_URLS = [
    "https://rsshub.app/apnews/topics/business",
    "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
]


def verify_db_013() -> bool:
    """Verify acceptance criteria for db-013 migration."""
    print("Verifying db-013...")

    supabase_key = settings.supabase_secret or settings.supabase_key
    supabase = create_client(settings.supabase_url, supabase_key)

    all_passed = True

    print("Checking authoritative sources are active...")
    for url in EXPECTED_ACTIVE_URLS:
        response = (
            supabase.table("blog_rss_sources")
            .select("url, active")
            .eq("url", url)
            .limit(1)
            .execute()
        )
        row = (response.data or [None])[0]
        ok = bool(row and row.get("active") is True)
        print(f"  {'PASS' if ok else 'FAIL'}: active source {url}")
        all_passed = all_passed and ok

    print("Checking fragile sources are inactive...")
    for url in EXPECTED_INACTIVE_URLS:
        response = (
            supabase.table("blog_rss_sources")
            .select("url, active")
            .eq("url", url)
            .limit(1)
            .execute()
        )
        row = (response.data or [None])[0]
        ok = bool(row and row.get("active") is False)
        print(f"  {'PASS' if ok else 'FAIL'}: inactive source {url}")
        all_passed = all_passed and ok

    print(f"db-013 verification {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


if __name__ == "__main__":
    raise SystemExit(0 if verify_db_013() else 1)
