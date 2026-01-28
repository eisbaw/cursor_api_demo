# TASK-59: MCP OAuth Token Storage and Validation Flow Analysis

## Overview

This document analyzes the MCP (Model Context Protocol) OAuth token storage and validation flow in Cursor IDE 2.3.41. The analysis reveals a sophisticated server-side token storage architecture where OAuth tokens for MCP servers are stored on Cursor's backend rather than locally.

## Key Finding: Server-Side Token Storage

Unlike traditional local OAuth token storage, Cursor implements **server-side token storage** for MCP OAuth. Tokens are transmitted to and stored on Cursor's backend servers (aiserver.v1 service) rather than using local secure storage mechanisms like the OS keychain.

## Protobuf Message Definitions

### Token Storage Request (`aiserver.v1.StoreMcpOAuthTokenRequest`)

Located at line ~271275:

```javascript
{
    typeName: "aiserver.v1.StoreMcpOAuthTokenRequest",
    fields: [
        { no: 1, name: "server_url", kind: "scalar", T: 9 },        // string
        { no: 2, name: "refresh_token", kind: "scalar", T: 9 },     // string
        { no: 3, name: "client_id", kind: "scalar", T: 9, opt: true },
        { no: 4, name: "client_secret", kind: "scalar", T: 9, opt: true },
        { no: 5, name: "redirect_uri", kind: "scalar", T: 9, opt: true }
    ]
}
```

### Token Storage Response (`aiserver.v1.StoreMcpOAuthTokenResponse`)

```javascript
{
    typeName: "aiserver.v1.StoreMcpOAuthTokenResponse",
    fields: []  // Empty response - confirmation only
}
```

### Token Validation Request (`aiserver.v1.ValidateMcpOAuthTokensRequest`)

Located at line ~271353:

```javascript
{
    typeName: "aiserver.v1.ValidateMcpOAuthTokensRequest",
    fields: [
        { no: 1, name: "server_urls", kind: "scalar", T: 9, repeated: true }  // string[]
    ]
}
```

### Token Validation Response (`aiserver.v1.ValidateMcpOAuthTokensResponse`)

```javascript
{
    typeName: "aiserver.v1.ValidateMcpOAuthTokensResponse",
    fields: [
        { no: 1, name: "results", kind: "message", T: ValidateMcpOAuthTokensResponse.Result, repeated: true }
    ]
}
```

### Validation Result Structure

```javascript
{
    typeName: "aiserver.v1.ValidateMcpOAuthTokensResponse.Result",
    fields: [
        { no: 1, name: "server_url", kind: "scalar", T: 9 },        // string
        { no: 2, name: "has_valid_token", kind: "scalar", T: 8 }     // boolean
    ]
}
```

## OAuth Pending State Management (PKCE Flow)

### Store Pending State Request (`aiserver.v1.StoreMcpOAuthPendingStateRequest`)

Located at line ~271450:

```javascript
{
    typeName: "aiserver.v1.StoreMcpOAuthPendingStateRequest",
    fields: [
        { no: 1, name: "server_url", kind: "scalar", T: 9 },
        { no: 2, name: "code_verifier", kind: "scalar", T: 9 },     // PKCE code verifier
        { no: 3, name: "client_id", kind: "scalar", T: 9, opt: true },
        { no: 4, name: "client_secret", kind: "scalar", T: 9, opt: true },
        { no: 5, name: "redirect_uri", kind: "scalar", T: 9, opt: true }
    ]
}
```

### Store Pending State Response (`aiserver.v1.StoreMcpOAuthPendingStateResponse`)

```javascript
{
    typeName: "aiserver.v1.StoreMcpOAuthPendingStateResponse",
    fields: [
        { no: 1, name: "state_id", kind: "scalar", T: 9 }           // Returned state identifier
    ]
}
```

### Get Pending State Request (`aiserver.v1.GetMcpOAuthPendingStateRequest`)

```javascript
{
    typeName: "aiserver.v1.GetMcpOAuthPendingStateRequest",
    fields: [
        { no: 1, name: "state_id", kind: "scalar", T: 9 }
    ]
}
```

### Get Pending State Response (`aiserver.v1.GetMcpOAuthPendingStateResponse`)

```javascript
{
    typeName: "aiserver.v1.GetMcpOAuthPendingStateResponse",
    fields: [
        { no: 1, name: "server_url", kind: "scalar", T: 9 },
        { no: 2, name: "code_verifier", kind: "scalar", T: 9 },
        { no: 3, name: "client_id", kind: "scalar", T: 9, opt: true },
        { no: 4, name: "client_secret", kind: "scalar", T: 9, opt: true },
        { no: 5, name: "redirect_uri", kind: "scalar", T: 9, opt: true }
    ]
}
```

## Local Storage Data Structures

### McpOAuthStoredData (`aiserver.v1.McpOAuthStoredData`)

Located at line ~448872:

```javascript
{
    typeName: "aiserver.v1.McpOAuthStoredData",
    fields: [
        { no: 1, name: "refresh_token", kind: "scalar", T: 9 },
        { no: 2, name: "client_id", kind: "scalar", T: 9 },
        { no: 3, name: "client_secret", kind: "scalar", T: 9, opt: true },
        { no: 4, name: "redirect_uris", kind: "scalar", T: 9, repeated: true }
    ]
}
```

### McpOAuthStoredClientInfo (`aiserver.v1.McpOAuthStoredClientInfo`)

```javascript
{
    typeName: "aiserver.v1.McpOAuthStoredClientInfo",
    fields: [
        { no: 1, name: "client_id", kind: "scalar", T: 9 },
        { no: 2, name: "client_secret", kind: "scalar", T: 9, opt: true },
        { no: 3, name: "redirect_uris", kind: "scalar", T: 9, repeated: true }
    ]
}
```

## gRPC Service Methods

The UserService in aiserver.v1 exposes these MCP OAuth methods (line ~719241):

```javascript
{
    storeMcpOAuthToken: {
        name: "StoreMcpOAuthToken",
        I: StoreMcpOAuthTokenRequest,
        O: StoreMcpOAuthTokenResponse,
        kind: Kt.Unary
    },
    validateMcpOAuthTokens: {
        name: "ValidateMcpOAuthTokens",
        I: ValidateMcpOAuthTokensRequest,
        O: ValidateMcpOAuthTokensResponse,
        kind: Kt.Unary
    },
    storeMcpOAuthPendingState: {
        name: "StoreMcpOAuthPendingState",
        I: StoreMcpOAuthPendingStateRequest,
        O: StoreMcpOAuthPendingStateResponse,
        kind: Kt.Unary
    },
    getMcpOAuthPendingState: {
        name: "GetMcpOAuthPendingState",
        I: GetMcpOAuthPendingStateRequest,
        O: GetMcpOAuthPendingStateResponse,
        kind: Kt.Unary
    }
}
```

## Agent Service Token Retrieval

The agent.v1 service provides token retrieval for background agents (line ~807613):

```javascript
{
    getMcpRefreshTokens: {
        name: "GetMcpRefreshTokens",
        I: GetMcpRefreshTokensRequest,  // Empty request
        O: GetMcpRefreshTokensResponse,
        kind: Kt.Unary
    }
}
```

### GetMcpRefreshTokensResponse

```javascript
{
    typeName: "agent.v1.GetMcpRefreshTokensResponse",
    fields: [
        { no: 1, name: "refresh_tokens", kind: "map", K: 9, V: { kind: "scalar", T: 9 } }
        // Map<string, string> - server_url -> refresh_token
    ]
}
```

## MCP Service IPC Commands

The MCPService uses IPC commands to interact with the extension host (line ~268984):

```javascript
{
    CallTool: "mcp.callTool",
    CreateClient: "mcp.createClient",
    DeleteClient: "mcp.deleteClient",
    ReloadClient: "mcp.reloadClient",
    ListOfferings: "mcp.listOfferings",
    ListToolsRaw: "mcp.listToolsRaw",
    LogoutServer: "mcp.logoutServer",
    ClearAllTokens: "mcp.clearAllTokens",
    GetInstructions: "mcp.getInstructions",
    GetPrompt: "mcp.getPrompt",
    ReadResource: "mcp.readResource"
}
```

## OAuth Flow Implementation

### Server Status Types

MCP servers have distinct status types including OAuth states:

```javascript
// Status type "needsAuth" with authorizationUrl
{
    type: "needsAuth",
    authorizationUrl: "<oauth_authorization_url>"
}
```

### OAuth Flow Sequence

1. **Initial Connection**: Client creates MCP client connection
2. **Auth Required**: Server responds with `needsAuth` status and `authorizationUrl`
3. **Store Pending State**: Client stores PKCE `code_verifier` via `StoreMcpOAuthPendingState`
4. **Browser Authorization**: User is redirected to OAuth provider
5. **Callback**: OAuth callback returns with authorization code
6. **Token Exchange**: Server exchanges code for tokens using stored `code_verifier`
7. **Token Storage**: Refresh token stored via `StoreMcpOAuthToken`
8. **Token Validation**: Subsequent connections validate via `ValidateMcpOAuthTokens`

### Clear OAuth State

Located at line ~448516:

```javascript
async clearServerOAuthState(e) {
    Lu(`[MCPService] Clearing OAuth state for server: ${e}`);
    try {
        const t = await this.getProvider();
        if (!t) throw new Error("No provider found");
        await t.runCommand(RU.LogoutServer, {
            identifier: e
        });
        Lu(`[MCPService] Successfully cleared OAuth state for server: ${e}`);
    } catch (t) {
        gC(`[MCPService] Error clearing OAuth state for server ${e}:`, t);
    }
}
```

### Clear All Tokens Command

Located at line ~448595:

```javascript
async clearAllTokens() {
    Lu("[MCPService] Clearing all OAuth tokens for MCP servers");
    try {
        const e = await this.getProvider();
        if (!e) throw new Error("No provider found");
        await e.runCommand(RU.ClearAllTokens, {});
        Lu("[MCPService] Successfully cleared all OAuth tokens");
    } catch (e) {
        gC("[MCPService] Error clearing all tokens:", e);
    }
}
```

### UI Action

```javascript
class ClearAllMcpTokensAction extends St {
    static ID = "workbench.action.mcp.clearAllTokens";
    title = { value: "Clear All MCP Tokens", original: "Clear All MCP Tokens" };
    category: zn.Cursor;
    f1: true;

    async run(e) {
        await e.get(L3).clearAllTokens();
    }
}
```

## Feature Gates

MCP OAuth is controlled by feature gates:

```javascript
mcp_oauth_scopes_enabled: {
    client: true,
    default: true
}

mcp_oauth_url_spam_guard: {
    client: true,
    default: true
}
```

## MCP Server Configuration Schema

OAuth credentials can be configured statically in server configs:

```javascript
{
    auth: {
        type: ["object"],
        description: "Static OAuth client credentials for this server (optional)",
        properties: {
            CLIENT_ID: {
                type: ["string"],
                description: "OAuth 2.0 Client ID"
            },
            CLIENT_SECRET: {
                type: ["string"],
                description: "OAuth 2.0 Client Secret (optional)"
            },
            scopes: {
                type: ["array"],
                items: { type: ["string"] }
            }
        }
    }
}
```

## Encryption/Secure Storage

### Platform-Specific Backends

The encryption service supports multiple backends (line ~466772):

```javascript
{
    unknown: "unknown",
    basicText: "basic_text",           // Fallback unencrypted
    gnomeAny: "gnome_any",
    gnomeLibsecret: "gnome_libsecret", // Linux GNOME Keyring
    gnomeKeyring: "gnome_keyring",
    kwallet: "kwallet",                // Linux KDE Wallet
    kwallet5: "kwallet5",
    kwallet6: "kwallet6",
    dplib: "dpapi",                    // Windows DPAPI
    keychainAccess: "keychain_access"  // macOS Keychain
}
```

### Secret Storage Service

```javascript
class SecretStorageService {
    _storagePrefix = "secret://";

    async get(key) {
        const stored = this._storageService.get(this._storagePrefix + key);
        if (!stored) return undefined;

        // Decrypt unless in-memory mode
        return this._type === "in-memory"
            ? stored
            : await this._encryptionService.decrypt(stored);
    }

    async set(key, value) {
        // Encrypt unless in-memory mode
        const encrypted = this._type === "in-memory"
            ? value
            : await this._encryptionService.encrypt(value);

        this._storageService.set(this._storagePrefix + key, encrypted);
    }
}
```

## Security Implications

### Server-Side Storage Benefits

1. **Centralized token management**: Tokens accessible across devices/sessions
2. **Backend refresh**: Server can handle token refresh without client involvement
3. **Audit capability**: Centralized logging of token operations
4. **Revocation**: Easy server-side token revocation

### Security Considerations

1. **Transit security**: Tokens transmitted over gRPC (should use TLS)
2. **Backend trust**: Users must trust Cursor's backend with MCP OAuth tokens
3. **PKCE implementation**: Code verifier stored server-side during flow
4. **Client secrets**: Optional client_secret field transmitted to backend

### Privacy Mode

MCP config files are included in the global cursorignore defaults:

```javascript
default: ["**/.env", "**/.env.*", "**/credentials.json", "**/.cursor/mcp.json", ...]
```

## Token Lifecycle

1. **Storage**: Refresh tokens stored via aiserver.v1 UserService
2. **Validation**: `validateMcpOAuthTokens` checks token validity by server URL
3. **Retrieval**: Background agents retrieve via `getMcpRefreshTokens` (agent.v1)
4. **Invalidation**: `LogoutServer` command clears OAuth state per server
5. **Bulk Clear**: `ClearAllTokens` command wipes all MCP OAuth tokens

## Related Analysis

- TASK-17-mcp-oauth.md - Initial MCP OAuth analysis
- TASK-49-mcp-oauth.md - OAuth flow details
- TASK-58-mcp-allowlist.md - MCP tool allowlisting
- TASK-3-mcp-registry.md - MCP server registry

## File References

- Source: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- Protobuf definitions: Lines 271265-271607 (aiserver.v1 OAuth messages)
- MCP OAuth storage types: Lines 448860-448952 (mcp_pb.js)
- Service definitions: Lines 719241-719264 (UserService OAuth methods)
- Agent token retrieval: Lines 807474-807619 (agent.v1 getMcpRefreshTokens)
- MCPService implementation: Lines 447015-448610

## Conclusion

Cursor 2.3.41 implements a hybrid OAuth token storage architecture for MCP:

1. **Server-side primary storage**: Refresh tokens and client credentials stored on Cursor's backend
2. **PKCE support**: Code verifier stored server-side during OAuth flow
3. **Batch validation**: Ability to validate multiple server tokens in one call
4. **Agent integration**: Background agents can retrieve tokens via dedicated API
5. **Local encryption available**: Platform-specific secure storage exists but primarily used for other secrets

This architecture enables cross-device token access and centralized management but requires trusting Cursor's backend with third-party OAuth credentials.
