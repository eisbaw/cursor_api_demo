---
id: TASK-179
title: Analyze model allowlist/blocklist server enforcement
status: To Do
assignee: []
created_date: '2026-01-28 06:41'
labels:
  - reverse-engineering
  - api
  - security
dependencies:
  - TASK-115
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-115 revealed client-side model blocking via AdminSettingsService.isModelBlocked(). This task should analyze server-side enforcement. Key questions: Are blocked model requests rejected at API level? What error responses are returned? Can the blocklist be bypassed by direct API calls?

Client-side implementation at line 290837:
- Normalizes model names (lowercase, replace - with .)
- Checks against blockedModels list
- Checks against allowedModels allowlist

References:
- /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-115-admin-settings.md
- /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js lines 290837-290842
<!-- SECTION:DESCRIPTION:END -->
