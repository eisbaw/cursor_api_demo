# TASK-3: MCPRegistryService and MCP Integration Analysis

Analysis of Model Context Protocol (MCP) integration in Cursor IDE based on decompiled source (version 2.3.41).

## MCPRegistryService Overview

The `aiserver.v1.MCPRegistryService` is a gRPC service that provides discovery of known/registered MCP servers from Cursor's backend.

### Service Definition (Line 449099-449112)
```javascript
// out-build/proto/aiserver/v1/mcp_connectweb.js
{
    typeName: "aiserver.v1.MCPRegistryService",
    methods: {
        getKnownServers: {
            name: "GetKnownServers",
            I: GetKnownServersRequest,  // Empty request
            O: GetKnownServersResponse, // Contains list of MCPServerRegistration
            kind: Kt.Unary
        }
    }
}
```

## MCPService Architecture

### Class Overview (Lines 447208-448698)

The `MCPService` (service ID: `mcpService`) is the central service managing all MCP server operations. It is implemented as `bTs` class (obfuscated name) extending `Ve` (Disposable base).

### Constructor Dependencies

```javascript
// 21 injected services via __decorate (Line 448698)
MCPService(
    storageService,           // @param(0, bn) - Persistent storage
    everythingProviderService,// @param(1, nF) - Fallback MCP provider
    reactiveStorageService,   // @param(2, pc) - Reactive state storage
    contextService,           // @param(3, Gn) - Workspace context
    fileService,              // @param(4, ts) - File system operations
    uriIdentityService,       // @param(5, pl) - URI handling
    environmentService,       // @param(6, gF) - Environment info
    pathService,              // @param(7, zf) - Path resolution
    notificationService,      // @param(8, Us) - User notifications
    composerModesService,     // @param(9, W_) - Composer mode management
    adminSettingsService,     // @param(10, rre) - Admin/team settings
    commandService,           // @param(11, $n) - Command execution
    analyticsService,         // @param(12, Bh) - Analytics tracking
    quickInputService,        // @param(13, To) - Quick input UI
    configurationResolverService, // @param(14, KU) - Variable resolution
    experimentsService,       // @param(15, yc) - Feature gates
    mcpProviderService,       // @param(16, vTs) - MCP provider registry
    appLayoutService,         // @param(17, qE) - App layout
    browserAutomationService, // @param(18, rpt) - Browser automation
    configurationService,     // @param(19, jt) - Settings
    composerDataService       // @param(20, Yo) - Composer data
)
```

### Server Sources (Lines 447671-447687)

The MCPService aggregates servers from multiple sources:

```javascript
getServers() {
    const providerServers = this.mcpProviderService.getAllProviders().map(provider => ({
        identifier: provider.id,
        name: provider.id,
        type: "streamableHttp",
        url: "mcp-provider://" + provider.id,
        projectManaged: false
    }));

    return [
        ...this.defaultServers,           // Built-in servers
        ...this.userConfiguredServers,    // From ~/.cursor/mcp.json
        ...this.projectManagedServers,    // From .cursor/mcp.json
        ...this.extensionRegisteredServers, // From VS Code extensions
        ...providerServers                // From MCP Provider Service
    ];
}
```

### Reactive State Signals (Lines 447209-447211)

MCPService uses SolidJS-style signals for reactive state management:

| Signal | Type | Purpose |
|--------|------|---------|
| `allServersSignal` | `MCPServer[]` | All registered servers |
| `toolsCacheSignal` | `Record<string, Tool[]>` | Tools by server ID |
| `promptsCacheSignal` | `Record<string, Prompt[]>` | Prompts by server ID |
| `resourcesCacheSignal` | `Record<string, Resource[]>` | Resources by server ID |
| `statusCacheSignal` | `Record<string, Status>` | Server status by ID |
| `progressCacheSignal` | `Record<string, Progress>` | Tool progress by token |
| `parsingErrorsSignal` | `Record<string, string>` | Config parsing errors |
| `elicitationRequestsCacheSignal` | `Record<string, Request>` | Pending elicitation requests |

## Protobuf Message Types

### Core MCP Messages

| Type Name | Fields | Description |
|-----------|--------|-------------|
| `aiserver.v1.MCPRegistryService` | - | gRPC service for server discovery |
| `aiserver.v1.MCPKnownServerInfo` | name, description, icon, endpoint, is_featured | Metadata about a known MCP server |
| `aiserver.v1.MCPServerRegistration` | domains[], info | Maps domains to server info |
| `aiserver.v1.GetKnownServersRequest` | (empty) | Request to get known servers |
| `aiserver.v1.GetKnownServersResponse` | servers[] | Response with server registrations |

### MCPKnownServerInfo Fields (Lines 448964-448989)

```javascript
{
    name: string,        // field no: 1, scalar T:9 (string)
    description: string, // field no: 2, scalar T:9
    icon: string,        // field no: 3, scalar T:9
    endpoint: string,    // field no: 4, scalar T:9
    is_featured: boolean // field no: 5, scalar T:8 (bool)
}
```

### MCPServerRegistration Fields (Lines 449014-449025)

```javascript
{
    domains: string[],   // field no: 1, repeated scalar T:9
    info: MCPKnownServerInfo // field no: 2, message
}
```

### MCP Tool Execution Messages

| Type Name | Fields | Description |
|-----------|--------|-------------|
| `aiserver.v1.MCPParams` | tools[], file_output_threshold_bytes | Tool call parameters |
| `aiserver.v1.MCPParams.Tool` | name, description, parameters, server_name | Individual tool definition |
| `aiserver.v1.MCPResult` | selected_tool, result | Tool execution result |
| `aiserver.v1.MCPStream` | - | Streaming tool output |
| `aiserver.v1.CallMcpToolParams` | - | Parameters for tool call |
| `aiserver.v1.CallMcpToolResult` | - | Result of tool call |

### Agent-side MCP Messages (agent.v1 namespace)

| Type Name | Fields | Description |
|-----------|--------|-------------|
| `agent.v1.McpToolDefinition` | name, provider_identifier, tool_name, description, input_schema | Tool schema definition |
| `agent.v1.McpTools` | mcp_tools[] | Collection of tool definitions |
| `agent.v1.McpInstructions` | server_name, instructions | Server-specific instructions |
| `agent.v1.McpDescriptor` | - | MCP descriptor for agent |
| `agent.v1.McpArgs` | - | Arguments for MCP call |
| `agent.v1.McpResult` | - | Result from MCP call |
| `agent.v1.McpSuccess` | - | Success result |
| `agent.v1.McpError` | - | Error result |
| `agent.v1.McpRejected` | - | User-rejected result |
| `agent.v1.McpPermissionDenied` | - | Permission denied result |
| `agent.v1.McpToolCall` | - | Tool call representation |

### MCP Resources Messages

| Type Name | Fields | Description |
|-----------|--------|-------------|
| `aiserver.v1.ListMcpResourcesParams` | - | Params for listing resources |
| `aiserver.v1.ListMcpResourcesResult` | - | Resource list result |
| `aiserver.v1.ListMcpResourcesResult.MCPResource` | - | Individual resource |
| `aiserver.v1.ReadMcpResourceParams` | - | Params for reading resource |
| `aiserver.v1.ReadMcpResourceResult` | - | Resource content result |

### MCP Configuration Messages

| Type Name | Fields | Description |
|-----------|--------|-------------|
| `aiserver.v1.GetMcpConfigRequest` | - | Get MCP configuration |
| `aiserver.v1.GetMcpConfigResponse` | - | Configuration response |
| `aiserver.v1.GetAvailableMcpServersRequest` | - | Get available servers |
| `aiserver.v1.GetAvailableMcpServersResponse` | - | Available servers list |
| `aiserver.v1.GetAvailableMcpServersResponse.McpServerInfo` | id, name, is_team_server, enabled, type, command, args, url | Server info |
| `aiserver.v1.SetMcpConfigRequest` | - | Set configuration |
| `aiserver.v1.SetMcpConfigResponse` | - | Set config response |

### MCP Access Control Messages

| Type Name | Fields | Description |
|-----------|--------|-------------|
| `aiserver.v1.AllowedMCPServer` | command, server_url | Allowed server definition |
| `aiserver.v1.AllowedMCPConfiguration` | disable_all, allowed_mcp_servers[] | Allowlist configuration |
| `aiserver.v1.MCPControls` | enabled, allowed_tools[] | MCP control settings |

### MCP OAuth Messages

| Type Name | Description |
|-----------|-------------|
| `aiserver.v1.StoreMcpOAuthTokenRequest` | Store OAuth token |
| `aiserver.v1.StoreMcpOAuthTokenResponse` | Token storage response |
| `aiserver.v1.ValidateMcpOAuthTokensRequest` | Validate OAuth tokens |
| `aiserver.v1.ValidateMcpOAuthTokensResponse` | Validation result |
| `aiserver.v1.StoreMcpOAuthPendingStateRequest` | Store pending OAuth state |
| `aiserver.v1.StoreMcpOAuthPendingStateResponse` | Pending state response |
| `aiserver.v1.GetMcpOAuthPendingStateRequest` | Get pending OAuth state |
| `aiserver.v1.GetMcpOAuthPendingStateResponse` | Pending state response |
| `aiserver.v1.McpOAuthStoredData` | Stored OAuth data |
| `aiserver.v1.McpOAuthStoredClientInfo` | OAuth client info |

## MCP Server Configuration Format

### Configuration File Locations

1. **User Config**: `~/.cursor/mcp.json`
2. **Project Config**: `<project-root>/.cursor/mcp.json`
3. **VSCode Compat**: `<project-root>/.vscode/mcp.json`
4. **Windsurf Import**: `~/.codeium/windsurf/mcp_config.json`

### JSON Schema (Lines 446872-447010)

Schema IDs:
- `vscode://schemas/mcp` - Server definition schema
- `vscode://schemas/mcp-config` - Full config file schema

```json
{
  "$schema": "vscode://schemas/mcp-config",
  "mcpServers": {
    "example-stdio-server": {
      "command": "python server.py",
      "args": ["--port", "8080"],
      "env": {
        "DEBUG": "true"
      }
    },
    "example-stdio-server-with-envfile": {
      "command": "python server.py",
      "envFile": "${workspaceFolder}/.env",
      "env": {
        "DEBUG": "true"
      }
    },
    "example-sse-server": {
      "url": "http://localhost:3000/sse",
      "headers": {
        "Authorization": "Bearer ${env:TOKEN}"
      },
      "auth": {
        "CLIENT_ID": "your-client-id"
      }
    }
  }
}
```

### Server Types

1. **stdio** - Command-line based servers (Lines 446880-446914)
   - `command`: Executable command (required)
   - `args`: Command arguments (optional array)
   - `env`: Environment variables (optional object)
   - `envFile`: Path to .env file (optional, supports variable resolution)
   - `enabledTools`: Array of tool names to enable (optional)

2. **streamableHttp** (SSE/HTTP) - Network-based servers (Lines 446915-446956)
   - `url`: Server URL (required)
   - `headers`: HTTP headers (optional object)
   - `auth`: OAuth configuration (optional)
     - `CLIENT_ID`: OAuth 2.0 Client ID
   - `enabledTools`: Array of tool names to enable (optional)

### Internal Server Configuration Object

```javascript
// stdio server
{
    identifier: string,       // Computed unique ID: "user-{name}" or "project-{path}-{name}"
    name: string,             // Server name from config key
    type: "stdio",
    command: string,
    args: string[],
    env: Record<string, string>,
    envFile?: string,
    projectManaged: boolean,  // true if from project .cursor/mcp.json
    projectPath?: string,     // folder key if project-managed
    extensionId?: string,     // if registered by extension
    enabledTools?: string[]
}

// streamableHttp server
{
    identifier: string,
    name: string,
    type: "streamableHttp",
    url: string,
    headers?: Record<string, string>,
    auth?: { CLIENT_ID?: string },
    projectManaged: boolean,
    projectPath?: string,
    extensionId?: string,
    enabledTools?: string[]
}
```

### Server Identifier Computation (Lines 447501-447507)

```javascript
computeIdentifier(server) {
    const prefix = this.computeIdentifierPrefix(server.projectPath);
    return server.extensionId
        ? `${prefix}${server.extensionId}-${server.name}`
        : `${prefix}${server.name}`;
}

computeIdentifierPrefix(projectPath) {
    return projectPath ? `project-${projectPath}-` : "user-";
}
```

## MCP Client Architecture

### Client Types (Lines 447018-447207)

Three client implementations abstract server communication:

#### 1. EverythingProviderClient (`fso` class)

Default client for servers managed through VS Code's "Everything Provider" pattern:

```javascript
class EverythingProviderClient {
    constructor(everythingProviderService, serverId);

    async getProvider() {
        // Waits up to 60s for provider to be available
        return this.everythingProviderService.waitForCommandEverythingProvider(60000, "mcp.createClient");
    }

    async callTool(name, args, useLeaseElicitation, toolCallId, abortSignal);
    async getPrompt(name, args);
    async readResource(uri);
    async listOfferings();      // Returns tools, prompts, resources
    async listToolsRaw();       // Returns raw tool definitions
    async createClient(serverInfo);
    async deleteClient();
    async reloadClient(serverInfo);
    async logoutServer();
    async clearAllTokens();
}
```

#### 2. MCPProviderClient (`UAc` class)

Client for servers registered through MCPProviderService:

```javascript
class MCPProviderClient {
    constructor(mcpProviderService, serverId) {
        this.provider = mcpProviderService.getMcpProvider(serverId);
        if (!this.provider) throw new Error(`MCP provider with id '${serverId}' not found`);
    }

    async callTool(name, args, useLeaseElicitation, toolCallId, abortSignal);
    async listOfferings();
    async listToolsRaw();
    getInstructions(); // Returns provider.instructions synchronously

    // No-op implementations:
    async getPrompt();
    async readResource();
    async createClient();
    async deleteClient();
    async reloadClient();
    async logoutServer();
    async clearAllTokens();
}
```

#### 3. RecoveryWrapperClient (`WAc` class)

Self-healing wrapper that attempts recovery on server failures:

```javascript
const MAX_RECOVERY_ATTEMPTS = 3; // eJt constant

class RecoveryWrapperClient {
    constructor({
        client,             // Underlying client
        serverId,
        shouldAttemptRecovery, // () => boolean
        recreateClient,     // () => Promise<boolean>
        onRecoverySuccess,  // () => void
        onRecoveryFailure   // () => void
    });

    async withRecovery(operation) {
        try {
            const result = await operation();
            this.consecutiveFailures = 0;
            return result;
        } catch (error) {
            if (this.isServerMissingError(error) && this.shouldAttemptRecovery()) {
                // Attempt recovery up to MAX_RECOVERY_ATTEMPTS times
            }
            throw error;
        }
    }

    isServerMissingError(error) {
        const message = error instanceof Error ? error.message : String(error);
        return message.includes("No server info found") || message.includes("No adapter found");
    }
}
```

### MCP Provider Commands (Line 268984)

Internal command IDs used for MCP operations:

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

## Server Status Management

### Status Types (Lines 447637-447660, 447927-447957)

```javascript
type ServerStatus =
    | { type: "disconnected" }
    | { type: "initializing" }
    | { type: "connected" }
    | { type: "error", error: string }
    | { type: "needsAuth", authorizationUrl?: string };
```

### Status File System (Lines 447919-447951)

When `mcp_file_system` feature gate is enabled, MCPService writes status files:

```javascript
// Location: .cursor/workspaces/{workspace}/mcp/{serverId}/STATUS.md
// Only created for error/needsAuth states

// Error message content:
"The MCP server errored. If you definitely need to use this tool or the user has explicitly asked for it to be used, concisely inform the user and instruct them to check the MCP status in Cursor Settings; otherwise try to proceed with a different approach."

// Auth required message:
"The MCP server needs authentication. If you definitely need to use this tool or the user has explicitly asked for it to be used, concisely inform the user and instruct them to check the MCP status in Cursor Settings; otherwise try to proceed with a different approach."
```

### Status Commands (Lines 447217-447256)

Commands for external status updates:

| Command ID | Purpose |
|------------|---------|
| `mcp.updateStatus` | Update server status from external source |
| `mcp.needsAuth` | Set server to needsAuth state with URL |
| `mcp.reloadClient` | Trigger client reload |
| `mcp.toolListChanged` | Refresh tools cache |
| `mcp.resourceListChanged` | Refresh resources cache |

## Tool/Resource/Prompt Discovery

### Cache Refresh Flow (Lines 447774-447825)

```javascript
async refreshCaches() {
    // Debounced - returns existing promise if refresh in progress
    if (this.refreshCachesPromise) return this.refreshCachesPromise;

    this.refreshCachesPromise = this._doRefreshCaches().finally(() => {
        this.refreshCachesPromise = undefined;
    });
    return this.refreshCachesPromise;
}

async _doRefreshCaches() {
    const servers = this.getServers();
    let tools = {}, prompts = {}, resources = {};

    for (const server of servers) {
        // Skip disabled servers (except provider servers)
        if (!this.isServerEnabled(server) && !this.isMcpProviderServer(server)) continue;

        const offerings = await this.getMcpClient(server.identifier).listOfferings();

        // Parse tools
        tools[server.identifier] = offerings.tools.map(tool => ({
            name: tool.name,
            description: tool.description,
            inputSchema: tool.parameters ? JSON.parse(tool.parameters) : {},
            outputSchema: tool.outputSchema ? JSON.parse(tool.outputSchema) : undefined
        }));

        // Parse prompts (if any)
        if (offerings.prompts.length > 0) {
            prompts[server.identifier] = offerings.prompts.map(prompt => ({
                name: prompt.name,
                description: prompt.description,
                inputSchema: prompt.parameters ? JSON.parse(prompt.parameters) : {}
            }));
        }

        // Parse resources (if any)
        if (offerings.resources?.length > 0) {
            resources[server.identifier] = offerings.resources.map(res => ({
                uri: res.uri,
                name: res.name,
                description: res.description,
                mimeType: res.mimeType,
                annotations: res.annotations
            }));
        }
    }

    this.setToolsCache(tools);
    this.setPromptsCache(prompts);
    this.setResourcesCache(resources);

    await this.writeMcpIndexFiles(tools, resources, prompts);
}
```

### MCP Index File Structure (Lines 447827-447917)

When `mcp_file_system` feature gate is enabled:

```
.cursor/workspaces/{workspace}/mcp/
├── {server-id}/
│   ├── tools/
│   │   ├── {tool-name}.json
│   │   └── ...
│   ├── resources/
│   │   ├── {resource-name}.json
│   │   └── ...
│   ├── prompts/
│   │   ├── {prompt-name}.json
│   │   └── ...
│   └── STATUS.md  (optional, only for error/auth states)
└── ...
```

Tool JSON format:
```json
{
    "name": "tool_name",
    "description": "Tool description",
    "arguments": { /* JSON Schema */ },
    "outputSchema": { /* optional JSON Schema */ }
}
```

## Extension API for MCP Registration

### Main Thread Handler (Lines 832669-832684)

```javascript
// MainThreadCursor class methods
async $registerMCPServer(serverConfig, extensionId) {
    const name = serverConfig.name;
    let config;

    if ("url" in serverConfig.server) {
        config = { url: serverConfig.server.url };
    } else if ("command" in serverConfig.server) {
        config = {
            command: serverConfig.server.command,
            args: serverConfig.server.args,
            env: serverConfig.server.env
        };
    } else {
        throw new Error(`Invalid MCP server config: expected either {name, server: {url}} or {name, server: {command, args, env}}`);
    }

    return this.mcpService.registerMCPServer(name, config, extensionId);
}

async $unregisterMCPServer(name, extensionId) {
    return this.mcpService.unregisterMCPServer(name, extensionId);
}
```

### MCPService Registration (Lines 448377-448426)

```javascript
async registerMCPServer(name, serverConfig, extensionId) {
    const sanitizedName = `extension-${sanitize(name)}`;
    const identifier = this.computeIdentifier({ name: sanitizedName, extensionId });

    // Check for duplicate
    if (this.extensionRegisteredServers.some(s => s.identifier === identifier)) {
        return; // Already registered
    }

    let server;
    if (typeof serverConfig === "string" || "url" in serverConfig) {
        // HTTP/SSE server
        const url = typeof serverConfig === "string" ? serverConfig : serverConfig.url;
        server = {
            identifier,
            name: sanitizedName,
            type: "streamableHttp",
            url: this.ensureUrlHasProtocol(url),
            headers: serverConfig.headers,
            projectManaged: false,
            extensionId
        };
    } else {
        // stdio server
        server = {
            identifier,
            name: sanitizedName,
            type: "stdio",
            command: serverConfig.command,
            args: serverConfig.args,
            env: serverConfig.env ?? {},
            projectManaged: false,
            extensionId
        };
    }

    this.extensionRegisteredServers.push(server);
    this.previouslyKnownServerIds.add(identifier);
    this.savePreviouslyKnownServerIds();

    // Initialize if enabled
    if (this.isServerEnabled(server)) {
        await this.createClient(server);
        await this.refreshCaches();
    }
}
```

## MCP Provider Service

### Service Definition (Lines 446850-446870)

```javascript
// Service ID: mcpProviderService (vTs)
class MCPProviderService extends Disposable {
    constructor(experimentService) {
        this._providers = new Map();
        this._onDidChangeProviders = new Emitter();
        this.onDidChangeProviders = this._onDidChangeProviders.event;
    }

    registerMcpProvider(provider) {
        // Check feature gate if specified
        if (provider.featureGateName && !this.experimentService.checkFeatureGate(provider.featureGateName)) {
            return; // Feature not enabled
        }
        this._providers.set(provider.id, provider);
        this._onDidChangeProviders.fire();
    }

    unregisterMcpProvider(id) {
        if (this._providers.delete(id)) {
            this._onDidChangeProviders.fire();
        }
    }

    getAllProviders() {
        return Array.from(this._providers.values());
    }

    getMcpProvider(id) {
        return this._providers.get(id);
    }
}
```

### Provider Registration via Main Thread (Lines 832781-832809)

```javascript
async $registerMcpProvider(id, featureGateName, instructions) {
    const provider = {
        id,
        featureGateName,
        instructions,
        listOfferings: async () => this._proxy.$mcpListOfferings(id),
        callTool: async (name, args, toolCallId) => this._proxy.$mcpCallTool(id, name, args, toolCallId)
    };

    this.mcpProviderService.registerMcpProvider(provider);
    this._proxy.$registerMcpProvider({ id, featureGateName, instructions });
}

async $getAllMcpProviderDefinitions() {
    return this.mcpProviderService.getAllProviders().map(p => ({
        id: p.id,
        featureGateName: p.featureGateName,
        instructions: p.instructions
    }));
}

async $unregisterMcpProvider(id) {
    this.mcpProviderService.unregisterMcpProvider(id);
    this._proxy.$onDidUnregisterMcpProvider(id);
}
```

## Elicitation System

### Elicitation Request Handling (Lines 447266-447306)

Elicitation allows MCP tools to request additional user input during execution:

```javascript
// Command: mcp.elicitationRequest
handler: async (accessor, params) => {
    const { request } = params;

    const respond = (response) => {
        this.commandService.executeCommand("mcp.elicitationResponse", {
            requestId: request.id,
            response
        });
    };

    this.setElicitationRequestsCache(cache => ({
        ...cache,
        [request.id]: {
            ...request,
            resolve: respond
        }
    }));
};

// Command: mcp.leaseElicitationRequest - for long-running operations
handler: async (accessor, params) => {
    const { toolCallId, request } = params;
    const handler = this.leaseElicitationHandlers.get(toolCallId);

    if (!handler) {
        return { action: "decline" };
    }

    const response = await handler({
        id: `lease-${toolCallId}-${Date.now()}`,
        message: request.message,
        requestedSchema: request.requestedSchema
    });

    return response;
};
```

### Elicitation Response Actions

```javascript
type ElicitationResponse =
    | { action: "accept", data?: object }
    | { action: "decline" }
    | { action: "cancel" };
```

### Lease Elicitation Handler Registration (Lines 448197-448201)

```javascript
registerLeaseElicitationHandler(toolCallId, handler) {
    this.leaseElicitationHandlers.set(toolCallId, handler);
}

unregisterLeaseElicitationHandler(toolCallId) {
    this.leaseElicitationHandlers.delete(toolCallId);
}
```

## MCP Server Discovery and Registration

### Discovery Flow (mcpWellKnownDetection.js, Lines 449114-449152)

1. **Feature Gate Check**: `mcp_discovery` experiment must be enabled
2. **Backend Query**: Call `MCPRegistryService.GetKnownServers()`
3. **Domain Matching**: Match visited URL hostname against known server domains
4. **Installation Suggestion**: Show notification to install matched server

```javascript
async checkUrlForMCPServer(url) {
    if (!this.experimentService.checkFeatureGate("mcp_discovery")) return;
    const response = await mcpRegistryBackendClient.getKnownServers({});
    const hostname = new URL(url).hostname;
    for (const server of response.servers) {
        if (server.domains.some(domain => hostname.includes(domain))) {
            return server.info;
        }
    }
}
```

### Registration Methods

1. **File-based Registration** (mcpService.js)
   - Watches `~/.cursor/mcp.json` for user servers
   - Watches `<project>/.cursor/mcp.json` for project servers
   - Parses JSON, validates schema, creates server objects

2. **Extension API Registration** (Lines 448377-448465)
   - Via `$registerMCPServer` / `$unregisterMCPServer` calls
   - Creates identifier with `extension-` prefix
   - Supports both stdio and HTTP/SSE servers

3. **Deep Link Installation** (mcp.deeplinkInstall command, Line 448723)
   - Accepts server name and config via deep link
   - Writes to user config file

### Server Approval System

- **Project-managed servers** require user approval before running
- Approval is tracked by hash of server configuration (Lines 448605-448614)
- Hash change (config modification) invalidates approval
- Stored in `approvedProjectMcpServers` reactive storage

```javascript
computeServerConfigHash(server) {
    const hashFields = ["command", "args", "env", "url", "headers"];
    const data = {};
    for (const field of hashFields) {
        if (field in server) data[field] = server[field];
    }
    return hashString(JSON.stringify(data)).toString(16).substring(0, 16);
}

computeApprovalKey(server) {
    const hash = this.computeServerConfigHash(server);
    return `${server.identifier}:${hash}`;
}
```

## Tool Call Routing

### Tool Name Format

MCP tools use a combined name format: `{serverId}-{toolName}`

Example: `cursor-ide-browser-screenshot` = server `cursor-ide-browser`, tool `screenshot`

### Tool Call Flow (Lines 448045-448087)

```javascript
async callTool(toolName, args, toolCallId, abortSignal, elicitationHandler, serverHint) {
    const servers = this.getServers();
    const availableTools = await this.getAvailableTools();

    let found = false;
    let lastError;

    for (const serverId in availableTools) {
        // Skip if server hint provided and doesn't match
        if (serverHint && serverId !== serverHint) continue;

        // Skip browser servers based on connection mode
        const server = servers.find(s => s.identifier === serverId);
        // ... browser mode filtering logic

        if (availableTools[serverId].find(t => t.name === toolName)) {
            found = true;
            try {
                const client = await this.getMcpClient(server.identifier);

                // Add Playwright log configs if browser server
                let callArgs = args;
                if (server.name === "cursor-ide-browser" || server.identifier === "cursor-browser-extension") {
                    callArgs = {
                        ...args,
                        __playwrightLogConfigs: this.experimentsService.getDynamicConfig("playwright_log_configs")
                    };
                }

                const result = await client.callTool(toolName, callArgs, false, toolCallId, abortSignal);
                if (result) {
                    this.clearProgressForTool(toolCallId);
                    return result;
                }
            } catch (error) {
                lastError = error;
            }
        }
    }

    if (found) {
        throw new Error(`Tool execution failed: ${lastError?.message}`);
    }
    throw new Error(`No server found with tool: ${toolName}`);
}
```

## Built-in Browser Server Constants (Line 446847)

```javascript
const CURSOR_BROWSER_EXTENSION = "cursor-browser-extension";  // wee
const CURSOR_IDE_BROWSER_NAME = "cursor-ide-browser";         // opt
const CURSOR_IDE_BROWSER_ID = "cursor-ide-browser";           // uxe
const CURSOR_BROWSER_EXTENSION_ID = "cursor-browser-extension"; // pB

const browserServerIds = ["cursor-browser-extension", "cursor-ide-browser"]; // dxe

// Additional special servers
const IOS_SIMULATOR_SERVER = "cursor-ios-simulator-connect";  // cso
const ANDROID_EMULATOR_SERVER = "cursor-android-emulator-connect"; // uso
```

## Tool Approval System

### Allowlist Management

Tools can be added to an allowlist for automatic approval:

```javascript
// Allowlist entry format: "serverId:toolName" or "serverId:*" for all tools
function addToAllowlist(toolName, serverId, currentList) {
    const entry = `${serverId}:${toolName}`;
    if (!currentList.includes(entry)) {
        return [...currentList, entry];
    }
    return currentList;
}
```

### Protection Modes

1. **mcpToolsProtection** - General MCP tools require approval
2. **playwrightProtection** - Browser automation tools require extra approval
3. **yoloMcpToolsDisabled** - Disables auto-run for all MCP tools

## Experiment Feature Gates

| Gate Name | Description |
|-----------|-------------|
| `mcp_discovery` | Enable MCP server discovery from URLs |
| `mcp_allowlists` | Enable tool allowlist management |
| `mcp_oauth_scopes_enabled` | Enable OAuth scope handling |
| `mcp_oauth_url_spam_guard` | Prevent OAuth URL spam |
| `mcp_file_system` | Enable MCP index file system |
| `enable_self_healing_mcp_ext_host_restart` | Enable recovery wrapper for MCP clients |
| `playwright_autorun` | Enable automatic Playwright server execution |
| `playwright_suggestion` | Enable Playwright installation suggestions |

## Key Storage Keys

| Key | Scope | Description |
|-----|-------|-------------|
| `mcpServers` | Application | List of user-configured servers (legacy) |
| `approvedProjectMcpServers` | Application | Approved project server hashes |
| `disabledMcpServers` | Application | Disabled server identifiers |
| `mcpDisabledTools` | Application | Disabled tool entries (`serverId|toolName`) |
| `mcpService.knownServerIds` | Application | Known server IDs for change detection |
| `mcpAllowedTools` | ComposerState | Allowed tool entries |
| `playwrightProtection` | ComposerState | Browser tool protection flag |
| `yoloMcpToolsDisabled` | ComposerState | Global MCP auto-run disable |
| `lastBrowserConnectionMode` | Application | Last browser mode: "editor", "playwright", "none" |

## File Locations Summary

| Path | Purpose |
|------|---------|
| `out-build/proto/aiserver/v1/mcp_connectweb.js` | gRPC service definitions |
| `out-build/vs/workbench/services/ai/browser/mcpService.js` | Main MCP service |
| `out-build/vs/workbench/services/ai/browser/mcpProviderService.js` | Provider registry |
| `out-build/vs/workbench/services/ai/browser/mcpWellKnownDetection.js` | Discovery service |
| `out-build/vs/workbench/services/ai/browser/mcpInstallationService.js` | Installation service |
| `out-build/vs/workbench/services/ai/browser/mcpSchema.js` | JSON schema definitions |
| `out-build/vs/workbench/services/ai/browser/common/mcpConstants.js` | Browser server constants |

## Potential Investigation Areas

1. **OAuth Token Refresh** - Token refresh timing and error handling
2. **MCP File System Integration** - How agent reads MCP index files
3. **Browser Server Lifecycle** - Playwright vs native browser integration
4. **Tool Schema Validation** - Full validation logic in composer
5. **Progress Notification Flow** - How progress updates reach UI

---

*Analysis based on Cursor IDE version 2.3.41 decompiled source*
