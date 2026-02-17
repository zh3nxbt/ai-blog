"""RalphLoop orchestrator for iterative blog post generation."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from anthropic import Anthropic

from config import settings
from ralph_content.agents.critique_agent import CritiqueAgent
from ralph_content.agents.product_marketing import ProductMarketingAgent
from ralph_content.core.api_cost import calculate_api_cost
from ralph_content.core.markdown_renderer import markdown_to_html
from ralph_content.core.timeout_manager import TimeoutManager
from ralph_content.prompts.major_news_screening import MAJOR_NEWS_SCREENING_PROMPT_TEMPLATE
from ralph_content.prompts.source_juice import SOURCE_JUICE_PROMPT_TEMPLATE
from ralph_content.prompts.content_strategy import (
    ContentStrategy,
    StrategyScreeningResult,
    STRATEGY_SCREENING_PROMPT_TEMPLATE,
)
from services.quality_validator import validate_content


@dataclass
class JuiceEvaluationResult:
    """Result of source juice evaluation."""

    should_proceed: bool
    reason: str
    juice_score: float
    best_source: Optional[str] = None
    potential_angle: Optional[str] = None
    cost_cents: int = 0


@dataclass
class MajorNewsScreeningResult:
    """Result of major news pre-screening."""

    items_with_scores: List[Dict[str, Any]]
    highest_scoring_major: Optional[Dict[str, Any]]
    cost_cents: int


@dataclass
class RalphLoopResult:
    """Result of a RalphLoop.run() execution."""

    blog_post_id: UUID
    final_quality_score: float
    iteration_count: int
    total_cost_cents: int
    status: str  # "published", "draft", "failed", "skipped", "skipped_no_juice"
    # Additional fields for notifications
    failure_reason: Optional[str] = None
    juice_score: Optional[float] = None
    source_summaries: Optional[List[str]] = None
    strategy_name: Optional[str] = None
    strategy_reason: Optional[str] = None


class RalphLoop:
    """Generate and refine blog posts with Ralph."""

    DEFAULT_QUALITY_THRESHOLD = 0.85
    DEFAULT_QUALITY_FLOOR = 0.70
    DEFAULT_TIMEOUT_MINUTES = 30
    DEFAULT_COST_LIMIT_CENTS = 100
    DEFAULT_JUICE_THRESHOLD = 0.6
    JUICE_EVAL_MODEL = "claude-3-5-haiku-20241022"
    DEFAULT_SOURCE_MIX = {
        "rss": 4,
        "evergreen": 1,
        "standards": 1,
        "vendor": 1,
    }
    SOURCE_TYPE_ORDER = ("rss", "evergreen", "standards", "vendor", "internal")
    MAX_ITERATIONS = 10
    FRESHNESS_HOURS = 48  # Sources older than this auto-fail juice check
    REJECTION_COOLDOWN_HOURS = 72  # Skip recently rejected sources for this long
    GENERATION_REFRESH_SOURCE_LIMIT = 8  # Refresh top feeds before generation
    GENERATION_REFRESH_ITEMS_PER_SOURCE = 10
    SELECTION_POOL_SIZE = 15  # Fetch this many items, then rank by urgency/recency
    MAJOR_NEWS_THRESHOLD = 0.7  # Score threshold for reserving a slot for major news
    MAJOR_NEWS_RESERVED_SLOTS = 1  # Number of slots reserved for major news
    PRE_SCREEN_MODEL = "claude-3-5-haiku-20241022"  # Cheap model for pre-screening
    # Posting schedule: 0=Monday, 1=Tuesday, ... 6=Sunday
    # Default: Monday, Wednesday, Friday (2-3 posts per week)
    DEFAULT_POSTING_DAYS = (0, 2, 4)  # Mon, Wed, Fri

    def __init__(
        self,
        agent: ProductMarketingAgent | None = None,
        critique_agent: CritiqueAgent | None = None,
        rss_service: Any | None = None,
        topic_item_service: Any | None = None,
        supabase_service: Any | None = None,
        quality_validator: Any | None = None,
        anthropic_client: Anthropic | None = None,
        min_items: int = 3,
        max_items: int = 10,  # Increased for better strategy selection
        quality_threshold: float | None = None,
        quality_floor: float | None = None,
        timeout_minutes: int | None = None,
        cost_limit_cents: int | None = None,
        juice_threshold: float | None = None,
        source_mix: Dict[str, int] | None = None,
        skip_if_exists: bool = True,
        posting_days: Tuple[int, ...] | None = None,
        check_posting_day: bool = True,
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
        self._anthropic_client = anthropic_client or Anthropic(
            api_key=settings.anthropic_api_key
        )
        self.min_items = min_items
        self.max_items = max_items

        self.quality_threshold = quality_threshold or self.DEFAULT_QUALITY_THRESHOLD
        self.quality_floor = quality_floor or self.DEFAULT_QUALITY_FLOOR
        self.timeout_minutes = timeout_minutes or self.DEFAULT_TIMEOUT_MINUTES
        self.cost_limit_cents = cost_limit_cents or self.DEFAULT_COST_LIMIT_CENTS
        self.juice_threshold = juice_threshold or self.DEFAULT_JUICE_THRESHOLD
        self.source_mix = source_mix or self.DEFAULT_SOURCE_MIX
        self.skip_if_exists = skip_if_exists
        self.posting_days = posting_days or self.DEFAULT_POSTING_DAYS
        self.check_posting_day = check_posting_day
        self._selection_screening_cost_cents = 0

    def _check_already_generated_today(self) -> Optional[UUID]:
        """
        Check if a blog post has already been generated today.

        Returns:
            UUID of existing post if found, None otherwise
        """
        client = self.supabase_service.get_supabase_client()
        utc_today = datetime.now(timezone.utc).date()
        start_of_day = f"{utc_today.isoformat()}T00:00:00+00:00"
        start_of_next_day = f"{(utc_today + timedelta(days=1)).isoformat()}T00:00:00+00:00"

        # Query for posts created today (any status)
        response = (
            client.table("blog_posts")
            .select("id, created_at, status")
            .gte("created_at", start_of_day)
            .lt("created_at", start_of_next_day)
            .execute()
        )

        if response.data:
            return UUID(response.data[0]["id"])
        return None

    def _check_sources_freshness(
        self, source_items: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Check if source items have fresh content (within FRESHNESS_HOURS).

        Evergreen sources are always considered fresh since they're timeless content.

        Args:
            source_items: List of source items with optional published_at timestamps

        Returns:
            Tuple of (has_fresh_content, reason)
        """
        if not source_items:
            return False, "No source items available"

        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.FRESHNESS_HOURS)
        fresh_count = 0
        evergreen_count = 0
        total_with_dates = 0

        for item in source_items:
            source_type = item.get("source_type", "").lower()

            # Evergreen sources are always considered fresh (timeless content)
            if source_type == "evergreen":
                evergreen_count += 1
                fresh_count += 1
                continue

            published_at = item.get("published_at")
            if not published_at:
                continue

            total_with_dates += 1

            # Parse the timestamp if it's a string
            if isinstance(published_at, str):
                try:
                    # Handle ISO format timestamps
                    if "T" in published_at:
                        if published_at.endswith("Z"):
                            published_at = published_at[:-1] + "+00:00"
                        parsed_dt = datetime.fromisoformat(published_at)
                    else:
                        parsed_dt = datetime.fromisoformat(published_at)

                    # Ensure timezone-aware
                    if parsed_dt.tzinfo is None:
                        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)

                    if parsed_dt >= cutoff:
                        fresh_count += 1
                except (ValueError, TypeError):
                    continue
            elif isinstance(published_at, datetime):
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=timezone.utc)
                if published_at >= cutoff:
                    fresh_count += 1

        # If no items have dates and no evergreen, assume they're fresh (benefit of the doubt)
        if total_with_dates == 0 and evergreen_count == 0:
            return True, "No published dates available, proceeding with evaluation"

        # Require at least one fresh source (including evergreen)
        if fresh_count > 0:
            if evergreen_count > 0 and fresh_count == evergreen_count:
                return True, f"{evergreen_count} evergreen source(s) included"
            elif evergreen_count > 0:
                return True, f"{fresh_count} fresh sources ({evergreen_count} evergreen + {fresh_count - evergreen_count} recent)"
            return True, f"{fresh_count}/{total_with_dates} sources are fresh"
        else:
            return False, f"All {total_with_dates} sources are older than {self.FRESHNESS_HOURS} hours"

    def _evaluate_source_juice(
        self, source_items: List[Dict[str, Any]]
    ) -> JuiceEvaluationResult:
        """
        Evaluate whether source items have enough "juice" to warrant a blog post.

        Uses Claude to analyze the newsworthiness and value of the sources.
        Automatically fails if all sources are older than FRESHNESS_HOURS.

        Args:
            source_items: List of source items to evaluate

        Returns:
            JuiceEvaluationResult with should_proceed, reason, juice_score, etc.
        """
        # First check freshness
        is_fresh, freshness_reason = self._check_sources_freshness(source_items)
        if not is_fresh:
            return JuiceEvaluationResult(
                should_proceed=False,
                reason=f"Auto-skip: {freshness_reason}",
                juice_score=0.0,
                best_source=None,
                potential_angle=None,
                cost_cents=0,
            )

        # Format source items for the prompt
        source_text_parts = []
        for i, item in enumerate(source_items, 1):
            title = item.get("title", "Untitled")
            summary = item.get("summary", item.get("content", "No summary"))
            source_type = item.get("source_type", "unknown")
            published = item.get("published_at", "Unknown date")
            url = item.get("url", "No URL")

            # Truncate summary if too long
            if len(summary) > 500:
                summary = summary[:500] + "..."

            source_text_parts.append(
                f"{i}. [{source_type.upper()}] {title}\n"
                f"   Published: {published}\n"
                f"   URL: {url}\n"
                f"   Summary: {summary}"
            )

        source_text = "\n\n".join(source_text_parts)
        prompt = SOURCE_JUICE_PROMPT_TEMPLATE.format(source_items=source_text)

        def _clean_json_candidate(text: str) -> str:
            """Normalize optional code-fenced model output before JSON parsing."""
            candidate = text.strip()
            if candidate.startswith("```"):
                lines = candidate.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                candidate = "\n".join(lines).strip()
            return candidate

        # Parse with one retry. Fail closed if structure cannot be trusted.
        cost_cents = 0
        result: Optional[Dict[str, Any]] = None
        parse_error: Optional[str] = None

        for attempt in range(2):
            retry_hint = ""
            if attempt > 0:
                retry_hint = (
                    "\n\nIMPORTANT: Return valid JSON only. "
                    "No markdown, no code fences, no prose."
                )

            response = self._anthropic_client.messages.create(
                model=self.JUICE_EVAL_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt + retry_hint}],
            )

            cost_cents += calculate_api_cost(
                response.usage.input_tokens,
                response.usage.output_tokens,
                model=self.JUICE_EVAL_MODEL,
            )

            response_text = _clean_json_candidate(response.content[0].text)
            try:
                result = json.loads(response_text)
                break
            except json.JSONDecodeError as exc:
                parse_error = str(exc)
                continue

        if result is None:
            return JuiceEvaluationResult(
                should_proceed=False,
                reason=(
                    "Failed to parse juice evaluation response; "
                    f"skipping generation for safety ({parse_error or 'unknown parse error'})"
                ),
                juice_score=0.0,
                best_source=None,
                potential_angle=None,
                cost_cents=cost_cents,
            )

        juice_score = float(result.get("juice_score", 0.5))
        should_proceed = result.get("should_proceed", juice_score >= self.juice_threshold)
        reason = result.get("reason", "No reason provided")
        best_source = result.get("best_source")
        potential_angle = result.get("potential_angle")

        # Override should_proceed based on juice_threshold
        if juice_score < self.juice_threshold:
            should_proceed = False
            if "below threshold" not in reason.lower():
                reason = f"{reason} (juice_score {juice_score:.2f} < threshold {self.juice_threshold})"

        return JuiceEvaluationResult(
            should_proceed=should_proceed,
            reason=reason,
            juice_score=juice_score,
            best_source=best_source,
            potential_angle=potential_angle,
            cost_cents=cost_cents,
        )

    def generate_initial_draft(self) -> UUID:
        """
        Generate the initial blog post draft.

        Returns:
            UUID: blog_posts ID of the created draft
        """
        source_items, _ = self._get_source_items()

        # Screen for content strategy
        strategy_result = self._screen_for_content_strategy(source_items)
        filtered_items = self._filter_items_by_strategy(source_items, strategy_result)

        strategy_context = {
            "anchor_index": 0 if strategy_result.strategy == ContentStrategy.ANCHOR_CONTEXT else None,
            "theme_name": next(iter(strategy_result.theme_clusters.keys()), "Manufacturing"),
            "unifying_angle": strategy_result.strategy_reason,
        }

        post_data = self.agent.generate_content(
            filtered_items,
            strategy=strategy_result.strategy,
            strategy_context=strategy_context,
        )
        title = post_data["title"]
        content_markdown = post_data["content_markdown"]
        content_html = markdown_to_html(content_markdown)
        blog_post_id = self.supabase_service.create_blog_post(
            title=title,
            content=content_html,
            status="draft",
            meta_description=post_data.get("meta_description"),
            meta_keywords=post_data.get("meta_keywords"),
            tags=post_data.get("tags"),
        )

        self.supabase_service.save_draft_iteration(
            blog_post_id=blog_post_id,
            iteration_number=1,
            content=content_markdown,
            quality_score=0.0,
            critique={"note": "initial draft", "strategy": strategy_result.strategy.value},
            title=title,
        )

        self._mark_source_items_as_used(filtered_items, blog_post_id)

        return blog_post_id

    def _get_source_items(self) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Fetch source items using the configured source mix."""
        targets = self._build_source_targets()
        desired_total = min(self.max_items, sum(targets.values()))
        desired_total = max(self.min_items, desired_total)

        def collect_items(initial_exclude_ids: set[str]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
            selected_items: List[Dict[str, Any]] = []
            selected_ids: set[str] = set(initial_exclude_ids)
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
                    source_mix_counts[source_type] = (
                        source_mix_counts.get(source_type, 0) + len(extra_items)
                    )
                    remaining_slots = desired_total - len(selected_items)

            return selected_items, source_mix_counts

        recently_rejected_ids = self._get_recently_rejected_source_ids()
        selected_items, source_mix_counts = collect_items(recently_rejected_ids)

        # If strict exclusion is too aggressive, fall back to full pool.
        if len(selected_items) < self.min_items and recently_rejected_ids:
            selected_items, source_mix_counts = collect_items(set())

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

        return targets

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        """Parse common datetime formats into timezone-aware UTC datetimes."""
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value

        if not isinstance(value, str) or not value:
            return None

        try:
            normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None

    def _item_sort_key(self, item: Dict[str, Any]) -> Tuple[float, int, float]:
        """
        Rank items by urgency, source priority, then recency.

        Higher tuple values are better.
        """
        urgency = float(item.get("urgency_score") or 0.0)
        source_priority = int(item.get("source_priority") or 0)

        published_at = self._parse_datetime(item.get("published_at"))
        created_at = self._parse_datetime(item.get("created_at"))
        recency_dt = published_at or created_at
        recency_ts = recency_dt.timestamp() if recency_dt else 0.0

        return (urgency, source_priority, recency_ts)

    def _get_recently_rejected_source_ids(self) -> set[str]:
        """
        Return source item IDs from recent skipped_no_juice runs.

        This prevents repeatedly evaluating the same weak pool.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.REJECTION_COOLDOWN_HOURS)

        try:
            client = self.supabase_service.get_supabase_client()
            response = (
                client.table("blog_agent_activity")
                .select("metadata")
                .eq("activity_type", "skipped_no_juice")
                .gte("created_at", cutoff.isoformat())
                .execute()
            )
        except Exception:
            return set()

        rejected_ids: set[str] = set()
        for row in response.data or []:
            metadata = row.get("metadata") or {}
            source_item_ids = metadata.get("source_item_ids") or []
            for item_id in source_item_ids:
                if isinstance(item_id, str) and item_id:
                    rejected_ids.add(item_id)

        return rejected_ids

    def _fetch_items_for_source_type(
        self,
        source_type: str,
        limit: int,
        exclude_ids: set[str],
    ) -> List[Dict[str, Any]]:
        """Fetch items for a source type, with special handling for RSS.

        For RSS items: Uses major news pre-screening to prioritize breaking news
        and reserves a slot for the highest-scoring major news item.

        For other types: Selects from a larger pool using deterministic ranking
        (source priority + recency) to favor stronger candidates.
        """
        if limit <= 0:
            return []

        # Fetch a larger pool to select from
        pool_size = max(self.SELECTION_POOL_SIZE, limit + len(exclude_ids))

        if source_type == "rss":
            # Use major news screening for RSS to prioritize important stories
            items = self._get_rss_items_for_mix(pool_size)
            return self._select_rss_with_major_news_slot(items, limit, exclude_ids)
        else:
            items = self.topic_item_service.fetch_unused_items_by_source_type(
                source_type=source_type,
                limit=pool_size,
            )

            # Filter out already-selected items
            filtered = [item for item in items if item.get("id") not in exclude_ids]
            ranked = sorted(filtered, key=self._item_sort_key, reverse=True)
            return ranked[:limit]

    def _get_rss_items_for_mix(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch unused RSS items for mixed-source selection."""
        # Keep the pool fresh before selection. This is ingestion-only, no LLM usage.
        if hasattr(self.rss_service, "refresh_active_sources"):
            try:
                self.rss_service.refresh_active_sources(
                    per_source_limit=self.GENERATION_REFRESH_ITEMS_PER_SOURCE,
                    max_sources=self.GENERATION_REFRESH_SOURCE_LIMIT,
                )
            except Exception as exc:
                # Generation can continue with existing items if refresh fails.
                try:
                    self.supabase_service.log_agent_activity(
                        agent_name="ralph-loop",
                        activity_type="rss_refresh_before_generation_failed",
                        success=False,
                        error_message=str(exc),
                        metadata={
                            "source_limit": self.GENERATION_REFRESH_SOURCE_LIMIT,
                            "items_per_source": self.GENERATION_REFRESH_ITEMS_PER_SOURCE,
                        },
                    )
                except Exception:
                    pass

        unused_items = self.rss_service.fetch_unused_items(limit=limit)

        if len(unused_items) < limit:
            sources = self.rss_service.fetch_active_sources()
            for source in sources:
                try:
                    self.rss_service.fetch_feed_items(
                        source["id"],
                        limit=self.GENERATION_REFRESH_ITEMS_PER_SOURCE,
                    )
                except Exception:
                    continue

                unused_items = self.rss_service.fetch_unused_items(limit=limit)
                if len(unused_items) >= limit:
                    break

            unused_items = self.rss_service.fetch_unused_items(limit=limit)

        for item in unused_items:
            item.setdefault("source_type", "rss")

        return sorted(unused_items, key=self._item_sort_key, reverse=True)

    def _pre_screen_rss_pool(
        self,
        items: List[Dict[str, Any]],
    ) -> MajorNewsScreeningResult:
        """
        Pre-screen RSS items to identify major news worthy of a reserved slot.

        Uses a cheap model (Haiku) to evaluate the pool and identify any items
        that represent breaking news or significant developments.

        Args:
            items: List of RSS items to screen

        Returns:
            MajorNewsScreeningResult with scored items and highest-scoring major news
        """
        # Skip screening if pool is small (no benefit from prioritization)
        if len(items) <= 4:
            return MajorNewsScreeningResult(
                items_with_scores=[
                    {**item, "urgency_score": 0.5, "is_major_news": False}
                    for item in items
                ],
                highest_scoring_major=None,
                cost_cents=0,
            )

        # Format items for the prompt
        items_for_prompt = []
        for i, item in enumerate(items):
            items_for_prompt.append({
                "index": i,
                "title": item.get("title", "Untitled"),
                "summary": (item.get("summary") or item.get("content", ""))[:300],
                "published_at": item.get("published_at"),
            })

        prompt = MAJOR_NEWS_SCREENING_PROMPT_TEMPLATE.format(
            items_json=json.dumps(items_for_prompt, indent=2)
        )

        # Call Haiku for cheap screening
        response = self._anthropic_client.messages.create(
            model=self.PRE_SCREEN_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        cost_cents = calculate_api_cost(
            response.usage.input_tokens,
            response.usage.output_tokens,
            model=self.PRE_SCREEN_MODEL,
        )

        # Parse response
        response_text = response.content[0].text.strip()

        # Handle optional code fences
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        try:
            result = json.loads(response_text)
            screening_results = result.get("screening_results", [])
        except json.JSONDecodeError:
            # If parsing fails, return items without scoring
            return MajorNewsScreeningResult(
                items_with_scores=[
                    {**item, "urgency_score": 0.5, "is_major_news": False}
                    for item in items
                ],
                highest_scoring_major=None,
                cost_cents=cost_cents,
            )

        # Attach scores to items
        items_with_scores = []
        for item in items:
            # Find matching result by index
            item_copy = dict(item)
            matching_result = None
            for i, orig_item in enumerate(items):
                if orig_item is item:
                    for sr in screening_results:
                        if sr.get("item_index") == i:
                            matching_result = sr
                            break
                    break

            if matching_result:
                item_copy["urgency_score"] = matching_result.get("urgency_score", 0.5)
                item_copy["is_major_news"] = matching_result.get("is_major_news", False)
                item_copy["major_news_reason"] = matching_result.get("reason", "")
            else:
                item_copy["urgency_score"] = 0.5
                item_copy["is_major_news"] = False

            items_with_scores.append(item_copy)

        # Find highest-scoring major news
        major_news_items = [
            item for item in items_with_scores
            if item.get("is_major_news") and item.get("urgency_score", 0) >= self.MAJOR_NEWS_THRESHOLD
        ]

        highest_scoring_major = None
        if major_news_items:
            highest_scoring_major = max(major_news_items, key=lambda x: x.get("urgency_score", 0))

        return MajorNewsScreeningResult(
            items_with_scores=items_with_scores,
            highest_scoring_major=highest_scoring_major,
            cost_cents=cost_cents,
        )

    def _select_rss_with_major_news_slot(
        self,
        pool: List[Dict[str, Any]],
        count: int,
        exclude_ids: set[str],
    ) -> List[Dict[str, Any]]:
        """
        Select RSS items with a reserved slot for major news.

        Calls pre-screening to identify major news, reserves one slot for the
        highest-scoring major news item if found, then fills remaining slots
        using ranked selection from the rest of the pool.

        Args:
            pool: Full pool of RSS items to select from
            count: Number of items to select
            exclude_ids: IDs to exclude from selection

        Returns:
            List of selected RSS items
        """
        # Filter out excluded items
        filtered_pool = [item for item in pool if item.get("id") not in exclude_ids]

        if len(filtered_pool) <= count:
            return filtered_pool

        # Pre-screen the pool
        screening_result = self._pre_screen_rss_pool(filtered_pool)
        self._selection_screening_cost_cents += screening_result.cost_cents
        selected: List[Dict[str, Any]] = []

        # Reserve slot for major news if found
        if screening_result.highest_scoring_major and self.MAJOR_NEWS_RESERVED_SLOTS > 0:
            major_item = screening_result.highest_scoring_major
            selected.append(major_item)
            remaining_count = count - 1
            remaining_pool = [
                item for item in screening_result.items_with_scores
                if item.get("id") != major_item.get("id")
            ]
        else:
            remaining_count = count
            remaining_pool = screening_result.items_with_scores

        # Fill remaining slots by ranked priority (urgency, source priority, recency)
        if remaining_count > 0 and remaining_pool:
            ranked_remaining = sorted(
                remaining_pool,
                key=self._item_sort_key,
                reverse=True,
            )
            additional = ranked_remaining[:remaining_count]
            selected.extend(additional)

        return selected

    def _screen_for_content_strategy(
        self,
        items: List[Dict[str, Any]],
    ) -> StrategyScreeningResult:
        """
        Analyze source items and recommend the best content strategy.

        Uses a cheap model (Haiku) to evaluate the pool and determine whether
        to use anchor+context, thematic, analysis, or deep-dive approach.

        Args:
            items: List of source items to analyze

        Returns:
            StrategyScreeningResult with recommended strategy and context
        """
        if len(items) <= 1:
            # Only one item - default to deep dive
            return StrategyScreeningResult(
                strategy=ContentStrategy.DEEP_DIVE,
                strategy_reason="Single source available - using deep dive",
                anchor_item_index=None,
                theme_clusters={},
                recommended_indices=[0] if items else [],
                items_with_scores=[
                    {**item, "urgency_score": 0.7, "themes": [], "summary": item.get("title", "")}
                    for item in items
                ],
                cost_cents=0,
            )

        # Format items for the prompt
        items_for_prompt = []
        for i, item in enumerate(items):
            items_for_prompt.append({
                "index": i,
                "title": item.get("title", "Untitled"),
                "summary": (item.get("summary") or item.get("content", ""))[:400],
                "source_type": item.get("source_type", "unknown"),
                "published_at": item.get("published_at"),
            })

        prompt = STRATEGY_SCREENING_PROMPT_TEMPLATE.format(
            items_json=json.dumps(items_for_prompt, indent=2)
        )

        # Call Haiku for cheap screening
        response = self._anthropic_client.messages.create(
            model=self.PRE_SCREEN_MODEL,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )

        cost_cents = calculate_api_cost(
            response.usage.input_tokens,
            response.usage.output_tokens,
            model=self.PRE_SCREEN_MODEL,
        )

        # Parse response
        response_text = response.content[0].text.strip()

        # Handle optional code fences
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback to analysis strategy if parsing fails
            return StrategyScreeningResult(
                strategy=ContentStrategy.ANALYSIS,
                strategy_reason="Parsing failed - defaulting to analysis approach",
                anchor_item_index=None,
                theme_clusters={},
                recommended_indices=list(range(len(items))),
                items_with_scores=[
                    {**item, "urgency_score": 0.5, "themes": [], "summary": item.get("title", "")}
                    for item in items
                ],
                cost_cents=cost_cents,
            )

        # Map strategy string to enum
        strategy_str = result.get("strategy", "analysis").lower()
        strategy_map = {
            "anchor_context": ContentStrategy.ANCHOR_CONTEXT,
            "thematic": ContentStrategy.THEMATIC,
            "analysis": ContentStrategy.ANALYSIS,
            "deep_dive": ContentStrategy.DEEP_DIVE,
        }
        strategy = strategy_map.get(strategy_str, ContentStrategy.ANALYSIS)

        # Build items_with_scores from response
        item_scores = result.get("item_scores", [])
        items_with_scores = []
        for item in items:
            item_copy = dict(item)
            # Find matching score
            for i, orig_item in enumerate(items):
                if orig_item is item:
                    for score_data in item_scores:
                        if score_data.get("item_index") == i:
                            item_copy["urgency_score"] = score_data.get("urgency_score", 0.5)
                            item_copy["themes"] = score_data.get("themes", [])
                            item_copy["summary"] = score_data.get("summary", "")
                            break
                    break
            items_with_scores.append(item_copy)

        return StrategyScreeningResult(
            strategy=strategy,
            strategy_reason=result.get("strategy_reason", ""),
            anchor_item_index=result.get("anchor_index"),
            theme_clusters=result.get("theme_clusters", {}),
            recommended_indices=result.get("recommended_indices", list(range(len(items)))),
            items_with_scores=items_with_scores,
            cost_cents=cost_cents,
        )

    def _filter_items_by_strategy(
        self,
        items: List[Dict[str, Any]],
        strategy_result: StrategyScreeningResult,
    ) -> List[Dict[str, Any]]:
        """
        Filter and reorder items based on strategy recommendation.

        Args:
            items: Original source items
            strategy_result: Strategy screening result

        Returns:
            Filtered/reordered list of items to use for content generation
        """
        recommended = strategy_result.recommended_indices

        # Get items in recommended order
        filtered = []
        for idx in recommended:
            if 0 <= idx < len(items):
                filtered.append(items[idx])

        # If no recommendations, use all items
        if not filtered:
            return items

        # For anchor strategy, ensure anchor is first
        if strategy_result.strategy == ContentStrategy.ANCHOR_CONTEXT:
            anchor_idx = strategy_result.anchor_item_index
            if anchor_idx is not None and 0 <= anchor_idx < len(items):
                anchor_item = items[anchor_idx]
                # Remove anchor from filtered if present, then prepend
                filtered = [item for item in filtered if item is not anchor_item]
                filtered.insert(0, anchor_item)

        # Limit to reasonable number based on strategy
        max_items = {
            ContentStrategy.ANCHOR_CONTEXT: 4,  # 1 anchor + 3 context
            ContentStrategy.THEMATIC: 4,
            ContentStrategy.ANALYSIS: 5,
            ContentStrategy.DEEP_DIVE: 2,
        }
        limit = max_items.get(strategy_result.strategy, 5)

        return filtered[:limit]

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

        # Check if today is a posting day (2-3 posts per week)
        if self.check_posting_day:
            today_weekday = datetime.now(timezone.utc).weekday()  # 0=Monday, 6=Sunday
            if today_weekday not in self.posting_days:
                from uuid import uuid4
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                posting_day_names = [day_names[d] for d in sorted(self.posting_days)]

                self.supabase_service.log_agent_activity(
                    agent_name="ralph-loop",
                    activity_type="skipped_not_posting_day",
                    success=True,
                    metadata={
                        "reason": "not_a_posting_day",
                        "today": day_names[today_weekday],
                        "posting_days": posting_day_names,
                        "timezone": "UTC",
                    },
                )
                return RalphLoopResult(
                    blog_post_id=uuid4(),
                    final_quality_score=0.0,
                    iteration_count=0,
                    total_cost_cents=0,
                    status="skipped_not_posting_day",
                    failure_reason=f"Not a posting day. Posts scheduled for: {', '.join(posting_day_names)}",
                )

        timeout_manager = TimeoutManager(
            timeout_minutes=self.timeout_minutes,
            cost_limit_cents=self.cost_limit_cents,
        )
        self._selection_screening_cost_cents = 0

        # Get source items first
        source_items, source_mix_counts = self._get_source_items()

        # Evaluate source juice before content generation
        juice_result = self._evaluate_source_juice(source_items)

        # Prepare detailed source item data for logging
        source_items_detail = []
        for item in source_items:
            source_items_detail.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "summary": item.get("summary", item.get("content", ""))[:500],  # Truncate for storage
                "url": item.get("url"),
                "published_at": item.get("published_at"),
                "source_type": item.get("source_type"),
                "source_name": item.get("source_name"),  # RSS feed name if available
            })

        # Log juice evaluation activity with full source details
        self.supabase_service.log_agent_activity(
            agent_name="ralph-loop",
            activity_type="juice_evaluation",
            success=True,
            metadata={
                "juice_score": juice_result.juice_score,
                "should_proceed": juice_result.should_proceed,
                "reason": juice_result.reason,
                "best_source": juice_result.best_source,
                "potential_angle": juice_result.potential_angle,
                "cost_cents": juice_result.cost_cents,
                "selection_screening_cost_cents": self._selection_screening_cost_cents,
                "source_mix": source_mix_counts,
                "source_count": len(source_items),
            },
            input_data={
                "source_items": source_items_detail,
                "juice_threshold": self.juice_threshold,
            },
        )

        # Skip if juice is too low
        if not juice_result.should_proceed:
            # Create a placeholder UUID for the result (no post created)
            from uuid import uuid4

            placeholder_id = uuid4()

            self.supabase_service.log_agent_activity(
                agent_name="ralph-loop",
                activity_type="skipped_no_juice",
                success=True,
                metadata={
                    "juice_score": juice_result.juice_score,
                    "juice_threshold": self.juice_threshold,
                    "reason": juice_result.reason,
                    "source_titles": [
                        item.get("title", "Untitled") for item in source_items[:5]
                    ],
                    "source_item_ids": [
                        item["id"] for item in source_items if item.get("id")
                    ],
                    "selection_screening_cost_cents": self._selection_screening_cost_cents,
                },
            )

            # Build source summaries for notification
            source_summaries = [
                f"[{item.get('source_type', 'unknown').upper()}] {item.get('title', 'Untitled')}"
                for item in source_items[:5]
            ]

            return RalphLoopResult(
                blog_post_id=placeholder_id,
                final_quality_score=0.0,
                iteration_count=0,
                total_cost_cents=(
                    juice_result.cost_cents + self._selection_screening_cost_cents
                ),
                status="skipped_no_juice",
                juice_score=juice_result.juice_score,
                failure_reason=juice_result.reason,
                source_summaries=source_summaries,
            )

        # Screen for content strategy
        strategy_result = self._screen_for_content_strategy(source_items)

        # Filter items based on strategy
        filtered_items = self._filter_items_by_strategy(source_items, strategy_result)

        # Build strategy context for content generation
        strategy_context = {
            "anchor_index": 0 if strategy_result.strategy == ContentStrategy.ANCHOR_CONTEXT else None,
            "theme_name": next(iter(strategy_result.theme_clusters.keys()), "Manufacturing"),
            "unifying_angle": strategy_result.strategy_reason,
        }

        # Log strategy selection
        self.supabase_service.log_agent_activity(
            agent_name="ralph-loop",
            activity_type="strategy_selection",
            success=True,
            metadata={
                "strategy": strategy_result.strategy.value,
                "strategy_reason": strategy_result.strategy_reason,
                "theme_clusters": strategy_result.theme_clusters,
                "recommended_indices": strategy_result.recommended_indices,
                "original_item_count": len(source_items),
                "filtered_item_count": len(filtered_items),
                "cost_cents": strategy_result.cost_cents,
            },
        )

        # Proceed with content generation using strategy
        post_data = self.agent.generate_content(
            filtered_items,
            strategy=strategy_result.strategy,
            strategy_context=strategy_context,
        )
        title = post_data["title"]
        content_markdown = post_data["content_markdown"]
        content_html = markdown_to_html(content_markdown)

        # Create blog post record
        blog_post_id = self.supabase_service.create_blog_post(
            title=title,
            content=content_html,
            status="draft",
            meta_description=post_data.get("meta_description"),
            meta_keywords=post_data.get("meta_keywords"),
            tags=post_data.get("tags"),
        )

        # Mark source items as used (use filtered items, not original)
        self._mark_source_items_as_used(filtered_items, blog_post_id)

        # Track costs per iteration (generation, critique, improvement)
        last_main_input = 0
        last_main_output = 0
        last_crit_input = 0
        last_crit_output = 0
        # Include juice evaluation and strategy screening costs
        total_cost_cents = (
            juice_result.cost_cents
            + strategy_result.cost_cents
            + self._selection_screening_cost_cents
        )

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

            # Hard stop after this iteration if the improvement call pushed cost over limit.
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
                        "reason": "cost_limit_exceeded_after_improvement",
                    },
                )
                break

        # Determine final status based on quality
        if quality_score >= self.quality_threshold:
            status = "published"
            failure_reason = None
        elif quality_score >= self.quality_floor:
            status = "draft"
            failure_reason = None
        else:
            status = "failed"
            failure_reason = (
                f"Quality score {quality_score:.2f} below minimum threshold "
                f"{self.quality_floor:.2f} after {iteration_count} iterations"
            )

        # Update blog post with final content and status
        client = self.supabase_service.get_supabase_client()
        update_data = {"content": markdown_to_html(current_content), "status": status}
        if status == "published":
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

        # Build source summaries for notification
        source_summaries = [
            f"[{item.get('source_type', 'unknown').upper()}] {item.get('title', 'Untitled')}"
            for item in filtered_items
        ]

        return RalphLoopResult(
            blog_post_id=blog_post_id,
            final_quality_score=quality_score,
            iteration_count=iteration_count,
            total_cost_cents=total_cost_cents,
            status=status,
            failure_reason=failure_reason,
            source_summaries=source_summaries,
            strategy_name=strategy_result.strategy.value,
            strategy_reason=strategy_result.strategy_reason,
        )
