# Ralph Task Workflow - Complete Checklist

**EVERY task must follow ALL these steps:**

## 1. Task Implementation
- [ ] Read PRD.json and find next task with `passes: false`
- [ ] Check if on correct branch (create if needed)
- [ ] Implement the task
- [ ] Run quality checks (black, ruff, tests if applicable)
- [ ] Verify ALL acceptance criteria pass

## 2. Git Commits
- [ ] Commit implementation with descriptive message
- [ ] Include "Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

## 3. Update Documentation
- [ ] Update `ralph/PRD.json` - Set task `passes: true`
- [ ] Update `ralph/progress.txt` - Add entry with:
  - Timestamp
  - Task ID
  - What was implemented
  - Files changed
  - **Learnings for future iterations** (sprint/phase-specific)
- [ ] Update `claude.md` - ONLY if there are long-term architectural lessons that apply across ALL phases
  - Examples: connectivity patterns, architectural decisions, infrastructure setup
  - Do NOT add sprint-specific details to claude.md

## 4. Final Commit
- [ ] Commit PRD.json and progress.txt updates
- [ ] Commit claude.md ONLY if updated

## 5. Push and PR (CRITICAL - DO NOT SKIP)
- [ ] Push branch: `git push -u origin <branch-name>`
- [ ] Create PR: `gh pr create --title "feat: <task-id> - <description>" --body "<summary>"`
- [ ] Include verification results in PR body
- [ ] Link to task ID in PR body

## 6. Complete
- [ ] Verify PR is created on GitHub
- [ ] Wait for review/merge before starting next task

---

## Common Mistakes to Avoid

❌ Skipping PR creation
❌ Not updating claude.md with long-term lessons
❌ Adding sprint-specific details to claude.md
❌ Forgetting to mark task as passes: true
❌ Not documenting learnings in progress.txt

## Quick Reference

```bash
# After implementation and commits:
git push -u origin task/<task-id>-<description>
gh pr create --title "feat: <task-id> - <description>" --body "Summary with verification results"
```
