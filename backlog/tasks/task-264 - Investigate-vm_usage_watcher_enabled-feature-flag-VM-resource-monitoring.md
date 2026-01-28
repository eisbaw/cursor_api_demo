---
id: TASK-264
title: Investigate vm_usage_watcher_enabled feature flag - VM resource monitoring
status: To Do
assignee: []
created_date: '2026-01-28 07:10'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - feature-flags
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-23 investigation found a `vm_usage_watcher_enabled` feature flag (line 293553). This appears to control VM resource monitoring.

Questions to investigate:
- What metrics are collected when this is enabled?
- How does it affect billing/cost tracking?
- What UI surfaces this information?
- Is it used for auto-scaling or resource management?

Reference: Line 293548-293556 in workbench.desktop.main.js
<!-- SECTION:DESCRIPTION:END -->
