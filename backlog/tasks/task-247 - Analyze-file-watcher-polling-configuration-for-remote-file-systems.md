---
id: TASK-247
title: Analyze file watcher polling configuration for remote file systems
status: To Do
assignee: []
created_date: '2026-01-28 07:08'
labels:
  - reverse-engineering
  - cursor-ide
  - file-watcher
  - configuration
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Discovered during TASK-66 analysis: The file watcher system supports polling mode for paths that require it, with configurable intervals (default 5000ms).

Key areas to investigate:
- Configuration options for watcher.recursive.usePolling
- Path-based polling configuration
- Performance impact of polling vs native watching
- Remote file system considerations (SSH, container workspaces)

Reference: Lines 1119594-1119597 in workbench.desktop.main.js
<!-- SECTION:DESCRIPTION:END -->
