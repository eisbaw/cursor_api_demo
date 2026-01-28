# TASK-117: BidiAppend Mechanism for SSE Mode Client-to-Server Data

## Executive Summary

When Cursor operates in SSE (Server-Sent Events) fallback mode due to HTTP/2 being unavailable, it cannot use true bidirectional streaming. The `BidiAppend` unary method in `aiserver.v1.BidiService` provides the mechanism for the client to send data back to the server in this configuration. This analysis documents the protocol schemas, sequencing mechanism, and architectural design of this fallback system.

## Key Finding: BidiAppend is a Workaround for HTTP/1.1 Limitations

In HTTP/2 mode, Cursor uses `BiDiStreaming` methods where both client and server can send messages on a single connection. In HTTP/1.1 SSE mode:
- **Server-to-Client**: Uses SSE endpoint (e.g., `StreamUnifiedChatWithToolsSSE`)
- **Client-to-Server**: Uses separate `BidiAppend` unary calls

This creates a "simulated" bidirectional stream using two separate HTTP/1.1 connections.

## Protocol Schemas

### BidiRequestId (Line 439107-439136)

Links all messages in a logical stream session:

```protobuf
message BidiRequestId {
    string request_id = 1;  // UUID identifying the stream session
}
```

**JavaScript Class:** `jre` (workbench module) / `hvt` (extension module)

### BidiAppendRequest (Line 439137-439176)

The payload sent from client to server during SSE mode:

```protobuf
message BidiAppendRequest {
    string data = 1;              // Serialized protobuf payload (JSON string)
    BidiRequestId request_id = 2; // Links to active SSE stream
    int64 append_seqno = 3;       // Sequence number for ordering
}
```

**JavaScript Class:** `CLc` / `Ceg`

**Field Details:**
- `data`: Contains the serialized `StreamUnifiedChatRequestWithTools` (or idempotent variant)
- `request_id`: Must match the ID used to initiate the SSE stream
- `append_seqno`: Starts at 0, increments for each append call

### BidiAppendResponse (Line 439177-439201)

Empty acknowledgment message:

```protobuf
message BidiAppendResponse {
    // Empty - acknowledgment only
}
```

**JavaScript Class:** `kLc` / `keg`

## BidiService Definition (Line 810612-810622)

```javascript
{
    typeName: "aiserver.v1.BidiService",
    methods: {
        bidiAppend: {
            name: "BidiAppend",
            I: CLc,      // BidiAppendRequest
            O: kLc,      // BidiAppendResponse
            kind: Kt.Unary  // NOT streaming - single request/response
        }
    }
}
```

**Key Observation:** BidiService only has a single unary method. The actual streaming methods are in ChatService and HealthService.

## SSE Endpoints Using BidiRequestId

### ChatService SSE Methods (Line 466441-466469)

```javascript
{
    // SSE fallback for chat
    streamUnifiedChatWithToolsSSE: {
        name: "StreamUnifiedChatWithToolsSSE",
        I: jre,      // BidiRequestId (not full request!)
        O: yJ,       // StreamUnifiedChatResponseWithTools
        kind: Kt.ServerStreaming
    },

    // Idempotent SSE fallback
    streamUnifiedChatWithToolsIdempotentSSE: {
        name: "StreamUnifiedChatWithToolsIdempotentSSE",
        I: jre,      // BidiRequestId
        O: OPr,      // StreamUnifiedChatResponseWithToolsIdempotent
        kind: Kt.ServerStreaming
    }
}
```

### HealthService SSE Methods (Line 823820-823831)

```javascript
{
    streamBidiSSE: {
        name: "StreamBidiSSE",
        I: jre,      // BidiRequestId
        O: ibt,      // HealthResponse
        kind: Kt.ServerStreaming
    }
}
```

## SSE Mode Communication Flow

### Step 1: Client Generates Request ID

```javascript
const requestId = generateUUID();  // e.g., "550e8400-e29b-41d4-a716-446655440000"
```

### Step 2: Client Opens SSE Stream

```javascript
// HTTP/1.1 SSE connection for receiving server responses
const sseStream = chatClient.streamUnifiedChatWithToolsSSE({
    requestId: requestId
});
```

**Note:** The SSE endpoint only receives `BidiRequestId` - no actual payload!

### Step 3: Client Sends Data via BidiAppend

```javascript
// Separate HTTP/1.1 requests for each client message
let seqno = 0;
for (const chunk of clientChunks) {
    await bidiClient.bidiAppend({
        data: chunk.toJsonString(),
        requestId: { requestId: requestId },
        appendSeqno: seqno++
    });
}
```

### Step 4: Server Correlates by Request ID

The server maintains a session map:
```
request_id -> {
    sse_connection: <active SSE stream>,
    received_seqnos: Set<int64>,
    pending_chunks: Map<seqno, data>
}
```

When `BidiAppend` is received:
1. Look up session by `request_id`
2. Check `append_seqno` for ordering/deduplication
3. Process data as if it arrived on bidirectional stream
4. Send response on associated SSE connection

## Sequence Number Semantics

### append_seqno in BidiAppendRequest

```javascript
// From Line 439139
this.appendSeqno = Pc.zero  // Initialized to BigInt(0)
```

**Purpose:**
1. **Ordering**: Server reorders out-of-order appends
2. **Deduplication**: Server ignores already-processed seqnos
3. **Loss Detection**: Gaps indicate lost messages

**Type:** `int64` (T: 3 in protobuf schema) - supports very long conversations

### Relationship to Other Sequence Numbers

| Field | Message Type | Direction | Purpose |
|-------|--------------|-----------|---------|
| `append_seqno` | BidiAppendRequest | Client -> Server | Order client chunks |
| `seqno` | IdempotentRequest | Client -> Server | Idempotent chunk ordering |
| `seqno` | BidiPollResponse | Server -> Client | Order server responses |
| `seqno_ack` | IdempotentResponse | Server -> Client | Acknowledge client chunks |

## Poll Mode Alternative

For HTTP/1.0 environments (no SSE support), polling is used instead:

### BidiPollRequest (Line 439202-439236)

```protobuf
message BidiPollRequest {
    BidiRequestId request_id = 1;
    optional bool start_request = 2;  // true to initiate new stream
}
```

### BidiPollResponse (Line 439238-439278)

```protobuf
message BidiPollResponse {
    int64 seqno = 1;       // Sequence number of this response chunk
    string data = 2;        // Serialized server response
    optional bool eof = 3;  // End of stream marker
}
```

### Poll Mode Flow

```
Client                                       Server
   |                                            |
   |---- BidiPollRequest(start=true) ---------->|
   |<--- BidiPollResponse(seqno=0, data=...) ---|
   |                                            |
   |---- BidiAppend(seqno=0, data=...) -------->|
   |<--- BidiAppendResponse (ack) --------------|
   |                                            |
   |---- BidiPollRequest (poll for more) ------>|
   |<--- BidiPollResponse(seqno=1, data=...) ---|
   |                                            |
   |---- BidiPollRequest ---------------------->|
   |<--- BidiPollResponse(eof=true) ------------|
```

## Configuration: HTTP Compatibility Mode

### Setting Keys (Line 268991)

```javascript
Qdt = "cursor.general.disableHttp2"      // Forces HTTP/1.1 mode
dHr = "cursor.general.disableHttp1SSE"   // Forces HTTP/1.0 poll mode
```

### Mode Selection Logic (Line 911769-911793)

```javascript
const mode = !disableHttp2() ? "http2" :
             disableHttp1SSE() ? "http1.0" : "http1.1";
```

| Mode | disableHttp2 | disableHttp1SSE | Transport |
|------|--------------|-----------------|-----------|
| HTTP/2 | false | false | BiDiStreaming |
| HTTP/1.1 | true | false | SSE + BidiAppend |
| HTTP/1.0 | true | true | Poll + BidiAppend |

## Error Handling and Retry

### BidiAppend Failure Handling

Since BidiAppend is a unary call, standard HTTP error handling applies:
- **Timeout**: Retry with same seqno (server deduplicates)
- **Connection Error**: Retry with exponential backoff
- **Server Error (5xx)**: Retry with same seqno
- **Client Error (4xx)**: Do not retry, propagate error

### Session Expiration

If the server closes the SSE connection:
1. Client detects connection loss
2. Client may re-open SSE with same `request_id`
3. Client replays unacknowledged appends (by seqno)

## Implementation Status in Cursor 2.3.41

### Observation: SSE/Poll Endpoints Defined but Rarely Used

The current codebase shows:

1. **Protobuf schemas fully defined** - All message types present
2. **Service endpoints registered** - SSE variants in ChatService and HealthService
3. **Client-side calling code minimal** - Most flows use HTTP/2 BiDiStreaming

### Why?

1. **Modern networks mostly support HTTP/2** - Fallback rarely needed
2. **Idempotent streaming preferred** - `startReliableStream()` handles reconnection
3. **Feature-gated** - `idempotent_agentic_composer` controls stream type
4. **Manual user trigger** - Users must explicitly set HTTP Compatibility Mode

## Reconstructed BidiAppend Usage Pattern

Based on analysis, the intended usage (if implemented) would be:

```javascript
async function sendClientDataInSSEMode(chatClient, bidiClient, requestId, chunks) {
    // Open SSE stream for receiving
    const sseStream = chatClient.streamUnifiedChatWithToolsSSE({
        requestId: requestId
    });

    // Send data via separate append calls
    let seqno = BigInt(0);
    for (const chunk of chunks) {
        await bidiClient.bidiAppend({
            data: chunk.toJsonString(),
            requestId: { requestId: requestId },
            appendSeqno: seqno++
        });
    }

    // Read responses from SSE stream
    for await (const response of sseStream) {
        handleServerResponse(response);
    }
}
```

## Limitations and Trade-offs

### SSE Mode Limitations

| Aspect | HTTP/2 BiDi | SSE + BidiAppend |
|--------|-------------|------------------|
| Latency | Lowest | Higher (separate connections) |
| Connection count | 1 | 2 (SSE + appends) |
| Message ordering | Built-in | Manual via seqno |
| Backpressure | Native gRPC | None |
| Proxy compatibility | Limited | Better |

### Security Considerations

1. **Request ID must be unguessable** - Use cryptographic UUIDs
2. **Server must validate request_id ownership** - Prevent hijacking
3. **Seqno validation** - Reject duplicate or out-of-range values

## Source Code Locations

| Component | File | Lines |
|-----------|------|-------|
| BidiRequestId schema | workbench.desktop.main.js | 439107-439136 |
| BidiAppendRequest schema | workbench.desktop.main.js | 439137-439176 |
| BidiAppendResponse schema | workbench.desktop.main.js | 439177-439201 |
| BidiPollRequest schema | workbench.desktop.main.js | 439202-439236 |
| BidiPollResponse schema | workbench.desktop.main.js | 439238-439278 |
| BidiService definition | workbench.desktop.main.js | 810612-810622 |
| ChatService SSE methods | workbench.desktop.main.js | 466441-466469 |
| HealthService SSE methods | workbench.desktop.main.js | 823820-823831 |
| HTTP mode settings | workbench.desktop.main.js | 450674-450698 |
| Mode selection UI | workbench.desktop.main.js | 911769-911793 |

## Related Analysis Documents

- **TASK-10**: BidiAppend Unary Method Role in SSE/Poll Fallback
- **TASK-9**: BidiService Usage Pattern Analysis
- **TASK-43**: SSE/Poll Fallback Mechanism
- **TASK-84**: Server-Side Idempotent Stream Handling
- **TASK-118**: HTTP/2 Configuration

## Open Questions for Further Investigation

1. **Actual BidiAppend call sites**: Where in extension host is BidiAppend actually invoked?
2. **Server-side session store**: How does server maintain request_id -> SSE connection mapping?
3. **Automatic fallback detection**: Does client auto-detect HTTP/2 failure and switch modes?
4. **Request batching**: Are multiple appends batched into single HTTP request?
5. **Encryption in SSE mode**: How is data field encrypted when using BidiAppend?

## Conclusion

The BidiAppend mechanism provides a robust fallback for environments where HTTP/2 bidirectional streaming is unavailable. By separating the server-to-client (SSE) and client-to-server (unary appends) channels, Cursor maintains functionality in restrictive network environments. The sequence number protocol ensures message ordering and deduplication, while the BidiRequestId links the two channels into a logical session.

However, in Cursor 2.3.41, this mechanism appears to be infrastructure prepared for compatibility rather than actively used in the main code paths, which prefer HTTP/2 BiDiStreaming or the newer idempotent streaming protocol.
