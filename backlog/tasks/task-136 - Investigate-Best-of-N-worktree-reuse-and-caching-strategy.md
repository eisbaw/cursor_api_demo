---
id: TASK-136
title: Investigate Best-of-N worktree reuse and caching strategy
status: To Do
assignee: []
created_date: '2026-01-28 00:11'
labels:
  - reverse-engineering
  - worktree
  - best-of-n
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-101-best-of-n-worktrees.md
  - reveng_2.3.41/analysis/TASK-56-worktree-lifecycle.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze whether Cursor's Best-of-N system reuses worktrees across runs or always creates fresh ones. Key questions:
- Is there any worktree pooling mechanism?
- How does the worktree cleanup cron interact with Best-of-N runs?
- What happens to worktrees when a Best-of-N run is aborted mid-execution?

Start by examining the WorktreeCleanupCron (line 960068-960124) and the protection rules (line 960632-960637) that prevent cleanup of recent worktrees.
<!-- SECTION:DESCRIPTION:END -->
