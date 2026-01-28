# TASK-82: Tool Timeout and Retry Behavior in Parallel Batches

## Executive Summary

This analysis documents how Cursor IDE handles tool execution timeouts and retry logic, particularly within parallel batch execution. The system uses a sophisticated concurrency control mechanism with TTL-based stale task cleanup, individual tool timeouts, and network-level retry interceptors.

## Key Findings

### 1. Tool Concurrency Configuration

The tool execution system is controlled by a dynamic configuration called `tools_concurrency_config`:

**Location:** Lines 295350-295365 and 484274-484292

```javascript
// Default configuration (fallback values)
tools_concurrency_config: {
    client: true,
    fallbackValues: {
        tools: {
            RIPGREP_RAW_SEARCH: {
                ttl: 10000,      // 10 seconds
                maxConcurrent: 5
            },
            RIPGREP_SEARCH: {
                ttl: 10000,      // 10 seconds
                maxConcurrent: 5
            }
        },
        defaultTtl: 10000,           // 10 seconds default TTL
        defaultMaxConcurrent: 999999  // Effectively unlimited by default
    }
}
```

### 2. TTL (Time-To-Live) Behavior

The TTL is **NOT a traditional timeout**. It's used for stale task cleanup, not for killing running tools.

**Location:** Lines 484284-484305 (`getToolTtl` and `cleanupStaleTools`)

```javascript
getToolTtl(e) {
    const t = this.experimentService.getDynamicConfig("tools_concurrency_config");
    const n = vt[e];  // Tool type name
    const s = t?.tools?.[n];
    // Return specific TTL if configured, otherwise default (1000ms fallback)
    return s?.ttl !== void 0 ? s.ttl : t?.defaultTtl ?? 1000;
}

cleanupStaleTools(e) {
    const t = this.toolStartTimestamps.get(e) ?? [];
    if (t.length === 0) return;
    const n = Date.now();
    const s = this.getToolTtl(e);
    // Count tools that have exceeded TTL
    const r = t.filter(o => n - o > s).length;
    if (r > 0) {
        console.warn(`[ToolV2Service] Cleaned up ${r} stale ${vt[e]} task(s) (TTL: ${s}ms exceeded)`);
        // Decrement active count for stale tools
        const o = this.activeToolCallsByType.get(e) ?? 0;
        this.activeToolCallsByType.set(e, Math.max(0, o - r));
        // Remove stale timestamps
        this.toolStartTimestamps.set(e, t.filter(a => n - a <= s));
    }
}
```

**Key Insight:** The TTL mechanism is a safety valve for the concurrency limiter, not for the tools themselves. If a tool hangs, after `ttl` milliseconds, the system will consider its "slot" available for new tools.

### 3. Individual Tool Timeouts (Server-Controlled)

Each tool call can have an individual timeout set by the server via `timeoutMs` property:

**Location:** Lines 484671-484677

```javascript
let pt, Ze = n;  // n is the AbortController
let Ke = () => {
    Ze.abort();
};
if (Oe.timeoutMs && (
    Ze = new AbortController,
    n.signal.addEventListener("abort", Ke),
    pt = setTimeout(() => {
        Ze.abort()
    }, Oe.timeoutMs)
)) {
    // Setup timeout...
}
```

**Behavior:**
- If `timeoutMs` is set on the tool call, a new AbortController is created
- A setTimeout triggers abort after `timeoutMs` milliseconds
- The parent abort signal is also propagated
- Timeout is cleared after tool completes (line 484931)

### 4. Shell Command Timeout Result

Shell commands have explicit timeout handling with a dedicated result type:

**Location:** Lines 467820-467821

```javascript
case "timeout":
    return `Command timed out after ${e.result.value.timeoutMs}ms`;
```

The protobuf schema includes timeout-related fields:

**Location:** Lines 112438, 112493

```javascript
{
    no: 8,
    name: "idle_timeout_seconds",
    kind: "scalar",
    T: 5,  // int32
    opt: true
},
{
    no: 3,
    name: "command_run_timeout_ms",
    kind: "scalar",
    T: 5,  // int32
    opt: true
}
```

### 5. Parallel Batch Execution

Tools are categorized for parallel execution based on type:

**Location:** Lines 484552, 484823-484903

```javascript
// Tools eligible for parallel execution
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

**Parallel Batch Handling:**
1. Tools in the parallel set are queued and executed concurrently
2. Each tool waits for a slot via `waitForToolSlot()`
3. Completion is tracked with `Promise.allSettled(g)` (line 484998)
4. Batch completion is logged: `[ToolV2Service] Parallel batch completed: ${w.length} tools in ${ke}ms`

**Location:** Lines 484996-485002

```javascript
Le && !Re && this.asyncOperationRegistry.exit(Le, "tool_loop_next_datum");
Le && g.length > 0 && this.asyncOperationRegistry.enter(Le, "tool_parallel_batch_wait");
try {
    await Promise.allSettled(g);  // Wait for all parallel tools
} finally {
    Le && g.length > 0 && this.asyncOperationRegistry.exit(Le, "tool_parallel_batch_wait");
}
ee();  // Finalize batch
```

### 6. What Happens When One Tool in a Batch Times Out?

**Finding:** Individual tool failures (including timeouts) do NOT affect other tools in the same batch.

**Location:** Lines 484847-484884

```javascript
} catch (rt) {
    const bt = Date.now();
    const tt = Oe.tool;
    console.error(`[ToolV2Service] Error executing tool ${Oe.tool}:`, {
        toolCallId: Oe.toolCallId,
        // ... error details
    });

    // Error is captured and sent as tool result
    const xt = await this.addAttachmentsToToolResult(new _y({
        tool: Oe.tool,
        toolCallId: Oe.toolCallId,
        error: {
            clientVisibleErrorMessage: kt,
            modelVisibleErrorMessage: _t,
            // ...
        }
    }), r?.composerId);

    // Track individual failure
    E.set(Oe.toolCallId, {
        success: false,
        errorMessage: Dt,
        endTime: bt
    });

    // Still send result to handler
    h.handleToolResult(xt, Oe.toolCallId);
    st(xt);  // Continue processing
}
```

### 7. Retry Logic for Failed Tools

#### Network-Level Retries

The system has a retry interceptor for network-level retries:

**Location:** Lines 294145-294152, 295470-295480

```javascript
// Feature gates
retry_interceptor_disabled: {
    client: true,
    default: true  // Disabled by default
},
retry_interceptor_enabled_for_streaming: {
    client: true,
    default: true  // Enabled for streaming
}

// Retry configuration
retry_interceptor_config: {
    client: true,
    fallbackValues: {
        retriableErrors: [
            { code: "Unavailable" },
            { code: "Unknown" },
            { code: "DeadlineExceeded" }
        ]
    }
}

// Retry parameters
retry_interceptor_params_config: {
    client: true,
    fallbackValues: {
        maxRetries: undefined,
        baseDelayMs: undefined,
        maxDelayMs: undefined
    }
}
```

#### Application-Level Retries

**Location:** Lines 300137-300147 (`R8t` utility function)

```javascript
let t = 0, n = e.initialRetryTimeMs;
for (; t < e.maxNumberOfRetries;) {
    try {
        if (e.signal?.aborted) throw new Error("Aborted");
        const s = await i();
        if (e.shouldRetry?.(s)) {
            if (t++, t >= e.maxNumberOfRetries) return s;
            await new Promise(r => setTimeout(r, n));
            n = Math.min(n * 2, e.maxDelayMs ?? Infinity);  // Exponential backoff
            continue;
        }
        return s;
    } catch (s) {
        // Handle error
    }
}
```

**Usage in Background Agent:**

**Location:** Lines 487899-487910

```javascript
{
    initialRetryTimeMs: 25,
    // ...
}
// And later:
shouldRetry: false  // Individual responses can indicate retry status
```

#### Tool-Level Retry Behavior

**Critical Finding:** Tools themselves do NOT automatically retry. Instead:
1. Failed tool calls return an error result to the model
2. The model can decide to retry by making another tool call
3. The error result contains `isRetryable` flag for the model's decision

**Location:** Lines 485885-485891

```javascript
t = new FA({
    error: e,
    details: {
        title: i.title ?? "Error",
        detail: i.detail ?? "An error occurred",
        isRetryable: i.isRetryable ?? true  // Default is retryable
    }
})
```

### 8. Timeout Configuration Options

| Configuration | Location | Default | Purpose |
|---------------|----------|---------|---------|
| `tools_concurrency_config.defaultTtl` | 295363 | 10000ms | Stale tool cleanup |
| `tools_concurrency_config.tools[X].ttl` | 295355-295361 | Per-tool | Tool-specific TTL |
| `tools_concurrency_config.defaultMaxConcurrent` | 295364 | 999999 | Default concurrent limit |
| `tools_concurrency_config.tools[X].maxConcurrent` | 295356, 295360 | 5 (ripgrep) | Tool-specific limit |
| `timeoutMs` (per tool call) | Server-sent | None | Individual tool timeout |
| `idle_timeout_seconds` | 112438 | Optional | Shell command idle timeout |
| `command_run_timeout_ms` | 112493 | Optional | Shell command run timeout |
| `retry_interceptor_params_config.maxRetries` | 295485 | undefined | Network retry count |
| `retry_interceptor_params_config.baseDelayMs` | 295486 | undefined | Retry base delay |
| `retry_interceptor_params_config.maxDelayMs` | 295487 | undefined | Max retry delay |

### 9. Telemetry and Observability

The system tracks parallel batch execution for telemetry:

**Location:** Lines 478880-478970 (`toolCallEventService`)

```javascript
trackToolCallStart(e, t, n, s, r = false, o, a = false) {
    // r = isParallel, o = parallelBatchSize
    this._eventBuffer.set(e, {
        toolCallId: e,
        toolType: t,
        chatRequestUuid: n,
        modelName: s,
        startTime: l,
        isParallel: r,
        parallelBatchSize: o,
        isStream: a
    });
}

submitParallelToolCallEvents(e, t, n, s) {
    // Submits events for all tools in parallel batch
    // Includes success/failure status per tool
}
```

## Architecture Diagram

```
                                    Parallel Tool Execution Flow
+--------------------------------------------------------------------------------+
|                              ToolV2Service                                       |
|                                                                                  |
|  +------------------+     +-------------------+     +------------------------+   |
|  | Concurrency      |     | Tool Execution    |     | Telemetry              |   |
|  | Control          |     |                   |     |                        |   |
|  |                  |     |                   |     |                        |   |
|  | - maxConcurrent  |---->| - waitForToolSlot |---->| - trackToolCallStart   |   |
|  | - TTL cleanup    |     | - runTool         |     | - trackToolCallEnd     |   |
|  | - slot queue     |     | - timeout abort   |     | - submitParallelBatch  |   |
|  +------------------+     +-------------------+     +------------------------+   |
|          |                        |                                             |
|          v                        v                                             |
|  +------------------+     +-------------------+                                  |
|  | Per-Tool Config  |     | Error Handling    |                                  |
|  |                  |     |                   |                                  |
|  | RIPGREP_SEARCH:  |     | - Individual fail |                                  |
|  |   ttl: 10000     |     | - isRetryable     |                                  |
|  |   maxConcurrent:5|     | - Model decides   |                                  |
|  +------------------+     +-------------------+                                  |
+--------------------------------------------------------------------------------+

                              Individual Tool Timeout
+--------------------------------------------------------------------------------+
|                                                                                  |
|  Server sends: { toolCallId: "...", timeoutMs: 5000, ... }                      |
|                                                                                  |
|  +---------------+         +-----------------+         +-------------------+     |
|  | Tool Call     |  5000ms | setTimeout      |  abort  | Tool AbortController|   |
|  | Received      |-------->| triggers        |-------->| aborts             |    |
|  +---------------+         +-----------------+         +-------------------+     |
|                                                                |                |
|                                                                v                |
|                                                        +-------------------+     |
|                                                        | Error Result      |     |
|                                                        | sent to model     |     |
|                                                        +-------------------+     |
+--------------------------------------------------------------------------------+
```

## Summary Table

| Question | Answer |
|----------|--------|
| What happens when one tool in a batch times out? | The tool returns an error result; other tools continue unaffected |
| Does it affect other tools in the same batch? | No, `Promise.allSettled` ensures all tools complete independently |
| How are retries handled for parallel tools? | Tools don't auto-retry; error results go to model which can make new calls |
| Default TTL for concurrent tools? | 10000ms (10 seconds) |
| What is TTL used for? | Stale tool cleanup in concurrency limiter, NOT killing running tools |
| Are there network-level retries? | Yes, via retry interceptor for Unavailable/Unknown/DeadlineExceeded errors |
| Default max concurrent? | 999999 (effectively unlimited), but RIPGREP tools limited to 5 |

## Potential Investigation Avenues

1. **Retry Interceptor Deep Dive**: The retry interceptor configuration has undefined defaults for maxRetries/delays - actual values may come from server
2. **Shell Command Timeouts**: The `idle_timeout_seconds` and `command_run_timeout_ms` deserve separate investigation for shell-specific behavior
3. **Server-Side Timeout Decisions**: The `timeoutMs` per-tool is server-controlled - understanding when/how the server sets this would be valuable

---

**Source:** `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`

**Key Code Locations:**
- Tool concurrency config: Lines 295050-295365
- ToolV2Service implementation: Lines 484264-485040
- Parallel batch tracking: Lines 478850-479025
- Retry interceptor config: Lines 294140-295140
- Shell timeout result handling: Lines 467814-467833
