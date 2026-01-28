---
id: TASK-196
title: Investigate shell command idle_timeout_seconds and command_run_timeout_ms
status: To Do
assignee: []
created_date: '2026-01-28 06:48'
labels:
  - reverse-engineering
  - shell-execution
  - timeout-handling
dependencies:
  - TASK-82
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-82-tool-timeout.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follow-up from TASK-82: The shell command execution has specific timeout parameters that were identified but not fully analyzed:

- `idle_timeout_seconds` - Appears to be for detecting idle/stalled commands
- `command_run_timeout_ms` - Overall command execution timeout
- How do these interact with the general tool timeout system?
- Are these server-controlled or client-controlled?

These may have different behavior from the general tool timeout mechanism.
<!-- SECTION:DESCRIPTION:END -->
