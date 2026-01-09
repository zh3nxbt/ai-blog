#!/bin/bash

claude --permission-mode acceptEdits "@claude.md @ralph/PRD.md @ralph/progress.txt \
1. Read claude.md for project principles and task prioritization guidance. \
2. Read the PRD and progress file. \
3. Find the next incomplete task following prioritization order. \
3a. If implementing a task in a series (e.g., db-003, svc-005), check 1-2 previous commits in that series for implementation patterns using 'git log --grep=<task-id>'. \
4. Create a new git branch named after the task (e.g., 'task/db-001-blog-posts-table'). \
5. Implement the task. \
6. Commit your changes to the branch. \
7. Update ralph/progress.txt with what you did. \
8. Push the branch to GitHub and create a pull request. \
ONLY DO ONE TASK AT A TIME."
