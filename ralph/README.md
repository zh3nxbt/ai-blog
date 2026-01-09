# Ralph - Autonomous Task Execution

This folder contains Ralph's configuration and automation files.

## Files

- **ralph-once.sh** - Shell script to execute one task at a time
- **PRD.md** - Product Requirements Document with all Phase 1 tasks
- **progress.txt** - Running log of completed tasks and learnings

## Usage

From the project root, run:

```bash
./ralph/ralph-once.sh
```

Ralph will:
1. Read the project guidelines from `claude.md`
2. Review the PRD and progress files
3. Pick the next incomplete task (following prioritization order)
4. Create a feature branch
5. Implement the task
6. Commit changes
7. Update progress.txt
8. Create a pull request for your review

## Workflow

Each execution handles exactly ONE task to ensure:
- Small, reviewable commits
- Clear progress tracking
- Easy rollback if needed
- Minimal risk per change

Review and merge the PR on GitHub before running again.
