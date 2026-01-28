---
id: TASK-57
title: >-
  Investigate Best-of-N Judge prompts: What criteria and prompts are used to
  select winning agent results
status: Done
assignee: []
created_date: '2026-01-27 14:49'
updated_date: '2026-01-27 22:36'
labels: []
dependencies: []
---

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Investigation Complete

Analyzed the Best-of-N Judge system in Cursor IDE. Key findings:

### Architecture
- Client-side service (`uiBestOfNJudgeService`) coordinates judging
- Uses bidirectional gRPC streaming to server
- Evaluates parallel agent runs in separate git worktrees

### Data Flow
1. Multiple models (e.g., composer-1, claude-4.5-opus-high, gpt-5.1-codex) run in parallel
2. Client collects git diffs from each worktree
3. Sends task + diffs to server via `StreamUiBestOfNJudge`
4. Server returns winner ID + reasoning string

### Configuration
- `judgeModel`: "gpt-5-high" (server-side default)
- `worktrees_bon_judge`: Feature flag (default: true)
- `disableBestOfNRecommender`: User setting to disable

### Key Limitation
The actual judging prompts/criteria are entirely server-side. Client only collects diffs and displays results.

### Analysis Written To
`reveng_2.3.41/analysis/TASK-57-best-of-n-judge.md`

### Follow-up Tasks Created
- TASK-101: Investigate worktree isolation
- TASK-102: Reverse engineer server-side prompts via API
- TASK-104: Analyze patchRejector integration
<!-- SECTION:FINAL_SUMMARY:END -->
