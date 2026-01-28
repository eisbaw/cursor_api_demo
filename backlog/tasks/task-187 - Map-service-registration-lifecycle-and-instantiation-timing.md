---
id: TASK-187
title: Map service registration lifecycle and instantiation timing
status: To Do
assignee: []
created_date: '2026-01-28 06:42'
labels:
  - investigation
  - dependency-injection
  - architecture
dependencies:
  - TASK-106
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js:25742-25755
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The `Rn()` function registers services with two instantiation modes:
- `0` (Eager): Service instantiated immediately
- `1` (Delayed): Service instantiated on first access

Investigate:
1. When exactly do eager services get instantiated?
2. How are delayed services proxied before instantiation?
3. What triggers the initial service graph resolution?
4. How are circular dependencies detected/prevented?
5. The role of `SyncDescriptor` (`Gl` class) in deferred instantiation
<!-- SECTION:DESCRIPTION:END -->
