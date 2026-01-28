---
id: TASK-267
title: Document service account API key scopes enumeration
status: To Do
assignee: []
created_date: '2026-01-28 07:15'
labels:
  - reverse-engineering
  - authentication
  - api
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-29-auth-schemas.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate and document the full list of available scopes for service account API keys:
- ServiceAccountKeyInfo.scopes field (Line ~274077)
- ApiKey.scopes field (Line ~273746)
- How scopes are validated and enforced
- Relationship between scopes and feature access

Related to TASK-29 service account findings at lines ~273833-274244.
<!-- SECTION:DESCRIPTION:END -->
