#!/bin/bash

claude --permission-mode acceptEdits "@claude.md @PRD.md @progress.txt \
1. Read claude.md for project principles and task prioritization guidance. \
2. Read the PRD and progress file. \
3. Find the next incomplete task following prioritization order. \
4. Implement it. \
5. Commit your changes. \
6. Update progress.txt with what you did. \
ONLY DO ONE TASK AT A TIME."
