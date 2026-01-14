#!/usr/bin/env python3
"""Verification script for ralph-011: RalphLoop.generate_initial_draft().

Acceptance Criteria:
1. `python -c 'from ralph.ralph_loop import RalphLoop'` exits with code 0
2. loop.generate_initial_draft() creates blog_posts record with status='draft'
3. blog_content_drafts has iteration_number=1 for created post
4. RSS items used are marked with used_in_blog = blog_post_id
5. Returns blog_post_id UUID
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class _FakeBlogPost:
    id: UUID
    title: str
    content: str
    status: str


@dataclass
class _FakeDraft:
    blog_post_id: UUID
    iteration_number: int
    content: str
    quality_score: float
    critique: dict
    title: str


class _FakeSupabaseService:
    def __init__(self) -> None:
        self.blog_post: _FakeBlogPost | None = None
        self.draft: _FakeDraft | None = None

    def create_blog_post(self, title: str, content: str, status: str = "draft") -> UUID:
        post_id = uuid4()
        self.blog_post = _FakeBlogPost(
            id=post_id,
            title=title,
            content=content,
            status=status,
        )
        return post_id

    def save_draft_iteration(
        self,
        blog_post_id: UUID,
        iteration_number: int,
        content: str,
        quality_score: float,
        critique: dict,
        title: str = None,
        api_cost_cents: int = 0,
    ) -> UUID:
        del api_cost_cents
        self.draft = _FakeDraft(
            blog_post_id=blog_post_id,
            iteration_number=iteration_number,
            content=content,
            quality_score=quality_score,
            critique=critique,
            title=title or "",
        )
        return uuid4()


class _FakeRssService:
    def __init__(self) -> None:
        self.items = [
            {"id": "item-1", "title": "Item 1"},
            {"id": "item-2", "title": "Item 2"},
            {"id": "item-3", "title": "Item 3"},
        ]
        self.used_mapping: dict[str, str] = {}
        self.mark_calls: list[tuple[list[str], str]] = []

    def fetch_unused_items(self, limit: int = 5):
        del limit
        return [item.copy() for item in self.items]

    def fetch_active_sources(self):
        return []

    def fetch_feed_items(self, source_id: str, limit: int = 10):
        del source_id, limit
        return []

    def mark_items_as_used(self, item_ids: list[str], blog_id: str) -> int:
        self.mark_calls.append((item_ids, blog_id))
        for item_id in item_ids:
            self.used_mapping[item_id] = blog_id
        return len(item_ids)


class _FakeAgent:
    def generate_content(self, rss_items):
        if not rss_items:
            raise ValueError("rss_items cannot be empty")
        content = "## Draft\n\n" + "machining " * 1200
        return "Initial Draft Title", content


def verify_ralph_011() -> bool:
    """Verify all acceptance criteria for ralph-011."""
    print("=" * 60)
    print("VERIFICATION: ralph-011 - RalphLoop.generate_initial_draft()")
    print("=" * 60)

    passed = 0
    total = 5

    from ralph.ralph_loop import RalphLoop

    fake_supabase = _FakeSupabaseService()
    fake_rss = _FakeRssService()
    fake_agent = _FakeAgent()
    loop = RalphLoop(
        agent=fake_agent,
        rss_service=fake_rss,
        supabase_service=fake_supabase,
    )

    print("\n[1/5] Verifying RalphLoop import and instantiation...")
    if loop:
        print("✓ RalphLoop instantiated")
        passed += 1
    else:
        print("✗ RalphLoop instantiation failed")

    print("\n[2/5] Running generate_initial_draft()...")
    try:
        blog_post_id = loop.generate_initial_draft()
        print(f"✓ generate_initial_draft() returned {blog_post_id}")
        passed += 1
    except Exception as exc:
        print(f"✗ generate_initial_draft() failed: {exc}")
        return False

    print("\n[3/5] Verifying blog_posts record status='draft'...")
    if fake_supabase.blog_post and fake_supabase.blog_post.status == "draft":
        print("✓ blog_posts record created with status='draft'")
        passed += 1
    else:
        print("✗ blog_posts record missing or status incorrect")

    print("\n[4/5] Verifying draft iteration_number=1...")
    if fake_supabase.draft and fake_supabase.draft.iteration_number == 1:
        print("✓ blog_content_drafts iteration_number is 1")
        passed += 1
    else:
        print("✗ blog_content_drafts iteration_number missing or incorrect")

    print("\n[5/5] Verifying RSS items marked as used and UUID returned...")
    if isinstance(blog_post_id, UUID) and fake_rss.used_mapping:
        mapped_ids = set(fake_rss.used_mapping.values())
        if str(blog_post_id) in mapped_ids:
            print("✓ RSS items marked with blog_post_id and UUID returned")
            passed += 1
        else:
            print("✗ RSS items not marked with blog_post_id")
    else:
        print("✗ blog_post_id not UUID or items not marked")

    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")
    print("=" * 60)

    if passed == total:
        print("\n✓ All acceptance criteria PASSED")
    else:
        print(f"\n✗ {total - passed} acceptance criteria FAILED")

    return passed == total


if __name__ == "__main__":
    try:
        success = verify_ralph_011()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
