#!/bin/bash

codex --dangerously-bypass-approvals-and-sandbox "@AGENTS.md @ralph/PRD.md @ralph/PRD.json @ralph/PHASES.md @ralph/progress.txt \
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
ONLY DO ONE TASK AT A TIME."
