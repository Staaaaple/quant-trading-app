---
name: follow-up
description: Progress tracking and step-by-step confirmation for software development, coding, implementation, debugging, building, testing, refactoring, and project work. Use whenever the user asks to develop, build, implement, fix, refactor, write, test, or modify code, software projects, or technical tasks. This skill enforces tracking progress in a .claude/PROGRESS.md file, creating granular tasks via TaskCreate, and confirming each step with the user before proceeding.
---

# Follow-Up Progress Tracking

When handling any software development or technical implementation request, follow this workflow exactly.

## 1. Initialize or Load Progress File

Locate `.claude/PROGRESS.md` in the current working directory (project root). If it does not exist, create it immediately with this template, filling in the placeholders:

```markdown
# Project Progress

- **Project:** {infer from directory name or user context}
- **Started:** {ISO 8601 timestamp}
- **Last Updated:** {ISO 8601 timestamp}

## Status
- Total Tasks: 0
- Completed: 0
- In Progress: 0
- Pending: 0

## Task List
<!-- Tasks added below -->

## Activity Log
<!-- Log entries added below -->
```

## 2. Plan and Decompose

Break the user's request into discrete, actionable steps. For each step, call `TaskCreate` with a clear subject and description. After creating all tasks, update `.claude/PROGRESS.md`:
- List each task under `## Task List` with status `[ ] Pending`
- Update the Status counts

## 3. Step-by-Step Execution with Confirmation

For **each** task (in dependency order):

1. **Announce the step** to the user in plain text. State what you are about to do and why. If the step involves introducing or using any non-open-source module, tool, engine, SDK, or proprietary service, explicitly warn the user and explain the licensing or cost implications before proceeding.
2. **Wait for explicit confirmation** before executing non-trivial or file-modifying steps. If the step is trivial and safe (e.g., reading a file), you may proceed, but still announce it. For anything that writes, edits, deletes, or runs commands, pause for the user's go-ahead.
3. **Execute** the step. Use the appropriate tools.
4. **Report the result** immediately after completion. Summarize what happened, any errors, and what changed. The summary must be detailed enough to include:
   - A brief description of each created or modified file and its role in the project.
   - The key imported libraries or modules and why they are used (e.g., `fastapi` for the web framework, `sqlalchemy` for ORM).
   - Any notable configuration values or design decisions.
5. **Update `.claude/PROGRESS.md`**:
   - Set `Last Updated` to the current timestamp
   - Mark the completed task as `[x] Completed` (or `[~] In Progress` if partially done)
   - Update Status counts
   - Append to `## Activity Log`:
     `- [{timestamp}] {task subject}: {one-line result summary}`
6. **Ask the user** "是否继续下一步？" / "Shall I proceed to the next step?" or similar, unless the user has already instructed you to continue through all steps.

Do **not** silently batch multiple steps. One task = one announcement + one execution + one report + one file update.

## 4. Handle Blockers and Changes

If a step fails or reveals that the plan needs to change:
1. Log the blocker in `.claude/PROGRESS.md` Activity Log
2. Propose a revised plan to the user
3. Only proceed after the user approves the new plan

## 5. Finalize

When all tasks are complete:
1. Mark all tasks as `[x] Completed`
2. Add a final Activity Log entry with a summary
3. Tell the user the work is done and reference `.claude/PROGRESS.md`
