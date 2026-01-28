---
id: TASK-287
title: Investigate patchRejectorStatus feature in background agent judge config
status: To Do
assignee: []
created_date: '2026-01-28 07:24'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - best-of-n
  - server-side
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The background_agent_judge_config contains a patchRejectorStatus setting with values "off", "warn", or "on". This feature appears to control patch rejection behavior during best-of-n judging but its implementation is not visible in client code.

Investigate:
- What patches does it reject and why
- Difference between "warn" and "on" modes
- How it interacts with the judge's winner selection
- Server-side implementation details (may require traffic capture)

Source reference: Lines 295283-295290 in workbench.desktop.main.js
<!-- SECTION:DESCRIPTION:END -->
