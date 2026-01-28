# TASK-39: Idempotent Stream Resumption Protocol Analysis

## Executive Summary

The Cursor IDE implements an **idempotent streaming protocol** for reliable communication with the AI backend, enabling stream resumption after disconnection. This analysis documents the protocol mechanism, replay attack prevention, and the cryptographic elements used to secure stream state.

## Feature Gates

The idempotent streaming feature is controlled by several feature gates:

| Feature Gate | Purpose |
|-------------|---------|
| `persist_idempotent_stream_state` | Enables persistent storage of stream state for cross-session resumption |
| `idempotent_agentic_composer` | Enables idempotent streaming for agentic composer operations |

## Protocol Architecture

### Core Components

1. **IdempotentStreamState** - Persisted state for stream resumption:
```javascript
idempotentStreamState: {
    idempotencyKey: string,        // Unique stream identifier
    idempotencyEventId: string,    // Last processed server event ID
    idempotentEncryptionKey: string, // 256-bit encryption key (base64)
    nextSeqno: number,             // Next sequence number for client chunks
    playbackChunks: Array<[seqno, jsonString]>  // Buffered unacknowledged chunks
}
```

2. **HTTP Headers** - Stream identity transmitted via headers:
```
x-idempotency-key: <unique-stream-id>
x-idempotency-event-id: <last-event-id>
x-idempotent-encryption-key: <base64-encoded-256-bit-key>
```

3. **Protobuf Messages**:
   - Request: `aiserver.v1.StreamUnifiedChatRequestWithToolsIdempotent`
   - Response: `aiserver.v1.StreamUnifiedChatResponseWithToolsIdempotent`

## Sequence Number (seqno) Protocol

The protocol uses a bidirectional sequence number mechanism for reliable delivery:

### Client-to-Server Flow

1. Each client chunk is assigned an incrementing `seqno`
2. Chunks are buffered in `playbackChunks` until acknowledged
3. On reconnection, all unacknowledged chunks are replayed in order

```javascript
// Chunk creation (line 488796-488803)
const D = w++,  // seqno increments
    P = new oNe({
        request: {
            case: "clientChunk",
            value: T  // Original chunk data
        },
        seqno: D
    });
g.playbackChunks.set(D, P);  // Buffer for replay
```

### Server-to-Client Flow

1. Server sends `seqnoAck` to acknowledge received chunks
2. Client removes acknowledged chunks from replay buffer
3. Server sends `eventId` with text/thinking responses for cursor position

```javascript
// seqno acknowledgment handling (line 488878-488891)
if (M.response.case === "seqnoAck") {
    g.playbackChunks.delete(M.response.value);
    // Also clean from persistent storage
    if (B?.idempotentStreamState && l) {
        this._composerDataService.updateComposerData(r, {
            idempotentStreamState: {
                ...H,
                playbackChunks: H.playbackChunks.filter(([G]) => G !== J)
            }
        })
    }
}
```

## Replay Attack Prevention

### Mechanism Analysis

The protocol employs several replay attack prevention mechanisms:

#### 1. Unique Idempotency Key Generation
```javascript
// Line 488773
const d = o?.idempotencyKey ?? es(),  // UUID generation
```
- Uses cryptographically random UUID (`es()` function)
- Unique per stream session
- Server can track and reject duplicate keys

#### 2. Event ID Tracking
```javascript
// Line 488897-488904
if (B.response?.case === "streamUnifiedChatResponse" &&
    (B.response.value.text || B.response.value.thinking)) {
    f = B.eventId;  // Track last server event
    // Persist to state
    this._composerDataService.updateComposerData(r, {
        idempotentStreamState: {
            ...G,
            idempotencyEventId: B.eventId
        }
    })
}
```
- Each meaningful server response includes an `eventId`
- Client sends last `eventId` on reconnection via header
- Server can resume from that point, preventing double-processing

#### 3. 256-bit Encryption Key
```javascript
// Line 488774-488776
h = o?.idempotentEncryptionKey ?? (() => {
    const E = new Uint8Array(32);  // 256 bits
    return crypto.getRandomValues(E), yO(Vs.wrap(E), !1, !0)
})();
```
- Cryptographically random 256-bit key
- Generated per stream session
- Base64-URL encoded for transmission
- Server validates key matches stream session

#### 4. Degraded Mode Detection
```javascript
// Line 488870-488872
if (M.response.case === "welcomeMessage") {
    M.response.value.isDegradedMode === !0 && (
        D = !0,
        console.warn("[composer] Idempotent streaming is in degraded mode"),
        this._composerDataService.updateComposerData(r, {
            idempotentStreamState: void 0  // Clear state, no replay possible
        })
    )
}
```
- Server can signal degraded mode (e.g., high load)
- Client disables replay on degraded mode
- Prevents amplification attacks during server stress

## Auto-Resume on Application Restart

### Triggering Condition
```javascript
// Line 945183
this.experimentService.checkFeatureGate("persist_idempotent_stream_state") &&
    this._autoResumeInterruptedStreams()
```

### Resume Logic
```javascript
// Line 945194-945230
async _autoResumeInterruptedStreams() {
    // Configurable lookback window (default 2 hours)
    const e = this.experimentService.getDynamicConfigParam(
        "idempotent_stream_config",
        "retry_lookback_window_ms"
    ) ?? 72e5;  // 7200 * 1000 = 2 hours

    const t = Date.now(),
        n = this.composerDataService.allComposersData.allComposers;

    for (const s of n) {
        // Skip if no idempotent state
        if (!a.data.idempotentStreamState) continue;

        // Skip if no active generation
        if (!a.data.chatGenerationUUID) {
            // Clear orphaned state
            this.composerDataService.updateComposerData(a.data.composerId, {
                idempotentStreamState: void 0
            });
            continue;
        }

        // Check time window
        const o = s.lastUpdatedAt ?? s.createdAt;
        if (t - o > e) continue;  // Too old

        // Resume the stream
        await this.composerChatService.submitChatMaybeAbortCurrent(
            a.data.composerId,
            "",
            { /* resume options */ }
        );
    }
}
```

### Resume Requirements
1. `persist_idempotent_stream_state` feature gate enabled
2. Composer has valid `idempotentStreamState`
3. Composer has active `chatGenerationUUID`
4. Last update within lookback window (default 2 hours)

## Connection Recovery Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Stream Connection Flow                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client                                Server                    │
│    │                                     │                       │
│    │──── Connect (idempotency headers) ──▶│                       │
│    │                                     │                       │
│    │◀────── WelcomeMessage ──────────────│                       │
│    │                                     │                       │
│    │──── ClientChunk (seqno=0) ─────────▶│                       │
│    │◀────── seqnoAck (0) ────────────────│                       │
│    │                                     │                       │
│    │──── ClientChunk (seqno=1) ─────────▶│                       │
│    │◀────── ServerChunk (eventId=X) ─────│                       │
│    │                                     │                       │
│    ╳  ~~~ Connection Lost ~~~            ╳                       │
│    │                                     │                       │
│    │──── Reconnect (same headers) ──────▶│                       │
│    │     + x-idempotency-event-id: X     │                       │
│    │                                     │                       │
│    │◀────── WelcomeMessage ──────────────│                       │
│    │                                     │                       │
│    │──── Replay ClientChunk (seqno=1) ──▶│  (if not acked)      │
│    │◀────── seqnoAck (1) ────────────────│  (already processed) │
│    │                                     │                       │
│    │◀────── Resume from eventId=X ───────│                       │
│    │                                     │                       │
└─────────────────────────────────────────────────────────────────┘
```

## Protobuf Schema

### Request Message
```protobuf
// aiserver.v1.StreamUnifiedChatRequestWithToolsIdempotent
message StreamUnifiedChatRequestWithToolsIdempotent {
  oneof request {
    ClientChunk client_chunk = 1;   // Regular chunk with seqno
    Empty abort = 2;                 // Abort signal
    Empty close = 3;                 // Close signal
  }
  optional string idempotency_key = 4;  // Stream identity (deprecated: in header)
  optional uint32 seqno = 5;            // Sequence number
}
```

### Response Message
```protobuf
// aiserver.v1.StreamUnifiedChatResponseWithToolsIdempotent
message StreamUnifiedChatResponseWithToolsIdempotent {
  oneof response {
    ServerChunk server_chunk = 1;    // Contains eventId
    WelcomeMessage welcome_message = 3;
    uint32 seqno_ack = 4;            // Acknowledgment
  }
}

message WelcomeMessage {
  string message = 1;
  bool is_degraded_mode = 2;
}
```

## Configuration

| Parameter | Location | Default | Description |
|-----------|----------|---------|-------------|
| `retry_lookback_window_ms` | `idempotent_stream_config` | 7200000 (2h) | Max age for auto-resume |

## Security Considerations

### Strengths
1. **Cryptographic randomness** - All keys/IDs use `crypto.getRandomValues()`
2. **Per-session keys** - New encryption key per stream prevents cross-session attacks
3. **Event-based cursor** - Server tracks position, not client (prevents manipulation)
4. **Degraded mode** - Graceful fallback prevents amplification during stress

### Potential Weaknesses
1. **Client-side state persistence** - State stored locally could be tampered
2. **No server signature** - Events are not cryptographically signed by server
3. **Replay window** - 2-hour default window is quite long for replay attempts

## Source References

| Component | File | Line Range |
|-----------|------|------------|
| startReliableStream | workbench.desktop.main.js | 488771-488960 |
| idempotentStreamState type | workbench.desktop.main.js | 266936, 488786 |
| _autoResumeInterruptedStreams | workbench.desktop.main.js | 945194-945231 |
| Protobuf definitions | workbench.desktop.main.js | 122170-122305 |
| Feature gates | workbench.desktop.main.js | 294165-294171 |
| Dynamic config | workbench.desktop.main.js | 295144-295146, 295499-295502 |

## Related Tasks
- TASK-10: BiDi Append Protocol
- TASK-12: Stream Encryption
- TASK-7: Protobuf Schemas
