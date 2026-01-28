---
id: TASK-213
title: Document Cursor Dashboard API for team management
status: To Do
assignee: []
created_date: '2026-01-28 06:54'
labels:
  - reverse-engineering
  - cursor-2.3.41
  - api
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Team hooks are fetched via cursorAuthenticationService.dashboardClient(). Investigate the dashboard API:
- Available endpoints (getTeamHooks, createTeamHook, updateTeamHook, deleteTeamHook)
- Authentication flow
- Team ID management
- Other team-related features
<!-- SECTION:DESCRIPTION:END -->
