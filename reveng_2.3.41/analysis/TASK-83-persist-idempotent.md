# TASK-83: persist_idempotent_stream_state Experiment Flag Analysis

## Overview

The `persist_idempotent_stream_state` feature flag enables persistent storage of idempotent stream state, allowing Cursor IDE to automatically resume interrupted AI chat/agent streams after crashes, network failures, or IDE restarts.

## Flag Definition

**Location**: Line 294169
```javascript
persist_idempotent_stream_state: {
    client: !0,  // true - client-side flag
    default: !1  // false - disabled by default
}
```

The flag is a client-side experiment that is **disabled by default**.

## What Triggers This Experiment

The flag is checked in four key locations:

### 1. Tool Wrapped Stream (Line 484524)
```javascript
const o = this.experimentService.checkFeatureGate("persist_idempotent_stream_state")
```
When enabled, the `toolWrappedStream` method stores tool call results in a persistent cache for replay.

### 2. Reliable Stream Start (Line 488772)
```javascript
const l = this._experimentService.checkFeatureGate("persist_idempotent_stream_state")
```
Controls whether `startReliableStream` persists stream state to composer data.

### 3. Chat Submission (Line 490175)
```javascript
const qm = this._experimentService.checkFeatureGate("idempotent_agentic_composer")
```
Related flag that determines whether to use `startReliableStream` vs direct streaming.

### 4. Composer Service Initialization (Line 945183)
```javascript
this.experimentService.checkFeatureGate("persist_idempotent_stream_state") &&
    this._autoResumeInterruptedStreams().catch(bi => {
        console.error("[composer] Error during auto-resume of interrupted streams:", bi)
    })
```
Triggers automatic stream resumption on IDE startup when the flag is enabled.

## State That Gets Persisted

When `persist_idempotent_stream_state` is enabled, the following state is stored in the composer's data:

### idempotentStreamState Object Structure
```javascript
idempotentStreamState: {
    idempotencyKey: string,           // UUID for server-side deduplication
    idempotencyEventId: string,       // Last processed server event ID
    idempotentEncryptionKey: string,  // 32-byte encryption key (base64)
    nextSeqno: number,                // Next sequence number for client chunks
    playbackChunks: Array<[number, string]>  // Unacknowledged client chunks (seqno -> JSON)
}
```

### toolCallResultCache Object
```javascript
toolCallResultCache: {
    [toolCallId: string]: ToolResult  // Cached tool execution results
}
```

The tool result cache is persisted to avoid re-executing tools during stream resumption. This is cleared when new server text/thinking content arrives.

## Storage Mechanism

### Primary Storage: Reactive Storage Service

The composer data (including idempotentStreamState) is stored via the `_reactiveStorageService`:

```javascript
// Line 297962
[this.allComposersData, this.setAllComposersData, this.resetComposers, te] =
    ryh(this._storageService, this._reactiveStorageService, ...)
```

The storage scope depends on workspace state:
- **Workspace mode**: `StorageScope.WORKSPACE` (scope = 1)
- **Empty window**: `StorageScope.APPLICATION` (scope = -1)

### Data Serialization

Stream state is serialized for storage:
```javascript
// Line 267041 - Serialization for storage
toolCallResultCache: en ? Object.fromEntries(
    Object.entries(en).map(([$i, wn]) => [$i, wn.toJsonString()])
) : void 0

// Line 266847 - Deserialization from storage
n.toolCallResultCache = Object.fromEntries(
    Object.entries(n.toolCallResultCache).map(([r, o]) => {
        const a = _y.fromJsonString(o);
        return [r, a]
    })
)
```

### Playback Chunks Storage

Playback chunks are stored as JSON strings and deserialized on resume:
```javascript
// Storage (line 488812)
playbackChunks: [...B.playbackChunks, [D, M]]  // M = P.toJsonString()

// Restoration (line 489159-489161)
const tt = new Map;
for (const [wt, mt] of Re.playbackChunks) try {
    const _t = oNe.fromJsonString(mt);
    tt.set(wt, _t)
}
```

## Impact on Reconnection Behavior

### Immediate Reconnection (Network Failure)

When a stream fails mid-execution:

1. **Error Detection** (Line 488914):
   ```javascript
   console.error("[composer] Error in startReliableStream", P, {
       signalAborted: s.aborted,
       idempotencyKey: d,
       idempotencyEventId: f,
       playbackChunks: Array.from(g.playbackChunks.keys()).sort()
   })
   ```

2. **Reconnecting State Set** (Line 488955):
   ```javascript
   this._composerDataService.updateComposerData(r, {
       isReconnecting: !0
   })
   await new Promise(A => setTimeout(A, 1e3))  // 1 second delay
   ```

3. **Retry Loop**: The stream automatically retries with saved state, replaying unacknowledged chunks.

### Deferred Resumption (IDE Restart)

On IDE startup, `_autoResumeInterruptedStreams` is called:

1. **Lookback Window Check** (Line 945195):
   ```javascript
   const e = this.experimentService.getDynamicConfigParam(
       "idempotent_stream_config",
       "retry_lookback_window_ms"
   ) ?? 72e5  // Default: 2 hours (7,200,000 ms)
   ```

2. **Iterate All Composers** (Line 945198):
   ```javascript
   const n = this.composerDataService.allComposersData.allComposers;
   for (const s of n) {
       // Check if composer has idempotentStreamState
       if (!a || !a.data.idempotentStreamState) continue;
       // Check if chatGenerationUUID exists
       if (!a.data.chatGenerationUUID) {
           // Clear invalid state
           this.composerDataService.updateComposerData(a.data.composerId, {
               idempotentStreamState: void 0
           });
           continue
       }
       // Resume the stream
       await this.composerChatService.submitChatMaybeAbortCurrent(
           a.data.composerId,
           "",
           { isResume: !0 }
       )
   }
   ```

3. **Status Restoration** (Line 266846):
   ```javascript
   if (s === "generating" && (n.idempotentStreamState && n.chatGenerationUUID ||
       (s = "aborted")))
   ```
   Composers in "generating" state are only kept generating if they have valid idempotent state.

## Server-Side Protocol

### HTTP Headers

The client sends idempotency information via headers:
```javascript
// Line 488863-488865
headers: {
    "x-idempotency-key": d,
    "x-idempotency-event-id": f,
    "x-idempotent-encryption-key": h
}
```

### Bidirectional Stream Messages

**Client -> Server**:
- `clientChunk`: Payload with sequence number
- `close`: Normal stream termination
- `abort`: User-initiated abort

**Server -> Client**:
- `welcomeMessage`: Contains `isDegradedMode` flag
- `seqnoAck`: Acknowledges client chunks (allows cleanup)
- `serverChunk`: Contains actual AI response with `eventId`

### Degraded Mode

The server can signal degraded mode (Line 488871):
```javascript
if (M.response.value.isDegradedMode === !0) {
    D = !0;
    console.warn("[composer] Idempotent streaming is in degraded mode - reconnection not available");
    this._composerDataService.updateComposerData(r, {
        idempotentStreamState: void 0
    })
}
```

When in degraded mode:
- Reconnection is disabled
- Idempotent state is cleared
- Errors are not retried

## Sequence Number Management

### Client-Side Chunk Numbering
```javascript
// Line 488796-488804
const D = w++;  // Increment seqno
const P = new oNe({
    request: {
        case: "clientChunk",
        value: T
    },
    seqno: D
});
g.playbackChunks.set(D, P);
g.internalAsyncPushable.push(P);
```

### Server Acknowledgment Handling
```javascript
// Line 488878-488890
if (M.response.case === "seqnoAck") {
    g.playbackChunks.delete(M.response.value);
    // Also update persisted state
    this._composerDataService.updateComposerData(r, {
        idempotentStreamState: {
            ...H,
            playbackChunks: H.playbackChunks.filter(([G]) => G !== J)
        }
    })
}
```

## Tool Result Caching

When the flag is enabled, tool results are cached to avoid re-execution on resume:

```javascript
// Line 484907-484923
const Xe = st?.toolCallResultCache?.[Oe.toolCallId];
if (Xe) {
    Je = Xe;  // Use cached result
} else {
    Je = await this.runTool(...);
    // Cache the result
    this.composerDataService.updateComposerData(r.composerId, {
        toolCallResultCache: {
            ...st?.toolCallResultCache,
            [Oe.toolCallId]: Je
        }
    })
}
```

The cache is cleared when new text/thinking arrives from the server (Line 488906):
```javascript
if (B.response.value.text || B.response.value.thinking) {
    this._composerDataService.updateComposerData(r, {
        idempotentStreamState: {...},
        toolCallResultCache: {}  // Clear cache
    })
}
```

## Dynamic Configuration

### idempotent_stream_config Parameters

**Schema** (Line 295144):
```javascript
idempotent_stream_config: ls.object({
    retry_lookback_window_ms: ls.number()
})
```

**Default Values** (Line 295499):
```javascript
idempotent_stream_config: {
    client: !0,
    fallbackValues: {
        retry_lookback_window_ms: 7200 * 1e3  // 2 hours
    }
}
```

This parameter controls how far back in time the auto-resume feature will look for interrupted streams.

## Related Flags

### idempotent_agentic_composer (Line 294165)
```javascript
idempotent_agentic_composer: {
    client: !0,
    default: !1
}
```

This flag determines whether to use the reliable stream infrastructure at all. When checked (Line 490175):
```javascript
const qm = this._experimentService.checkFeatureGate("idempotent_agentic_composer");
const MT = qm ? this.startReliableStream(...) : rm.streamUnifiedChatWithTools(...)
```

The relationship:
- `idempotent_agentic_composer`: Enables the reliable streaming protocol
- `persist_idempotent_stream_state`: Adds persistent storage for crash recovery

## UI Indicators

The `isReconnecting` state is exposed to the UI (Line 714837):
```javascript
w = ve(() => a().isReconnecting ?? !1)
```

Status display (Line 751204):
```javascript
n().isReconnecting === !0 && f.push("reconnecting")
```

## Error Handling

### Abort Signal Handling
```javascript
// Line 488929-488952
if (s.aborted) {
    // Send abort message to server
    await e.streamUnifiedChatWithToolsIdempotent(abortGenerator, {
        headers: {
            "x-idempotency-key": d,
            "x-idempotency-event-id": f,
            "x-idempotent-encryption-key": h
        }
    })
}
```

### Fatal Error Detection
```javascript
// Line 488923-488927
if (P instanceof lb) {
    const A = P.findDetails(FA);
    if (A && A.length > 0) throw P;  // Don't retry
}
```

## Summary

The `persist_idempotent_stream_state` experiment flag enables:

1. **Crash Recovery**: Streams can be resumed after IDE crashes or unexpected shutdowns
2. **Network Resilience**: Automatic retry with replay of unacknowledged chunks
3. **Tool Result Caching**: Prevents redundant tool executions during resume
4. **Configurable Window**: 2-hour default lookback for auto-resume on startup
5. **Encryption**: All persisted chunks use the idempotent encryption key

The feature is currently disabled by default and requires both `idempotent_agentic_composer` (for reliable streaming) and `persist_idempotent_stream_state` (for persistent storage) to be enabled for full crash recovery functionality.
