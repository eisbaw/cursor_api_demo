# TASK-27: MCP Tool Integration Schemas

Analysis of MCP (Model Context Protocol) tool integration schemas in Cursor IDE based on decompiled source.

## ClientSideToolV2 Enum - MCP Integration Points

The `ClientSideToolV2` enum (from `aiserver.v1.ClientSideToolV2`) defines all client-side tools, including three MCP-related tools:

| Enum Value | Field Number | Description |
|------------|--------------|-------------|
| `CLIENT_SIDE_TOOL_V2_MCP` | 19 | Legacy MCP tool call (multiple tools selection) |
| `CLIENT_SIDE_TOOL_V2_LIST_MCP_RESOURCES` | 44 | List available MCP resources |
| `CLIENT_SIDE_TOOL_V2_READ_MCP_RESOURCE` | 45 | Read a specific MCP resource |
| `CLIENT_SIDE_TOOL_V2_CALL_MCP_TOOL` | 49 | Direct MCP tool call (single tool) |

### Full ClientSideToolV2 Enum (Line 104366-104501)

```javascript
// aiserver.v1.ClientSideToolV2
{
    CLIENT_SIDE_TOOL_V2_UNSPECIFIED: 0,
    CLIENT_SIDE_TOOL_V2_READ_SEMSEARCH_FILES: 1,
    CLIENT_SIDE_TOOL_V2_RIPGREP_SEARCH: 3,
    CLIENT_SIDE_TOOL_V2_READ_FILE: 5,
    CLIENT_SIDE_TOOL_V2_LIST_DIR: 6,
    CLIENT_SIDE_TOOL_V2_EDIT_FILE: 7,
    CLIENT_SIDE_TOOL_V2_FILE_SEARCH: 8,
    CLIENT_SIDE_TOOL_V2_SEMANTIC_SEARCH_FULL: 9,
    CLIENT_SIDE_TOOL_V2_DELETE_FILE: 11,
    CLIENT_SIDE_TOOL_V2_REAPPLY: 12,
    CLIENT_SIDE_TOOL_V2_RUN_TERMINAL_COMMAND_V2: 15,
    CLIENT_SIDE_TOOL_V2_FETCH_RULES: 16,
    CLIENT_SIDE_TOOL_V2_WEB_SEARCH: 18,
    CLIENT_SIDE_TOOL_V2_MCP: 19,              // MCP tool (legacy)
    CLIENT_SIDE_TOOL_V2_SEARCH_SYMBOLS: 23,
    CLIENT_SIDE_TOOL_V2_BACKGROUND_COMPOSER_FOLLOWUP: 24,
    CLIENT_SIDE_TOOL_V2_KNOWLEDGE_BASE: 25,
    CLIENT_SIDE_TOOL_V2_FETCH_PULL_REQUEST: 26,
    CLIENT_SIDE_TOOL_V2_DEEP_SEARCH: 27,
    CLIENT_SIDE_TOOL_V2_CREATE_DIAGRAM: 28,
    CLIENT_SIDE_TOOL_V2_FIX_LINTS: 29,
    CLIENT_SIDE_TOOL_V2_READ_LINTS: 30,
    CLIENT_SIDE_TOOL_V2_GO_TO_DEFINITION: 31,
    CLIENT_SIDE_TOOL_V2_TASK: 32,
    CLIENT_SIDE_TOOL_V2_AWAIT_TASK: 33,
    CLIENT_SIDE_TOOL_V2_TODO_READ: 34,
    CLIENT_SIDE_TOOL_V2_TODO_WRITE: 35,
    CLIENT_SIDE_TOOL_V2_EDIT_FILE_V2: 38,
    CLIENT_SIDE_TOOL_V2_LIST_DIR_V2: 39,
    CLIENT_SIDE_TOOL_V2_READ_FILE_V2: 40,
    CLIENT_SIDE_TOOL_V2_RIPGREP_RAW_SEARCH: 41,
    CLIENT_SIDE_TOOL_V2_GLOB_FILE_SEARCH: 42,
    CLIENT_SIDE_TOOL_V2_CREATE_PLAN: 43,
    CLIENT_SIDE_TOOL_V2_LIST_MCP_RESOURCES: 44,  // MCP resources
    CLIENT_SIDE_TOOL_V2_READ_MCP_RESOURCE: 45,   // MCP resources
    CLIENT_SIDE_TOOL_V2_READ_PROJECT: 46,
    CLIENT_SIDE_TOOL_V2_UPDATE_PROJECT: 47,
    CLIENT_SIDE_TOOL_V2_TASK_V2: 48,
    CLIENT_SIDE_TOOL_V2_CALL_MCP_TOOL: 49,       // MCP direct call
    CLIENT_SIDE_TOOL_V2_APPLY_AGENT_DIFF: 50,
    CLIENT_SIDE_TOOL_V2_ASK_QUESTION: 51,
    CLIENT_SIDE_TOOL_V2_SWITCH_MODE: 52,
    CLIENT_SIDE_TOOL_V2_GENERATE_IMAGE: 53,
    CLIENT_SIDE_TOOL_V2_COMPUTER_USE: 54,
    CLIENT_SIDE_TOOL_V2_WRITE_SHELL_STDIN: 55
}
```

## MCP Tool Schemas (aiserver.v1 namespace)

### MCPParams (Line 112932-112968)

Parameters for legacy MCP tool call with multiple tool selection:

```protobuf
message MCPParams {
    repeated MCPParams.Tool tools = 1;
    optional int64 file_output_threshold_bytes = 2;
}

message MCPParams.Tool {
    string name = 1;            // Full tool name (e.g., "serverId-toolName")
    string description = 2;      // Tool description
    string parameters = 3;       // JSON-stringified input schema
    string server_name = 4;      // MCP server name
}
```

### MCPResult (Line 113014-113048)

Result from legacy MCP tool call:

```protobuf
message MCPResult {
    string selected_tool = 1;    // Name of tool that was selected/executed
    string result = 2;           // Execution result as string
}
```

### CallMcpToolParams (Line 113316-113355)

Parameters for direct MCP tool call:

```protobuf
message CallMcpToolParams {
    string server = 1;           // MCP server identifier
    string tool_name = 2;        // Tool name on the server
    google.protobuf.Struct tool_args = 3;  // Tool arguments as JSON struct
}
```

### CallMcpToolResult (Line 113356-113390)

Result from direct MCP tool call:

```protobuf
message CallMcpToolResult {
    string server = 1;           // MCP server identifier
    string tool_name = 2;        // Tool name
    google.protobuf.Struct result = 3;  // Result as JSON struct
}
```

## MCP Resource Schemas (aiserver.v1 namespace)

### ListMcpResourcesParams (Line 113080-113110)

```protobuf
message ListMcpResourcesParams {
    optional string server = 1;  // Filter by server (optional)
}
```

### ListMcpResourcesResult (Line 113111-113141)

```protobuf
message ListMcpResourcesResult {
    repeated MCPResource resources = 1;
}

message ListMcpResourcesResult.MCPResource {
    string uri = 1;              // Resource URI
    optional string name = 2;     // Display name
    optional string description = 3;
    optional string mime_type = 4;
    string server = 5;           // Server identifier
    map<string, string> annotations = 6;  // Custom annotations
}
```

### ReadMcpResourceParams (Line 113204-113244)

```protobuf
message ReadMcpResourceParams {
    string server = 1;           // Server identifier
    string uri = 2;              // Resource URI to read
    optional string download_path = 3;  // Local path for blob download
}
```

### ReadMcpResourceResult (Line 113245-113295)

```protobuf
message ReadMcpResourceResult {
    string uri = 1;
    optional string name = 2;
    optional string description = 3;
    optional string mime_type = 4;
    oneof content {
        string text = 5;         // Text content
        bytes blob = 6;          // Binary content
    }
    map<string, string> annotations = 7;
}
```

## Agent-side MCP Schemas (agent.v1 namespace)

### McpToolDefinition (Line 119231-119280)

Definition of an MCP tool for agent consumption:

```protobuf
message McpToolDefinition {
    string name = 1;             // Full tool name
    string provider_identifier = 4;  // Server identifier
    string tool_name = 5;        // Tool name on server
    string description = 2;      // Tool description
    google.protobuf.Struct input_schema = 3;  // JSON Schema for inputs
}
```

### McpTools (Line 119281-119311)

Collection of tool definitions:

```protobuf
message McpTools {
    repeated McpToolDefinition mcp_tools = 1;
}
```

### McpInstructions (Line 119312-119346)

Server-specific instructions for the agent:

```protobuf
message McpInstructions {
    string server_name = 1;      // Server display name
    string instructions = 2;     // Usage instructions
}
```

### McpDescriptor (Line 119347-119399)

Full descriptor for an MCP server:

```protobuf
message McpDescriptor {
    string server_name = 1;          // Display name
    string server_identifier = 2;    // Unique identifier
    optional string folder_path = 3; // Project folder if applicable
    optional string server_use_instructions = 4;  // Usage instructions
    repeated McpToolDescriptor tools = 5;  // Available tools
}

message McpToolDescriptor {
    string tool_name = 1;
    optional string definition_path = 2;  // Path to tool definition file
}
```

## MCP Tool Result Types (agent.v1 namespace)

### McpToolResultContentItem (Line 130762-130800)

Content item in tool result (supports text and images):

```protobuf
message McpToolResultContentItem {
    oneof content {
        McpToolResultTextContent text = 1;
        McpToolResultImageContent image = 2;
    }
}
```

### McpSuccess (Line 130801-130836)

Successful tool execution result:

```protobuf
message McpSuccess {
    repeated McpToolResultContentItem content = 1;
    bool is_error = 2;  // True if server returned error content
}
```

### McpError (Line 130837-130866)

Error result from tool execution:

```protobuf
message McpError {
    string error = 1;    // Error message
}
```

### McpRejected (Line 130867-130901)

User rejected tool execution:

```protobuf
message McpRejected {
    string reason = 1;       // Rejection reason
    bool is_readonly = 2;    // If in readonly mode
}
```

### McpPermissionDenied (Line 130902-130936)

Permission denied for tool execution:

```protobuf
message McpPermissionDenied {
    string error = 1;        // Error message
    bool is_readonly = 2;    // If in readonly mode
}
```

## ClientSideToolV2Call and ClientSideToolV2Result

### ClientSideToolV2Call Structure (Lines 104954-105275)

The `ClientSideToolV2Call` message wraps tool invocations with a oneof for params:

```javascript
// Key fields for MCP tools in ClientSideToolV2Call:
{
    tool: ClientSideToolV2,        // Enum value
    tool_call_id: string,          // Unique call ID
    name: string,                  // Tool name
    raw_args: string,              // Raw JSON arguments
    timeout_ms: int64,             // Optional timeout
    is_streaming: bool,            // Streaming mode
    is_last_message: bool,

    // MCP-specific param fields (oneofs):
    mcp_params: MCPParams,                       // field 27
    list_mcp_resources_params: ListMcpResourcesParams,  // field 57
    read_mcp_resource_params: ReadMcpResourceParams,    // field 58
    call_mcp_tool_params: CallMcpToolParams,     // field 62
}
```

### ClientSideToolV2Result Structure (Lines 105292-105450)

```javascript
// Key result fields for MCP tools:
{
    tool: ClientSideToolV2,
    tool_call_id: string,

    // MCP-specific result fields (oneofs):
    mcp_result: MCPResult,                       // field 28
    list_mcp_resources_result: ListMcpResourcesResult,  // field (varies)
    read_mcp_resource_result: ReadMcpResourceResult,    // field (varies)
    call_mcp_tool_result: CallMcpToolResult,     // field (varies)
}
```

## MCP Human Review System

### MCPToolReviewModel (Line 309953-310023)

Model for MCP tool approval UI:

```javascript
class MCPToolReviewModel extends ReviewModel {
    // Review data stored in bubble.additionalData.reviewData
    getDefaultReviewData() {
        return {
            status: "none",
            selectedOption: "rejectAndTellWhatToDoDifferently",
            isShowingInput: false,
            highlightedOption: undefined
        };
    }

    getCurrentlyDisplayedOptions() {
        // Options: run, skip, rejectAndTellWhatToDoDifferently, allowlistTool
        return [RUN, SKIP, REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY, ALLOWLIST_TOOL];
    }

    getHeaderText() {
        // Shows "Run {toolName} on {serverName}?" or "Run MCP tool?"
    }
}
```

### MCPToolHumanReviewOption Enum (Ak)

```javascript
enum MCPToolHumanReviewOption {
    RUN = "run",
    REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY = "rejectAndTellWhatToDoDifferently",
    ALLOWLIST_TOOL = "allowlistTool",
    SKIP = "skip"
}
```

### MCPToolReviewResultType Enum (Mx)

```javascript
enum MCPToolReviewResultType {
    RUN = "run",
    REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY = "rejectAndTellWhatToDoDifferently",
    ALLOWLIST_TOOL = "allowlistTool",
    SKIP = "skip",
    NONE = "none"
}
```

## MCP Service Commands (RU)

Internal command IDs for MCP operations (Line 268984):

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

## MCP Offerings Structure

When listing offerings from an MCP server, the structure returned includes:

```javascript
// From listOfferings() call
{
    tools: [{
        name: string,
        description: string,
        parameters: string,     // JSON-stringified JSON Schema
        outputSchema?: string   // Optional output schema
    }],
    prompts: [{
        name: string,
        description: string,
        parameters: string      // JSON-stringified JSON Schema for arguments
    }],
    resources: [{
        uri: string,
        name: string,
        description: string,
        mimeType: string,
        annotations: object
    }]
}
```

## Tool Cache Structures

The MCPService maintains caches for tools, prompts, and resources:

```javascript
// Tools cache: Map<serverIdentifier, Tool[]>
{
    name: string,
    description: string,
    inputSchema: object,        // Parsed JSON Schema
    outputSchema?: object       // Optional output schema
}

// Prompts cache: Map<serverIdentifier, Prompt[]>
{
    name: string,
    description: string,
    inputSchema: object         // Parsed JSON Schema for arguments
}

// Resources cache: Map<serverIdentifier, Resource[]>
{
    uri: string,
    name: string,
    description: string,
    mimeType: string,
    annotations: object
}
```

## Tool Index File Format

Tools are written to `.cursor/mcps/{serverName}/tools/{toolName}.json`:

```json
{
    "name": "tool_name",
    "description": "Tool description",
    "arguments": { /* JSON Schema */ },
    "outputSchema": { /* Optional JSON Schema */ }
}
```

## Integration Flow Summary

1. **Tool Discovery**: MCPService calls `listOfferings()` on each server
2. **Tool Selection**: AI selects tools from available definitions
3. **Tool Call Dispatch**:
   - `CLIENT_SIDE_TOOL_V2_MCP`: Legacy multi-tool selection with `MCPParams`
   - `CLIENT_SIDE_TOOL_V2_CALL_MCP_TOOL`: Direct single tool call with `CallMcpToolParams`
4. **Human Review**: If not allowlisted, shows MCPToolReviewModel UI
5. **Execution**: `mcpService.callTool()` executes via MCP client
6. **Result Handling**: Returns `MCPResult` or `CallMcpToolResult`

## File Locations Summary

| Path | Purpose |
|------|---------|
| `out-build/proto/aiserver/v1/tools_pb.js` | ClientSideToolV2 enum, MCP params/results |
| `out-build/proto/agent/v1/mcp_pb.js` | Agent-side MCP definitions |
| `out-build/vs/workbench/services/ai/browser/mcpService.js` | MCP service implementation |
| `out-build/vs/workbench/contrib/composer/browser/toolCallHumanReviewService.js` | Human review models |

---

## MCP Server Configuration Schemas (aiserver.v1 namespace)

### AllowedMCPServer (Line 276422-276458)

Configuration for an allowed MCP server:

```protobuf
message AllowedMCPServer {
    optional string command = 1;     // Command for stdio servers
    optional string server_url = 2;  // URL for HTTP servers
}
```

### AllowedMCPConfiguration (Line 276459-276495)

Configuration for allowed MCP servers (enterprise/team level):

```protobuf
message AllowedMCPConfiguration {
    optional bool disable_all = 1;                    // Disable all MCP servers
    repeated AllowedMCPServer allowed_mcp_servers = 2;  // Allowlist of servers
}
```

### MCPControls (Line 276578-276613)

Enterprise/team controls for MCP:

```protobuf
message MCPControls {
    bool enabled = 1;                      // Whether MCP is enabled
    repeated string allowed_tools = 2;     // Allowlist of tool names
}
```

### MCPInstructions (Line 92230-92269)

Instructions provided by MCP servers:

```protobuf
message MCPInstructions {
    string server_name = 1;        // Name of the MCP server
    string server_identifier = 2;  // Unique identifier for the server
    string instructions = 3;       // Instructions text from the server
}
```

---

## MCP Registry Service (aiserver.v1 namespace)

### MCPKnownServerInfo (Line 448953-449002)

Known/discoverable MCP server information:

```protobuf
message MCPKnownServerInfo {
    string name = 1;         // Server display name
    string description = 2;  // Server description
    string icon = 3;         // Icon path/URL
    string endpoint = 4;     // Server endpoint
    bool is_featured = 5;    // Whether this is a featured server
}
```

### MCPServerRegistration (Line 449003-449038)

```protobuf
message MCPServerRegistration {
    repeated string domains = 1;  // Associated domains for discovery
    MCPKnownServerInfo info = 2;  // Server information
}
```

### MCPRegistryService (Line 449098-449111)

gRPC service for discovering known MCP servers:

```protobuf
service MCPRegistryService {
    rpc GetKnownServers(GetKnownServersRequest) returns (GetKnownServersResponse);
}

message GetKnownServersRequest {}

message GetKnownServersResponse {
    repeated MCPServerRegistration servers = 1;
}
```

---

## Elicitation System

MCP supports elicitation (interactive prompts from servers):

### Elicitation Request Commands

```javascript
// Command IDs
"mcp.elicitationRequest"      // Incoming elicitation request from server
"mcp.elicitationResponse"     // Send response back to server
"mcp.leaseElicitationRequest" // For long-running tool operations
```

### Elicitation Request Structure

```javascript
{
    id: string,              // Unique request ID
    message: string,         // Message to display to user
    requestedSchema: object, // JSON Schema for expected response
    serverIdentifier: string,
    toolCallId: string,
    resolve: Function        // Callback to resolve the request
}
```

### Elicitation Response Actions

- `decline` - Reject the elicitation request
- Other actions based on the requested schema

### Lease Elicitation

A variant for long-running tool operations that may need user interaction during execution. The MCPService maintains handlers for lease elicitation per toolCallId.

```javascript
// Register handler
registerLeaseElicitationHandler(toolCallId: string, handler: Function)

// Unregister handler
unregisterLeaseElicitationHandler(toolCallId: string)
```

---

## MCP Tool Execution Flow

### Agent-side McpArgs (Line 130586-130639)

Arguments passed to local MCP execution:

```protobuf
message McpArgs {
    string name = 1;                      // Tool name
    map<string, Value> args = 2;          // Arguments as key-value pairs
    string tool_call_id = 3;              // Unique ID for this call
    string provider_identifier = 4;       // Server/provider identifier
    string tool_name = 5;                 // Full tool name
}
```

### McpResult (agent.v1) (Line 130640-130690)

Result from local MCP tool execution:

```protobuf
message McpResult {
    oneof result {
        McpSuccess success = 1;
        McpError error = 2;
        McpRejected rejected = 3;
        McpPermissionDenied permission_denied = 4;
    }
}
```

### McpTextContent (Line 130691-130726)

```protobuf
message McpTextContent {
    string text = 1;
    optional FileLocation output_location = 2;  // Location if written to file
}
```

### McpImageContent (Line 130727-130761)

```protobuf
message McpImageContent {
    bytes data = 1;       // Raw image data
    string mime_type = 2; // Image MIME type
}
```

---

## MCP Resource Execution Schemas (agent.v1 namespace)

### ListMcpResourcesExecArgs (Line 130937-130967)

```protobuf
message ListMcpResourcesExecArgs {
    optional string server = 1;
}
```

### ListMcpResourcesExecResult (Line 130968-131012)

```protobuf
message ListMcpResourcesExecResult {
    oneof result {
        ListMcpResourcesSuccess success = 1;
        ListMcpResourcesError error = 2;
        ListMcpResourcesRejected rejected = 3;
    }
}
```

### ListMcpResourcesExecResult.McpResource (Line 131013-131074)

```protobuf
message McpResource {
    string uri = 1;
    optional string name = 2;
    optional string description = 3;
    optional string mime_type = 4;
    string server = 5;
    map<string, string> annotations = 6;
}
```

### ReadMcpResourceExecArgs (Line 131166-131180)

```protobuf
message ReadMcpResourceExecArgs {
    string server = 1;
    string uri = 2;
}
```

---

## Hooks System Integration

MCP execution integrates with Cursor's hooks system:

- `beforeMCPExecution` - Called before MCP tool execution
- `afterMCPExecution` - Called after MCP tool execution

These hooks can be configured at enterprise, team, project, or user level.

```javascript
// Hook execution in MCP handler
const result = await this.cursorHooksService.executeHookForStep(
    Eb.beforeMCPExecution,
    executionContext
);

// After execution
await this.cursorHooksService.executeHookForStep(Eb.afterMCPExecution, {
    toolName: toolName,
    result: result,
    // ... other context
});
```

---

## Server Types

MCP servers can be of two types:

1. **stdio** - Command-line servers with stdio transport
   - Configured with `command` and optional `args`
   - Uses `envFile` for environment variables
   - Recovery mechanism with consecutive failure tracking

2. **streamableHttp** - HTTP/SSE servers
   - Configured with `server_url`
   - Supports OAuth authentication
   - Logout clears OAuth state

---

## Key Implementation Classes

### MCPService (bTs - Line 447208+)

Main service managing MCP servers and tool execution:

```javascript
class MCPService {
    // Server management
    getServers(): Server[]
    createClient(server: ServerConfig): Promise<boolean>
    deleteClient(server: Server): Promise<void>
    reloadClient(serverId: string): Promise<void>

    // Tool execution
    callTool(toolName, args, useLeaseElicitation, toolCallId, abortSignal): Promise<Result>
    callToolForLease(serverId, toolName, args, useLease, toolCallId, abortSignal): Promise<Result>

    // Resources & prompts
    getPrompt(promptName, args): Promise<Prompt>
    readResource(uri, serverId): Promise<Resource>

    // Caching
    getAvailableTools(): Map<string, Tool[]>
    getToolsForComposer(mcpDescriptors): Tool[]
    getInstructionsForComposer(): Instruction[]

    // Elicitation
    handleElicitationRequest(serverId, toolName, toolCallId, request): Promise<Response>
    registerLeaseElicitationHandler(toolCallId, handler): void
}
```

### MCP Client Provider Wrapper (WAc - Line 447150+)

Wrapper with recovery mechanism for MCP client operations:

```javascript
class MCPClientProviderWrapper {
    constructor({ client, serverId, shouldAttemptRecovery, recreateClient, onRecoverySuccess, onRecoveryFailure })

    // Wraps all operations with recovery logic
    async withRecovery(operation): Promise<Result>

    // Detects "server missing" errors
    isServerMissingError(error): boolean

    // Recovery: max 3 consecutive failures before backing off
    consecutiveFailures: number
}
```

---

## Potential Investigation Avenues

1. **MCP OAuth Flow**: The streamableHttp server type mentions OAuth - investigate the OAuth state management and token handling.

2. **Playwright Integration**: Special handling exists for Playwright MCP with log configs - investigate `playwright_log_configs` experiment.

3. **Browser Features**: MCP has integration with browser features settings that affect cache refresh.

4. **Index Files Format**: MCP writes index files for tools, resources, and prompts - detailed format documented in Tool Index File section.

5. **Extension MCP Registration**: Investigate `registerMCPServer` and `unregisterMCPServer` for extension API.

---

*Analysis based on Cursor IDE version 2.3.41 decompiled source*
*Updated with elicitation system, registry service, and configuration schemas*
