"""RalphLoop entrypoint module with CLI support.

Usage:
    python -m ralph.ralph_loop          # Normal run (skips if post exists today)
    python -m ralph.ralph_loop --force  # Force run even if post exists today

Generates one blog post using the RalphLoop iterative refinement system.
Prints summary to stdout and exits with code 0 on success, 1 on failure.
"""

import argparse
import os
import sys
import traceback

from ralph_content.ralph_loop import JuiceEvaluationResult, RalphLoop, RalphLoopResult

__all__ = ["JuiceEvaluationResult", "RalphLoop", "RalphLoopResult"]


def _send_notification(
    alert_type: str,
    title: str,
    details: str,
    blog_post_id: str | None = None,
) -> None:
    """Send email notification if configured. Logs to activity table."""
    from services.email_service import is_configured, send_alert, EmailServiceError

    if not is_configured():
        print(f"[{alert_type}] Email not configured, skipping notification")
        return

    try:
        email_id = send_alert(
            alert_type=alert_type,
            title=title,
            details=details,
            blog_post_id=blog_post_id,
        )
        print(f"[{alert_type}] Notification sent (email_id: {email_id})")

        # Log notification to activity table
        try:
            from services import supabase_service
            supabase_service.log_agent_activity(
                agent_name="ralph-loop",
                activity_type="notification_sent",
                success=True,
                metadata={
                    "alert_type": alert_type,
                    "title": title,
                    "email_id": email_id,
                    "blog_post_id": blog_post_id,
                },
            )
        except Exception as log_err:
            print(f"Warning: Failed to log notification activity: {log_err}")

    except EmailServiceError as e:
        print(f"[{alert_type}] Failed to send notification: {e}")


def main() -> int:
    """Execute RalphLoop and print summary to stdout.

    Returns:
        0 on success (published, draft, or skipped), 1 on failure
    """
    parser = argparse.ArgumentParser(
        description="Generate a blog post using RalphLoop iterative refinement"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force generation even if a post already exists today",
    )
    parser.add_argument(
        "--force-day",
        action="store_true",
        help="Force generation even if today is not a scheduled posting day",
    )
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv()

    # Validate required environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_SECRET", "ANTHROPIC_API_KEY"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        return 1

    # Read configuration from environment with defaults
    quality_threshold = float(os.environ.get("RALPH_QUALITY_THRESHOLD", "0.85"))
    timeout_minutes = int(os.environ.get("RALPH_TIMEOUT_MINUTES", "30"))
    cost_limit_cents = int(os.environ.get("RALPH_COST_LIMIT_CENTS", "100"))
    juice_threshold = float(os.environ.get("RALPH_JUICE_THRESHOLD", "0.6"))
    skip_if_exists = not args.force
    check_posting_day = not args.force_day

    print("Starting RalphLoop blog generation...")
    print(f"  Quality threshold: {quality_threshold}")
    print(f"  Juice threshold: {juice_threshold}")
    print(f"  Timeout: {timeout_minutes} minutes")
    print(f"  Cost limit: {cost_limit_cents} cents")
    print(f"  Skip if exists: {skip_if_exists}")
    print(f"  Check posting day: {check_posting_day}")
    print()

    try:
        loop = RalphLoop(
            quality_threshold=quality_threshold,
            timeout_minutes=timeout_minutes,
            cost_limit_cents=cost_limit_cents,
            juice_threshold=juice_threshold,
            skip_if_exists=skip_if_exists,
            check_posting_day=check_posting_day,
        )
        result = loop.run()

        # Print summary
        print()
        print("=" * 50)
        print("RalphLoop Complete")
        print("=" * 50)
        print(f"Status:      {result.status}")
        print(f"Quality:     {result.final_quality_score:.2f}")
        print(f"Iterations:  {result.iteration_count}")
        print(f"Cost:        {result.total_cost_cents} cents")
        print(f"Blog ID:     {result.blog_post_id}")
        print("=" * 50)

        # Send notifications based on status
        if result.status == "published":
            source_list = "\n".join(result.source_summaries or ["No sources listed"])
            strategy_name = result.strategy_name or "default"
            strategy_reason = result.strategy_reason or "No strategy context"
            details = f"""Quality Score: {result.final_quality_score:.2f}
Iterations: {result.iteration_count}
Cost: {result.total_cost_cents} cents

Strategy: {strategy_name}
Approach: {strategy_reason}

Sources Used:
{source_list}"""
            _send_notification(
                alert_type="SUCCESS",
                title="Blog post published",
                details=details,
                blog_post_id=str(result.blog_post_id),
            )

        elif result.status == "skipped":
            print("\nPost already exists for today. Use --force to generate anyway.")

        elif result.status == "skipped_not_posting_day":
            print(f"\n{result.failure_reason}")
            print("Use --force-day to generate anyway.")

        elif result.status == "skipped_no_juice":
            print("\nSources lacked sufficient value to generate content.")
            # Build details for notification
            source_list = "\n".join(result.source_summaries or ["No sources available"])
            details = f"""Juice Score: {result.juice_score:.2f} (threshold: {juice_threshold})
Reason: {result.failure_reason or 'Unknown'}

Sources Evaluated:
{source_list}

Cost: {result.total_cost_cents} cents"""
            _send_notification(
                alert_type="SKIPPED",
                title="Sources lacked value - no post generated",
                details=details,
            )

        elif result.status == "failed":
            details = f"""Quality Score: {result.final_quality_score:.2f}
Iterations: {result.iteration_count}
Reason: {result.failure_reason or 'Quality below minimum threshold'}

Cost: {result.total_cost_cents} cents"""
            _send_notification(
                alert_type="FAILED",
                title="Content generation failed quality check",
                details=details,
                blog_post_id=str(result.blog_post_id),
            )

        # Exit 0 for published, draft, skipped, skipped_not_posting_day, or skipped_no_juice; 1 for failed
        return 0 if result.status in ("published", "draft", "skipped", "skipped_not_posting_day", "skipped_no_juice") else 1

    except Exception as e:
        # Send error notification
        error_details = f"""Error: {e}

Traceback:
{traceback.format_exc()}"""
        _send_notification(
            alert_type="ERROR",
            title=f"Exception during generation: {type(e).__name__}",
            details=error_details,
        )
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
