---
id: TASK-190
title: Document server-side request_id session management
status: To Do
assignee: []
created_date: '2026-01-28 06:43'
labels:
  - reverse-engineering
  - protocol
  - server-side
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-117-bidiappend-sse.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When using SSE + BidiAppend mode, the server must correlate BidiAppend requests with the corresponding SSE stream using the request_id.

Key areas to investigate:
- Server-side session store structure (Redis, in-memory, etc.)
- How request_id ownership is validated to prevent hijacking
- Session timeout and cleanup mechanisms
- Cross-server affinity requirements for SSE streams
<!-- SECTION:DESCRIPTION:END -->
