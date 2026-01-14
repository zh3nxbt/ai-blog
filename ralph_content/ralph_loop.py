"""RalphLoop orchestrator for initial draft generation."""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from ralph_content.agents.product_marketing import ProductMarketingAgent


class RalphLoop:
    """Generate and refine blog posts with Ralph."""

    def __init__(
        self,
        agent: ProductMarketingAgent | None = None,
        rss_service: Any | None = None,
        supabase_service: Any | None = None,
        min_items: int = 3,
        max_items: int = 5,
    ) -> None:
        if min_items < 1:
            raise ValueError("min_items must be >= 1")
        if max_items < min_items:
            raise ValueError("max_items must be >= min_items")

        if rss_service is None:
            from services import rss_service as rss_service_module

            rss_service = rss_service_module

        if supabase_service is None:
            from services import supabase_service as supabase_service_module

            supabase_service = supabase_service_module

        self.agent = agent or ProductMarketingAgent()
        self.rss_service = rss_service
        self.supabase_service = supabase_service
        self.min_items = min_items
        self.max_items = max_items

    def generate_initial_draft(self) -> UUID:
        """
        Generate the initial blog post draft.

        Returns:
            UUID: blog_posts ID of the created draft
        """
        rss_items = self._get_rss_items()
        rss_items_for_generation = rss_items[: self.max_items]

        title, content = self.agent.generate_content(rss_items_for_generation)
        blog_post_id = self.supabase_service.create_blog_post(
            title=title,
            content=content,
            status="draft",
        )

        self.supabase_service.save_draft_iteration(
            blog_post_id=blog_post_id,
            iteration_number=1,
            content=content,
            quality_score=0.0,
            critique={"note": "initial draft"},
            title=title,
        )

        item_ids = [item["id"] for item in rss_items_for_generation if item.get("id")]
        if not item_ids:
            raise ValueError("No RSS item IDs available to mark as used")

        self.rss_service.mark_items_as_used(item_ids, str(blog_post_id))

        return blog_post_id

    def _get_rss_items(self) -> List[Dict[str, Any]]:
        """Fetch enough unused RSS items, replenishing if needed."""
        unused_items = self.rss_service.fetch_unused_items(limit=self.max_items)

        if len(unused_items) < self.min_items:
            sources = self.rss_service.fetch_active_sources()
            if not sources:
                raise ValueError("No active RSS sources found")

            for source in sources:
                try:
                    self.rss_service.fetch_feed_items(source["id"], limit=10)
                except Exception:
                    continue

                unused_items = self.rss_service.fetch_unused_items(limit=self.max_items)
                if len(unused_items) >= self.min_items:
                    break

            unused_items = self.rss_service.fetch_unused_items(limit=self.max_items)

        if len(unused_items) < self.min_items:
            raise ValueError(
                f"Insufficient RSS items: need at least {self.min_items}, found {len(unused_items)}"
            )

        return unused_items
