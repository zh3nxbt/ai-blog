#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <iterations>"
  exit 1
fi

for ((i=1; i<=$1; i++)); do
  echo "=== Iteration $i of $1 ==="

  result=$(claude -p --permission-mode acceptEdits "@claude.md @ralph/PRD.md @ralph/PHASES.md @ralph/progress.txt \
1. Read claude.md for project principles and task prioritization guidance. \
2. Read PHASES.md to understand the current phase, exit criteria, and what's next. \
3. Read the PRD and progress file. \
4. Find the next incomplete task following prioritization order. \
4a. If implementing a task in a series (e.g., db-003, svc-005), check 1-2 previous commits in that series for implementation patterns using 'git log --grep=<task-id>'. \
5. Create a new git branch named after the task (e.g., 'task/spike-001-rss-service'). \
6. Implement the task. \
7. Commit your changes to the branch. \
8. Update ralph/progress.txt with what you did. \
9. Push the branch to GitHub and create a pull request. \
ONLY DO ONE TASK AT A TIME. \
If the PRD is complete, output <promise>COMPLETE</promise>.")

  echo "$result"

  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "PRD complete after $i iterations."
    exit 0
  fi
done

echo "Completed $1 iterations. PRD may not be complete yet."
