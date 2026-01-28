---
id: TASK-263
title: >-
  Investigate fullLocal backgroundComposerEnv mode - how does non-VM local
  execution work
status: To Do
assignee: []
created_date: '2026-01-28 07:10'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - background-composer
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The investigation of TASK-23 revealed a `fullLocal` mode for Background Composer that allows running without cloud VMs. This uses a local backend port instead of cloud infrastructure.

Key findings to investigate:
- How is the local backend started and managed?
- What port does `localBackendPort()` return?
- What infrastructure runs locally in fullLocal mode?
- Is this used for development/testing or available to end users?

Reference: Line 440546-440547 in workbench.desktop.main.js
<!-- SECTION:DESCRIPTION:END -->
