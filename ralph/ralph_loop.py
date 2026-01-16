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

from ralph_content.ralph_loop import JuiceEvaluationResult, RalphLoop, RalphLoopResult

__all__ = ["JuiceEvaluationResult", "RalphLoop", "RalphLoopResult"]


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

    print("Starting RalphLoop blog generation...")
    print(f"  Quality threshold: {quality_threshold}")
    print(f"  Juice threshold: {juice_threshold}")
    print(f"  Timeout: {timeout_minutes} minutes")
    print(f"  Cost limit: {cost_limit_cents} cents")
    print(f"  Skip if exists: {skip_if_exists}")
    print()

    try:
        loop = RalphLoop(
            quality_threshold=quality_threshold,
            timeout_minutes=timeout_minutes,
            cost_limit_cents=cost_limit_cents,
            juice_threshold=juice_threshold,
            skip_if_exists=skip_if_exists,
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

        if result.status == "skipped":
            print("\nPost already exists for today. Use --force to generate anyway.")
        elif result.status == "skipped_no_juice":
            print("\nSources lacked sufficient value to generate content.")

        # Exit 0 for published, draft, skipped, or skipped_no_juice; 1 for failed
        return 0 if result.status in ("published", "draft", "skipped", "skipped_no_juice") else 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
