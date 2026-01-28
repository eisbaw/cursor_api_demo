---
id: TASK-243
title: Investigate terminal execution service v3 sandbox enforcement
status: To Do
assignee: []
created_date: '2026-01-28 07:03'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - security
  - sandbox
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate how terminal execution service v3 differs from v2, specifically regarding sandbox enforcement. The code checks `VSCODE_TERMINAL_EXECUTION_SERVICE_VERSION` env var and v3 is required for sandbox support. Determine the exact OS-level sandbox mechanism used (likely landlock on Linux, sandbox on macOS). Located in terminalExecutionServiceV3 (line 1127857 onwards).
<!-- SECTION:DESCRIPTION:END -->
