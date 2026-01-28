---
id: TASK-94
title: Investigate ExtHostShellExec implementation in extension host bundle
status: To Do
assignee: []
created_date: '2026-01-27 22:35'
labels:
  - reverse-engineering
  - shell-exec
  - extension-host
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The ExtHostShellExec proxy is defined but its implementation is likely in a separate extension host worker bundle. Need to locate and analyze: 1) How shell processes are actually spawned 2) How sandbox policies are enforced at process level 3) How streaming output is captured and forwarded
<!-- SECTION:DESCRIPTION:END -->
