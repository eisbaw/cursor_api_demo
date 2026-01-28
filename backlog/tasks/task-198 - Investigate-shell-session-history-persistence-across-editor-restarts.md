---
id: TASK-198
title: Investigate shell session history persistence across editor restarts
status: To Do
assignee: []
created_date: '2026-01-28 06:48'
labels:
  - reverse-engineering
  - shell-exec
  - terminal-ui
  - persistence
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-98-shellexec-pty.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From TASK-98 analysis: The ShellExecPseudoTerminal can replay history from session data, but it's unclear whether/how this history persists across editor restarts. Need to investigate:

1. Where session history is stored (memory only vs disk?)
2. How getSessionHistory() retrieves past executions
3. Whether persistent terminals can reconnect after restart
4. Integration with VS Code's terminal persistence mechanism
<!-- SECTION:DESCRIPTION:END -->
