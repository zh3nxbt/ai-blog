"""Tests for the blog-generation helper CLI."""

from blog.generate_helpers import build_parser


def test_helper_cli_exposes_only_blog_pipeline_commands():
    parser = build_parser()
    subparsers_action = next(
        action for action in parser._actions if action.dest == "command"
    )

    assert set(subparsers_action.choices) == {
        "check-today",
        "fetch-sources",
        "validate",
        "save-post",
        "mark-used",
        "log-activity",
    }
