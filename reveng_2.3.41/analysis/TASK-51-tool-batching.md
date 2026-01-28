# TASK-51: Tool Batching and Parallel Execution in Cursor Agent

## Overview

Cursor's agent implements a sophisticated tool batching system that allows certain tools to execute in parallel while ensuring others run sequentially. This document analyzes the implementation found in `workbench.desktop.main.js`.

## Key Components

### 1. ToolV2Service - Main Orchestrator

Location: Lines ~484200-485100 in beautified source

The `ToolV2Service` manages tool execution through its `toolWrappedStream` method, which processes incoming tool calls from the server and decides whether to execute them in parallel or sequentially.

### 2. Parallel-Eligible Tools Set

**Location**: Line 484552

```javascript
ie = new Set([
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
])
```

These 12 tools are allowed to execute in parallel batches.

### 3. Streaming Tools (Sequential Only)

**Location**: Line 215345

```javascript
U5r = [
    vt.WEB_SEARCH,
    vt.EDIT_FILE,
    vt.EDIT_FILE_V2,
    vt.BACKGROUND_COMPOSER_FOLLOWUP,
    vt.SWITCH_MODE
]
```

Streaming tools MUST run sequentially because they require incremental data transfer.

### 4. Tools That Do NOT Support Streaming

Several tools explicitly throw errors if streaming is attempted:

- **MCP tools** (Line 477382): `"MCP tools do not support streaming"`
- **CALL_MCP_TOOL** (Line 482671): `"call_mcp_tool does not support streaming"`
- **KNOWLEDGE_BASE** (Line 480613): `"Knowledge Base tool does not support streaming"`

## Batching Algorithm

### Phase 1: Tool Classification

When a tool call arrives (`clientSideToolV2Call`), the service checks:

1. **Is it a streaming tool?** (`Oe.isStreaming`)
   - If yes: Execute sequentially, flush any pending parallel batch

2. **Is it in the parallel-eligible set?** (`ie.has(Oe.tool)`)
   - If yes: Add to parallel batch
   - If no: Execute sequentially, flush any pending parallel batch

### Phase 2: Parallel Batch Execution

**Algorithm** (Lines 484823-484903):

```javascript
// When parallel-eligible tool arrives:
if (ie.has(Oe.tool)) {
    // Track batch start time
    _ === void 0 && (_ = Date.now());

    // Add to current batch
    w.push(Oe.toolCallId);

    // Create async task with slot-based concurrency
    g.push((async () => {
        try {
            // Wait for available slot
            await this.waitForToolSlot(Oe.tool, n.signal);

            // Increment active count
            this.incrementToolCount(Oe.tool);

            // Execute tool
            await executeToolFn();
        } finally {
            // Release slot
            this.decrementToolCount(Oe.tool);

            // Mark as completed
            p.add(Oe.toolCallId);

            // Check if batch is complete
            te();  // Calls ee() if all tools in batch completed
        }
    })());
}
```

### Phase 3: Batch Completion

**Function `ee()`** (Lines 484539-484547):

```javascript
const ee = () => {
    if (w.length > 0 && _ !== void 0) {
        const Pe = Date.now();
        const ke = Pe - _;
        console.log(`[ToolV2Service] Parallel batch completed: ${w.length} tools in ${ke}ms`);

        // Update telemetry for all tools in batch
        for (const Ne of w) {
            this.toolCallEventService.updateToolCallAsParallel(Ne, w.length);
        }

        // Submit batch telemetry
        this.toolCallEventService.submitParallelToolCallEvents(w, _, Pe, E);

        // Reset batch state
        w = [];
        _ = void 0;
        E = new Map;
    }
};
```

### Phase 4: Final Batch Wait

**Lines 484996-485001**:

```javascript
// After processing all tool calls from stream
await Promise.allSettled(g);  // Wait for all parallel tasks
ee();  // Finalize any remaining batch
```

## Concurrency Control

### Per-Tool-Type Limits

**Location**: Lines 295350-295365

```javascript
tools_concurrency_config: {
    tools: {
        RIPGREP_RAW_SEARCH: {
            ttl: 10000,
            maxConcurrent: 5
        },
        RIPGREP_SEARCH: {
            ttl: 10000,
            maxConcurrent: 5
        }
    },
    defaultTtl: 10000,
    defaultMaxConcurrent: Infinity  // Most tools have no limit
}
```

### Slot Management

**waitForToolSlot** (Lines 484309-484328):
- Returns immediately if `maxConcurrent === Infinity`
- Cleans up stale tools (TTL-based)
- Creates a Promise that resolves when a slot becomes available
- Uses `toolWaitQueues` to manage waiting tasks

**incrementToolCount** / **decrementToolCount** (Lines 484330-484344):
- Tracks active tool calls per type
- Maintains start timestamps for TTL cleanup
- Resolves waiting tasks when slots free up

## Tool Categories Summary

### Parallel Tools (Can batch)

| Tool | Description | Concurrency Limit |
|------|-------------|-------------------|
| READ_FILE_V2 | Read file contents | Unlimited |
| LIST_DIR_V2 | List directory | Unlimited |
| FILE_SEARCH | Search files by name | Unlimited |
| GLOB_FILE_SEARCH | Glob pattern search | Unlimited |
| SEMANTIC_SEARCH_FULL | Codebase semantic search | Unlimited |
| READ_SEMSEARCH_FILES | Read semantic search results | Unlimited |
| RIPGREP_SEARCH | Code/text search | 5 |
| RIPGREP_RAW_SEARCH | Raw ripgrep | 5 |
| SEARCH_SYMBOLS | Symbol search | Unlimited |
| READ_LINTS | Read lint errors | Unlimited |
| DEEP_SEARCH | Deep codebase search | Unlimited |
| TASK | Background task | Unlimited |

### Sequential Tools (Never batch)

| Tool | Reason |
|------|--------|
| EDIT_FILE / EDIT_FILE_V2 | File modification requires ordering |
| RUN_TERMINAL_COMMAND_V2 | Side effects, user approval |
| DELETE_FILE | Destructive, requires ordering |
| WEB_SEARCH | Streaming response |
| MCP / CALL_MCP_TOOL | External service, no streaming |
| KNOWLEDGE_BASE | No streaming support |
| REAPPLY | Edit operation |
| CREATE_DIAGRAM | Streaming |
| SWITCH_MODE | State change |
| All other tools | Default sequential |

## UI Grouping vs Execution Batching

Note: There are TWO separate batching concepts:

### 1. Execution Batching (This document)
- Handled by `ToolV2Service`
- Affects when tools actually run
- Uses `Promise.allSettled` for parallel execution

### 2. UI Grouping (Display only)
**Location**: Line 720732

```javascript
// UI groups these for display purposes:
groupReads && (a === vt.READ_FILE || a === vt.READ_FILE_V2)

[vt.WEB_SEARCH, vt.LIST_DIR, vt.LIST_DIR_V2, vt.RIPGREP_SEARCH,
 vt.RIPGREP_RAW_SEARCH, vt.SEMANTIC_SEARCH_FULL, vt.FILE_SEARCH,
 vt.GLOB_FILE_SEARCH, vt.READ_SEMSEARCH_FILES, vt.SEARCH_SYMBOLS,
 vt.GO_TO_DEFINITION]
```

This is separate from execution - it just controls how tool calls appear in the UI.

## Telemetry

The `ToolCallEventService` tracks:
- `isParallel: boolean` - Whether tool ran in a batch
- `parallelBatchSize: number` - Size of the batch
- Individual tool duration
- Batch start/end times
- Per-tool success/failure status

## Key Observations

1. **Read-only tools batch**: All parallel-eligible tools are read-only or side-effect-free
2. **Write tools are sequential**: File edits, terminal commands, deletions run one at a time
3. **Ripgrep has limits**: 5 concurrent searches to avoid overwhelming the system
4. **Streaming forces sequential**: Any tool with `isStreaming=true` flushes the batch
5. **Batch completion is eager**: Batch completes when all tools in it finish, not when stream ends

## Related Tasks for Deeper Investigation

Consider creating tasks for:
- How the server decides to emit tools in parallel vs sequential
- How tool timeouts interact with batching
- The retry/error handling behavior for parallel batches
- How `persist_idempotent_stream_state` experiment affects batching
