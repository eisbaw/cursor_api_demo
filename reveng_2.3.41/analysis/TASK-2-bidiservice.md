# TASK-2: BidiService Bidirectional Streaming Protocol Analysis

## Overview

This document analyzes the `aiserver.v1.BidiService` bidirectional streaming protocol implementation in Cursor IDE 2.3.41. The BidiService provides a mechanism for bidirectional communication between the client and server, primarily used for AI-powered chat interactions with tool support.

## Source Locations

- **Main source file**: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`
- **Proto definitions**: Lines 439104-439279 (bidi_pb.js output)
- **Service definition**: Line 810612-810622
- **Stall detector**: Lines 465748-465856
- **Reliable stream implementation**: Lines 488771-488960

## BidiService Definition

```javascript
// Line 810612-810622
var eru = {
    typeName: "aiserver.v1.BidiService",
    methods: {
        bidiAppend: {
            name: "BidiAppend",
            I: CLc,  // BidiAppendRequest
            O: kLc,  // BidiAppendResponse
            kind: Kt.Unary  // Note: Unary method, not streaming
        }
    }
};
```

**Key Finding**: The BidiService.BidiAppend method is actually a Unary RPC, not a bidirectional stream. The true bidirectional streaming happens through other endpoints like `StreamUnifiedChatWithTools` and `StreamUnifiedChatWithToolsIdempotent`.

## Protobuf Message Types

### BidiRequestId (Line 439107-439136)
```javascript
// typeName: "aiserver.v1.BidiRequestId"
{
    request_id: string  // Field 1, scalar type 9 (string)
}
```

### BidiAppendRequest (CLc) - Line 439137-439176
```javascript
// typeName: "aiserver.v1.BidiAppendRequest"
{
    data: string,           // Field 1 - The data payload
    request_id: BidiRequestId,  // Field 2 - Reference to request
    append_seqno: int64     // Field 3 - Sequence number (T: 3 = int64)
}
```

### BidiAppendResponse (kLc) - Line 439177-439201
```javascript
// typeName: "aiserver.v1.BidiAppendResponse"
{
    // Empty response - acknowledgment only
}
```

### BidiPollRequest (oxe) - Line 439202-439237
```javascript
// typeName: "aiserver.v1.BidiPollRequest"
{
    request_id: BidiRequestId,  // Field 1 - Which request to poll
    start_request: boolean?     // Field 2 - Optional flag to start
}
```

### BidiPollResponse (axe) - Line 439238-439279
```javascript
// typeName: "aiserver.v1.BidiPollResponse"
{
    seqno: int64,    // Field 1 - Sequence number
    data: string,    // Field 2 - Response data
    eof: boolean?    // Field 3 - End of stream marker
}
```

## Streaming Method Types

The codebase uses the bufbuild/connect `Kt` enum for method types (Line 85839):

```javascript
Kt = {
    Unary: 0,
    ServerStreaming: 1,
    ClientStreaming: 2,
    BiDiStreaming: 3
}
```

## Three-Tier Streaming Architecture

Cursor implements a sophisticated fallback pattern for streaming:

### Tier 1: True BiDi Streaming
Used when the network supports it (typically HTTP/2):
- `StreamUnifiedChatWithTools` - kind: BiDiStreaming
- `StreamUnifiedChatWithToolsIdempotent` - kind: BiDiStreaming

### Tier 2: SSE (Server-Sent Events)
Fallback for environments without full bidi support:
- `StreamUnifiedChatWithToolsSSE` - kind: ServerStreaming
- `StreamUnifiedChatWithToolsIdempotentSSE` - kind: ServerStreaming

### Tier 3: Polling
Ultimate fallback using BidiPoll:
- `StreamUnifiedChatWithToolsPoll` - kind: ServerStreaming
- Uses `BidiPollRequest`/`BidiPollResponse` messages

## Idempotent Streaming Protocol

The most sophisticated streaming implementation uses idempotent streams for reliability:

### StreamUnifiedChatRequestWithToolsIdempotent (oNe) - Line 122170-122226
```javascript
// typeName: "aiserver.v1.StreamUnifiedChatRequestWithToolsIdempotent"
{
    request: oneof {
        client_chunk: Hlt,  // Field 1 - Normal chat message
        abort: QD,          // Field 2 - Abort signal
        close: QD           // Field 3 - Close stream
    },
    idempotency_key: string?,  // Field 4 - For deduplication
    seqno: uint32?             // Field 5 - Sequence number
}
```

### StreamUnifiedChatResponseWithToolsIdempotent (OPr) - Line 122262-122306
```javascript
// typeName: "aiserver.v1.StreamUnifiedChatResponseWithToolsIdempotent"
{
    response: oneof {
        server_chunk: yJ,        // Field 1 - Chat response
        welcome_message: dcl,    // Field 3 - Connection confirmation
        seqno_ack: uint32        // Field 4 - Acknowledgment
    }
}
```

### WelcomeMessage (dcl) - Line 122228-122261
```javascript
// typeName: "aiserver.v1.WelcomeMessage"
{
    message: string,
    is_degraded_mode: boolean  // Indicates reconnection not available
}
```

## Reliable Stream Implementation (startReliableStream)

Located at lines 488771-488960, this implements automatic reconnection:

### Key Features:

1. **Idempotency Keys**: Generated per-stream for deduplication
   ```javascript
   const d = o?.idempotencyKey ?? es()  // Generate UUID if not provided
   ```

2. **Encryption Key**: Random 32-byte key for stream encryption
   ```javascript
   const h = o?.idempotentEncryptionKey ?? (() => {
       const E = new Uint8Array(32);
       return crypto.getRandomValues(E), yO(Vs.wrap(E), !1, !0)
   })()
   ```

3. **Playback Chunks**: Maintains a map of unacknowledged messages for replay
   ```javascript
   let g = {
       playbackChunks: o?.playbackChunks ?? new Map,
       internalAsyncPushable: new l$(void 0)
   }
   ```

4. **Sequence Numbers**: Each client message gets a unique seqno
   ```javascript
   const D = w++,
       P = new oNe({
           request: { case: "clientChunk", value: T },
           seqno: D
       })
   ```

### HTTP Headers Used:
```javascript
headers: {
    "x-idempotency-key": d,        // Unique stream identifier
    "x-idempotency-event-id": f,   // Last processed event
    "x-idempotent-encryption-key": h  // Stream encryption key
}
```

### Message Flow:

1. **Client sends**: `clientChunk` messages with incrementing seqno
2. **Server responds**:
   - `welcomeMessage` - Connection established
   - `seqnoAck` - Acknowledgment of received message
   - `serverChunk` - Actual response data
3. **Stream ends**: Client sends `close` message

### Error Recovery:

```javascript
// On error, retry with 1 second delay (unless degraded mode)
if (P instanceof lb) {  // ConnectError
    const A = P.findDetails(FA);  // Check for ErrorDetails
    if (A && A.length > 0) throw ... // Non-recoverable error
}
// If not aborted, wait and retry
await new Promise(A => setTimeout(A, 1e3))
```

## Stall Detection (JOc class)

Located at lines 465761-465854, monitors stream health:

### Metrics Tracked:
- `agent_client.stream.stall.count` - Number of stalls detected
- `agent_client.stream.stall.duration_ms` - How long stalls last
- `agent_client.stream.did_stall` - Streams that experienced stalls
- `agent_client.stream.total` - Total streams monitored

### Activity Types Tracked:
- `inbound_message` - Server-to-client messages
- `outbound_write` - Client-to-server messages
- `ctx.signal` - Abort signals
- `stream` - Stream lifecycle events
- `disposed` - Cleanup events

### Heartbeat Support:
```javascript
onClientSentHeartbeat() {
    this.lastClientSentHeartbeatAt = Date.now()
}
onServerSentHeartbeat() {
    this.lastServerSentHeartbeatAt = Date.now()
}
```

## Heartbeat Messages

### Agent Heartbeat Types:

1. **HeartbeatUpdate** (agent.v1.HeartbeatUpdate) - Line 141824
   - Empty message, used as keep-alive

2. **ClientHeartbeat** (agent.v1.ClientHeartbeat) - Line 142620
   - Sent by client to indicate activity

3. **ExecClientHeartbeat** (agent.v1.ExecClientHeartbeat) - Line 132239
   - For shell execution streams
   - Contains `id: uint32` field

## Error Handling

### ErrorDetails (FA) - Line 92643-92686
```javascript
// typeName: "aiserver.v1.ErrorDetails"
{
    error: ErrorType,     // Enum value
    details: iIr,         // Additional details message
    is_expected: boolean? // Whether error was anticipated
}
```

### Error Types (fu enum) - Line 92685
Comprehensive error enumeration including:
- `UNSPECIFIED (0)` - Unknown error
- `BAD_API_KEY (1)` - Invalid API key
- `NOT_LOGGED_IN (2)` - Authentication required
- `FREE_USER_RATE_LIMIT_EXCEEDED (7)` - Rate limiting
- `PRO_USER_RATE_LIMIT_EXCEEDED (8)` - Rate limiting
- `RESOURCE_EXHAUSTED (41)` - Server overload
- `TIMEOUT (25)` - Request timeout
- `USER_ABORTED_REQUEST (21)` - User cancellation
- `CONVERSATION_TOO_LONG (43)` - Context limit
- `RATE_LIMITED (50)` - Generic rate limit
- `HOOKS_BLOCKED (53)` - Pre/post hooks blocked

## Connect Protocol

Built on bufbuild/connect-es library:

### ConnectError (lb) - Line 267317
```javascript
lb = class bCt extends Error {
    constructor(e, t = Rk.Unknown, n, s, r) {
        super(fyh(e, t))
        this.name = "ConnectError"
        this.rawMessage = e
        this.code = t          // gRPC status code
        this.metadata = new Headers(n ?? {})
        this.details = s ?? []
        this.cause = r
    }
    findDetails(e) { ... }  // Extract typed error details
}
```

### Stream Handling Functions:

1. **BiDi Streaming** (Cyh) - Line 267451:
   ```javascript
   function Cyh(i, e, t) {
       return function(n, s) {
           return v$l(i.stream(e, t, s?.signal, s?.timeoutMs,
               s?.headers, n, s?.contextValues), s)
       }
   }
   ```

2. **Server Streaming** (Syh) - Line 267433:
   ```javascript
   function Syh(i, e, t) {
       return function(n, s) {
           return v$l(i.stream(e, t, s?.signal, s?.timeoutMs,
               s?.headers, pyh([n]), s?.contextValues), s)
       }
   }
   ```

## Degraded Mode

When `isDegradedMode === true` in WelcomeMessage:
1. Stream reconnection is disabled
2. `idempotentStreamState` is cleared
3. Errors are not automatically retried
4. User sees warning in console

```javascript
if (M.response.value.isDegradedMode === !0) {
    D = !0
    console.warn("[composer] Idempotent streaming is in degraded mode - reconnection not available")
    this._composerDataService.updateComposerData(r, {
        idempotentStreamState: void 0
    })
}
```

## Stream State Persistence

When `persist_idempotent_stream_state` feature gate is enabled:

```javascript
idempotentStreamState: {
    idempotencyKey: string,
    idempotencyEventId: string,
    idempotentEncryptionKey: string,
    nextSeqno: number,
    playbackChunks: Array<[seqno, jsonString]>
}
```

This allows stream resumption across page reloads or network interruptions.

## Summary

The BidiService protocol in Cursor 2.3.41 is a sophisticated implementation that:

1. **Uses Connect protocol** (bufbuild/connect-es) for RPC
2. **Implements three-tier fallback**: BiDi -> SSE -> Polling
3. **Provides reliability** through idempotent streams with automatic retry
4. **Monitors health** via stall detection and heartbeats
5. **Handles errors** with structured error details and recovery logic
6. **Persists state** for cross-session stream resumption

The actual bidirectional streaming happens through `StreamUnifiedChatWithToolsIdempotent`, not `BidiService.BidiAppend` which is a simple unary method. The poll-based fallback (`BidiPollRequest`/`BidiPollResponse`) enables bidi-like behavior even on networks that don't support true bidirectional streaming.
