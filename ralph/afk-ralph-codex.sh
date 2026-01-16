#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <iterations>"
  exit 1
fi

for ((i=1; i<=$1; i++)); do
  echo "=== Iteration $i of $1 ==="

  codex_cmd=(codex "@AGENTS.md @ralph/PRD.md @ralph/PRD.json @ralph/PHASES.md @ralph/progress.txt \
1. Read AGENTS.md for project principles and task prioritization guidance. \
2. Read PHASES.md to understand the current phase, exit criteria, and what's next. \
3. Read the PRD.md for requirements and PRD.json for the task list with acceptance criteria. \
4. Read progress.txt for completed work and learnings. \
5. Find the next incomplete task (passes: false) in PRD.json following prioritization order. \
5a. If implementing a task in a series (e.g., sys-002, alert-001), check 1-2 previous commits in that series for implementation patterns using 'git log --grep=<task-id>'. \
6. Create a new git branch named after the task (e.g., 'task/sys-001-systemd-service'). \
7. Implement the task. \
8. Commit your changes to the branch. \
9. Update ralph/progress.txt with what you did. \
10. Push the branch to GitHub and create a pull request. \
ONLY DO ONE TASK AT A TIME. \
If the PRD is complete, output <promise>COMPLETE</promise>.")

  if [ -t 1 ]; then
    result=$("${codex_cmd[@]}")
  else
    if command -v script >/dev/null 2>&1; then
      result=$(script -q -c "${codex_cmd[*]}" /dev/null)
    else
      echo "Error: stdout is not a terminal and 'script' is not available." >&2
      exit 1
    fi
  fi

  echo "$result"

  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "PRD complete after $i iterations."
    exit 0
  fi
done

echo "Completed $1 iterations. PRD may not be complete yet."
