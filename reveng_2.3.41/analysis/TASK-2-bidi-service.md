# TASK-2: BidiService Bidirectional Streaming Protocol Analysis

## Overview

The `aiserver.v1.BidiService` is a gRPC service that provides bidirectional streaming capabilities for Cursor's agent workflow. However, contrary to what its name suggests, the BidiService itself only exposes a single **Unary** method. The actual bidirectional streaming is implemented through the `ChatService` methods.

## BidiService Definition

**Location:** Line 810612-810622 in `workbench.desktop.main.js`

```javascript
{
    typeName: "aiserver.v1.BidiService",
    methods: {
        bidiAppend: {
            name: "BidiAppend",
            I: CLc,  // BidiAppendRequest
            O: kLc,  // BidiAppendResponse
            kind: Kt.Unary  // Note: This is Unary, not BiDiStreaming
        }
    }
}
```

## Message Types

### BidiRequestId (Line 439115)
```protobuf
message BidiRequestId {
    string request_id = 1;  // Unique identifier for a bidi session
}
```

### BidiAppendRequest (Line 439145)
```protobuf
message BidiAppendRequest {
    string data = 1;           // Payload data to append
    BidiRequestId request_id = 2;  // Links to session
    int64 append_seqno = 3;    // Sequence number for ordering
}
```

### BidiAppendResponse (Line 439185)
```protobuf
message BidiAppendResponse {
    // Empty response - acknowledgment only
}
```

### BidiPollRequest (Line 439210)
```protobuf
message BidiPollRequest {
    BidiRequestId request_id = 1;
    optional bool start_request = 2;
}
```

### BidiPollResponse (Line 439246)
```protobuf
message BidiPollResponse {
    int64 seqno = 1;      // Sequence number
    string data = 2;       // Response payload
    optional bool eof = 3; // End of stream marker
}
```

## ChatService Bidirectional Methods

The actual bidirectional streaming for agent communication happens through ChatService (Line 466426-466507):

### Method Types (Kt Enum)
- `Kt.Unary = 0` - Single request/response
- `Kt.ServerStreaming = 1` - Server streams responses
- `Kt.ClientStreaming = 2` - Client streams requests
- `Kt.BiDiStreaming = 3` - Both sides stream

### Bidirectional Methods

1. **StreamUnifiedChatWithTools** (`Kt.BiDiStreaming`)
   - Input: `StreamUnifiedChatRequestWithTools`
   - Output: `StreamUnifiedChatResponseWithTools`
   - Basic bidirectional streaming for tool-calling

2. **StreamUnifiedChatWithToolsIdempotent** (`Kt.BiDiStreaming`)
   - Input: `StreamUnifiedChatRequestWithToolsIdempotent`
   - Output: `StreamUnifiedChatResponseWithToolsIdempotent`
   - Idempotent version with reconnection support

### Fallback Methods (Server Streaming only)

3. **StreamUnifiedChatWithToolsSSE** (`Kt.ServerStreaming`)
   - Input: `BidiRequestId`
   - Output: `StreamUnifiedChatResponseWithTools`
   - SSE fallback when WebSocket bidi unavailable

4. **StreamUnifiedChatWithToolsPoll** (`Kt.ServerStreaming`)
   - Input: `BidiPollRequest`
   - Output: `BidiPollResponse`
   - Polling fallback for environments that don't support streaming

5. **StreamUnifiedChatWithToolsIdempotentSSE** (`Kt.ServerStreaming`)
   - Idempotent SSE version

6. **StreamUnifiedChatWithToolsIdempotentPoll** (`Kt.ServerStreaming`)
   - Idempotent polling version

## Bidirectional Request/Response Protocol

### StreamUnifiedChatRequestWithTools (Line 121955)
```protobuf
message StreamUnifiedChatRequestWithTools {
    oneof request {
        StreamUnifiedChatRequest stream_unified_chat_request = 1;
        ClientSideToolV2Result client_side_tool_v2_result = 2;
    }
}
```

### StreamUnifiedChatResponseWithTools (Line 122102)
```protobuf
message StreamUnifiedChatResponseWithTools {
    oneof response {
        ClientSideToolV2Call client_side_tool_v2_call = 1;
        StreamUnifiedChatResponse stream_unified_chat_response = 2;
        ConversationSummary conversation_summary = 3;
        UserRules user_rules = 4;
        StreamStart stream_start = 5;
    }
    optional SpanContext tracing_context = 6;
    string event_id = 7;
}
```

### Idempotent Request Wrapper (Line 122170)
```protobuf
message StreamUnifiedChatRequestWithToolsIdempotent {
    oneof request {
        StreamUnifiedChatRequestWithTools client_chunk = 1;
        Empty abort = 2;
        Empty close = 3;
    }
    optional string idempotency_key = 4;
    optional uint32 seqno = 5;
}
```

### Idempotent Response Wrapper (Line 122262)
```protobuf
message StreamUnifiedChatResponseWithToolsIdempotent {
    oneof response {
        StreamUnifiedChatResponseWithTools server_chunk = 1;
        WelcomeMessage welcome_message = 3;
        uint32 seqno_ack = 4;
    }
}
```

## Handshake/Connection Protocol

### Idempotent Stream Initialization (Line 488771-488839)

1. **Key Generation:**
   - `idempotencyKey`: UUID for session identification
   - `idempotentEncryptionKey`: 32-byte random key for encryption
   - `idempotencyEventId`: Starting event ID (defaults to "0")
   - `nextSeqno`: Sequence counter starting at 0

2. **HTTP Headers:**
   ```
   x-idempotency-key: <uuid>
   x-idempotency-event-id: <event_id>
   x-idempotent-encryption-key: <base64_key>
   ```

3. **Connection Setup:**
   - Client wraps messages in `StreamUnifiedChatRequestWithToolsIdempotent` with seqno
   - Each chunk is stored in `playbackChunks` for potential replay
   - Client can send `abort` or `close` messages to end stream

### Welcome Message Handling (Line 488870-488876)

Upon connection, server sends `WelcomeMessage`:
```protobuf
message WelcomeMessage {
    string message = 1;
    bool is_degraded_mode = 2;
}
```

- `isDegradedMode = true`: Reconnection not available, no retry on failure
- `isDegradedMode = false`: Full reconnection support active

### Sequence Number Acknowledgment

Server sends `seqno_ack` to confirm receipt of client chunks:
- Client removes acknowledged chunks from `playbackChunks`
- Enables memory cleanup and state persistence

## Reconnection Logic (Line 488841-488960)

1. **Retry Loop:**
   - On disconnection, client retries connection
   - Replay all unacknowledged chunks from `playbackChunks`
   - Resume from last `idempotencyEventId`

2. **Abort Handling:**
   - On outer abort signal, send abort message before closing
   - Separate abort message with same idempotency key

3. **Degraded Mode:**
   - When server indicates degraded mode, disable retry
   - Clear `idempotentStreamState` from composer data

## Agent Workflow Integration

### Tool-Wrapped Stream (Line 484523-485007)

The `toolWrappedStream` method orchestrates the bidirectional protocol:

1. **Incoming Stream Processing:**
   - Server sends `ClientSideToolV2Call` messages
   - Client executes tools locally
   - Client sends `ClientSideToolV2Result` back through bidi stream

2. **Tool Call Flow:**
   ```
   Server -> ClientSideToolV2Call (tool request)
   Client: Execute tool
   Client -> ClientSideToolV2Result (tool result) via Hlt.request.clientSideToolV2Result
   ```

3. **Streaming vs Non-Streaming Tools:**
   - Streaming tools: Multiple partial messages before final result
   - Non-streaming tools: Single execution and result

### Feature Flag Control (Line 490175)

```javascript
const qm = this._experimentService.checkFeatureGate("idempotent_agentic_composer");
// If enabled: use startReliableStream with idempotent protocol
// If disabled: use plain streamUnifiedChatWithTools
```

## Comparison with Older ChatService

### Old: StreamUnifiedChat
- `Kt.ServerStreaming` only
- No tool calling
- One-way stream from server

### Current: StreamUnifiedChatWithTools
- `Kt.BiDiStreaming`
- Full tool calling support
- Client sends tool results back
- No built-in reconnection

### Current: StreamUnifiedChatWithToolsIdempotent
- `Kt.BiDiStreaming`
- Idempotent operations
- Reconnection support via playback
- Sequence number tracking
- Event ID checkpointing

## TestBidi Service

A test service exists (Line 440200-440204):
```javascript
{
    testBidi: {
        name: "TestBidi",
        I: TestBidiRequest,   // { message: string }
        O: TestBidiResponse,  // { message: string }
        kind: Kt.BiDiStreaming
    }
}
```

Used for testing bidirectional streaming infrastructure.

## Further Investigation Needed

1. **BidiService.BidiAppend actual usage:** The Unary BidiAppend method's role in the SSE/Poll fallback mechanisms
2. **Encryption key usage:** How the `idempotent-encryption-key` header is used for payload encryption
3. **Server-side implementation:** How the server handles idempotency and state persistence
4. **Rate limiting/backpressure:** How sequence numbers relate to flow control

## Key File Locations

- Proto definitions: `out-build/proto/aiserver/v1/bidi_pb.js` (Line 439105)
- Chat service proto: `out-build/proto/aiserver/v1/chat_connectweb.js` (Line 466424)
- Reliable stream implementation: `composerChatService.js` (Line 488771)
- Tool handling: `ToolV2Service` (Line 484523)
