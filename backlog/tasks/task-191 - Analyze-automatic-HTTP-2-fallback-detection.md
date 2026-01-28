---
id: TASK-191
title: Analyze automatic HTTP/2 fallback detection
status: To Do
assignee: []
created_date: '2026-01-28 06:43'
labels:
  - reverse-engineering
  - networking
  - ux
dependencies: []
references:
  - reveng_2.3.41/analysis/TASK-117-bidiappend-sse.md
  - reveng_2.3.41/analysis/TASK-43-sse-poll-fallback.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate whether Cursor automatically detects HTTP/2 failures and switches to SSE mode, or if users must manually configure the HTTP Compatibility Mode setting.

Key areas to investigate:
- Error detection in HTTP/2 connection establishment
- Automatic retry logic with protocol downgrade
- User notification when fallback is triggered
- Persistence of fallback decision across sessions
<!-- SECTION:DESCRIPTION:END -->
