# TASK-43: SSE/Poll Fallback Mechanism Analysis

## Executive Summary

Cursor implements a sophisticated multi-tier protocol fallback system to handle corporate proxies and network environments that don't support modern streaming protocols. The system provides three HTTP compatibility levels: HTTP/2 (optimal), HTTP/1.1 with SSE, and HTTP/1.0 polling.

## Protocol Hierarchy

### 1. HTTP/2 Bidirectional Streaming (Default)
- **Protocol**: HTTP/2 with gRPC-style bidirectional streaming
- **Endpoint**: `StreamUnifiedChatWithTools` (BiDiStreaming)
- **Use Case**: Full-duplex communication, lowest latency
- **Configuration Key**: `cursor.general.disableHttp2`

### 2. HTTP/1.1 Server-Sent Events (SSE)
- **Protocol**: HTTP/1.1 with SSE for server-to-client streaming
- **Endpoint**: `StreamUnifiedChatWithToolsSSE` (ServerStreaming)
- **Input Type**: `BidiRequestId` (jre) - request ID reference
- **Use Case**: When HTTP/2 is blocked but SSE works
- **Configuration Key**: `cursor.general.disableHttp1SSE`

### 3. HTTP/1.0 Long Polling
- **Protocol**: HTTP/1.0 with repeated poll requests
- **Endpoint**: `StreamUnifiedChatWithToolsPoll` (ServerStreaming)
- **Input Type**: `BidiPollRequest` (oxe)
- **Output Type**: `BidiPollResponse` (axe)
- **Use Case**: Most restrictive proxy environments

## Configuration Settings

### Settings Definitions (Line ~450674)
```javascript
// Disable HTTP/2
[Qdt]: {  // "cursor.general.disableHttp2"
    title: "Disable HTTP/2",
    type: "boolean",
    default: false,
    description: "Disable HTTP/2 for all requests, and use HTTP/1.1 instead.
                  This increases resource utilization and latency, but is useful
                  if you're behind a corporate proxy that blocks HTTP/2.",
    policy: {
        name: "NetworkDisableHttp2",
        minimumVersion: "1.99"
    }
}

// Disable HTTP/1.1 SSE
[dHr]: {  // "cursor.general.disableHttp1SSE"
    title: "Disable HTTP/1.1 SSE",
    type: "boolean",
    default: false,
    description: "Disable HTTP/1.1 SSE for agent chat. This increases resource
                  utilization and latency, but is useful if you're behind a
                  corporate proxy that does not support HTTP/1.1 SSE streaming responses."
}
```

### HTTP Compatibility Mode UI (Line ~911766)
```javascript
{
    label: "HTTP Compatibility Mode",
    description: "HTTP/2 is recommended for low-latency streaming. In some
                  corporate proxy and VPN environments, the compatibility
                  mode may need to be lowered.",
    value: !disableHttp2 ? "http2" :
           disableHttp1SSE ? "http1.0" : "http1.1",
    items: [
        { id: "http2",  label: "HTTP/2" },
        { id: "http1.1", label: "HTTP/1.1" },
        { id: "http1.0", label: "HTTP/1.0" }
    ],
    onChange: mode => {
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

## Server-Side Protocol Control

### Http2Config Enum (Line ~826343)
```javascript
nbt = {
    UNSPECIFIED: 0,           // "HTTP2_CONFIG_UNSPECIFIED"
    FORCE_ALL_DISABLED: 1,    // "HTTP2_CONFIG_FORCE_ALL_DISABLED"
    FORCE_ALL_ENABLED: 2,     // "HTTP2_CONFIG_FORCE_ALL_ENABLED"
    FORCE_BIDI_DISABLED: 3,   // "HTTP2_CONFIG_FORCE_BIDI_DISABLED"
    FORCE_BIDI_ENABLED: 4     // "HTTP2_CONFIG_FORCE_BIDI_ENABLED"
}
```

### Server Config Integration
```javascript
// ServerConfig includes http2Config field (Line ~827787)
{
    http2Config: nbt.UNSPECIFIED,
    // ... other config
}
```

## Network Diagnostics (Line ~911500)

### Streaming Test Logic
```javascript
// SSE endpoint selection based on settings
const endpointName = disableHttp2() ? "streamSSE" : "stream";

// Stream validation (Line ~911708)
const result = chunkCount < 5
    ? new Error(`Incomplete response (${chunkCount}/${times.length} valid chunks)`)
    : times[0] > 2000
        ? new Error("Streaming responses are being buffered by a proxy in your network environment")
        : true;
```

### Bidirectional Stream Test (Line ~911746)
```javascript
const result =
    chunkCount == 0 || times.length == 0 || (chunkCount > 1 && chunkCount < 5)
        ? new Error(`Incomplete response (${chunkCount}/${times.length} valid chunks)`)
        : chunkCount == 1 || times[0] > 2000
            ? new Error(
                disableHttp2()
                    ? "HTTP/1.1 SSE responses are being buffered by a proxy in your network environment"
                    : "Bidirectional streaming is not supported by the http2 proxy in your network environment"
              )
            : true;
```

### Diagnostic Tests Run
1. **DNS Lookup** - Multiple sources (nodejs, system)
2. **HTTP/2 Ping** - Protocol negotiation check
3. **TLS** - Certificate validation
4. **Unary RPC** - Basic request/response
5. **Ping** - Simple latency test
6. **Stream** - Server-streaming validation
7. **Bidi** - Bidirectional streaming validation
8. **Marketplace** - Extension marketplace connectivity

## Protobuf Schemas

### BidiRequestId (Line ~439107)
```protobuf
message BidiRequestId {
    string request_id = 1;
}
```

### BidiPollRequest (Line ~439202)
```protobuf
message BidiPollRequest {
    BidiRequestId request_id = 1;
    optional bool start_request = 2;
}
```

### BidiPollResponse (Line ~439238)
```protobuf
message BidiPollResponse {
    int64 seqno = 1;
    string data = 2;
    optional bool eof = 3;
}
```

## Service Endpoint Matrix

### ChatService (Line ~466426)
| Method | Input | Output | Kind |
|--------|-------|--------|------|
| StreamUnifiedChatWithTools | Hlt (request) | yJ | BiDiStreaming |
| StreamUnifiedChatWithToolsSSE | jre (BidiRequestId) | yJ | ServerStreaming |
| StreamUnifiedChatWithToolsPoll | oxe (BidiPollRequest) | axe (BidiPollResponse) | ServerStreaming |
| StreamUnifiedChatWithToolsIdempotent | oNe | OPr | BiDiStreaming |
| StreamUnifiedChatWithToolsIdempotentSSE | jre (BidiRequestId) | OPr | ServerStreaming |
| StreamUnifiedChatWithToolsIdempotentPoll | oxe (BidiPollRequest) | axe (BidiPollResponse) | ServerStreaming |

### HealthService (Line ~823808)
| Method | Input | Output | Kind |
|--------|-------|--------|------|
| stream | L2s | ibt | ServerStreaming |
| streamSSE | L2s | ibt | ServerStreaming |
| streamBidi | L2s | ibt | BiDiStreaming |
| streamBidiSSE | jre (BidiRequestId) | ibt | ServerStreaming |
| streamBidiPoll | oxe (BidiPollRequest) | axe (BidiPollResponse) | ServerStreaming |

## Proxy Detection Logic

### Buffering Detection
The system detects proxy buffering by measuring response timing:
- **Threshold**: First chunk > 2000ms indicates buffering
- **Chunk Count**: Incomplete responses (1-4 chunks) indicate connectivity issues
- **Error Messages**: Specific messages for HTTP/2 vs SSE issues

### Automatic Fallback
While the settings are manual, the diagnostics provide clear guidance:
1. Run network diagnostics
2. Identify which protocol tier fails
3. User adjusts HTTP Compatibility Mode accordingly

## Degraded Mode

### Idempotent Stream Degraded Mode (Line ~488871)
```javascript
if (response.value.isDegradedMode === true) {
    isDegraded = true;
    console.warn("[composer] Idempotent streaming is in degraded mode - reconnection not available");
    this._composerDataService.updateComposerData(composerId, {
        idempotentStreamState: undefined
    });
}
```

## Key Source Locations

| Component | Line Range | Description |
|-----------|------------|-------------|
| Settings Definitions | 450674-450698 | HTTP/2 and SSE disable settings |
| Http2Config Enum | 826343-826361 | Server-side protocol control enum |
| ChatService Endpoints | 466426-466470 | SSE/Poll endpoint definitions |
| HealthService Endpoints | 823808-823831 | Diagnostic endpoint definitions |
| Network Diagnostics UI | 911500-911800 | Diagnostic test implementations |
| BidiPoll Protobuf | 439107-439278 | Polling protocol buffers |

## Implementation Notes

### Client-Side Selection
```javascript
// Protocol selection in stream call (Line ~911694)
const methodName = disableHttp2() ? "streamSSE" : "stream";
const response = await client[methodName]({ payload: "foo" });
```

### Idempotent Streaming
The idempotent variants (StreamUnifiedChatWithToolsIdempotent*) support:
- Stream resumption on reconnection
- Sequence number tracking
- Encryption key management
- Degraded mode detection

## Reliable Stream Implementation (Updated)

### startReliableStream Method (Line ~488771)

The reliable stream provides idempotent streaming with automatic recovery:

```javascript
async * startReliableStream(e, t, n, s, r, o, a) {
    const l = this._experimentService.checkFeatureGate("persist_idempotent_stream_state");
    const d = o?.idempotencyKey ?? es();  // UUID generation
    const h = o?.idempotentEncryptionKey ?? (() => {
        const E = new Uint8Array(32);
        crypto.getRandomValues(E);
        return yO(Vs.wrap(E), !1, !0);  // Base64 encode
    })();
    let f = o?.idempotencyEventId ?? "0";
    let g = {
        playbackChunks: o?.playbackChunks ?? new Map,
        internalAsyncPushable: new l$(void 0)
    };
    let p = !1;
    let w = o?.nextSeqno ?? 0;
    // ... stream implementation
}
```

### Idempotent Stream Headers

Key headers sent with idempotent requests (Line ~488860-488866):
```javascript
headers: {
    ...n,
    "x-idempotency-key": d,         // Unique stream identifier
    "x-idempotency-event-id": f,    // Event position for resume
    "x-idempotent-encryption-key": h // Stream encryption key
}
```

### Stream State Persistence (Line ~488785-488792)

```javascript
idempotentStreamState: {
    idempotencyKey: d,
    idempotencyEventId: "0",
    idempotentEncryptionKey: h,
    nextSeqno: 0,
    playbackChunks: []
}
```

### Sequence Acknowledgment (Line ~488878-488889)

```javascript
if (M.response.case === "seqnoAck") {
    g.playbackChunks.delete(M.response.value);
    const B = this._composerDataService.getComposerData(r);
    if (B?.idempotentStreamState && l) {
        const H = B.idempotentStreamState;
        const J = M.response.value;
        this._composerDataService.updateComposerData(r, {
            idempotentStreamState: {
                ...H,
                playbackChunks: H.playbackChunks.filter(([G]) => G !== J)
            }
        });
    }
}
```

### Reconnection Logic (Line ~488954-488960)

```javascript
this._composerDataService.updateComposerData(r, {
    isReconnecting: !0
});
await new Promise(A => setTimeout(A, 1e3));  // 1 second delay before retry
```

## Auto-Resume Mechanism (Line ~945194)

```javascript
async _autoResumeInterruptedStreams() {
    const e = this.experimentService.getDynamicConfigParam(
        "idempotent_stream_config",
        "retry_lookback_window_ms"
    ) ?? 72e5;  // 7200000ms = 2 hours default

    const t = Date.now();
    const n = this.composerDataService.allComposersData.allComposers;

    for (const s of n) {
        const o = s.lastUpdatedAt ?? s.createdAt;
        if (t - o > e) continue;  // Skip streams outside lookback window

        const a = await this.composerDataService.getComposerHandleById(s.composerId);
        if (!a || !a.data.idempotentStreamState) continue;
        // Attempt to resume stream...
    }
}
```

## Feature Gate Control

### Idempotent Streaming Feature Gates (Line ~294165-294172)

```javascript
idempotent_agentic_composer: {
    client: !0,
    default: !1  // Disabled by default
},
persist_idempotent_stream_state: {
    client: !0,
    default: !1  // Disabled by default
}
```

### Decision Point (Line ~490175-490189)

```javascript
const qm = this._experimentService.checkFeatureGate("idempotent_agentic_composer");
const MT = qm
    ? this.startReliableStream(rm, uu, hb, wn.signal, e, ke, ks)
    : rm.streamUnifiedChatWithTools(uu, {
        signal: wn.signal,
        headers: hb,
        onHeader: ks
    });
```

## BidiAppend Service (Line ~810613-810621)

For sending client data in SSE mode:

```javascript
// BidiService definition
{
    typeName: "aiserver.v1.BidiService",
    methods: {
        bidiAppend: {
            name: "BidiAppend",
            I: CLc,  // BidiAppendRequest
            O: kLc,  // BidiAppendResponse
            kind: Kt.Unary
        }
    }
}
```

### BidiAppendRequest (Line ~439137-439176)

```protobuf
message BidiAppendRequest {
    string data = 1;              // Data to append
    BidiRequestId request_id = 2; // Stream reference
    int64 append_seqno = 3;       // Sequence number
}
```

## Dynamic Configuration

### idempotent_stream_config (Line ~295499-295503)

```javascript
idempotent_stream_config: {
    client: !0,
    fallbackValues: {
        retry_lookback_window_ms: 7200 * 1e3  // 2 hours
    }
}
```

### reliable_stream_fault_injection (Line ~295417-295423)

Testing configuration for fault injection:
```javascript
reliable_stream_fault_injection: {
    client: !0,
    fallbackValues: {
        enabled: !1,
        baseIntervalMs: 1e3,
        exponentialFactor: .05
    }
}
```

## WelcomeMessage Proto (Line ~122227-122260)

Server signals degraded mode:

```protobuf
message WelcomeMessage {
    string message = 1;
    bool is_degraded_mode = 2;
}
```

## Recommendations for Further Investigation

1. **TASK: Investigate BidiAppend mechanism** - How client data is sent in SSE mode via unary BidiAppend calls
2. **TASK: Map server-side Http2Config enforcement** - How server config overrides client preferences
3. **TASK: Analyze polling backoff strategy** - Poll interval configuration and adaptive delays
4. **TASK: Document keepalive configurations** - http1_keepalive_config and http2_ping_config impact
5. **TASK: Analyze encryption key exchange** - How idempotent encryption keys are negotiated and rotated

## Conclusion

Cursor's fallback mechanism is a well-designed tiered system that:
1. Defaults to optimal HTTP/2 bidirectional streaming
2. Falls back to HTTP/1.1 SSE when HTTP/2 fails
3. Uses long polling as a last resort for restrictive environments
4. Provides clear diagnostics for users to identify issues
5. Supports server-side protocol enforcement via Http2Config
6. Implements idempotent streaming with automatic recovery (feature-gated)
7. Persists stream state for 2-hour lookback window for resume capability
8. Uses sequence numbers for message ordering and acknowledgment
