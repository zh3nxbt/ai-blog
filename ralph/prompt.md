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
3. **Create feature branch:** `git checkout -b task/[story-id]-[short-description]`
   - Example: `task/svc-001-supabase-client`
4. Implement **ONLY that ONE story** (do not continue to the next story)
5. Run quality checks (typecheck, lint, test)
6. If checks pass, commit implementation: `feat: [Story ID] - [Story Title]`
7. **Update documentation** (commit separately):
   - Update `ralph/PRD.json` to set `passes: true` for the completed story
   - Append progress entry to `ralph/progress.txt` with implementation details
   - Update `claude.md` if there are architectural learnings (see "Update claude.md" section below)
8. Commit documentation updates: `docs: update PRD and progress for [story-id] completion`
9. **Push branch:** `git push -u origin task/[story-id]-[short-description]`
10. **Create PR to main:** `gh pr create --title "feat: [story-id] - [description]" --body "<summary>"`
11. **STOP** - End your response. Do not start the next story.
    - PR will be reviewed/merged to main by user
    - Feature branch will be deleted after merge

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

**Always consider:** Does this work reveal architectural knowledge that future implementations need?

Update `claude.md` for reusable knowledge that future work will need:
- **Architectural decisions:** Database connectivity, infrastructure, security patterns, API design
  - Example: "Use SUPABASE_SECRET for backend operations to bypass RLS policies"
- **Module-specific patterns:** API conventions, gotchas, dependencies, testing requirements
  - Example: "All RSS parsing must handle malformed XML gracefully"
- **Security/reliability patterns:** Authentication, error handling, data validation
  - Example: "Always validate external API responses before database insertion"

**Do NOT add to claude.md:**
- Sprint-specific progress (belongs in progress.txt)
- Temporary workarounds or fixes
- Task-specific implementation details
- Information already documented in progress.txt

**When in doubt:** If future agents implementing similar features would benefit from knowing this, add it to claude.md.

## Quality Requirements

- ALL commits must pass quality checks (typecheck, lint, test)
- Keep changes minimal and follow existing patterns

## Browser Testing (Frontend Stories)

For UI changes: Load `dev-browser` skill, verify changes work, screenshot if needed.

## Git Workflow Summary

Each task follows this pattern:
1. **Create feature branch** from main: `task/[story-id]-[description]`
2. **Implement and commit** changes to the branch
3. **Push branch** to GitHub: `git push -u origin <branch>`
4. **Create PR** to main for review/approval
5. **PR gets merged** to main (by user or auto-merge)
6. **Branch gets deleted** after merge (keeps repo clean)

This ensures:
- ✅ All work goes through PRs (visible for review/approval)
- ✅ Clean main branch with proper PR history
- ✅ No clutter from old feature branches
