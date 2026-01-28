---
id: TASK-59
title: Analyze MCP OAuth token storage and validation flow
status: Done
assignee: []
created_date: '2026-01-27 14:49'
updated_date: '2026-01-28 07:09'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyzed MCP OAuth token storage and validation flow in Cursor IDE 2.3.41. Key findings:

1. **Server-Side Token Storage**: OAuth tokens for MCP servers are stored on Cursor's backend (aiserver.v1 service), not locally
2. **Protobuf Messages**: Identified StoreMcpOAuthTokenRequest/Response, ValidateMcpOAuthTokensRequest/Response, and PKCE state management messages
3. **PKCE Flow**: Code verifier stored server-side during OAuth authorization flow
4. **Agent Integration**: Background agents retrieve tokens via agent.v1.GetMcpRefreshTokens RPC
5. **IPC Commands**: mcp.logoutServer and mcp.clearAllTokens for token management
6. **Feature Gates**: mcp_oauth_scopes_enabled and mcp_oauth_url_spam_guard control OAuth behavior
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Identified MCP OAuth token storage mechanism (server-side via aiserver.v1)
- [x] #2 Documented protobuf message definitions for all OAuth operations
- [x] #3 Analyzed PKCE flow implementation with code_verifier storage
- [x] #4 Documented token validation flow and batch validation capability
- [x] #5 Identified encryption service backends (keychain, DPAPI, kwallet, etc.)
- [x] #6 Documented IPC commands for token management
- [x] #7 Created comprehensive analysis markdown file
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Summary

Completed comprehensive analysis of MCP OAuth token storage and validation flow in Cursor IDE 2.3.41.

## Key Findings

### Server-Side Token Architecture
- OAuth tokens stored on Cursor's backend (aiserver.v1 UserService) rather than local secure storage
- Enables cross-device token access and centralized management
- Requires trusting Cursor's backend with third-party OAuth credentials

### Protobuf Message Definitions
- `StoreMcpOAuthTokenRequest`: server_url, refresh_token, client_id, client_secret, redirect_uri
- `ValidateMcpOAuthTokensRequest`: Batch validation of multiple server URLs
- `StoreMcpOAuthPendingStateRequest`: PKCE code_verifier storage during OAuth flow
- `McpOAuthStoredData`: Local representation of stored OAuth data

### Token Flow
1. Server responds with "needsAuth" status and authorizationUrl
2. Client stores PKCE code_verifier via StoreMcpOAuthPendingState
3. User completes OAuth in browser
4. Token exchange and storage via StoreMcpOAuthToken
5. Validation via ValidateMcpOAuthTokens on reconnection

### IPC Commands
- mcp.logoutServer: Clear OAuth state for specific server
- mcp.clearAllTokens: Clear all MCP OAuth tokens

## Files Changed
- Created: /home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-59-mcp-token-storage.md
<!-- SECTION:FINAL_SUMMARY:END -->
