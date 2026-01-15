#!/bin/bash

codex --dangerously-bypass-approvals-and-sandbox "@AGENTS.md @ralph/PRD.md @ralph/PHASES.md @ralph/progress.txt \
1. Read AGENTS.md for project principles and task prioritization guidance. \
2. Read PHASES.md to understand the current phase, exit criteria, and what's next. \
3. Read the PRD and progress file. \
4. Find the next incomplete task following prioritization order. \
4a. If implementing a task in a series (e.g., db-003, svc-005), check 1-2 previous commits in that series for implementation patterns using 'git log --grep=<task-id>'. \
5. Create a new git branch named after the task (e.g., 'task/spike-001-rss-service'). \
6. Implement the task. \
7. Commit your changes to the branch. \
8. Update ralph/progress.txt with what you did. \
9. Push the branch to GitHub and create a pull request. \
ONLY DO ONE TASK AT A TIME."
