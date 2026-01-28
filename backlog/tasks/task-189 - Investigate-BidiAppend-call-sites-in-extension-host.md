---
id: TASK-189
title: Investigate BidiAppend call sites in extension host
status: To Do
assignee: []
created_date: '2026-01-28 06:43'
labels:
  - reverse-engineering
  - protocol
  - networking
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-117-bidiappend-sse.md
  - 'reveng_2.3.41/beautified/workbench.desktop.main.js:810612-810622'
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The BidiAppend unary method is defined in aiserver.v1.BidiService but actual call sites in the extension host were not found during TASK-117 investigation.

Key areas to investigate:
- Search for where BidiService client is instantiated
- Find actual bidiAppend() method invocations
- Determine if SSE mode is automatically triggered or only via manual configuration
- Trace the code path from HTTP/2 disabled setting to BidiAppend usage
<!-- SECTION:DESCRIPTION:END -->
