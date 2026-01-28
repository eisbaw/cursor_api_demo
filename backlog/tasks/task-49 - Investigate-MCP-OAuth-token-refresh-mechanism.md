---
id: TASK-49
title: Investigate MCP OAuth token refresh mechanism
status: Done
assignee: []
created_date: '2026-01-27 14:48'
updated_date: '2026-01-28 07:01'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Deep investigation into MCP OAuth token refresh mechanism in Cursor IDE 2.3.41. Analyzed token storage architecture (server-side via aiserver.v1), PKCE implementation for OAuth flow, token validation mechanism, and lifecycle management. Key finding: token refresh is handled server-side transparently - the client only receives boolean validation results, not expiry timestamps.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Investigated the MCP OAuth token refresh mechanism in Cursor IDE 2.3.41 decompiled source.

### Key Findings

1. **Server-Side Token Storage**: MCP OAuth refresh tokens are stored on Cursor's backend (`aiserver.v1.UserSettingsService`), not locally. This enables cross-device persistence and centralizes security.

2. **Token Refresh is Implicit**: The actual token refresh logic is handled server-side. The client-side code only handles:
   - Initiating OAuth flows (via PKCE)
   - Storing/validating tokens through backend RPCs
   - Responding to `needsAuth` status changes

3. **Validation via Boolean Check**: `ValidateMcpOAuthTokens` returns only `hasValidToken: boolean`. The client doesn't receive expiry timestamps - refresh is triggered by backend validation failure.

4. **PKCE Implementation**: Uses `code_verifier`/`state_id` pattern stored server-side during OAuth authorization flow.

5. **Agent Token Access**: Background Composer agents can retrieve tokens via `agent.v1.ControlService.GetMcpRefreshTokens`, returning a map of server URLs to refresh tokens.

6. **Token Lifecycle**: Tokens are cleared when server config changes (hash mismatch) or server is removed.

### Analysis Output

Written to `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-49-mcp-oauth.md`
<!-- SECTION:FINAL_SUMMARY:END -->
