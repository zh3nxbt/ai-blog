"""RalphLoop orchestrator for iterative blog post generation."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from ralph_content.agents.critique_agent import CritiqueAgent
from ralph_content.agents.product_marketing import ProductMarketingAgent
from ralph_content.core.api_cost import calculate_api_cost
from ralph_content.core.markdown_renderer import markdown_to_html
from ralph_content.core.timeout_manager import TimeoutManager
from services.quality_validator import validate_content


@dataclass
class RalphLoopResult:
    """Result of a RalphLoop.run() execution."""

    blog_post_id: UUID
    final_quality_score: float
    iteration_count: int
    total_cost_cents: int
    status: str  # "published", "draft", "failed", "skipped"


class RalphLoop:
    """Generate and refine blog posts with Ralph."""

    DEFAULT_QUALITY_THRESHOLD = 0.85
    DEFAULT_TIMEOUT_MINUTES = 30
    DEFAULT_COST_LIMIT_CENTS = 100
    DEFAULT_SOURCE_MIX = {
        "rss": 2,
        "evergreen": 1,
        "standards": 1,
        "vendor": 1,
    }
    SOURCE_TYPE_ORDER = ("rss", "evergreen", "standards", "vendor", "internal")
    MAX_ITERATIONS = 10

    def __init__(
        self,
        agent: ProductMarketingAgent | None = None,
        critique_agent: CritiqueAgent | None = None,
        rss_service: Any | None = None,
        topic_item_service: Any | None = None,
        supabase_service: Any | None = None,
        quality_validator: Any | None = None,
        min_items: int = 3,
        max_items: int = 5,
        quality_threshold: float | None = None,
        timeout_minutes: int | None = None,
        cost_limit_cents: int | None = None,
        source_mix: Dict[str, int] | None = None,
        skip_if_exists: bool = True,
    ) -> None:
        if min_items < 1:
            raise ValueError("min_items must be >= 1")
        if max_items < min_items:
            raise ValueError("max_items must be >= min_items")

        if rss_service is None:
            from services import rss_service as rss_service_module

            rss_service = rss_service_module

        if topic_item_service is None:
            from services import topic_item_service as topic_item_service_module

            topic_item_service = topic_item_service_module

        if supabase_service is None:
            from services import supabase_service as supabase_service_module

            supabase_service = supabase_service_module

        self.agent = agent or ProductMarketingAgent()
        self.critique_agent = critique_agent or CritiqueAgent()
        self.rss_service = rss_service
        self.topic_item_service = topic_item_service
        self.supabase_service = supabase_service
        self.quality_validator = quality_validator or validate_content
        self.min_items = min_items
        self.max_items = max_items

        self.quality_threshold = quality_threshold or self.DEFAULT_QUALITY_THRESHOLD
        self.timeout_minutes = timeout_minutes or self.DEFAULT_TIMEOUT_MINUTES
        self.cost_limit_cents = cost_limit_cents or self.DEFAULT_COST_LIMIT_CENTS
        self.source_mix = source_mix or self.DEFAULT_SOURCE_MIX
        self.skip_if_exists = skip_if_exists

    def _check_already_generated_today(self) -> Optional[UUID]:
        """
        Check if a blog post has already been generated today.

        Returns:
            UUID of existing post if found, None otherwise
        """
        client = self.supabase_service.get_supabase_client()
        today = date.today().isoformat()

        # Query for posts created today (any status)
        response = (
            client.table("blog_posts")
            .select("id, created_at, status")
            .gte("created_at", f"{today}T00:00:00")
            .lt("created_at", f"{today}T23:59:59.999999")
            .execute()
        )

        if response.data:
            return UUID(response.data[0]["id"])
        return None

    def generate_initial_draft(self) -> UUID:
        """
        Generate the initial blog post draft.

        Returns:
            UUID: blog_posts ID of the created draft
        """
        source_items, _ = self._get_source_items()

        title, content_markdown = self.agent.generate_content(source_items)
        content_html = markdown_to_html(content_markdown)
        blog_post_id = self.supabase_service.create_blog_post(
            title=title,
            content=content_html,
            status="draft",
        )

        self.supabase_service.save_draft_iteration(
            blog_post_id=blog_post_id,
            iteration_number=1,
            content=content_markdown,
            quality_score=0.0,
            critique={"note": "initial draft"},
            title=title,
        )

        self._mark_source_items_as_used(source_items, blog_post_id)

        return blog_post_id

    def _get_source_items(self) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Fetch source items using the configured source mix."""
        targets = self._build_source_targets()
        desired_total = min(self.max_items, sum(targets.values()))
        desired_total = max(self.min_items, desired_total)

        selected_items: List[Dict[str, Any]] = []
        selected_ids: set[str] = set()
        source_mix_counts: Dict[str, int] = {key: 0 for key in targets}

        for source_type in self.SOURCE_TYPE_ORDER:
            target_count = targets.get(source_type, 0)
            if target_count <= 0:
                continue

            items = self._fetch_items_for_source_type(
                source_type=source_type,
                limit=target_count,
                exclude_ids=selected_ids,
            )
            if items:
                selected_items.extend(items)
                selected_ids.update(item["id"] for item in items if item.get("id"))
                source_mix_counts[source_type] = source_mix_counts.get(source_type, 0) + len(items)

        remaining_slots = desired_total - len(selected_items)
        if remaining_slots > 0:
            for source_type in self.SOURCE_TYPE_ORDER:
                if remaining_slots <= 0:
                    break

                extra_items = self._fetch_items_for_source_type(
                    source_type=source_type,
                    limit=remaining_slots,
                    exclude_ids=selected_ids,
                )
                if not extra_items:
                    continue

                selected_items.extend(extra_items)
                selected_ids.update(item["id"] for item in extra_items if item.get("id"))
                source_mix_counts[source_type] = source_mix_counts.get(source_type, 0) + len(extra_items)
                remaining_slots = desired_total - len(selected_items)

        if len(selected_items) < self.min_items:
            raise ValueError(
                "Insufficient source items: "
                f"need at least {self.min_items}, found {len(selected_items)}"
            )

        return selected_items[: self.max_items], source_mix_counts

    def _build_source_targets(self) -> Dict[str, int]:
        """Compute target counts per source type based on the default mix."""
        targets: Dict[str, int] = {}
        remaining = self.max_items

        for source_type in self.SOURCE_TYPE_ORDER:
            desired = self.source_mix.get(source_type, 0)
            if desired <= 0 or remaining <= 0:
                continue
            take = min(desired, remaining)
            targets[source_type] = take
            remaining -= take

        if remaining > 0:
            targets["rss"] = targets.get("rss", 0) + remaining

        return targets

    def _fetch_items_for_source_type(
        self,
        source_type: str,
        limit: int,
        exclude_ids: set[str],
    ) -> List[Dict[str, Any]]:
        """Fetch items for a source type while avoiding already-selected IDs."""
        if limit <= 0:
            return []

        fetch_limit = limit + len(exclude_ids)
        if source_type == "rss":
            items = self._get_rss_items_for_mix(fetch_limit)
        else:
            items = self.topic_item_service.fetch_unused_items_by_source_type(
                source_type=source_type,
                limit=fetch_limit,
            )

        filtered = [item for item in items if item.get("id") not in exclude_ids]
        return filtered[:limit]

    def _get_rss_items_for_mix(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch unused RSS items for mixed-source selection."""
        unused_items = self.rss_service.fetch_unused_items(limit=limit)

        if len(unused_items) < limit:
            sources = self.rss_service.fetch_active_sources()
            for source in sources:
                try:
                    self.rss_service.fetch_feed_items(source["id"], limit=10)
                except Exception:
                    continue

                unused_items = self.rss_service.fetch_unused_items(limit=limit)
                if len(unused_items) >= limit:
                    break

            unused_items = self.rss_service.fetch_unused_items(limit=limit)

        for item in unused_items:
            item.setdefault("source_type", "rss")

        return unused_items

    def _mark_source_items_as_used(
        self,
        source_items: List[Dict[str, Any]],
        blog_post_id: UUID,
    ) -> None:
        """Mark RSS and topic items as used for a blog post."""
        rss_item_ids = [
            item["id"]
            for item in source_items
            if item.get("id") and item.get("source_type") == "rss"
        ]
        topic_item_ids = [
            item["id"]
            for item in source_items
            if item.get("id") and item.get("source_type") != "rss"
        ]

        if rss_item_ids:
            self.rss_service.mark_items_as_used(rss_item_ids, str(blog_post_id))

        if topic_item_ids:
            self.topic_item_service.mark_items_as_used(topic_item_ids, str(blog_post_id))

        if not rss_item_ids and not topic_item_ids:
            raise ValueError("No source item IDs available to mark as used")

    def run(self) -> RalphLoopResult:
        """
        Execute the full generate-critique-refine loop.

        Creates an initial draft, evaluates quality, and iteratively improves
        until the quality threshold is met or limits (timeout, cost, iterations)
        are exceeded.

        Returns:
            RalphLoopResult with blog_post_id, final_quality_score, iteration_count,
            total_cost_cents, and status ("published", "draft", "failed", or "skipped")
        """
        # Idempotency check: skip if post already generated today
        if self.skip_if_exists:
            existing_post_id = self._check_already_generated_today()
            if existing_post_id:
                self.supabase_service.log_agent_activity(
                    agent_name="ralph-loop",
                    activity_type="skipped",
                    success=True,
                    context_id=existing_post_id,
                    metadata={
                        "reason": "post_already_exists_today",
                        "existing_post_id": str(existing_post_id),
                    },
                )
                return RalphLoopResult(
                    blog_post_id=existing_post_id,
                    final_quality_score=0.0,
                    iteration_count=0,
                    total_cost_cents=0,
                    status="skipped",
                )

        timeout_manager = TimeoutManager(
            timeout_minutes=self.timeout_minutes,
            cost_limit_cents=self.cost_limit_cents,
        )

        # Generate initial draft
        source_items, source_mix_counts = self._get_source_items()
        title, content_markdown = self.agent.generate_content(source_items)
        content_html = markdown_to_html(content_markdown)

        # Create blog post record
        blog_post_id = self.supabase_service.create_blog_post(
            title=title,
            content=content_html,
            status="draft",
        )

        # Mark source items as used
        self._mark_source_items_as_used(source_items, blog_post_id)

        # Track costs per iteration (generation, critique, improvement)
        last_main_input = 0
        last_main_output = 0
        last_crit_input = 0
        last_crit_output = 0
        total_cost_cents = 0

        input_tokens, output_tokens = self.agent.get_total_tokens()
        generation_cost = calculate_api_cost(
            input_tokens - last_main_input,
            output_tokens - last_main_output,
        )
        last_main_input = input_tokens
        last_main_output = output_tokens
        total_cost_cents += generation_cost

        # Evaluate initial quality
        validation_result = self.quality_validator(content_markdown, title)
        quality_score = validation_result["overall_score"]

        # Save initial draft iteration
        self.supabase_service.save_draft_iteration(
            blog_post_id=blog_post_id,
            iteration_number=1,
            content=content_markdown,
            quality_score=quality_score,
            critique=validation_result,
            title=title,
            api_cost_cents=generation_cost,
        )

        iteration_count = 1

        # Log initial draft activity
        self.supabase_service.log_agent_activity(
            agent_name=self.agent.agent_name,
            activity_type="content_draft",
            success=True,
            context_id=blog_post_id,
            metadata={
                "iteration": iteration_count,
                "quality_score": quality_score,
                "cost_cents": total_cost_cents,
                "source_mix": source_mix_counts,
            },
        )

        # Iterate until quality threshold is met or limits exceeded
        current_title = title
        current_content = content_markdown

        while quality_score < self.quality_threshold:
            # Check iteration limit
            if iteration_count >= self.MAX_ITERATIONS:
                self.supabase_service.log_agent_activity(
                    agent_name="ralph-loop",
                    activity_type="iteration_limit",
                    success=False,
                    context_id=blog_post_id,
                    metadata={
                        "final_iteration": iteration_count,
                        "quality_score": quality_score,
                        "reason": "max_iterations_exceeded",
                    },
                )
                break

            # Check timeout
            if timeout_manager.is_timeout_exceeded():
                self.supabase_service.log_agent_activity(
                    agent_name="ralph-loop",
                    activity_type="timeout",
                    success=False,
                    context_id=blog_post_id,
                    metadata={
                        "final_iteration": iteration_count,
                        "quality_score": quality_score,
                        "reason": "timeout_exceeded",
                    },
                )
                break

            # Check cost limit
            if timeout_manager.is_cost_limit_exceeded(total_cost_cents):
                self.supabase_service.log_agent_activity(
                    agent_name="ralph-loop",
                    activity_type="cost_limit",
                    success=False,
                    context_id=blog_post_id,
                    metadata={
                        "final_iteration": iteration_count,
                        "quality_score": quality_score,
                        "total_cost_cents": total_cost_cents,
                        "reason": "cost_limit_exceeded",
                    },
                )
                break

            # Get critique for current content
            start_time = time.monotonic()
            critique = self.critique_agent.evaluate_content(
                title=current_title,
                content=current_content,
                current_score=quality_score,
            )
            critique_duration_ms = int((time.monotonic() - start_time) * 1000)

            # Update cost tracking
            crit_input, crit_output = self.critique_agent.get_total_tokens()
            critique_cost = calculate_api_cost(
                crit_input - last_crit_input,
                crit_output - last_crit_output,
            )
            last_crit_input = crit_input
            last_crit_output = crit_output
            total_cost_cents += critique_cost

            # Log critique activity
            self.supabase_service.log_agent_activity(
                agent_name=self.critique_agent.agent_name,
                activity_type="critique",
                success=True,
                context_id=blog_post_id,
                duration_ms=critique_duration_ms,
                metadata={
                    "iteration": iteration_count,
                    "critique_score": critique.get("quality_score", 0.0),
                },
            )

            # Check cost again after critique
            if timeout_manager.is_cost_limit_exceeded(total_cost_cents):
                self.supabase_service.log_agent_activity(
                    agent_name="ralph-loop",
                    activity_type="cost_limit",
                    success=False,
                    context_id=blog_post_id,
                    metadata={
                        "final_iteration": iteration_count,
                        "quality_score": quality_score,
                        "total_cost_cents": total_cost_cents,
                        "reason": "cost_limit_exceeded_after_critique",
                    },
                )
                break

            # Improve content based on critique
            start_time = time.monotonic()
            improved_content = self.agent.improve_content(
                content=current_content,
                critique=critique,
            )
            improve_duration_ms = int((time.monotonic() - start_time) * 1000)

            # Update cost tracking
            imp_input, imp_output = self.agent.get_total_tokens()
            improvement_cost = calculate_api_cost(
                imp_input - last_main_input,
                imp_output - last_main_output,
            )
            last_main_input = imp_input
            last_main_output = imp_output
            total_cost_cents += improvement_cost

            # Evaluate improved content
            validation_result = self.quality_validator(improved_content, current_title)
            new_quality_score = validation_result["overall_score"]

            iteration_count += 1

            # Save improved draft iteration
            self.supabase_service.save_draft_iteration(
                blog_post_id=blog_post_id,
                iteration_number=iteration_count,
                content=improved_content,
                quality_score=new_quality_score,
                critique=validation_result,
                title=current_title,
                api_cost_cents=total_cost_cents,
            )

            # Log improvement activity
            self.supabase_service.log_agent_activity(
                agent_name=self.agent.agent_name,
                activity_type="content_draft",
                success=True,
                context_id=blog_post_id,
                duration_ms=improve_duration_ms,
                metadata={
                    "iteration": iteration_count,
                    "quality_score": new_quality_score,
                    "previous_score": quality_score,
                    "improvement": new_quality_score - quality_score,
                },
            )

            current_content = improved_content
            quality_score = new_quality_score

        # Determine final status based on quality
        if quality_score >= self.quality_threshold:
            status = "published"
        elif quality_score >= 0.70:
            status = "draft"
        else:
            status = "failed"

        # Update blog post with final content and status
        client = self.supabase_service.get_supabase_client()
        update_data = {"content": markdown_to_html(current_content), "status": status}
        if status == "published":
            from datetime import datetime, timezone

            update_data["published_at"] = datetime.now(timezone.utc).isoformat()

        client.table("blog_posts").update(update_data).eq("id", str(blog_post_id)).execute()

        # Log final status
        self.supabase_service.log_agent_activity(
            agent_name="ralph-loop",
            activity_type="publish" if status == "published" else "finalize",
            success=status != "failed",
            context_id=blog_post_id,
            metadata={
                "final_status": status,
                "final_quality_score": quality_score,
                "iteration_count": iteration_count,
                "total_cost_cents": total_cost_cents,
                "source_mix": source_mix_counts,
            },
        )

        return RalphLoopResult(
            blog_post_id=blog_post_id,
            final_quality_score=quality_score,
            iteration_count=iteration_count,
            total_cost_cents=total_cost_cents,
            status=status,
        )
