---
id: TASK-230
title: Investigate MCP token transmission to servers
status: To Do
assignee: []
created_date: '2026-01-28 07:02'
labels:
  - reverse-engineering
  - mcp
  - oauth
  - security
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-49-mcp-oauth.md
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-17-mcp-oauth.md
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze how OAuth access tokens are transmitted from Cursor's backend to MCP servers during API calls. This includes examining the ExtHost OAuth provider implementation and how tokens are attached to MCP protocol requests.
<!-- SECTION:DESCRIPTION:END -->
