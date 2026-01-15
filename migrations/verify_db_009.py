"""Verify mix-002: evergreen topic bank seed data."""

from supabase import create_client

from config import settings


EXPECTED_MIN_TOPICS = 25
EVERGREEN_SOURCE_NAME = "Evergreen Topic Bank"


def _print_summary(results: list[tuple[str, bool]]) -> None:
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    for label, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status}: {label}")
    print("=" * 60)
    print(f"Total: {passed}/{total} criteria passed")
    print("=" * 60)


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def verify_db_009() -> bool:
    """Verify all acceptance criteria for mix-002."""
    print("🔍 Verifying mix-002: evergreen topic bank\n")

    supabase_key = settings.supabase_secret or settings.supabase_key
    supabase = create_client(settings.supabase_url, supabase_key)

    results: list[tuple[str, bool]] = []

    # 1. Evergreen source exists
    print("✓ Checking: Evergreen source exists...")
    try:
        sources = (
            supabase.table("blog_topic_sources")
            .select("id, source_type, name")
            .eq("source_type", "evergreen")
            .execute()
        )
        evergreen_sources = [s for s in sources.data if s.get("name") == EVERGREEN_SOURCE_NAME]
        source_ids = [s["id"] for s in evergreen_sources]
        if evergreen_sources:
            results.append(("Evergreen source exists", True))
            print(f"  ✅ PASS ({len(evergreen_sources)} source)\n")
        else:
            results.append(("Evergreen source exists", False))
            print("  ❌ FAIL: No evergreen source found\n")
            _print_summary(results)
            return False
    except Exception as e:
        results.append(("Evergreen source exists", False))
        print(f"  ❌ FAIL: {e}\n")
        _print_summary(results)
        return False

    # 2. At least 25 evergreen topics seeded
    print("✓ Checking: At least 25 evergreen topics seeded...")
    items = None
    try:
        items = (
            supabase.table("blog_topic_items")
            .select("id, title, summary, url")
            .in_("source_id", source_ids)
            .execute()
        )
        item_count = len(items.data)
        if item_count >= EXPECTED_MIN_TOPICS:
            results.append(("At least 25 evergreen topics seeded", True))
            print(f"  ✅ PASS ({item_count} topics)\n")
        else:
            results.append(("At least 25 evergreen topics seeded", False))
            print(f"  ❌ FAIL: Found {item_count} topics\n")
    except Exception as e:
        results.append(("At least 25 evergreen topics seeded", False))
        print(f"  ❌ FAIL: {e}\n")

    # 3. Evergreen topics include title and summary
    print("✓ Checking: Evergreen topics include title and summary...")
    if items is None:
        results.append(("Evergreen topics include title and summary", False))
        print("  ❌ FAIL: No items loaded for validation\n")
    else:
        try:
            missing_fields = [
                item
                for item in items.data
                if not _has_text(item.get("title")) or not _has_text(item.get("summary"))
            ]
            if missing_fields:
                results.append(("Evergreen topics include title and summary", False))
                print(f"  ❌ FAIL: {len(missing_fields)} items missing title/summary\n")
            else:
                results.append(("Evergreen topics include title and summary", True))
                print("  ✅ PASS\n")
        except Exception as e:
            results.append(("Evergreen topics include title and summary", False))
            print(f"  ❌ FAIL: {e}\n")

    # 4. Evergreen topics may omit url without validation errors
    print("✓ Checking: Evergreen topics may omit url...")
    if items is None:
        results.append(("Evergreen topics may omit url", False))
        print("  ❌ FAIL: No items loaded for validation\n")
    else:
        try:
            null_url_count = sum(1 for item in items.data if item.get("url") is None)
            if null_url_count > 0:
                results.append(("Evergreen topics may omit url", True))
                print(f"  ✅ PASS ({null_url_count} topics without url)\n")
            else:
                results.append(("Evergreen topics may omit url", False))
                print("  ❌ FAIL: No topics with null url\n")
        except Exception as e:
            results.append(("Evergreen topics may omit url", False))
            print(f"  ❌ FAIL: {e}\n")

    _print_summary(results)
    return all(ok for _, ok in results)


if __name__ == "__main__":
    raise SystemExit(0 if verify_db_009() else 1)
