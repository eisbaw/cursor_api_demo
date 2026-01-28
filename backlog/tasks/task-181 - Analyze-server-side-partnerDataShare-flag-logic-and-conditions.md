---
id: TASK-181
title: Analyze server-side partnerDataShare flag logic and conditions
status: To Do
assignee: []
created_date: '2026-01-28 06:41'
labels:
  - reverse-engineering
  - privacy
  - server-analysis
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-100-partner-data.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The partnerDataShare flag is fetched from the server and determines whether telemetry is shared with model providers. Investigate what server-side conditions trigger this flag to be set true and whether users have any control over it. This affects privacy implications for all users.
<!-- SECTION:DESCRIPTION:END -->
