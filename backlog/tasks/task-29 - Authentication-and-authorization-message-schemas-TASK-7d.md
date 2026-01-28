---
id: TASK-29
title: Authentication and authorization message schemas (TASK-7d)
status: Done
assignee: []
created_date: '2026-01-27 14:10'
updated_date: '2026-01-28 07:15'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Comprehensive analysis of authentication and authorization protobuf message schemas in Cursor IDE 2.3.41. Documented 26 sections covering AuthService, session management, login/logout flows, JWT keys, privacy modes, MCP OAuth, GitHub access tokens, temporary access tokens, service accounts, API keys, repository authorization, scope upgrades, and client-side token management implementation.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## TASK-29 Analysis Complete

### Findings Summary

Documented comprehensive authentication and authorization schemas in `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/analysis/TASK-29-auth-schemas.md`

#### Key Discoveries:

**1. AuthService (aiserver.v1)** - 12 RPC methods for authentication management including GetSessionToken, CheckSessionToken, ListActiveSessions, RevokeSession, and ListJwtPublicKeys.

**2. Session Management** - SessionType enum with 8 types: WEB, CLIENT, BUGBOT, BACKGROUND_AGENT, SUPPORT_IMPERSONATION, API_KEY_TOKEN, TRAINING, plus UNSPECIFIED.

**3. Token Destinations** - GetSessionTokenRequest.Destination enum: PORTAL, AISERVER, AUTH_PROXY.

**4. MCP OAuth Flow** - PKCE-based OAuth with StoreMcpOAuthTokenRequest, ValidateMcpOAuthTokensRequest/Response, and StoreMcpOAuthPendingStateRequest for code_verifier storage.

**5. Service Account System** - Full CRUD operations for team service accounts with RotateServiceAccountApiKeyRequest/Response for key rotation.

**6. Client-Side Token Management** (Lines ~1097663-1098999):
   - Token refresh threshold: 1272 hours (53 days)
   - JWT-based expiration checking
   - Auto-refresh scheduling via setTimeout
   - Storage keys: cursorAuth/accessToken, cursorAuth/refreshToken

**7. Membership Types** - FREE, PRO, PRO_PLUS, ENTERPRISE, FREE_TRIAL, ULTRA

**8. Error Codes** - Authentication-specific errors including ERROR_AGENT_REQUIRES_LOGIN, ERROR_FREE_USER_USAGE_LIMIT, ERROR_PRO_USER_USAGE_LIMIT

### Source File Locations
- AuthService definition: Line ~814570
- Session schemas: Lines ~813570-813768
- Login/Logout: Lines ~100112-100934
- MCP OAuth: Lines ~271260-271563
- Service accounts: Lines ~273833-274244
- Token management: Lines ~1097663-1098999
<!-- SECTION:FINAL_SUMMARY:END -->
