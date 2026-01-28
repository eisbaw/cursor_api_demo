---
id: TASK-159
title: Investigate team hooks dashboard API (getTeamHooks)
status: To Do
assignee: []
created_date: '2026-01-28 06:34'
labels:
  - reverse-engineering
  - hooks
  - api
dependencies:
  - TASK-96
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-96-shell-validators.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The hooks service fetches team-level hooks from the Cursor dashboard API via `cursorAuthenticationService.dashboardClient().getTeamHooks()`. Need to investigate:
1. The API endpoint and authentication mechanism
2. Hook distribution protocol (how hooks are synced from dashboard to local)
3. Team hooks storage structure in `~/.cursor/managed/team_{id}/hooks/`
4. First-time notification flow for team hooks
5. Refresh scheduler mechanism for team hooks
<!-- SECTION:DESCRIPTION:END -->
