"""Verify db-014: machinist/manufacturing resource seed data."""

from supabase import create_client

from config import settings


EXPECTED_ACTIVE_RSS_URLS = [
    "https://www.nist.gov/blogs/manufacturing-innovation-blog/rss.xml",
    "https://www.nist.gov/news-events/news.xml",
    "https://www.govinfo.gov/rss/fr.xml",
    "https://www.govinfo.gov/rss/cfr.xml",
    "https://www.osha.gov/rss/newsreleases.xml",
    "https://www.osha.gov/rss/fedreg.xml",
    "https://www.osha.gov/rss/directives.xml",
    "https://www.osha.gov/rss/interps.xml",
]

EXPECTED_TOPIC_SOURCE_COUNTS = {
    ("standards", "OSHA Machine Shop Standards Library"): 7,
    ("standards", "NIST Manufacturing Improvement Library"): 3,
    ("evergreen", "Production Engineering Evergreen Bank"): 12,
}


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def verify_db_014() -> bool:
    """Verify acceptance criteria for db-014 migration."""
    print("Verifying db-014...")

    supabase_key = settings.supabase_secret or settings.supabase_key
    supabase = create_client(settings.supabase_url, supabase_key)

    all_passed = True

    print("Checking authoritative RSS resources are active...")
    for url in EXPECTED_ACTIVE_RSS_URLS:
        response = (
            supabase.table("blog_rss_sources")
            .select("url, active")
            .eq("url", url)
            .limit(1)
            .execute()
        )
        row = (response.data or [None])[0]
        ok = bool(row and row.get("active") is True)
        print(f"  {'PASS' if ok else 'FAIL'}: active rss source {url}")
        all_passed = all_passed and ok

    print("Checking topic sources and seeded item counts...")
    source_ids: list[str] = []
    standards_source_ids: list[str] = []

    for (source_type, source_name), min_count in EXPECTED_TOPIC_SOURCE_COUNTS.items():
        source_response = (
            supabase.table("blog_topic_sources")
            .select("id, active")
            .eq("source_type", source_type)
            .eq("name", source_name)
            .limit(1)
            .execute()
        )
        source_row = (source_response.data or [None])[0]
        source_ok = bool(source_row and source_row.get("active") is True)
        print(
            f"  {'PASS' if source_ok else 'FAIL'}: topic source {source_type}/{source_name}"
        )
        all_passed = all_passed and source_ok
        if not source_row:
            continue

        source_id = source_row["id"]
        source_ids.append(source_id)
        if source_type == "standards":
            standards_source_ids.append(source_id)

        items_response = (
            supabase.table("blog_topic_items")
            .select("id", count="exact")
            .eq("source_id", source_id)
            .execute()
        )
        item_count = items_response.count or 0
        count_ok = item_count >= min_count
        print(
            f"  {'PASS' if count_ok else 'FAIL'}: {source_name} has >= {min_count} items (found {item_count})"
        )
        all_passed = all_passed and count_ok

    if source_ids:
        print("Checking seeded topic items have title + summary...")
        items = (
            supabase.table("blog_topic_items")
            .select("title, summary, url, source_id")
            .in_("source_id", source_ids)
            .execute()
        )
        bad_items = [
            item
            for item in (items.data or [])
            if not _has_text(item.get("title")) or not _has_text(item.get("summary"))
        ]
        text_ok = len(bad_items) == 0
        print(f"  {'PASS' if text_ok else 'FAIL'}: title/summary validation")
        all_passed = all_passed and text_ok

    if standards_source_ids:
        print("Checking standards items include URLs...")
        standards_items = (
            supabase.table("blog_topic_items")
            .select("url")
            .in_("source_id", standards_source_ids)
            .execute()
        )
        missing_urls = [
            item for item in (standards_items.data or []) if not _has_text(item.get("url"))
        ]
        url_ok = len(missing_urls) == 0
        print(f"  {'PASS' if url_ok else 'FAIL'}: standards items have URLs")
        all_passed = all_passed and url_ok

    print(f"db-014 verification {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


if __name__ == "__main__":
    raise SystemExit(0 if verify_db_014() else 1)
