# TASK-67: Automatic HTTP Fallback Detection Logic

## Executive Summary

Cursor IDE implements a **manual HTTP fallback system** rather than automatic protocol detection and fallback. Users must manually configure HTTP compatibility mode based on network diagnostic results. The system provides three protocol tiers (HTTP/2, HTTP/1.1 SSE, HTTP/1.0 polling) with comprehensive diagnostics to help users identify which tier works in their environment.

Notably, while connection errors trigger automatic **stream resumption**, they do not trigger automatic **protocol downgrade**. The Http2Config enum received from the server allows server-side protocol enforcement, but active client-side enforcement logic was not found in the analyzed code.

## Key Finding: No Automatic Protocol Fallback

Based on code analysis, Cursor **does NOT** automatically detect and switch HTTP protocols. Instead:

1. **User-Configured**: Protocol selection via Settings > Network > HTTP Compatibility Mode
2. **Diagnostic-Guided**: Network diagnostics help users identify issues
3. **Server-Overridable**: Server can potentially force protocol via Http2Config (infrastructure exists but may not be actively used)

## Configuration Settings

### Client-Side Settings (Lines 268991, 450674-450697)

```javascript
// Configuration key constants
Qdt = "cursor.general.disableHttp2"       // Disable HTTP/2 entirely
dHr = "cursor.general.disableHttp1SSE"    // Disable SSE fallback (forces polling)

// Settings schema
{
    "cursor.general.disableHttp2": {
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
    },
    "cursor.general.disableHttp1SSE": {
        title: "Disable HTTP/1.1 SSE",
        type: "boolean",
        default: false,
        description: "Disable HTTP/1.1 SSE for agent chat. This increases resource
                     utilization and latency, but is useful if you're behind a
                     corporate proxy that does not support HTTP/1.1 SSE streaming responses."
    }
}
```

### Protocol Selection Logic (Line 911768-911791)

```javascript
// HTTP Compatibility Mode value calculation
get value() {
    // If HTTP/2 is NOT disabled -> "http2"
    // If HTTP/2 disabled AND SSE disabled -> "http1.0"
    // If HTTP/2 disabled but SSE enabled -> "http1.1"
    return !disableHttp2() ? "http2"
         : disableHttp1SSE() ? "http1.0"
         : "http1.1";
}

// Mode change handler
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
```

## Network Capability Detection

### Network Diagnostics Panel (Lines 911491-911757)

The `Mmu()` function implements comprehensive network diagnostics:

```javascript
function Mmu() {
    // Configuration state bound to settings
    const [disableHttp2, setDisableHttp2] = H3(Qdt, configService, false);
    const [disableHttp1SSE, setDisableHttp1SSE] = H3(dHr, configService, false);

    // Diagnostic result state
    const [results, setResults] = Be({
        dns: undefined,
        http2: undefined,
        tls: undefined,
        unary: undefined,
        ping: undefined,
        stream: undefined,
        bidi: undefined,
        marketplace: undefined
    });

    // Run all diagnostics
    const runDiagnostics = () => {
        Promise.all([
            runDNS(),
            disableHttp2() ? Promise.resolve() : runHttp2Ping(),
            runTLS(),
            runMarketplace(),
            runUnary(),
            runPing(),
            runStream(),
            runBidi()
        ]);
    };
}
```

### Diagnostic Test Details

#### 1. DNS Lookup Test (Lines 911534-911555)
```javascript
// Tests DNS resolution with multiple resolver sources
for (const source of ["nodejs", "system"]) {
    for (let attempt = 0; attempt < 4; attempt++) {
        const result = await everythingProvider.runCommand(
            "connectDebug.dnsLookup",
            { source }
        );
        // Checks: response exists, no error, resolution time < 1500ms
    }
}
```

#### 2. HTTP/2 Protocol Test (Lines 911556-911581)
```javascript
const runHttp2Ping = async () => {
    const result = await everythingProvider.runCommand(
        "connectDebug.http2Ping",  // HUt.Http2Ping
        {}
    );

    // Check negotiated protocol
    const success = result.protocol === "h2"  // HTTP/2
        ? true
        : new Error(`Unexpected protocol: ${result.protocol}`);
};
```

#### 3. TLS Certificate Test (Lines 911582-911614)
```javascript
const runTLS = async () => {
    const result = await provider.runCommand("connectDebug.inspectTLSInfo", {});

    // Validates certificate issuer
    const issuer = result.issuer.toString();
    const success = issuer.includes("Google Trust Services") ||
                   issuer.includes("Amazon RSA")
        ? true
        : new Warning(`Encrypted traffic is being intercepted by
                       unrecognized certificate: ${issuer}`);
};
```

#### 4. Server-Streaming Test (Lines 911687-911717)
```javascript
const runStream = async () => {
    // Selects endpoint based on HTTP/2 setting
    const methodName = disableHttp2() ? "streamSSE" : "stream";
    const response = await healthClient[methodName]({ payload: "foo" });

    let chunkCount = 0;
    let times = [];

    for await (const chunk of response) {
        chunkCount++;
        times.push(elapsed);
    }

    // Detection logic for proxy buffering
    const result = chunkCount < 5
        ? new Error(`Incomplete response (${chunkCount}/${times.length} valid chunks)`)
        : times[0] > 2000  // First chunk > 2 seconds indicates buffering
            ? new Error("Streaming responses are being buffered by a proxy in your network environment")
            : true;
};
```

#### 5. Bidirectional Streaming Test (Lines 911719-911756)
```javascript
const runBidi = async () => {
    const inputStream = new l$(8000);  // 8 second timeout
    const response = await healthClient.streamBidi(inputStream);

    inputStream.push({ payload: "foo" });

    for await (const chunk of response) {
        if (chunkCount > 4) break;
        await sleep(500);
        inputStream.push({ payload: "foo" });
    }

    // Complex validation with different error messages
    const result =
        (chunkCount == 0 || times.length == 0 || (chunkCount > 1 && chunkCount < 5))
            ? new Error(`Incomplete response (${chunkCount}/${times.length} valid chunks)`)
        : (chunkCount == 1 || times[0] > 2000)
            ? new Error(
                disableHttp2()
                    ? "HTTP/1.1 SSE responses are being buffered by a proxy"
                    : "Bidirectional streaming is not supported by the http2 proxy"
              )
        : true;
};
```

## Server-Side Protocol Control

### Http2Config Enum (Lines 826343-826361)

```javascript
// Internal name: nbt
// Protobuf type: aiserver.v1.Http2Config
nbt = {
    UNSPECIFIED: 0,           // "HTTP2_CONFIG_UNSPECIFIED"
    FORCE_ALL_DISABLED: 1,    // "HTTP2_CONFIG_FORCE_ALL_DISABLED"
    FORCE_ALL_ENABLED: 2,     // "HTTP2_CONFIG_FORCE_ALL_ENABLED"
    FORCE_BIDI_DISABLED: 3,   // "HTTP2_CONFIG_FORCE_BIDI_DISABLED"
    FORCE_BIDI_ENABLED: 4     // "HTTP2_CONFIG_FORCE_BIDI_ENABLED"
}
```

### GetServerConfigResponse (Lines 827785-827787)

```javascript
// Class: M2s
// Contains http2Config field for server-side protocol enforcement
{
    http2Config: nbt.UNSPECIFIED,  // Default: no override
    // ... other config
}
```

### Default ServerConfig (Lines 1144232-1144234)

```javascript
dLu = new M2s({
    indexingConfig: uLu,
    http2Config: nbt.UNSPECIFIED  // Server doesn't override by default
});
```

## Connection Error Handling and Stream Resumption

### LostConnection Error Class (Lines 465227-465233)

```javascript
// Located in: ../packages/agent-client/src/exec-controller.ts
_pt = class extends Error {
    constructor(message) {
        super(message);
        this.name = "LostConnection";
    }
}
```

### Protocol Error to LostConnection Mapping (Lines 465274-465284)

The following errors trigger a `LostConnection` exception:

```javascript
// 1. Missing EndStreamResponse
if (error instanceof ConnectError &&
    error.rawMessage === "protocol error: missing EndStreamResponse") {
    throw new LostConnection(error.message);
}

// 2. Stream write after end
if (error instanceof ConnectError && error.code === Code.Aborted) {
    if (error.cause?.code?.includes("ERR_STREAM_WRITE_AFTER_END")) {
        throw new LostConnection(error.message);
    }
}

// 3. AbortError
if (error instanceof AbortError) {
    throw new LostConnection(error.message);
}

// 4. NGHTTP2 Protocol Error (HTTP/2 specific)
if (error instanceof ConnectError && error.code === Code.Internal) {
    if (error.cause?.message?.includes("NGHTTP2_PROTOCOL_ERROR")) {
        throw new LostConnection(error.message);
    }
}
```

### Automatic Stream Resumption (Lines 466119-466130)

When a `LostConnection` occurs, the system attempts automatic reconnection:

```javascript
if (rejectedResult.reason instanceof LostConnection && !canceled) {
    // Get latest conversation checkpoint
    const checkpoint = conversationStore.getLatestCheckpoint();
    if (!checkpoint) throw new Error("No latest conversation state found");

    // Create resume action
    const resumeAction = new ConversationAction({
        action: {
            case: "resumeAction",
            value: new ResumeAction()
        }
    });

    // Reset stream and reconnect
    clientStream.resetStream();
    stallDetector[Symbol.dispose]();

    // Recursive call to resume conversation
    await this.run(ctx, checkpoint, resumeAction, ...otherParams);
}
```

**Important**: This is **stream resumption**, not **protocol fallback**. The reconnection uses the same protocol settings.

## Stall Detection System

### StallDetector Class (Lines 465748-465854)

```javascript
// Located in: ../packages/agent-client/src/stall-detector.ts
JOc = class {
    constructor(ctx, thresholdMs) {
        this.thresholdMs = thresholdMs;
        this.lastActivityTime = Date.now();
        this.startTimer();
    }

    trackActivity(type, messageType) {
        this.lastActivityTime = Date.now();
        this.startTimer();  // Reset timer
    }

    startTimer() {
        clearTimeout(this.timer);
        this.timer = setTimeout(() => {
            this.onStallDetected();
        }, this.thresholdMs);
    }

    onStallDetected() {
        // Log warning and emit metrics
        log.warn(ctx, "[NAL client stall detector] Bidirectional stream stall detected");
        stallCounter.increment(ctx, 1, { activity_type, message_type });
    }
}
```

### Stall Detection Metrics (Lines 465751-465758)

```javascript
// Counters for monitoring
VOc = Wdt("agent_client.stream.stall.count", {
    description: "Number of bidirectional stream stalls detected",
    labelNames: ["activity_type", "message_type"]
});

HOc = W4("agent_client.stream.stall.duration_ms", {
    description: "Duration of stream stalls in milliseconds",
    labelNames: ["activity_type"]
});

$Oc = Wdt("agent_client.stream.did_stall", {
    description: "Number of streams that experienced at least one stall"
});
```

## HTTP/2 Ping Configuration

### Dynamic Config Schema (Lines 295077-295082)

```javascript
http2_ping_config: ls.object({
    enabled: ls.array(ls.string()),        // Services to enable pings for
    pingIdleConnection: ls.boolean().nullable(),
    pingIntervalMs: ls.number().nullable(),
    pingTimeoutMs: ls.number().nullable(),
    idleConnectionTimeoutMs: ls.number().nullable()
})
```

### HTTP/2 Disable Pings Feature Flag (Lines 294141-294143)

```javascript
http2_disable_pings: {
    client: true,
    default: false  // Pings enabled by default
}
```

## HTTP/1.1 Keepalive Configuration

### Config Schema (Lines 295084-295085)

```javascript
http1_keepalive_config: ls.object({
    keepAliveInitialDelayMs: ls.number().nullable()
})
```

### Feature Flag (Lines 294153-294155)

```javascript
http1_keepalive_disabled: {
    client: true,
    default: false  // Keepalive enabled by default
}
```

## Debug Timeout Prevention

### Configuration (Lines 450685-450691)

```javascript
"cursor.debug.timeoutPrevention": {
    title: "Debug Timeout Prevention",
    type: "string",
    enum: ["local_only", "always", "never"],
    enumDescriptions: [
        "Prevent timeouts on localhost only (default)",
        "Always prevent timeouts (for debugging non-local backends)",
        "Never prevent timeouts (normal operation)"
    ],
    default: "local_only",
    description: 'Prevent "Connection failed" errors when paused at breakpoints
                  during debugging. This works by disabling HTTP/2 keepalive pings.'
}
```

## HealthService Protocol Variants

### Service Definition (Lines 823788-823832)

```javascript
// aiserver.v1.HealthService
{
    // Unary methods
    ping:         { kind: Kt.Unary },
    unary:        { kind: Kt.Unary },

    // Server-streaming variants
    stream:       { kind: Kt.ServerStreaming },     // HTTP/2
    streamSSE:    { kind: Kt.ServerStreaming },     // HTTP/1.1 SSE

    // Bidirectional variants
    streamBidi:     { kind: Kt.BiDiStreaming },     // HTTP/2 BiDi
    streamBidiSSE:  { kind: Kt.ServerStreaming },   // HTTP/1.1 SSE fallback
    streamBidiPoll: { kind: Kt.ServerStreaming }    // HTTP/1.0 polling
}
```

## Retry Interceptor Configuration

### Config Schema (Lines 295122-295137)

```javascript
retry_interceptor_config: ls.object({
    retriableErrors: ls.array(ls.object({
        code: ls.string(),
        errorMessage: ls.string().optional(),
        method: ls.string().optional()
    }))
})

// Default retriable errors
fallbackValues: {
    retriableErrors: [
        { code: "Unavailable" },
        { code: "Internal" },
        { code: "DeadlineExceeded" }
    ]
}
```

### Retry Parameters (Lines 295133-295137)

```javascript
retry_interceptor_params_config: ls.object({
    maxRetries: ls.number().optional(),
    baseDelayMs: ls.number().optional(),
    maxDelayMs: ls.number().optional()
})
```

## Detection Triggers Summary

| Detection Type | Trigger Condition | Action |
|----------------|-------------------|--------|
| Proxy Buffering | First chunk > 2000ms | Displays warning in diagnostics |
| Incomplete Stream | < 5 valid chunks received | Error in diagnostics |
| HTTP/2 Not Negotiated | Protocol != "h2" | Error in diagnostics |
| TLS Interception | Unrecognized certificate issuer | Warning in diagnostics |
| Stream Stall | No activity for threshold period | Logs warning, emits metrics |
| Connection Lost | NGHTTP2_PROTOCOL_ERROR, AbortError, etc. | Triggers stream resumption |

## What IS Automatic vs Manual

### Automatic Behaviors
1. **Stream Resumption**: On `LostConnection`, automatically reconnects with same protocol
2. **Stall Detection**: Monitors stream activity and logs warnings
3. **Retry on Transient Errors**: Retries on Unavailable, Internal, DeadlineExceeded

### Manual Behaviors
1. **Protocol Selection**: User must configure HTTP Compatibility Mode
2. **Fallback Decision**: User runs diagnostics, interprets results, changes settings
3. **TLS Warning Response**: User decides whether to proceed with intercepted certificate

## Key Source Locations

| Component | Line Range | Description |
|-----------|------------|-------------|
| Config Keys | 268991 | Qdt, dHr configuration key definitions |
| Settings Schema | 450674-450697 | HTTP/2 and SSE disable settings |
| Http2Config Enum | 826343-826361 | Server-side protocol control |
| HealthService | 823788-823832 | Protocol variant endpoints |
| Network Diagnostics | 911491-911757 | Mmu() diagnostic implementation |
| HTTP Compatibility UI | 911765-911794 | Protocol selection dropdown |
| LostConnection Class | 465227-465233 | Connection error type |
| Error Mapping | 465274-465284 | Protocol errors to LostConnection |
| Stream Resumption | 466119-466130 | Automatic reconnection logic |
| Stall Detector | 465748-465854 | Stream activity monitoring |
| Retry Config | 295122-295137 | Retry interceptor configuration |
| Ping Config | 295077-295082 | HTTP/2 ping configuration |

## Conclusion

Cursor's HTTP fallback system is primarily **user-driven** with **diagnostic assistance**, not automatic detection. The system:

1. **Does NOT** automatically detect HTTP/2 failures and switch to HTTP/1.1
2. **Does NOT** automatically detect SSE failures and switch to polling
3. **DOES** provide comprehensive diagnostics to identify protocol issues
4. **DOES** automatically resume streams after connection loss (same protocol)
5. **DOES** allow server-side protocol enforcement via Http2Config (infrastructure exists)

Users in problematic network environments must:
1. Run network diagnostics (Settings > Network > Run Diagnostic)
2. Identify which protocol tier fails
3. Manually select HTTP Compatibility Mode (HTTP/2, HTTP/1.1, or HTTP/1.0)

## Related Analysis Documents

- TASK-43: SSE/Poll Fallback Mechanism (protocol tiers and endpoints)
- TASK-118: Server-Side Http2Config Enforcement Logic (server config details)
- TASK-119: Polling Backoff Strategy (poll interval configuration)
- TASK-120: HTTP Keepalive Configuration (connection health)
