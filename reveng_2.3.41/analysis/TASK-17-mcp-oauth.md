# TASK-17: MCP OAuth Token Management and Provider Architecture

Analysis of OAuth token management for MCP (Model Context Protocol) servers in Cursor IDE based on decompiled source (version 2.3.41).

## Executive Summary

Cursor implements a sophisticated OAuth 2.0 token management system for MCP servers that use HTTP/SSE transport (streamableHttp). The system leverages Cursor's backend (`aiserver.v1`) as an intermediary to store and validate OAuth tokens, using PKCE (Proof Key for Code Exchange) for enhanced security during the authorization flow.

## OAuth Token Storage Architecture

### Backend gRPC Service Methods

The OAuth token management is handled through the `aiserver.v1` service with these key methods:

| Method | Purpose | Input Message | Output Message |
|--------|---------|---------------|----------------|
| `StoreMcpOAuthToken` | Store refresh token after OAuth flow | `StoreMcpOAuthTokenRequest` | `StoreMcpOAuthTokenResponse` |
| `ValidateMcpOAuthTokens` | Check token validity for multiple servers | `ValidateMcpOAuthTokensRequest` | `ValidateMcpOAuthTokensResponse` |
| `StoreMcpOAuthPendingState` | Store PKCE state during auth flow | `StoreMcpOAuthPendingStateRequest` | `StoreMcpOAuthPendingStateResponse` |
| `GetMcpOAuthPendingState` | Retrieve pending state for callback | `GetMcpOAuthPendingStateRequest` | `GetMcpOAuthPendingStateResponse` |

### Token Storage Message Structures

#### StoreMcpOAuthTokenRequest (Line 271267-271307)
```javascript
{
    serverUrl: string,        // MCP server URL (required)
    refreshToken: string,     // OAuth refresh token (required)
    clientId?: string,        // OAuth client ID (optional)
    clientSecret?: string,    // OAuth client secret (optional)
    redirectUri?: string      // OAuth redirect URI (optional)
}
```

#### StoreMcpOAuthPendingStateRequest (Line 271442-271494)
```javascript
{
    serverUrl: string,        // MCP server URL
    codeVerifier: string,     // PKCE code verifier
    clientId?: string,        // OAuth client ID
    clientSecret?: string,    // OAuth client secret
    redirectUri?: string      // OAuth redirect URI
}
```

Response returns a `stateId` used during callback.

#### GetMcpOAuthPendingStateResponse (Line 271555-271607)
```javascript
{
    serverUrl: string,        // Original server URL
    codeVerifier: string,     // PKCE code verifier for token exchange
    clientId?: string,        // OAuth client ID
    clientSecret?: string,    // OAuth client secret
    redirectUri?: string      // OAuth redirect URI
}
```

#### ValidateMcpOAuthTokensRequest (Line 271345-271375)
```javascript
{
    serverUrls: string[]      // Array of server URLs to validate
}
```

#### ValidateMcpOAuthTokensResponse.Result (Line 271407-271441)
```javascript
{
    serverUrl: string,        // Server URL
    hasValidToken: boolean    // Whether token is valid
}
```

### Local OAuth Data Storage

#### McpOAuthStoredData (Line 448864-448910)
Used for storing OAuth data locally:
```javascript
{
    refreshToken: string,     // OAuth refresh token
    clientId: string,         // OAuth client ID
    clientSecret?: string,    // OAuth client secret (optional)
    redirectUris: string[]    // Allowed redirect URIs
}
```

#### McpOAuthStoredClientInfo (Line 448911-448952)
Client information storage:
```javascript
{
    clientId: string,         // OAuth client ID
    clientSecret?: string,    // OAuth client secret (optional)
    redirectUris: string[]    // Allowed redirect URIs
}
```

## OAuth Flow Architecture

### Server Configuration with OAuth

MCP servers can specify OAuth credentials in the configuration schema (Line 446936-446957):

```json
{
  "mcpServers": {
    "my-oauth-server": {
      "url": "https://api.example.com/mcp",
      "auth": {
        "CLIENT_ID": "your-client-id",
        "CLIENT_SECRET": "your-client-secret",
        "scopes": ["read", "write"]
      }
    }
  }
}
```

Schema properties:
- `CLIENT_ID` (required): OAuth 2.0 Client ID
- `CLIENT_SECRET` (optional): OAuth 2.0 Client Secret
- `scopes` (optional): OAuth 2.0 scopes to request (auto-fetched from server if not provided)

### Authentication State Machine

MCP servers have a status that includes an authentication state:

```javascript
// Server status types
{
    type: "needsAuth",
    authorizationUrl: string  // URL to redirect user for OAuth
}
```

Status flow:
1. `initializing` - Server starting up
2. `needsAuth` - OAuth authentication required
3. `connected` - Successfully connected
4. `error` - Connection error
5. `disconnected` - Server disconnected

### OAuth Command Handlers (Lines 447221-447232)

```javascript
// Command to trigger needsAuth status
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

## Token Passing to MCP Servers

### Client Creation Flow

When creating an MCP client for a streamableHttp server (Lines 448245-448266):

```javascript
async createClient(server) {
    const resolvedServer = await this.resolveServerVariables(server);
    const mcpClient = await this.getMcpClient(resolvedServer.identifier);

    const serverInfo = {
        type: "streamableHttp",
        serverUrl: resolvedServer.url,
        headers: resolvedServer.headers,    // Custom headers
        auth: resolvedServer.auth,          // OAuth configuration
        projectPath: resolvedServer.projectPath
    };

    return await mcpClient.createClient(serverInfo);
}
```

The `auth` object containing `CLIENT_ID`, `CLIENT_SECRET`, and `scopes` is passed directly to the client creation command.

### Provider Routing

Token-related operations are routed through the `everythingProviderService`:

```javascript
// MCP Command enum (Line 268984)
{
    CallTool: "mcp.callTool",
    CreateClient: "mcp.createClient",
    DeleteClient: "mcp.deleteClient",
    ReloadClient: "mcp.reloadClient",
    LogoutServer: "mcp.logoutServer",
    ClearAllTokens: "mcp.clearAllTokens",
    // ...
}
```

## Token Lifecycle Management

### Clearing OAuth State

```javascript
// clearServerOAuthState (Line 448516-448526)
async clearServerOAuthState(identifier) {
    const provider = await this.getProvider();
    await provider.runCommand(RU.LogoutServer, { identifier });
}
```

This is called when:
1. Server configuration changes (hash mismatch)
2. Server is removed from configuration
3. User explicitly logs out

### Clearing All Tokens

```javascript
// clearAllTokens (Line 448595-448603)
async clearAllTokens() {
    const provider = await this.getProvider();
    await provider.runCommand(RU.ClearAllTokens, {});
}
```

### Server Removal Token Cleanup (Lines 448439-448445)

```javascript
async unregisterMCPServer(name, extensionId) {
    await this.deleteClient(server);
    if (server.type === "streamableHttp") {
        await this.clearServerOAuthState(server.identifier);
    }
}
```

## Feature Gates

| Gate | Default | Description |
|------|---------|-------------|
| `mcp_oauth_scopes_enabled` | `true` | Enable OAuth scope handling |
| `mcp_oauth_url_spam_guard` | `true` | Prevent OAuth URL spam attacks |

These are defined at Line 294290-294300.

## UI Integration

### Server Status Display (Lines 909174-909220)

The UI shows authentication status:
```javascript
const needsAuth = () => server.status.type === "needsAuth";
const isHttpServer = () => server.type === "streamableHttp";

// On connect button click
if (needsAuth() && status.type === "needsAuth") {
    openerService.open(status.authorizationUrl);
}
```

### Reconnect with Fresh OAuth (Lines 909395-909411)

```javascript
async initiateReconnect() {
    // Clear existing OAuth state
    await mcpService.clearServerOAuthState(server.identifier);

    // Listen for status changes
    const listener = mcpService.onDidChangeServerStatus(({identifier, status}) => {
        if (status.type === "needsAuth") {
            // Open authorization URL in browser
            openerService.open(status.authorizationUrl);
        }
    });

    // Trigger reload to start fresh OAuth flow
    await mcpService.reloadClient(server.identifier);
}
```

## Security Considerations

### PKCE Implementation

The system uses PKCE (Proof Key for Code Exchange):
1. `codeVerifier` is generated client-side
2. Stored via `StoreMcpOAuthPendingState` with a returned `stateId`
3. Retrieved via `GetMcpOAuthPendingState` during callback
4. Used for token exchange with the MCP server

### Token Storage Location

Tokens are stored on Cursor's backend (`aiserver.v1`), not locally. This:
- Enables cross-device token persistence
- Centralizes token validation
- Keeps refresh tokens server-side for security

### URL Spam Guard

Feature gate `mcp_oauth_url_spam_guard` prevents:
- Repeated authorization URL opens
- Potential phishing through malicious MCP servers

## Provider Architecture Summary

```
                                    +-------------------+
                                    | Cursor Backend    |
                                    | (aiserver.v1)     |
                                    +-------------------+
                                            |
                                            | gRPC
                                            |
+------------------+     +------------------+------------------+
| MCPService       |---->| EverythingProviderService         |
| (Browser/Main)   |     | - Routing to ExtHost providers    |
+------------------+     +-----------------------------------+
        |                            |
        | Commands                   |
        |                            v
        |                +-------------------+
        |                | ExtHostMcp        |
        |                | (Extension Host)  |
        +--------------->+-------------------+
                                   |
                                   | MCP Protocol
                                   v
                         +-------------------+
                         | MCP Servers       |
                         | (stdio/HTTP)      |
                         +-------------------+
```

## Potential Investigation Areas

1. **Token Refresh Logic** - How refresh tokens are used to obtain new access tokens
2. **ExtHost OAuth Handling** - Deep dive into extension host's OAuth implementation
3. **Server Discovery OAuth** - How discovered servers handle OAuth registration
4. **Team/Enterprise OAuth** - OAuth differences for team-managed servers
5. **OAuth Error Recovery** - How token failures are handled and recovered

---

*Analysis based on Cursor IDE version 2.3.41 decompiled source*
*Related: See TASK-3-mcp-registry.md for MCP server registration details*
