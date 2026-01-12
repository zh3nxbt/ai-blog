# Ralph Agent Instructions

## BEFORE YOU START - MANDATORY READING

**STOP. Read these files in this order:**

1. **`claude.md`** (in project root) - Core principles, database patterns, code style, content guidelines
2. **`ralph/PRD.json`** - Your task list
3. **`ralph/progress.txt`** - Check "Codebase Patterns" section at top

**Why this matters:**
- `claude.md` contains architectural knowledge that prevents mistakes
- Example: Database connection patterns (lines 37-64) explain pooler vs direct connections
- Example: Content guidelines (lines 104-164) list forbidden AI slop phrases
- Previous agents skipped this and needed multiple bugfix cycles for documented issues

**Do not skip this step.**

---

You are an autonomous coding agent working on a software project.

## CRITICAL RULE: ONE STORY PER ITERATION

Complete ONE story, then STOP. Do not continue to the next story.

## Your Task

1. You should have already read claude.md, PRD.json, and progress.txt per the instructions above
2. Pick the **highest priority** user story where `passes: false`
3. Implement **ONLY that ONE story** (do not continue to the next story)
4. Run quality checks (typecheck, lint, test)
5. If checks pass, commit implementation: `feat: [Story ID] - [Story Title]`
6. Update the PRD to set `passes: true` for the completed story
7. Append your progress to `progress.txt`
8. Update `claude.md` ONLY if there are long-term architectural lessons (see below)
9. Commit PRD/progress updates (and claude.md if updated)
10. Push to main: `git push origin main`
11. **STOP** - End your response. Do not start the next story.

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
2. **Create NEW PR:** `gh pr create --title "feat: <task-id> - <description>" --body "<summary>"`
   - Each story must have its own dedicated PR
3. **Check:** If ALL stories have `passes: true`, reply with `<promise>COMPLETE</promise>`
4. **STOP:** Otherwise, end your response. Next story will be picked up in next iteration.
