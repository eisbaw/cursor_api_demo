---
id: TASK-274
title: Document Service Account management schemas
status: To Do
assignee: []
created_date: '2026-01-28 07:17'
labels:
  - reverse-engineering
  - protobuf
  - enterprise
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-7-protobuf-schemas.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The decompiled source contains service account management messages for team API access:
- CreateTeamServiceAccountRequest/Response (line ~273833)
- ListTeamServiceAccountsRequest/Response (line ~273909)
- DeleteTeamServiceAccountRequest/Response (line ~274108)
- RotateServiceAccountApiKeyRequest/Response (line ~274168)
- GetServiceAccountSpendLimitRequest/Response (line ~283333)
- SetServiceAccountSpendLimitRequest/Response (line ~283418)

These provide programmatic API access for teams, which could be useful for automation.
<!-- SECTION:DESCRIPTION:END -->
