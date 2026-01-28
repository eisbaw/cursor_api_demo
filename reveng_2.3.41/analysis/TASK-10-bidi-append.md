# TASK-10: BidiService.BidiAppend Unary Method Role in SSE/Poll Fallback

## Executive Summary

The `BidiAppend` unary method in `BidiService` provides a mechanism for clients to send messages to the server when true bidirectional streaming is unavailable. Combined with `StreamBidiSSE` and `StreamBidiPoll` methods, this enables Cursor to function in restrictive network environments (corporate proxies, VPNs) that don't support HTTP/2 or gRPC bidirectional streaming.

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
            kind: Kt.Unary  // UNARY method, not streaming
        }
    }
}
```

## Message Types

### BidiRequestId (Line 439115)
```protobuf
message BidiRequestId {
    string request_id = 1;  // Session identifier linking requests
}
```

### BidiAppendRequest (Line 439145)
```protobuf
message BidiAppendRequest {
    string data = 1;              // Serialized payload to append
    BidiRequestId request_id = 2; // Links to existing session
    int64 append_seqno = 3;       // Sequence number for ordering
}
```

### BidiAppendResponse (Line 439185)
```protobuf
message BidiAppendResponse {
    // Empty - acknowledgment only
}
```

### BidiPollRequest (Line 439210)
```protobuf
message BidiPollRequest {
    BidiRequestId request_id = 1;
    optional bool start_request = 2;  // True to initiate a new stream
}
```

### BidiPollResponse (Line 439246)
```protobuf
message BidiPollResponse {
    int64 seqno = 1;       // Sequence number of this response
    string data = 2;        // Serialized response payload
    optional bool eof = 3;  // End of stream marker
}
```

## Fallback Architecture Overview

### Transport Modes

| Mode | Protocol | Bidi Support | Use Case |
|------|----------|--------------|----------|
| HTTP/2 | gRPC | Full BiDiStreaming | Default, best performance |
| HTTP/1.1 | SSE | Server-only streaming | Proxies that block HTTP/2 |
| HTTP/1.0 | Polling | No streaming | Most restrictive environments |

### Method Mapping by Mode

| Mode | Client-to-Server | Server-to-Client |
|------|------------------|------------------|
| HTTP/2 | `StreamBidi` (BiDiStreaming) | Same bidirectional stream |
| HTTP/1.1 SSE | `BidiAppend` (Unary) | `StreamBidiSSE` (ServerStreaming) |
| HTTP/1.0 Poll | `BidiAppend` (Unary) | `StreamBidiPoll` (ServerStreaming) |

## HealthService Fallback Methods

**Location:** Line 823787-823832

The HealthService demonstrates the complete fallback pattern:

```javascript
{
    typeName: "aiserver.v1.HealthService",
    methods: {
        // True bidirectional (HTTP/2 only)
        streamBidi: {
            name: "StreamBidi",
            kind: Kt.BiDiStreaming
        },
        // SSE fallback (HTTP/1.1)
        streamBidiSSE: {
            name: "StreamBidiSSE",
            I: jre,  // BidiRequestId only (no payload in initial request)
            O: ibt,  // Standard response
            kind: Kt.ServerStreaming
        },
        // Polling fallback (HTTP/1.0)
        streamBidiPoll: {
            name: "StreamBidiPoll",
            I: oxe,  // BidiPollRequest
            O: axe,  // BidiPollResponse
            kind: Kt.ServerStreaming
        }
    }
}
```

## ChatService Fallback Methods

**Location:** Line 466426-466507

```javascript
{
    typeName: "aiserver.v1.ChatService",
    methods: {
        // Full bidi with tools (HTTP/2)
        streamUnifiedChatWithTools: {
            kind: Kt.BiDiStreaming
        },
        // SSE fallback
        streamUnifiedChatWithToolsSSE: {
            name: "StreamUnifiedChatWithToolsSSE",
            I: jre,  // BidiRequestId
            O: yJ,   // StreamUnifiedChatResponseWithTools
            kind: Kt.ServerStreaming
        },
        // Poll fallback
        streamUnifiedChatWithToolsPoll: {
            name: "StreamUnifiedChatWithToolsPoll",
            I: oxe,  // BidiPollRequest
            O: axe,  // BidiPollResponse
            kind: Kt.ServerStreaming
        },
        // Idempotent versions also exist for each
        streamUnifiedChatWithToolsIdempotent: { ... },
        streamUnifiedChatWithToolsIdempotentSSE: { ... },
        streamUnifiedChatWithToolsIdempotentPoll: { ... }
    }
}
```

## Configuration Settings

### Setting Keys (Line 268991)

```javascript
Qdt = "cursor.general.disableHttp2"      // Forces HTTP/1.1 mode
dHr = "cursor.general.disableHttp1SSE"   // Forces HTTP/1.0 polling mode
```

### Setting Descriptions (Lines 450674-450698)

```javascript
{
    "cursor.general.disableHttp2": {
        title: "Disable HTTP/2",
        type: "boolean",
        default: false,
        description: "Disable HTTP/2 for all requests, and use HTTP/1.1 instead.
                      This increases resource utilization and latency, but is useful
                      if you're behind a corporate proxy that blocks HTTP/2."
    },
    "cursor.general.disableHttp1SSE": {
        title: "Disable HTTP/1.1 SSE",
        type: "boolean",
        default: false,
        description: "Disable HTTP/1.1 SSE for agent chat. This increases resource
                      utilization and latency, but is useful if you're behind a
                      corporate proxy that does not support HTTP/1.1 SSE streaming
                      responses."
    }
}
```

## Fallback Trigger Conditions

### Network Diagnostics Panel (Line 911491-911870)

The Settings > Network panel provides diagnostics that help identify needed fallbacks:

```javascript
function Mmu() {
    const [disableHttp2, setDisableHttp2] = H3("cursor.general.disableHttp2", ...);
    const [disableHttp1SSE, setDisableHttp1SSE] = H3("cursor.general.disableHttp1SSE", ...);

    // HTTP Compatibility Mode UI
    // http2: disableHttp2=false
    // http1.1: disableHttp2=true, disableHttp1SSE=false
    // http1.0: disableHttp2=true, disableHttp1SSE=true
}
```

### Mode Selection Logic (Lines 911769-911793)

```javascript
{
    label: "HTTP Compatibility Mode",
    description: "HTTP/2 is recommended for low-latency streaming.
                  In some corporate proxy and VPN environments,
                  the compatibility mode may need to be lowered.",
    value: !disableHttp2() ? "http2" : disableHttp1SSE() ? "http1.0" : "http1.1",
    items: [
        { id: "http2", label: "HTTP/2" },
        { id: "http1.1", label: "HTTP/1.1" },
        { id: "http1.0", label: "HTTP/1.0" }
    ],
    onChange: (mode) => {
        switch (mode) {
            case "http2":
                setDisableHttp2(false);
                setDisableHttp1SSE(false);
                break;
            case "http1.1":
                setDisableHttp2(true);
                setDisableHttp1SSE(false);
                break;
            case "http1.0":
                setDisableHttp2(true);
                setDisableHttp1SSE(true);
                break;
        }
    }
}
```

### Stream Method Selection (Line 911694)

```javascript
// In network diagnostics stream test
const streamMethod = disableHttp2() ? "streamSSE" : "stream";
const response = await healthClient[streamMethod]({ payload: "foo" });
```

### Bidi Stream Error Detection (Line 911746)

```javascript
// Error messages help users identify the right mode
const error = disableHttp2()
    ? "HTTP/1.1 SSE responses are being buffered by a proxy in your network environment"
    : "Bidirectional streaming is not supported by the http2 proxy in your network environment";
```

## Server-Side Http2Config

**Location:** Line 826343-826361

The server can also enforce transport mode via configuration:

```javascript
(function(Http2Config) {
    Http2Config[Http2Config.UNSPECIFIED = 0] = "UNSPECIFIED";
    Http2Config[Http2Config.FORCE_ALL_DISABLED = 1] = "FORCE_ALL_DISABLED";
    Http2Config[Http2Config.FORCE_ALL_ENABLED = 2] = "FORCE_ALL_ENABLED";
    Http2Config[Http2Config.FORCE_BIDI_DISABLED = 3] = "FORCE_BIDI_DISABLED";
    Http2Config[Http2Config.FORCE_BIDI_ENABLED = 4] = "FORCE_BIDI_ENABLED";
})(Http2Config || (Http2Config = {}));
```

This allows server-controlled fallback when needed.

## SSE/Poll Fallback Flow

### SSE Mode (HTTP/1.1)

1. Client sends initial request with `BidiRequestId` to `StreamBidiSSE`
2. Server opens SSE connection, streams responses
3. Client sends messages via `BidiAppend` unary calls with same `request_id`
4. Server correlates by `request_id` and includes in ongoing stream
5. Sequence numbers (`append_seqno`) ensure ordering

### Poll Mode (HTTP/1.0)

1. Client sends `BidiPollRequest` with `start_request=true` to initiate
2. Server creates session with `request_id`
3. Client repeatedly polls `StreamBidiPoll` for responses
4. Client sends messages via `BidiAppend` unary calls
5. `BidiPollResponse.eof=true` signals stream end

## BidiAppend Usage Pattern

```javascript
// Pseudo-code for SSE/Poll client sending a message
async function sendClientMessage(requestId, data, seqno) {
    await bidiService.bidiAppend({
        requestId: { requestId: requestId },
        data: serializeToString(data),
        appendSeqno: seqno
    });
    // Empty response = acknowledgment
}
```

## Observations and Limitations

### Current Implementation Status

1. **Defined but rarely used**: The SSE and Poll fallback methods are defined in the protobuf schemas but actual client-side calling code appears minimal in the current codebase.

2. **Idempotent streams preferred**: Modern agent workflow uses `startReliableStream` with idempotent protocol (`streamUnifiedChatWithToolsIdempotent`) which has its own reconnection/replay mechanism.

3. **Feature gate controlled**: The `idempotent_agentic_composer` feature gate controls whether idempotent streaming is used.

### Sequence Number Semantics

- `append_seqno` in BidiAppendRequest: Client-assigned, monotonically increasing
- `seqno` in BidiPollResponse: Server-assigned, tracks response order
- Enables out-of-order handling and duplicate detection

### Trade-offs

| Mode | Latency | Resource Use | Reliability |
|------|---------|--------------|-------------|
| HTTP/2 Bidi | Lowest | Lowest | Reconnect may lose state |
| SSE + Append | Medium | Medium | Server maintains state |
| Poll + Append | Highest | Highest | Most compatible |

## Related Files

- Proto definitions: `out-build/proto/aiserver/v1/bidi_pb.js`
- Chat service: `out-build/proto/aiserver/v1/chat_connectweb.js`
- Health service: Inline at Line 823787
- Settings config: Line 450665

## Further Investigation Tasks

1. **Actual BidiAppend call sites**: Search for where BidiAppend is actually called in extension host
2. **Server-side correlation**: How server correlates Append messages with SSE/Poll streams
3. **Automatic fallback detection**: Whether client auto-detects need for fallback
4. **Performance metrics**: Latency impact measurements for each mode
