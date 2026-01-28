---
id: TASK-186
title: Investigate observable debugger integration (bO function)
status: To Do
assignee: []
created_date: '2026-01-28 06:42'
labels:
  - investigation
  - debugging
  - observables
dependencies:
  - TASK-106
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js:15093-15108
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The observable system includes a debug hook accessed via `bO()` function. This debugger receives callbacks for:
- `handleObservableCreated`
- `handleObservableUpdated`
- `handleAutorunCreated`
- `handleAutorunStarted`
- `handleAutorunFinished`
- `handleAutorunDisposed`
- `handleAutorunDependencyChanged`
- `handleDerivedRecomputed`
- `handleDerivedCleared`
- `handleDerivedDependencyChanged`
- `handleBeginTransaction`
- `handleEndTransaction`

Investigate how this debugger is enabled, its UI integration, and whether it's used in production or only development builds.
<!-- SECTION:DESCRIPTION:END -->
