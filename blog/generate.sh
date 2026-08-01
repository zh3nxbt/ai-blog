#!/bin/bash
#
# Blog Generation via Claude Code CLI
#
# Invokes claude -p with the generation prompt. Claude Code reads source
# material, writes the post, validates, and publishes — all through
# the generate_helpers.py CLI.
#
# Usage: bash blog/generate.sh
# Intended to be called by systemd (blog-generator.service)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROMPT_FILE="$PROJECT_DIR/blog/prompts/generate.md"

if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
    VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
elif [[ -x "$PROJECT_DIR/.venv/Scripts/python.exe" ]]; then
    VENV_PYTHON="$PROJECT_DIR/.venv/Scripts/python.exe"
else
    echo "ERROR: Python virtual environment not found in $PROJECT_DIR/.venv" >&2
    echo "Create it and install requirements before running generation." >&2
    exit 1
fi

# Make `python` in the Claude prompt resolve to this project's virtual
# environment on both Linux and native Windows Git Bash.
export PATH="$(dirname "$VENV_PYTHON"):$PATH"

log_failure_activity() {
    local error_message="$1"
    local output=""

    output=$(
        "$VENV_PYTHON" -m blog.generate_helpers log-activity \
            --agent "blog-generator" \
            --type "blog_generation" \
            --failure \
            --error "$error_message" \
            2>&1 || true
    )

    if [[ -n "$output" ]]; then
        echo "$output" >&2
    fi
}

# --- Prerequisites ---

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "ERROR: Prompt file not found: $PROMPT_FILE" >&2
    exit 1
fi

if ! command -v claude &>/dev/null; then
    echo "ERROR: claude CLI not found in PATH" >&2
    exit 1
fi

# Prevent "nested session" error if invoked from within Claude Code
unset CLAUDECODE

# Claude Code needs either a real login session or ANTHROPIC_API_KEY.
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    AUTH_STATUS="$(claude auth status 2>&1 || true)"
    if [[ "$AUTH_STATUS" != *'"loggedIn": true'* ]]; then
        echo "ERROR: Claude Code is not authenticated." >&2
        echo "$AUTH_STATUS" >&2
        log_failure_activity "claude auth missing or invalid"
        exit 1
    fi
fi

# --- Run Claude Code ---

cd "$PROJECT_DIR"

PROMPT=$(cat "$PROMPT_FILE")
CLAUDE_OUTPUT="$(mktemp)"
trap 'rm -f "$CLAUDE_OUTPUT"' EXIT

# claude -p runs headless (no TTY needed).
# --dangerously-skip-permissions: required for systemd (no interactive approval)
# --allowedTools: restrict to Bash, Read, Write (no git, no web)
# --model sonnet: uses latest Sonnet (4.6) for both editorial decisions and writing
if claude -p "$PROMPT" \
    --dangerously-skip-permissions \
    --allowedTools "Bash(execute commands),Read(read files),Write(write files)" \
    --model sonnet \
    >"$CLAUDE_OUTPUT" 2>&1; then
    cat "$CLAUDE_OUTPUT"
    echo "Blog generation completed successfully."
    exit 0
else
    EXIT_CODE=$?
    cat "$CLAUDE_OUTPUT" >&2
    echo "ERROR: Claude Code exited with code $EXIT_CODE" >&2
    log_failure_activity "claude -p exited with code $EXIT_CODE"

    exit "$EXIT_CODE"
fi
