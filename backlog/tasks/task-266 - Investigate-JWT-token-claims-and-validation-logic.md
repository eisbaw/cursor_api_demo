---
id: TASK-266
title: Investigate JWT token claims and validation logic
status: To Do
assignee: []
created_date: '2026-01-28 07:15'
labels:
  - reverse-engineering
  - authentication
  - security
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-29-auth-schemas.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze the JWT token structure used by Cursor IDE, including:
- Token payload claims (exp, sub, aud, etc.)
- How tokens are validated client-side (Gst function at ~1097700)
- The 1272-hour (53-day) refresh threshold constant Q8s
- Token storage and retrieval from cursorAuth/accessToken key

Related to TASK-29 findings on token management at lines ~1097663-1098999.
<!-- SECTION:DESCRIPTION:END -->
