---
id: TASK-260
title: Analyze extension host MCP OAuth callback handler implementation
status: To Do
assignee: []
created_date: '2026-01-28 07:09'
labels:
  - mcp
  - oauth
  - extension-host
  - reverse-engineering
dependencies: []
references:
  - >-
    /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-59-mcp-token-storage.md
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The MCP OAuth flow involves IPC commands (mcp.logoutServer, mcp.clearAllTokens) that are handled in the extension host. Investigate:

1. How the extension host receives OAuth callback redirects
2. How it exchanges authorization codes for tokens
3. How tokens are forwarded to the aiserver.v1 backend via StoreMcpOAuthToken
4. Error handling for OAuth failures
5. Token refresh logic in the extension host

Related to TASK-59 MCP OAuth token storage analysis which covered the workbench side.
<!-- SECTION:DESCRIPTION:END -->
