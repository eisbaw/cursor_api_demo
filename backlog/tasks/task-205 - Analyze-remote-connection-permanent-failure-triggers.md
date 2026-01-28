---
id: TASK-205
title: Analyze remote connection permanent failure triggers
status: To Do
assignee: []
created_date: '2026-01-28 06:49'
labels:
  - reverse-engineering
  - remote-development
  - error-handling
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-119-polling-backoff.md
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:1082549'
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The remote connection manager (ZZt class, line ~1082549) has complex logic for determining permanent failures vs recoverable errors.

Investigate:
- VSCODE_CONNECTION_ERROR code handling
- Grace period calculation (360 attempts / ~3 hours)
- Special handling for background composer connections
- TemporarilyNotAvailable vs permanent error classification
- triggerPermanentFailure static method and its instance-wide effect

Key source locations:
- Lines 1082549-1082670: ZZt connection manager class
- Lines 1082630-1082662: Error classification logic
- mee.isTemporarilyNotAvailable() and isHandled() checks

This affects all remote development scenarios including SSH and WSL.
<!-- SECTION:DESCRIPTION:END -->
