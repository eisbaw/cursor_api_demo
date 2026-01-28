# TASK-49: MCP OAuth Token Refresh Mechanism Investigation

Analysis of the MCP OAuth token refresh mechanism in Cursor IDE based on decompiled source (version 2.3.41).

## Executive Summary

The MCP OAuth token refresh mechanism in Cursor IDE is a server-mediated system where refresh tokens are stored on Cursor's backend rather than locally. The token refresh flow is implicit - Cursor's backend handles token refresh transparently when making requests to MCP servers. The client-side code primarily deals with token storage, validation checking, and OAuth flow initiation, while actual token refresh logic appears to be handled server-side by the aiserver.v1 service.

## Key Findings

### 1. Token Storage Architecture

MCP OAuth tokens are NOT stored locally in the IDE. Instead, they are stored on Cursor's backend through the `aiserver.v1.UserSettingsService` gRPC service.

#### Storage RPC Methods (Lines 719241-719263)

```javascript
{
    storeMcpOAuthToken: {
        name: "StoreMcpOAuthToken",
        I: nJl,  // StoreMcpOAuthTokenRequest
        O: sJl,  // StoreMcpOAuthTokenResponse
        kind: Kt.Unary
    },
    validateMcpOAuthTokens: {
        name: "ValidateMcpOAuthTokens",
        I: rJl,  // ValidateMcpOAuthTokensRequest
        O: oJl,  // ValidateMcpOAuthTokensResponse
        kind: Kt.Unary
    },
    storeMcpOAuthPendingState: {
        name: "StoreMcpOAuthPendingState",
        I: lJl,  // StoreMcpOAuthPendingStateRequest
        O: cJl,  // StoreMcpOAuthPendingStateResponse
        kind: Kt.Unary
    },
    getMcpOAuthPendingState: {
        name: "GetMcpOAuthPendingState",
        I: uJl,  // GetMcpOAuthPendingStateRequest
        O: dJl,  // GetMcpOAuthPendingStateResponse
        kind: Kt.Unary
    }
}
```

### 2. Token Validation Mechanism

The `ValidateMcpOAuthTokens` RPC method checks if tokens for given server URLs are still valid:

#### ValidateMcpOAuthTokensRequest (Line 271345-271375)
```javascript
{
    serverUrls: string[]  // Array of MCP server URLs to validate
}
```

#### ValidateMcpOAuthTokensResponse.Result (Line 271415-271428)
```javascript
{
    serverUrl: string,      // Server URL checked
    hasValidToken: boolean  // Whether the token is still valid
}
```

**Key Insight**: The validation check returns a simple boolean (`hasValidToken`). This suggests that token expiry detection and refresh is handled server-side. The IDE doesn't receive expiry timestamps - it only knows if a token is valid or not.

### 3. Token Refresh Flow

#### What Triggers Re-authentication

Re-authentication is triggered when a server status changes to `needsAuth`:

```javascript
// Line 447221-447232
Os.registerCommand({
    id: "mcp.needsAuth",
    handler(context, params) {
        updateServerStatus(params.identifier, {
            type: "needsAuth",
            authorizationUrl: params.authorizationUrl
        });
    }
});
```

The server reports `needsAuth` status when:
1. Initial authentication is required
2. Token validation fails on the backend
3. Refresh token is invalid or expired

#### UI-Triggered Reconnection (Lines 909395-909411)

```javascript
async initiateReconnect() {
    // Step 1: Clear existing OAuth state
    await mcpService.clearServerOAuthState(serverIdentifier);

    // Step 2: Listen for status changes
    const listener = mcpService.onDidChangeServerStatus(({identifier, status}) => {
        if (status.type === "needsAuth") {
            // Opens browser for OAuth flow
            openerService.open(status.authorizationUrl);
        }
    });

    // Step 3: Reload client to start fresh OAuth flow
    await mcpService.reloadClient(serverIdentifier);
}
```

### 4. PKCE Implementation for OAuth Flow

The system uses PKCE (Proof Key for Code Exchange) for secure OAuth authorization:

#### StoreMcpOAuthPendingStateRequest (Lines 271443-271494)
```javascript
{
    serverUrl: string,       // MCP server URL
    codeVerifier: string,    // PKCE code verifier (generated client-side)
    clientId?: string,       // OAuth client ID
    clientSecret?: string,   // OAuth client secret
    redirectUri?: string     // OAuth redirect URI
}
```

Response returns a `stateId` that is used during the OAuth callback to retrieve the pending state.

#### GetMcpOAuthPendingStateResponse (Lines 271556-271607)
```javascript
{
    serverUrl: string,       // Original server URL
    codeVerifier: string,    // PKCE code verifier for token exchange
    clientId?: string,       // OAuth client ID
    clientSecret?: string,   // OAuth client secret
    redirectUri?: string     // OAuth redirect URI
}
```

### 5. Agent-Side Token Access

The Background Composer Agent has a separate RPC for retrieving MCP refresh tokens:

#### agent.v1.ControlService.GetMcpRefreshTokens (Lines 807476-807618)

```javascript
// Request - empty, retrieves all tokens for the authenticated user
{
    typeName: "agent.v1.GetMcpRefreshTokensRequest"
}

// Response - map of server URL to refresh token
{
    typeName: "agent.v1.GetMcpRefreshTokensResponse",
    refreshTokens: {
        [serverUrl: string]: string  // Map of server URL to refresh token
    }
}
```

This suggests that background agents can independently request MCP tokens to authenticate with MCP servers during autonomous operation.

### 6. Local Token Data Structures

While tokens are stored server-side, there are local structures for OAuth client information:

#### McpOAuthStoredData (Line 448864-448910)
```javascript
{
    refreshToken: string,      // OAuth refresh token
    clientId: string,          // OAuth client ID
    clientSecret?: string,     // OAuth client secret (optional)
    redirectUris: string[]     // Allowed redirect URIs
}
```

#### McpOAuthStoredClientInfo (Line 448911-448952)
```javascript
{
    clientId: string,          // OAuth client ID
    clientSecret?: string,     // OAuth client secret (optional)
    redirectUris: string[]     // Allowed redirect URIs
}
```

These structures appear to be used for local caching or transmission to the backend.

### 7. Token Lifecycle Events

#### Configuration Changes Invalidate Tokens (Lines 448466-448482)

```javascript
async _handleMcpConfigFileChange(uri, configType, existingServers) {
    for (const server of existingServers) {
        const newServer = newServersMap.get(server.identifier);

        // Server removed - clear OAuth state
        if (!newServer) {
            await this.deleteClient(server);
            if (server.type === "streamableHttp") {
                await this.clearServerOAuthState(server.identifier);
            }
        }

        // Server config changed (hash mismatch) - clear OAuth state
        if (configHashChanged) {
            await this.deleteClient(server);
            if (server.type === "streamableHttp") {
                await this.clearServerOAuthState(server.identifier);
            }
        }
    }
}
```

#### clearServerOAuthState Implementation (Lines 448516-448526)

```javascript
async clearServerOAuthState(identifier) {
    const provider = await this.getProvider();
    await provider.runCommand(RU.LogoutServer, { identifier });
}
```

#### clearAllTokens Implementation (Lines 448595-448603)

```javascript
async clearAllTokens() {
    const provider = await this.getProvider();
    await provider.runCommand(RU.ClearAllTokens, {});
}
```

### 8. Feature Gates for OAuth

| Gate | Default | Description |
|------|---------|-------------|
| `mcp_oauth_scopes_enabled` | `true` | Enable OAuth scope handling for MCP servers |
| `mcp_oauth_url_spam_guard` | `true` | Prevent OAuth authorization URL spam attacks |

Line 294290-294300.

### 9. Security Architecture

#### Token Storage Security

1. **Server-Side Storage**: Refresh tokens stored on Cursor's backend, not locally
2. **PKCE Flow**: Uses code verifier/challenge for authorization code exchange
3. **State Management**: OAuth pending state stored server-side with unique state IDs

#### Encryption Service (Lines 466762-466855)

The SecretStorageService uses platform encryption when available:

```javascript
async initialize() {
    if (!this._useInMemoryStorage &&
        await this._encryptionService.isEncryptionAvailable()) {
        // Use persisted storage with encryption
        this._type = "persisted";
    } else {
        // Fallback to in-memory storage
        this._type = "in-memory";
    }
}
```

Platform encryption backends (Line 466769-466773):
- `kwallet` / `kwallet5` / `kwallet6` (Linux KDE)
- `gnome-libsecret` / `gnome_keyring` (Linux GNOME)
- `dpapi` (Windows)
- `keychain_access` (macOS)

### 10. Error Handling

#### Error Codes Related to Authentication (Lines 92734-92739)

```javascript
{
    no: 11,
    name: "ERROR_AUTH_TOKEN_NOT_FOUND"
},
{
    no: 12,
    name: "ERROR_AUTH_TOKEN_EXPIRED"
}
```

#### Token Expiry Handling (Lines 451391-451401)

```javascript
if (errorCode === fu.AUTH_TOKEN_EXPIRED) {
    this.cursorAuthenticationService.refreshAuthentication()
        .then(async () => {
            const newToken = await this.cursorAuthenticationService.getAccessToken();
            if (rerunCallback && newToken &&
                !this.cursorAuthenticationService.isTokenExpired(newToken)) {
                rerunCallback();
            }
        });
}
```

Note: This is for Cursor's main authentication, but shows the pattern for token expiry handling.

## Token Refresh Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MCP OAuth Token Refresh Flow                       │
└─────────────────────────────────────────────────────────────────────────────┘

1. INITIAL AUTH FLOW
   ┌──────────┐     OAuth Config      ┌─────────────────┐
   │  Cursor  │ ──────────────────────▶ │   MCP Server    │
   │   IDE    │                        │  (streamableHttp)│
   └──────────┘                        └─────────────────┘
        │                                      │
        │ StoreMcpOAuthPendingState           │
        │ (PKCE code_verifier, client_id)     │
        ▼                                      │
   ┌──────────────────┐                       │
   │  Cursor Backend  │                       │
   │  (aiserver.v1)   │◀──────────────────────┘
   └──────────────────┘    Authorization Code Exchange
        │
        │ Returns stateId
        ▼
   Browser redirects to authorizationUrl
        │
        │ User completes OAuth
        ▼
   ┌──────────────────┐
   │  Cursor Backend  │ ◀── OAuth callback with code + stateId
   │  (aiserver.v1)   │
   └──────────────────┘
        │
        │ GetMcpOAuthPendingState (retrieve code_verifier)
        │ Exchange code for tokens
        │ StoreMcpOAuthToken (store refresh_token)
        ▼
   Tokens stored server-side

2. TOKEN VALIDATION (ongoing)
   ┌──────────┐  ValidateMcpOAuthTokens   ┌──────────────────┐
   │  Cursor  │ ─────────────────────────▶│  Cursor Backend  │
   │   IDE    │                           │  (aiserver.v1)   │
   └──────────┘                           └──────────────────┘
        │                                         │
        │ Response: hasValidToken: boolean        │
        │◀────────────────────────────────────────┘
        │
   If hasValidToken === false:
        │
        │ Server status changes to "needsAuth"
        ▼
   Start fresh OAuth flow (step 1)

3. TOKEN REFRESH (server-side, implicit)
   ┌──────────────────┐      API Request      ┌─────────────────┐
   │  Cursor Backend  │ ─────────────────────▶│   MCP Server    │
   │  (aiserver.v1)   │                       │                 │
   └──────────────────┘                       └─────────────────┘
        │                                            │
        │ If access_token expired:                   │
        │ - Use stored refresh_token                 │
        │ - Get new access_token                     │
        │ - Update stored tokens                     │
        ▼                                            │
   Token refresh handled transparently ◀─────────────┘
```

## Gaps in Current Understanding

1. **Actual Refresh Token Exchange**: The decompiled code shows storage and validation of tokens, but the actual refresh token exchange logic appears to be server-side in `aiserver.v1`.

2. **Access Token Caching**: It's unclear how long access tokens are cached or if they're passed through on every request.

3. **Token Expiry Timestamps**: The client doesn't appear to receive or track token expiry times - it only gets boolean validation results.

4. **Multi-Device Sync**: How tokens are synchronized across multiple devices using the same Cursor account.

## Potential Investigation Areas

1. **Server-Side Refresh Logic**: Would require analyzing Cursor's backend API to understand actual refresh behavior.

2. **Token Transmission**: How tokens are passed to MCP servers during API calls.

3. **Token Scope Handling**: How OAuth scopes are requested and validated.

4. **Enterprise OAuth**: Differences in OAuth handling for enterprise/team deployments.

---

*Analysis based on Cursor IDE version 2.3.41 decompiled source*
*Related: See TASK-17-mcp-oauth.md for OAuth provider architecture details*
