#!/bin/bash
#
# Ralph Blog Generation via Claude Code CLI
#
# Invokes claude -p with the generation prompt. Claude Code reads source
# material, writes the post, validates, and publishes — all through
# the generate_helpers.py CLI.
#
# Usage: bash ralph/ralph-generate.sh
# Intended to be called by systemd (ralph.service)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROMPT_FILE="$PROJECT_DIR/ralph/prompts/generate.md"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"

# --- Prerequisites ---

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "ERROR: Prompt file not found: $PROMPT_FILE" >&2
    exit 1
fi

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "ERROR: Virtual environment Python not found: $VENV_PYTHON" >&2
    exit 1
fi

if ! command -v claude &>/dev/null; then
    echo "ERROR: claude CLI not found in PATH" >&2
    exit 1
fi

# Prevent "nested session" error if invoked from within Claude Code
unset CLAUDECODE

# --- Run Claude Code ---

cd "$PROJECT_DIR"

PROMPT=$(cat "$PROMPT_FILE")

# claude -p runs headless (no TTY needed).
# --dangerously-skip-permissions: required for systemd (no interactive approval)
# --allowedTools: restrict to Bash, Read, Write (no git, no web)
# --model sonnet: uses latest Sonnet (4.6) for both editorial decisions and writing
if claude -p "$PROMPT" \
    --dangerously-skip-permissions \
    --allowedTools "Bash(execute commands),Read(read files),Write(write files)" \
    --model sonnet; then
    echo "Ralph generation completed successfully."
    exit 0
else
    EXIT_CODE=$?
    echo "ERROR: Claude Code exited with code $EXIT_CODE" >&2

    # Fallback: send error notification via Python helper
    "$VENV_PYTHON" -m ralph.generate_helpers notify \
        --type ERROR \
        --title "Claude Code generation crashed" \
        --details "claude -p exited with code $EXIT_CODE. Check journalctl -u ralph.service for details." \
        2>/dev/null || true

    "$VENV_PYTHON" -m ralph.generate_helpers log-activity \
        --agent "ralph-generate" \
        --type "blog_generation" \
        --failure \
        --error "claude -p exited with code $EXIT_CODE" \
        2>/dev/null || true

    exit 0  # Don't fail the systemd unit — error is logged and notified
fi
