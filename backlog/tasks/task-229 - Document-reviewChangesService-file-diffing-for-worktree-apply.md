---
id: TASK-229
title: Document reviewChangesService file diffing for worktree apply
status: To Do
assignee: []
created_date: '2026-01-28 06:56'
labels:
  - best-of-n
  - worktree
  - diff
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-64-bon-apply.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The apply process uses `reviewChangesService.getResources()` to collect changed files. Investigate:
- How resources are computed (diff between worktree and main)
- Different modes: ld.All, ld.Pending, ld.DiffWithMain, ld.PR
- How new/deleted files are handled
- The `omitTextModelCreation` optimization
<!-- SECTION:DESCRIPTION:END -->
