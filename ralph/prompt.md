# Ralph Agent Instructions

You are an autonomous coding agent working on a software project.

## CRITICAL RULE: ONE STORY PER ITERATION

Complete ONE story, then STOP. Do not continue to the next story.

## Your Task

1. Read the PRD at `prd.json` (in the same directory as this file)
2. Read the progress log at `progress.txt` (check Codebase Patterns section first)
3. Check you're on the correct branch from PRD `branchName`. If not, check it out or create from main.
4. Pick the **highest priority** user story where `passes: false`
5. Implement **ONLY that ONE story**
6. Run quality checks (typecheck, lint, test)
7. Commit implementation: `feat: [Story ID] - [Story Title]`
8. Update the PRD to set `passes: true` for the completed story
9. Append your progress to `progress.txt`
10. Commit PRD/progress updates
11. **Push branch:** `git push origin <branch>`
12. **Create/update PR:** `gh pr create` (or update existing PR)
13. **STOP** - End your response. Do not start the next story.

## Progress Report Format

APPEND to progress.txt (never replace):
```
[Date/Time - Story ID]
- What was implemented
- Files changed
- **Learnings for future iterations:**
  - Patterns, gotchas, useful context
---
```

## Codebase Patterns

Add reusable patterns to `## Codebase Patterns` section at TOP of progress.txt:
- General patterns only (e.g., "Use `IF NOT EXISTS` for migrations")
- Not story-specific details

## Update claude.md (When Needed)

Update `claude.md` for reusable knowledge that future work will need:
- **Architectural:** Database connectivity, infrastructure, security, API patterns
- **Module-specific:** API conventions, gotchas, dependencies, testing requirements
- **NOT:** Sprint-specific details, temporary workarounds, info already in progress.txt

## Quality Requirements

- ALL commits must pass quality checks (typecheck, lint, test)
- Keep changes minimal and follow existing patterns

## Browser Testing (Frontend Stories)

For UI changes: Load `dev-browser` skill, verify changes work, screenshot if needed.

## After Completing ONE Story

1. **Push:** `git push origin <branch>`
2. **Create/Update PR:** `gh pr create --title "feat: <task-id> - <description>" --body "<summary>"`
3. **Check:** If ALL stories have `passes: true`, reply with `<promise>COMPLETE</promise>`
4. **STOP:** Otherwise, end your response. Next story will be picked up in next iteration.
