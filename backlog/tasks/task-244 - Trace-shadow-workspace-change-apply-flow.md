---
id: TASK-244
title: Trace shadow workspace change apply flow
status: To Do
assignee: []
created_date: '2026-01-28 07:03'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - shadow-workspace
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-5-shadow-workspace.md
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Trace how approved changes from the shadow workspace are applied to the main workspace. The shadow workspace allows AI to iterate on changes in isolation - need to understand the exact mechanism by which final changes are transferred back to the main workspace when the user approves them. Look for accept/apply handlers that bridge shadow and main workspaces.
<!-- SECTION:DESCRIPTION:END -->
