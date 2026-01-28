# TASK-60: MCP Tool Streaming and Progress Reporting Mechanism

## Executive Summary

Analysis of Cursor IDE 2.3.41 reveals that **MCP tools do NOT support true streaming** - they use a request-response model with progress notifications as a workaround. The system provides progress reporting through a dedicated notification mechanism and tracks tool execution state through a "bubble data" UI abstraction.

## Key Finding: No Streaming Support

The code explicitly throws errors when streaming methods are called on MCP tools:

```javascript
// From out-build/vs/workbench/services/ai/browser/toolsV2/mcpHandler.js (line 477381-477386)
async streamedCall(e, t, n, s, r) {
    throw new Error("MCP tools do not support streaming")
}
async finishStream(e, t, n, s) {
    throw new Error("MCP tools do not support streaming")
}

// From out-build/vs/workbench/services/ai/browser/toolsV2/callMcpToolHandler.js (line 482670-482675)
async streamedCall(e, t, n, s, r) {
    throw new Error("call_mcp_tool does not support streaming")
}
async finishStream(e, t, n, s) {
    throw new Error("call_mcp_tool does not support streaming")
}
```

This is significant - while the protobuf schema defines stream message types, the actual tool execution is synchronous.

## Protobuf Stream Types (Defined But Minimal)

The following stream types are defined in the protobuf schema:

### Stream Message Types
| Type Name | Field Number | Description |
|-----------|-------------|-------------|
| `MCPStream` | 29 | `aiserver.v1.MCPStream` - Contains tools array |
| `CallMcpToolStream` | 63 | `aiserver.v1.CallMcpToolStream` - Empty fields |
| `ListMcpResourcesStream` | 58 | `aiserver.v1.ListMcpResourcesStream` - Empty fields |
| `ReadMcpResourceStream` | 59 | `aiserver.v1.ReadMcpResourceStream` - Empty fields |

### MCPStream Schema
```javascript
// aiserver.v1.MCPStream (line 113052-113078)
static {
    this.typeName = "aiserver.v1.MCPStream"
}
static {
    this.fields = v.util.newFieldList(() => [{
        no: 1,
        name: "tools",
        kind: "message",
        T: I1e,  // MCPParams_Tool
        repeated: !0
    }])
}
```

Note: `CallMcpToolStream`, `ListMcpResourcesStream`, and `ReadMcpResourceStream` all have **empty field definitions** - they are placeholders.

## Progress Reporting Mechanism

### Progress Notification Command
Progress is reported through a VS Code command system:

```javascript
// From MCPService constructor (line 447258-447263)
Os.registerCommand({
    id: "mcp.progressNotification",
    handler: async (ee, te) => {
        Lu(`[MCPService] Received progress notification for: ${te.progressToken}`, te.notification),
        this.setProgressCache(ie => ({
            ...ie,
            [te.progressToken]: te.notification
        }))
    }
})
```

### Progress Cache Structure
The progress cache is keyed by `progressToken` (which corresponds to `toolCallId`) and stores progress notifications with the structure:

```javascript
// From progress consumer code (line 927415-927426)
const d = e.mcpService.progressCache()[a];  // a = toolCallId
if (d && "progress" in d) {
    let h = "total" in d ? d.total : void 0,
        f = "message" in d ? d.message : void 0;
    return {
        progress: d.progress,
        total: h,
        message: f
    }
}
```

### Progress Cleanup
Progress is cleared when tool execution completes:

```javascript
// From MCPService.callTool (line 448078)
if (B) return this.clearProgressForTool(n), ...

// clearProgressForTool implementation (line 448167-448173)
clearProgressForTool(e) {
    e && this.setProgressCache(t => {
        const {
            [e]: n, ...s
        } = t;
        return s
    })
}
```

## Elicitation System (User Interaction During Tool Execution)

MCP tools support a unique "elicitation" mechanism for requesting user input during long-running operations:

### Elicitation Commands
```javascript
// Standard elicitation request (line 447266-447281)
Os.registerCommand({
    id: "mcp.elicitationRequest",
    handler: async (ee, te) => {
        Lu(`[MCPService] Received elicitation request: ${te.request.message}`);
        // Creates a resolve callback for async user response
        this.setElicitationRequestsCache(ne => ({
            ...ne,
            [te.request.id]: {
                ...te.request,
                resolve: ie
            }
        }))
    }
})

// Lease elicitation for extension-owned tools (line 447284-447302)
Os.registerCommand({
    id: "mcp.leaseElicitationRequest",
    handler: async (ee, te) => {
        const ie = this.leaseElicitationHandlers.get(te.toolCallId);
        // Routes to registered handler
    }
})
```

### Elicitation Request Structure
```javascript
{
    id: "unique-request-id",
    message: string,
    requestedSchema: object,  // JSON Schema for expected response
    serverIdentifier: string,
    toolCallId: string,
    resolve: (response) => void
}
```

## Tool Execution Flow

### Standard MCP Tool Call (vt.MCP)
```javascript
// From mcpHandler.js (line 477248-477372)
async setup(e, t, n, s, r) {
    // 1. Extract tool parameters
    const o = e.tools?.[0];
    const a = JSON.parse(o.parameters ?? "{}");

    // 2. Handle user approval if needed
    if (!capability.shouldAutoRun_runEverythingMode()) {
        await new Promise((resolve, reject) => {
            capability.addPendingDecision(bubbleId, vt.MCP, toolCallId, decision => {
                decision ? resolve() : reject(new t$("User rejected the tool call"))
            }, true)
        })
    }

    // 3. Execute tool (synchronous await)
    const g = performance.now();
    const p = await this.mcpService.callTool(o.name, a, n, t.signal, s);
    const w = k4c(performance.now() - g);  // Duration in seconds

    // 4. Execute post-hook
    await this.cursorHooksService.executeHookForStep(Eb.afterMCPExecution, {...});

    // 5. Return result
    return new rue({
        selectedTool: o.name,
        result: JSON.stringify(T)
    });
}
```

### New call_mcp_tool (vt.CALL_MCP_TOOL)
A newer, more structured tool call API:

```javascript
// From callMcpToolHandler.js (line 482409-482676)
// Accepts explicit server identifier and tool name
// Uses CallMcpToolParams with server, toolName, toolArgs fields
// Returns CallMcpToolResult with result as google.protobuf.Struct
```

## Tool Result Types

### MCPResult Schema
```javascript
// aiserver.v1.MCPResult (line 113017-113027)
static {
    this.typeName = "aiserver.v1.MCPResult"
}
static {
    this.fields = v.util.newFieldList(() => [{
        no: 1,
        name: "selected_tool",
        kind: "scalar",
        T: 9  // string
    }, {
        no: 2,
        name: "result",
        kind: "scalar",
        T: 9  // string (JSON)
    }])
}
```

### CallMcpToolResult Schema
```javascript
// aiserver.v1.CallMcpToolResult (line 113359-113369)
static {
    this.typeName = "aiserver.v1.CallMcpToolResult"
}
static {
    this.fields = v.util.newFieldList(() => [{
        no: 1,
        name: "server",
        kind: "scalar",
        T: 9  // string
    }, {
        no: 2,
        name: "result",
        kind: "message",
        T: ZD  // google.protobuf.Struct
    }])
}
```

### FinalToolResult (Streaming Response Marker)
```javascript
// aiserver.v1.StreamUnifiedChatResponse.FinalToolResult (line 124292-124305)
static {
    this.typeName = "aiserver.v1.StreamUnifiedChatResponse.FinalToolResult"
}
static {
    this.fields = v.util.newFieldList(() => [{
        no: 1,
        name: "tool_call_id",
        kind: "scalar",
        T: 9
    }, {
        no: 2,
        name: "result",
        kind: "message",
        T: _y  // ClientSideToolV2Result
    }])
}
```

## UI Integration: Bubble Data System

Tool execution state is displayed through a "bubble" system in the composer UI:

### Bubble Data Structure for MCP Tools
```javascript
// Tool state tracking via bubbleData
{
    tool: vt.MCP | vt.CALL_MCP_TOOL,
    toolCallId: string,
    params: {
        tools: [{name, serverName, parameters}],  // for vt.MCP
        toolName: string,  // for CALL_MCP_TOOL
        server: string     // for CALL_MCP_TOOL
    },
    additionalData: {
        status: "running" | "success" | "error",
        reviewData: {
            status: "None" | "Requested" | "Done",
            selectedOption: Ak.*
        }
    }
}
```

### MCPToolReviewModel (Human Approval)
```javascript
// From toolCallHumanReviewService.js (line 309953-310023)
Jht = class extends qht {
    constructor(i, e) {
        super(), this.toolFormer = i, this.bubbleId = e
    }

    getHumanReviewData() {
        const i = this.toolFormer.getBubbleData(this.bubbleId);
        if (!(!i || i.tool !== vt.MCP && i.tool !== vt.CALL_MCP_TOOL))
            return i.additionalData?.reviewData
    }

    getCurrentlyDisplayedOptions() {
        // Returns [RUN, SKIP, REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY, ALLOWLIST_TOOL]
    }

    getHeaderText() {
        // Returns "Run {toolName} on {serverName}?"
    }
}
```

### MCP Approval Types
```javascript
// MCPToolHumanReviewOption enum (Ak)
Ak = {
    RUN: "run",
    SKIP: "skip",
    REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY: "rejectAndTellWhatToDoDifferently",
    ALLOWLIST_TOOL: "allowlistTool"
}

// MCPToolReviewResultType enum (Mx)
Mx = {
    RUN: "run",
    REJECT_AND_TELL_WHAT_TO_DO_DIFFERENTLY: "rejectAndTellWhatToDoDifferently",
    ALLOWLIST_TOOL: "allowlistTool",
    SKIP: "skip",
    NONE: "none"
}

// MCPApprovalType enum (NJe)
NJe = {
    USER: "user",
    ALLOWLIST: "allowlist",
    FULL_AUTO: "full_auto",
    NONE: "none"
}
```

## Client Implementation: Tool Call Execution

### MCPClient Interface Methods
```javascript
// From various MCP client implementations
callTool(toolName, args, useLeaseElicitation, toolCallId, signal)
getPrompt(name, args)
readResource(uri)
listOfferings()
listToolsRaw()
createClient(config)
deleteClient()
reloadClient(config)
clearAllTokens()
```

### MCPService.callTool Implementation
```javascript
// From MCPService (line 448045-448086)
async callTool(e, t, n, s, r, o) {
    s?.throwIfAborted();

    // Find server with the requested tool
    const a = this.getServers();
    const l = await this.getAvailableTools();

    for (const g in l) {
        if (o && g !== o) continue;  // Optional server filter
        const p = a.find(A => A.identifier === g);

        if (l[g].find(A => A.name === e)) {
            // Add Playwright log configs if applicable
            if (p.name === opt || p.identifier === pB) {
                M = { ...t, __playwrightLogConfigs: H };
            }

            const A = await this.getMcpClient(p.identifier);
            const B = await A.callTool(e, M, false, n, s);

            if (B) {
                this.clearProgressForTool(n);
                this.clearElicitationRequestsForToolCall(n);
                return B;
            }
        }
    }

    throw new Error(`No server found with tool: ${e}`);
}
```

## Recovery Mechanism

The MCP client wrapper includes automatic recovery for failed servers:

```javascript
// RecoveringMcpClient (line 447148-447179)
async withRecovery(operation) {
    try {
        return await operation();
    } catch (e) {
        if (this.isServerMissingError(e) && this.shouldAttemptRecovery()) {
            if (this.consecutiveFailures >= eJt) {  // MAX_RECOVERY_ATTEMPTS
                this.onRecoveryFailure();
                throw e;
            }

            const t = await this.recreateClient();
            if (t) {
                this.consecutiveFailures = 0;
                this.onRecoverySuccess();
                return await operation();
            }
        }
        throw e;
    }
}
```

## StreamableHTTP vs stdio

MCP servers can be connected via two transport types:

```javascript
// Server type determination (line 447577-447586)
const T = {
    identifier: w,
    name: g,
    type: "streamableHttp",  // or "stdio"
    url: E,
    headers: ...,
    auth: ...
};

// Type-specific config (line 448249-448259)
const r = t.type === "stdio" ? {
    type: "stdio",
    command: t.command ?? "",
    args: t.args,
    env: t.env ?? {},
    projectPath: t.projectPath
} : {
    type: "streamableHttp",
    serverUrl: s,
    headers: t.headers,
    auth: t.auth
};
```

## Key Observations

1. **No True Streaming**: MCP tools execute synchronously despite stream message type definitions
2. **Progress via Notifications**: Progress is reported through command-based notifications keyed by toolCallId
3. **Elicitation for Interaction**: Long-running tools can request user input through an elicitation system
4. **Two Tool APIs**: Legacy `vt.MCP` and newer `vt.CALL_MCP_TOOL` with explicit server targeting
5. **Human Review Integration**: Built-in approval workflow with allowlist support
6. **Recovery Mechanism**: Automatic retry with client recreation for transient failures
7. **Bubble-Based UI**: Tool state tracked through bubble data abstraction

## Related Files

- `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js` (primary source)
  - Lines 447010-448560: MCPService implementation
  - Lines 477230-477390: MCP tool handler
  - Lines 482408-482676: call_mcp_tool handler
  - Lines 309530-310023: Human review service for MCP tools

## Potential Follow-Up Investigations

1. Investigate how progress notifications are generated by MCP servers (likely server-side implementation)
2. Document the elicitation schema and expected response formats
3. Analyze how allowlisting persists across sessions
4. Examine how concurrent tool calls are handled (serialization vs parallelism)
