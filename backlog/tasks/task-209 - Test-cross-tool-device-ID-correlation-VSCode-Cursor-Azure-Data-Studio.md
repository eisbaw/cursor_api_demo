---
id: TASK-209
title: 'Test cross-tool device ID correlation (VSCode, Cursor, Azure Data Studio)'
status: To Do
assignee: []
created_date: '2026-01-28 06:50'
labels:
  - reverse-engineering
  - privacy
  - testing
  - cross-application
dependencies:
  - TASK-121
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The @vscode/deviceid package stores device IDs in shared Microsoft developer tools directories:
- macOS: `~/Library/Application Support/Microsoft/DeveloperTools/deviceid`
- Linux: `$XDG_CACHE_HOME/Microsoft/DeveloperTools/deviceid`

This suggests that VSCode, Cursor, Azure Data Studio, and other Microsoft dev tools may share the same `devDeviceId`.

Investigation should:
1. Install multiple Microsoft dev tools on a test system
2. Verify whether they share the same devDeviceId file/registry entry
3. Document privacy implications of cross-tool correlation
4. Identify which Microsoft tools use this package

Discovered during TASK-121 analysis.
<!-- SECTION:DESCRIPTION:END -->
