"""RalphLoop orchestrator for iterative blog post generation."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List
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
    status: str  # "published", "draft", "failed"


class RalphLoop:
    """Generate and refine blog posts with Ralph."""

    DEFAULT_QUALITY_THRESHOLD = 0.85
    DEFAULT_TIMEOUT_MINUTES = 30
    DEFAULT_COST_LIMIT_CENTS = 100
    MAX_ITERATIONS = 10

    def __init__(
        self,
        agent: ProductMarketingAgent | None = None,
        critique_agent: CritiqueAgent | None = None,
        rss_service: Any | None = None,
        supabase_service: Any | None = None,
        quality_validator: Any | None = None,
        min_items: int = 3,
        max_items: int = 5,
        quality_threshold: float | None = None,
        timeout_minutes: int | None = None,
        cost_limit_cents: int | None = None,
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
        self.critique_agent = critique_agent or CritiqueAgent()
        self.rss_service = rss_service
        self.supabase_service = supabase_service
        self.quality_validator = quality_validator or validate_content
        self.min_items = min_items
        self.max_items = max_items

        self.quality_threshold = quality_threshold or self.DEFAULT_QUALITY_THRESHOLD
        self.timeout_minutes = timeout_minutes or self.DEFAULT_TIMEOUT_MINUTES
        self.cost_limit_cents = cost_limit_cents or self.DEFAULT_COST_LIMIT_CENTS

    def generate_initial_draft(self) -> UUID:
        """
        Generate the initial blog post draft.

        Returns:
            UUID: blog_posts ID of the created draft
        """
        rss_items = self._get_rss_items()
        rss_items_for_generation = rss_items[: self.max_items]

        title, content_markdown = self.agent.generate_content(rss_items_for_generation)
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

    def run(self) -> RalphLoopResult:
        """
        Execute the full generate-critique-refine loop.

        Creates an initial draft, evaluates quality, and iteratively improves
        until the quality threshold is met or limits (timeout, cost, iterations)
        are exceeded.

        Returns:
            RalphLoopResult with blog_post_id, final_quality_score, iteration_count,
            total_cost_cents, and status ("published", "draft", or "failed")
        """
        timeout_manager = TimeoutManager(
            timeout_minutes=self.timeout_minutes,
            cost_limit_cents=self.cost_limit_cents,
        )

        # Generate initial draft
        rss_items = self._get_rss_items()
        rss_items_for_generation = rss_items[: self.max_items]

        title, content_markdown = self.agent.generate_content(rss_items_for_generation)
        content_html = markdown_to_html(content_markdown)

        # Create blog post record
        blog_post_id = self.supabase_service.create_blog_post(
            title=title,
            content=content_html,
            status="draft",
        )

        # Mark RSS items as used
        item_ids = [item["id"] for item in rss_items_for_generation if item.get("id")]
        if item_ids:
            self.rss_service.mark_items_as_used(item_ids, str(blog_post_id))

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
            iteration_cost = critique_cost + improvement_cost
            self.supabase_service.save_draft_iteration(
                blog_post_id=blog_post_id,
                iteration_number=iteration_count,
                content=improved_content,
                quality_score=new_quality_score,
                critique=validation_result,
                title=current_title,
                api_cost_cents=iteration_cost,
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
            },
        )

        return RalphLoopResult(
            blog_post_id=blog_post_id,
            final_quality_score=quality_score,
            iteration_count=iteration_count,
            total_cost_cents=total_cost_cents,
            status=status,
        )
