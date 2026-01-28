---
id: TASK-212
title: Analyze Cursor workspace trust management
status: To Do
assignee: []
created_date: '2026-01-28 06:54'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - security
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The hooks system respects workspace trust for project-level hooks. Investigate the workspaceTrustManagementService:
- How workspace trust is determined
- Trust prompts and user interaction
- Impact on hooks, extensions, and agent capabilities
- Trust persistence and configuration
<!-- SECTION:DESCRIPTION:END -->
