---
id: TASK-228
title: Investigate replace_files_on_worktree_apply feature gate behavior
status: To Do
assignee: []
created_date: '2026-01-28 06:56'
labels:
  - best-of-n
  - worktree
  - feature-gate
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-64-bon-apply.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The `replace_files_on_worktree_apply` feature gate (default: false) changes how files are copied from worktree to workspace. Investigate:
- What is the difference between replace mode and standard mode?
- Why is this disabled by default?
- What edge cases does replace mode handle differently?
- Location: Lines 293885-293888, 948577-948580
<!-- SECTION:DESCRIPTION:END -->
