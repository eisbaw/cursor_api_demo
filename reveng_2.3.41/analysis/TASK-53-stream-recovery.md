# TASK-53: Stream Recovery and toolCallResultCache Analysis

## Executive Summary

Cursor IDE 2.3.41 implements a sophisticated **idempotent streaming protocol** for AI chat sessions that enables reliable stream recovery after network interruptions. The `toolCallResultCache` mechanism is a critical component that ensures tool execution results are preserved during reconnection, preventing duplicate tool executions.

## Architecture Overview

### Key Components

1. **IdempotentStreamState** - Persisted state for stream recovery
2. **toolCallResultCache** - In-memory and persisted cache of tool execution results
3. **playbackChunks** - Queued messages for replay during reconnection
4. **seqnoAck** - Server acknowledgment of received sequence numbers

### Feature Gate

The feature is controlled by `persist_idempotent_stream_state` feature gate (default: false).

```javascript
// Feature gate check
const l = this._experimentService.checkFeatureGate("persist_idempotent_stream_state")
```

## Protobuf Message Definitions

### Client-to-Server (oNe class)
**Type:** `aiserver.v1.StreamUnifiedChatRequestWithToolsIdempotent`

Fields:
- `client_chunk` (message) - The actual chat/tool request
- `abort` (message) - Abort request
- `close` (message) - Close request
- `idempotency_key` (string, optional) - Unique key for the session
- `seqno` (uint32, optional) - Sequence number for ordering

### Server-to-Client (OPr class)
**Type:** `aiserver.v1.StreamUnifiedChatResponseWithToolsIdempotent`

Fields (oneof response):
- `server_chunk` (message, no: 1) - Server response with eventId
- `welcome_message` (message, no: 3) - Connection welcome, includes degraded mode flag
- `seqno_ack` (uint32, no: 4) - Acknowledgment of received sequence number

### WelcomeMessage (dcl class)
**Type:** `aiserver.v1.WelcomeMessage`

Fields:
- `message` (string)
- `is_degraded_mode` (bool) - When true, reconnection is not available

## IdempotentStreamState Structure

```javascript
idempotentStreamState: {
    idempotencyKey: string,        // UUID identifying the stream session
    idempotencyEventId: string,    // Last processed event ID (starts at "0")
    idempotentEncryptionKey: string, // 32-byte encryption key (base64)
    nextSeqno: number,             // Next sequence number to use
    playbackChunks: Array<[number, string]>  // [seqno, JSON-serialized chunk]
}
```

## Stream Recovery Flow

### 1. Initial Stream Setup

```javascript
// Line 488771-488792
async * startReliableStream(e, t, n, s, r, o, a) {
    const l = this._experimentService.checkFeatureGate("persist_idempotent_stream_state"),
        d = o?.idempotencyKey ?? es(),  // Generate new UUID if not resuming
        h = o?.idempotentEncryptionKey ?? (() => {
            const E = new Uint8Array(32);
            return crypto.getRandomValues(E), yO(Vs.wrap(E), !1, !0)
        })();

    // Initialize state if new stream
    !o && l && this._composerDataService.updateComposerData(r, {
        idempotentStreamState: {
            idempotencyKey: d,
            idempotencyEventId: "0",
            idempotentEncryptionKey: h,
            nextSeqno: 0,
            playbackChunks: []
        }
    })
}
```

### 2. HTTP Headers for Idempotent Streaming

```javascript
// Line 488861-488865
headers: {
    ...n,
    "x-idempotency-key": d,
    "x-idempotency-event-id": f,
    "x-idempotent-encryption-key": h
}
```

### 3. Chunk Tracking and Persistence

Each outbound chunk is:
1. Assigned a sequence number
2. Stored in `playbackChunks` Map (memory)
3. Persisted to `idempotentStreamState.playbackChunks` (storage)

```javascript
// Line 488793-488815
for await (const T of t) {
    const D = w++,  // Increment sequence number
        P = new oNe({
            request: {
                case: "clientChunk",
                value: T
            },
            seqno: D
        });
    g.playbackChunks.set(D, P);
    g.internalAsyncPushable.push(P);

    // Persist to storage
    if (A?.idempotentStreamState && l) {
        const M = P.toJsonString();
        this._composerDataService.updateComposerData(r, {
            idempotentStreamState: {
                ...B,
                playbackChunks: [...B.playbackChunks, [D, M]],
                nextSeqno: D + 1
            }
        })
    }
}
```

### 4. Server Acknowledgment Handling

When server acknowledges a sequence number, it's removed from playback queue:

```javascript
// Line 488878-488891
if (M.response.case === "seqnoAck") {
    g.playbackChunks.delete(M.response.value);
    const B = this._composerDataService.getComposerData(r);
    if (B?.idempotentStreamState && l) {
        const H = B.idempotentStreamState,
            J = M.response.value;
        this._composerDataService.updateComposerData(r, {
            idempotentStreamState: {
                ...H,
                playbackChunks: H.playbackChunks.filter(([G]) => G !== J)
            }
        })
    }
}
```

### 5. Event ID Tracking

The `idempotencyEventId` is updated when receiving text/thinking responses:

```javascript
// Line 488896-488907
if (B.response?.case === "streamUnifiedChatResponse" &&
    (B.response.value.text || B.response.value.thinking)) {
    f = B.eventId;
    if (J?.idempotentStreamState && l) {
        this._composerDataService.updateComposerData(r, {
            idempotentStreamState: {
                ...G,
                idempotencyEventId: B.eventId
            },
            toolCallResultCache: {}  // Clear cache on new text response
        })
    }
}
```

## toolCallResultCache Mechanism

### Purpose

The `toolCallResultCache` prevents re-execution of tools during stream recovery. When the client reconnects and replays messages, tool results are served from cache instead of re-executing.

### Cache Structure

```javascript
toolCallResultCache: {
    [toolCallId: string]: _y  // _y is ClientSideToolV2Result
}
```

### Cache Type (_y class)
**Type:** `aiserver.v1.ClientSideToolV2Result`

Fields:
- `tool` (enum) - Tool type identifier
- `result` (oneof) - The actual tool result
- `toolCallId` (string) - Unique identifier for the tool call

### Cache Population

When a tool executes successfully, the result is cached:

```javascript
// Line 484906-484923
const st = r?.composerId ? this.composerDataService.getComposerData(r.composerId) : void 0,
    Xe = st?.toolCallResultCache?.[Oe.toolCallId];

if (Xe) {
    Je = Xe;  // Use cached result
} else {
    // Execute tool and cache result
    Je = await this.runTool(Oe, ...);
    r?.composerId && o && this.composerDataService.updateComposerData(r.composerId, {
        toolCallResultCache: {
            ...st?.toolCallResultCache,
            [Oe.toolCallId]: Je
        }
    })
}
```

### Cache Serialization/Deserialization

**Serialization** (for storage):
```javascript
// Line 267041
toolCallResultCache: en ? Object.fromEntries(
    Object.entries(en).map(([$i, wn]) => [$i, wn.toJsonString()])
) : void 0
```

**Deserialization** (on load):
```javascript
// Line 266846-266857
if (n.toolCallResultCache && typeof n.toolCallResultCache == "object") {
    try {
        n.toolCallResultCache = Object.fromEntries(
            Object.entries(n.toolCallResultCache).map(([r, o]) => {
                try {
                    if (o instanceof _y) return [r, o];
                    const a = _y.fromJsonString(o);
                    return [r, a]
                } catch (a) {
                    console.warn(`[composer] Failed to deserialize cached tool result for ${r}:`, a);
                    return null
                }
            }).filter(r => r !== null)
        )
    } catch (r) {
        console.error("[composer] Failed to deserialize toolCallResultCache:", r);
        n.toolCallResultCache = void 0
    }
}
```

### Cache Invalidation

The cache is cleared when:

1. **New text/thinking response received** - Line 488906: `toolCallResultCache: {}`
2. **Deserialization failure** - Line 266857: `n.toolCallResultCache = void 0`
3. **Stream completes** - implicitly cleared with idempotentStreamState

## Reconnection and Recovery

### Auto-Resume on Startup

```javascript
// Line 945183-945231
async _autoResumeInterruptedStreams() {
    const e = this.experimentService.getDynamicConfigParam(
        "idempotent_stream_config", "retry_lookback_window_ms"
    ) ?? 72e5;  // Default: 2 hours (7200 * 1000)

    for (const s of allComposers) {
        const o = s.lastUpdatedAt ?? s.createdAt;
        if (t - o > e) continue;  // Skip if too old

        if (!a.data.idempotentStreamState) continue;
        if (!a.data.chatGenerationUUID) {
            // Clear orphaned state
            this.composerDataService.updateComposerData(a.data.composerId, {
                idempotentStreamState: void 0
            });
            continue
        }

        // Resume the stream
        await this.composerChatService.submitChatMaybeAbortCurrent(
            a.data.composerId, "", { isResume: !0 }
        )
    }
}
```

### Resume Stream Initialization

```javascript
// Line 489153-489177
const Re = ne.idempotentStreamState;
if (Re && ne.chatGenerationUUID) {
    Pe = !0;  // isResume flag
    const tt = new Map;
    for (const [wt, mt] of Re.playbackChunks) {
        try {
            const _t = oNe.fromJsonString(mt);
            tt.set(wt, _t)
        } catch (_t) {
            console.error("[composer] Failed to deserialize playback chunk:", _t)
        }
    }
    ke = {
        idempotencyKey: Re.idempotencyKey,
        idempotencyEventId: Re.idempotencyEventId,
        idempotentEncryptionKey: Re.idempotentEncryptionKey,
        nextSeqno: Re.nextSeqno,
        playbackChunks: tt
    }
}
```

### Playback During Reconnection

```javascript
// Line 488849-488857
const P = (async function*() {
    for (const M of g.playbackChunks.values()) yield M;  // Replay stored chunks
    for await (const M of g.internalAsyncPushable) yield M;  // Then new chunks
    p && (yield new oNe({
        request: { case: "close", value: {} }
    }))
})()
```

## Degraded Mode Handling

When server indicates degraded mode, reconnection is disabled:

```javascript
// Line 488870-488875
if (M.response.case === "welcomeMessage") {
    M.response.value.isDegradedMode === !0 && (
        D = !0,  // Mark as degraded
        console.warn("[composer] Idempotent streaming is in degraded mode - reconnection not available"),
        this._composerDataService.updateComposerData(r, {
            idempotentStreamState: void 0  // Clear recovery state
        })
    )
}
```

In degraded mode, errors are not retried:
```javascript
// Line 488920
if (D) throw console.error("[composer] Error in degraded mode, not retrying"), ...
```

## Error Handling and Retry Logic

### Retry Loop

```javascript
// Line 488841-488956
let _ = 0;
for (; !s.aborted;) {
    _++;  // Retry counter
    try {
        // Stream processing...
    } catch (P) {
        if (D) throw P;  // No retry in degraded mode

        // Check for non-retryable errors
        if (P instanceof lb) {
            const A = P.findDetails(FA);
            if (A && A.length > 0) throw P;
        }

        if (s.aborted) {
            // Send abort to server
            await e.streamUnifiedChatWithToolsIdempotent(abortGenerator, {...});
            return;
        }

        // Set reconnecting flag and wait
        this._composerDataService.updateComposerData(r, { isReconnecting: !0 });
        await new Promise(A => setTimeout(A, 1e3));  // 1 second delay
    }
}
```

## Stream State Cleanup

State is cleared on:

1. **Abort** (Line 946367-946370):
```javascript
chatGenerationUUID: void 0,
status: "aborted",
idempotentStreamState: void 0
```

2. **Stream completion** (Line 490698):
```javascript
idempotentStreamState: void 0
```

3. **Non-resume start** (Line 489179-489180):
```javascript
if (!Pe && ne.idempotentStreamState) {
    this._composerDataService.updateComposerData(e, {
        idempotentStreamState: void 0
    })
}
```

## NAL Client Stall Detector

A separate component monitors stream health:

```javascript
// Line 465816-465853
onStallDetected() {
    // Logs warning when stream stalls beyond threshold
    Sro.warn(this.ctx,
        "[NAL client stall detector] Bidirectional stream stall detected - no activity for threshold period",
        ...
    );
}

emitLog() {
    // Called when stream activity resumes
    Sro.info(this.ctx,
        "[NAL client stall detector] Stream activity resumed after stall",
        ...
    );
}
```

## Configuration

### Dynamic Config: `idempotent_stream_config`

```javascript
idempotent_stream_config: {
    retry_lookback_window_ms: number  // Default: 7,200,000 (2 hours)
}
```

## Security Considerations

1. **Encryption Key** - 32-byte random key generated per session
2. **Key Transmission** - Sent via `x-idempotent-encryption-key` header
3. **Persistence** - Keys are persisted with stream state (potential security concern)

## File Locations

- **Main implementation**: `workbench.desktop.main.js`
- **startReliableStream**: Line 488771
- **toolCallResultCache handling**: Lines 484906-484923
- **State deserialization**: Lines 266846-266857
- **Auto-resume**: Lines 945183-945231

## Key Takeaways

1. **Idempotent streaming** uses sequence numbers and server acknowledgments to ensure exactly-once delivery
2. **toolCallResultCache** prevents tool re-execution by caching results keyed by `toolCallId`
3. **playbackChunks** stores unacknowledged messages for replay during reconnection
4. **Event ID tracking** allows server to resume from the correct position
5. **Degraded mode** gracefully disables reconnection when server cannot support it
6. **Auto-resume** automatically recovers interrupted streams within a 2-hour window

## Related Investigation Avenues

- Analyze the encryption mechanism for idempotent stream state
- Investigate how tool results are validated on replay
- Study the NAL (Next Agent Layer) stall detection in more depth
- Examine the interaction between subagents and stream recovery
