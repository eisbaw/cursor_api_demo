---
id: TASK-227
title: Analyze worktree apply merge conflict detection and resolution
status: To Do
assignee: []
created_date: '2026-01-28 06:56'
labels:
  - best-of-n
  - worktree
  - git
  - merge
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-64-bon-apply.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
During `_applyWorktreeToCurrentBranchViaMerge`, the system detects merge conflicts in applied files but does not block the operation. Investigate:
- How merge conflicts are detected (line 948607-948615)
- What conflict markers are used ("Current (Your changes)" vs "Incoming (Agent changes)")
- How users resolve conflicts after apply
- Whether there's automatic conflict resolution attempted
<!-- SECTION:DESCRIPTION:END -->
