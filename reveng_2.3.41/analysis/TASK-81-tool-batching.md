# TASK-81: Server-Side Tool Batching Decisions

## Overview

This analysis investigates how the Cursor server decides when to emit tool calls in parallel vs sequential. While TASK-51 covers client-side batching execution, this task focuses on the server-side protocol and signaling mechanisms.

## Key Finding: Server Sends Sequential, Client Decides Parallel

After analyzing the codebase, the key insight is:

**The server sends tool calls sequentially through the stream, but the CLIENT decides whether to run them in parallel based on tool type classification.**

The server does not make batching decisions - it simply emits tool calls as the model generates them. The client-side `ToolV2Service` is responsible for:
1. Classifying incoming tools as parallel-eligible or sequential
2. Queuing parallel tools for batch execution
3. Maintaining slot-based concurrency limits
4. Tracking batch timing and telemetry

## Protocol Analysis

### StreamUnifiedChatResponseWithTools Schema

**Location**: Lines 122102-122170

```protobuf
message StreamUnifiedChatResponseWithTools {
  oneof response {
    ClientSideToolV2Call client_side_tool_v2_call = 1;
    StreamUnifiedChatResponse stream_unified_chat_response = 2;
    ConversationSummary conversation_summary = 3;
    UserRules user_rules = 4;
    StreamStart stream_start = 5;
  }
  optional TracingContext tracing_context = 6;
  string event_id = 7;
}
```

The server sends tool calls one at a time via `client_side_tool_v2_call`. There is no batch envelope or grouping mechanism at the protocol level.

### ClientSideToolV2Call Structure

**Location**: Lines 104949-105020

```javascript
class ClientSideToolV2Call {
    tool: ClientSideToolV2;           // Tool type enum
    params: { case: string, value: any };  // Tool parameters (oneof)
    toolCallId: string;               // Unique ID for this call
    name: string;                     // Tool name
    isStreaming: boolean;             // Whether tool streams results
    isLastMessage: boolean;           // Final chunk for streaming tools
    internal: boolean;                // Internal tool (no UI bubble)
    rawArgs: string;                  // Raw JSON arguments
    toolIndex: number;                // Position in model's output (0, 1, 2...)
    modelCallId: string;              // Groups tools from same model call
    timeoutMs: number;                // Optional timeout
}
```

Key observations:
- `toolIndex` indicates position in the model's output, suggesting the model can emit multiple tools
- `modelCallId` groups tools that came from the same model inference call
- No explicit "batch" or "parallel" flag from server

### Server-Side Batch Signal: `parallel_tool_calls_complete`

**Location**: Lines 124172-124176

```protobuf
message StreamUnifiedChatResponse {
    // ... other fields ...
    optional bool parallel_tool_calls_complete = 32;  // field number 32
}
```

The server CAN signal that a parallel batch is complete via this boolean field. However:
- It's optional (many responses won't include it)
- The client doesn't appear to rely on it for execution decisions
- It seems to be more for telemetry/tracking than control flow

### Chat Request Event Types

**Location**: Lines 828200-828238

```javascript
ChatRequestEventType = {
    UNSPECIFIED: 0,
    REQUEST_START: 1,
    MODEL_PROVIDER_REQUEST_START: 2,
    START_STREAMING: 3,
    END_STREAMING: 4,
    TOOL_CALL_START: 5,
    TOOL_CALL_END: 6,
    TOOL_CALL_STREAM_FINISHED: 8,
    REQUEST_END: 7,
    PARALLEL_TOOL_CALL_START: 9,    // Parallel tracking
    PARALLEL_TOOL_CALL_END: 10,      // Parallel tracking
    STREAM_STATE_CHANGE: 11
}
```

The `PARALLEL_TOOL_CALL_START` and `PARALLEL_TOOL_CALL_END` events are for telemetry reporting, not control flow.

### `parallel_tool_call_id` Field

**Location**: Lines 828468-828472

```protobuf
optional string parallel_tool_call_id = 20;
```

In the `ChatRequestEventV2` message, there's a `parallel_tool_call_id` field used to group related parallel tool calls in telemetry data.

## Client-Side Batching Decision Logic

### Step 1: Classify Tool as Parallel-Eligible

**Location**: Line 484552

```javascript
const ie = new Set([
    vt.READ_FILE_V2,
    vt.LIST_DIR_V2,
    vt.FILE_SEARCH,
    vt.SEMANTIC_SEARCH_FULL,
    vt.READ_SEMSEARCH_FILES,
    vt.RIPGREP_SEARCH,
    vt.RIPGREP_RAW_SEARCH,
    vt.SEARCH_SYMBOLS,
    vt.READ_LINTS,
    vt.DEEP_SEARCH,
    vt.TASK,
    vt.GLOB_FILE_SEARCH
]);
```

The client has a hardcoded set of tools that CAN run in parallel. This is determined by tool characteristics (read-only, no side effects).

### Step 2: Processing Incoming Tool Calls

**Location**: Lines 484595-484904

```javascript
if (Pe.response.case === "clientSideToolV2Call") {
    const Oe = Pe.response.value;

    if (Oe.isStreaming) {
        // Streaming tools run sequentially
        ee();  // Flush any pending parallel batch
        // Execute tool...
    } else if (ie.has(Oe.tool)) {
        // Parallel-eligible: add to batch
        _ === void 0 && (_ = Date.now());  // Start batch timer
        w.push(Oe.toolCallId);              // Track in batch
        g.push(asyncToolExecution());        // Queue for parallel execution
    } else {
        // Sequential tool
        ee();  // Flush any pending parallel batch
        // Execute tool synchronously, blocking stream processing
    }
}
```

### Step 3: Batch Completion Detection

The batch completes when:
1. A non-parallel tool arrives (streaming or sequential) - triggers `ee()` flush
2. All parallel tools in the current batch finish - checked by `te()`
3. The stream ends - final `ee()` call

```javascript
// te() - Check if batch is ready to finalize
const te = () => {
    w.length > 0 && _ !== void 0 && w.every(ke => p.has(ke)) && ee()
};

// ee() - Finalize and report batch
const ee = () => {
    if (w.length > 0 && _ !== void 0) {
        const Pe = Date.now();
        const ke = Pe - _;
        console.log(`[ToolV2Service] Parallel batch completed: ${w.length} tools in ${ke}ms`);
        // Update telemetry, reset batch state...
    }
};
```

## Concurrency Control (Per-Tool-Type)

**Location**: Lines 295350-295365, 484274-484346

The client applies per-tool-type concurrency limits via a dynamic config:

```javascript
tools_concurrency_config: {
    tools: {
        RIPGREP_RAW_SEARCH: { ttl: 10000, maxConcurrent: 5 },
        RIPGREP_SEARCH: { ttl: 10000, maxConcurrent: 5 }
    },
    defaultTtl: 10000,
    defaultMaxConcurrent: 999999  // Effectively unlimited
}
```

The `waitForToolSlot()` function implements slot-based queuing:

```javascript
async waitForToolSlot(toolType, signal) {
    const maxConcurrent = this.getMaxConcurrent(toolType);
    if (maxConcurrent === Infinity) return;  // No limit

    this.cleanupStaleTools(toolType);  // TTL-based cleanup

    const activeCount = this.activeToolCallsByType.get(toolType) ?? 0;
    if (activeCount < maxConcurrent) return;  // Slot available

    // No slot: create Promise that resolves when slot frees up
    return new Promise((resolve, reject) => {
        const queue = this.toolWaitQueues.get(toolType) ?? [];
        queue.push({ resolve, reject, cancelled: false });
        this.toolWaitQueues.set(toolType, queue);
        // Handle abort signal...
    });
}
```

## How the Model Affects Batching

The model's output directly affects what tools arrive in the stream:

### 1. Model Emits Multiple Tools in One Response

When the model generates multiple tool calls in a single turn:
- Each tool gets a unique `toolCallId`
- All share the same `modelCallId`
- `toolIndex` indicates order (0, 1, 2, ...)

The server sends these sequentially through the stream, but they arrive in quick succession. If they're all parallel-eligible, the client batches them.

### 2. Streaming Tools Force Sequential Execution

Streaming tools (`isStreaming: true`) like `EDIT_FILE_V2`:
- Flush any pending parallel batch
- Execute one at a time
- Send multiple chunks (`isLastMessage: false` until final chunk)

### 3. Tool Dependencies are Implicit

There's no explicit dependency mechanism. Dependencies are handled by:
- **Tool type classification**: Write tools are sequential, so they naturally wait for reads
- **Stream ordering**: Server sends tools in order model generated them
- **User approval**: Some tools require approval, which blocks execution

## Telemetry and Tracking

### ToolCallEventService

**Location**: Lines 478925-478999

Tracks parallel execution for analytics:

```javascript
trackParallelToolCallBatch(toolCallIds, toolType, requestUuid, modelName) {
    const batchSize = toolCallIds.length;
    for (const id of toolCallIds) {
        this.trackToolCallStart(id, toolType, requestUuid, modelName, true, batchSize);
    }
}

updateToolCallAsParallel(toolCallId, batchSize) {
    const event = this._eventBuffer.get(toolCallId);
    if (event) {
        event.isParallel = true;
        event.parallelBatchSize = batchSize;
    }
}
```

### Reported Metrics

Each tool call event includes:
- `isParallel: boolean` - Was it part of a parallel batch?
- `parallelBatchSize: number` - How many tools in the batch?
- `duration` - Execution time
- `approvalWaitDuration` - Time waiting for user approval
- `isStream` - Was it a streaming tool?

## Key Observations

1. **Server is Passive**: The server simply streams tool calls as the model generates them. It doesn't make batching decisions.

2. **Client is Active**: The `ToolV2Service` on the client side classifies tools and decides parallel vs sequential execution.

3. **No Batch Boundaries in Protocol**: The `parallel_tool_calls_complete` field exists but isn't used for control flow. Batches are determined by tool classification, not server signals.

4. **modelCallId Groups Tools**: Tools from the same model inference share a `modelCallId`, but this doesn't affect batching - only tool type does.

5. **Concurrency is Per-Type**: Each tool type can have its own concurrency limit (ripgrep = 5, others = unlimited by default).

6. **Streaming Breaks Batches**: Any streaming tool (EDIT_FILE, etc.) forces a batch flush and sequential execution.

## Questions for Further Investigation

1. **Why doesn't the server batch?** Performance or simplicity? Could batching at the server level improve efficiency?

2. **How does the LLM decide tool order?** Does Cursor influence the model to emit read tools first?

3. **What happens with MCP tools?** They explicitly don't support streaming - are they ever batched?

4. **How does `persist_idempotent_stream_state` affect batching?** This experiment flag is checked but not deeply analyzed.

## Related Tasks

- TASK-51: Client-side tool batching implementation details (completed)
- TASK-52: Tool call schema analysis
- TASK-112: Tool approval flow
