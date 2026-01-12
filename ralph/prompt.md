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

## Your Task

1. You should have already read claude.md, PRD.json, and progress.txt per the instructions above
2. Check you're on the correct branch from PRD `branchName`. If not, check it out or create from main.
3. Pick the **highest priority** user story where `passes: false`
4. Implement that single user story
5. Run quality checks (e.g., typecheck, lint, test - use whatever your project requires)
6. If checks pass, commit implementation with message: `feat: [Story ID] - [Story Title]`
7. Update the PRD to set `passes: true` for the completed story
8. Append your progress to `progress.txt`
9. Update `claude.md` ONLY if there are long-term architectural lessons (see below)
10. Commit PRD/progress updates (and claude.md if updated)
11. Push branch and create PR: `git push -u origin <branch>` then `gh pr create`

## Progress Report Format

APPEND to progress.txt (never replace, always append):
```
[Date/Time - Story ID]
- What was implemented
- Files changed
- **Learnings for future iterations:**
  - Patterns discovered (e.g., "this codebase uses X for Y")
  - Gotchas encountered (e.g., "don't forget to update Z when changing W")
  - Useful context (e.g., "the evaluation panel is in component X")
---
```

The learnings section is critical - it helps future iterations avoid repeating mistakes and understand the codebase better.

## Consolidate Patterns

If you discover a **reusable pattern** that future iterations should know, add it to the `## Codebase Patterns` section at the TOP of progress.txt (create it if it doesn't exist). This section should consolidate the most important learnings:

```
## Codebase Patterns
- Example: Use `sql<number>` template for aggregations
- Example: Always use `IF NOT EXISTS` for migrations
- Example: Export types from actions.ts for UI components
```

Only add patterns that are **general and reusable**, not story-specific details.

## Update AGENTS.md Files

Before committing, check if any edited files have learnings worth preserving in nearby AGENTS.md files:

1. **Identify directories with edited files** - Look at which directories you modified
2. **Check for existing AGENTS.md** - Look for AGENTS.md in those directories or parent directories
3. **Add valuable learnings** - If you discovered something future developers/agents should know:
   - API patterns or conventions specific to that module
   - Gotchas or non-obvious requirements
   - Dependencies between files
   - Testing approaches for that area
   - Configuration or environment requirements

**Examples of good AGENTS.md additions:**
- "When modifying X, also update Y to keep them in sync"
- "This module uses pattern Z for all API calls"
- "Tests require the dev server running on PORT 3000"
- "Field names must match the template exactly"

**Do NOT add:**
- Story-specific implementation details
- Temporary debugging notes
- Information already in progress.txt

Only update AGENTS.md if you have **genuinely reusable knowledge** that would help future work in that directory.

## Update claude.md (Long-term Architecture)

**When to update claude.md:**
Update `claude.md` ONLY when you discover long-term architectural patterns or decisions that apply across ALL phases of the project.

**Examples of what belongs in claude.md:**
- Database connectivity patterns (e.g., connection pooler for Supabase)
- Architectural decisions affecting multiple components
- Infrastructure setup patterns
- Security patterns and requirements
- API integration patterns

**Examples of what does NOT belong in claude.md:**
- Sprint or phase-specific implementation details
- Task-specific learnings (those go in progress.txt)
- Temporary workarounds or hacks
- Story-specific patterns

**Rule of thumb:** If it's relevant to the current sprint/phase only, it goes in `progress.txt`. If it's relevant to all future work across all phases, it goes in `claude.md`.

## Quality Requirements

- ALL commits must pass your project's quality checks (typecheck, lint, test)
- Do NOT commit broken code
- Keep changes focused and minimal
- Follow existing code patterns

## Browser Testing (Required for Frontend Stories)

For any story that changes UI, you MUST verify it works in the browser:

1. Load the `dev-browser` skill
2. Navigate to the relevant page
3. Verify the UI changes work as expected
4. Take a screenshot if helpful for the progress log

A frontend story is NOT complete until browser verification passes.

## Push Branch and Create PR (REQUIRED)

After all commits are complete, you MUST:

1. **Push the branch:**
   ```bash
   git push -u origin task/<task-id>-<description>
   ```

2. **Create a pull request:**
   ```bash
   gh pr create --title "feat: <task-id> - <description>" --body "<summary with verification results>"
   ```

3. **Verify PR is created** - Check that the PR URL is returned

**Do NOT skip this step.** All work must go through pull requests for review.

## Stop Condition

After completing a user story, check if ALL stories have `passes: true`.

If ALL stories are complete and passing, reply with:
<promise>COMPLETE</promise>

If there are still stories with `passes: false`, end your response normally (another iteration will pick up the next story).

## Important

- Work on ONE story per iteration
- Commit frequently
- Keep CI green
- Read the Codebase Patterns section in progress.txt before starting
- ALWAYS create a PR after completing a task (never skip this)
