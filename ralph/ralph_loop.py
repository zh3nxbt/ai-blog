"""RalphLoop entrypoint module with CLI support.

Usage:
    python -m ralph.ralph_loop

Generates one blog post using the RalphLoop iterative refinement system.
Prints summary to stdout and exits with code 0 on success, 1 on failure.
"""

import os
import sys

from ralph_content.ralph_loop import RalphLoop, RalphLoopResult

__all__ = ["RalphLoop", "RalphLoopResult"]


def main() -> int:
    """Execute RalphLoop and print summary to stdout.

    Returns:
        0 on success (published or draft), 1 on failure
    """
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

    print("Starting RalphLoop blog generation...")
    print(f"  Quality threshold: {quality_threshold}")
    print(f"  Timeout: {timeout_minutes} minutes")
    print(f"  Cost limit: {cost_limit_cents} cents")
    print()

    try:
        loop = RalphLoop(
            quality_threshold=quality_threshold,
            timeout_minutes=timeout_minutes,
            cost_limit_cents=cost_limit_cents,
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

        # Exit 0 for published or draft, 1 for failed
        return 0 if result.status in ("published", "draft") else 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
