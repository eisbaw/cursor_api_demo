# TASK-120: HTTP Keepalive and Ping Configurations

## Executive Summary

Cursor implements a multi-layered keepalive system spanning internal socket protocols, HTTP/2 ping configurations, and retry mechanisms. These configurations aim to maintain connection liveness, detect stale connections, and provide debugging capabilities for timeout issues.

## Protocol Keepalive Constants

### Internal Protocol Constants (Line ~794918)

The internal IPC protocol defines fixed timing constants:

```javascript
// enu - Protocol timing constants
{
    HeaderLength: 13,           // 13 bytes per message header
    AcknowledgeTime: 2000,      // 2 seconds - ACK response timeout
    TimeoutTime: 20000,         // 20 seconds - Socket timeout threshold
    ReconnectionGraceTime: 10800000,  // 3 hours (108e5ms) - Long reconnection window
    ReconnectionShortGraceTime: 300000,  // 5 minutes (3e5ms) - Short reconnection window
    KeepAliveSendTime: 5000     // 5 seconds - Keepalive interval
}
```

### Message Types (Line ~794891)

```javascript
// Qiu - Protocol message types
{
    None: 0,
    Regular: 1,
    Control: 2,
    Ack: 3,
    Disconnect: 5,
    ReplayRequest: 6,
    Pause: 7,
    Resume: 8,
    KeepAlive: 9  // Dedicated keepalive message type
}
```

## Internal Socket Keepalive Implementation

### JDf Class - Protocol Handler (Line ~795150)

The internal protocol handler implements keepalive for socket connections:

```javascript
constructor(options) {
    this._shouldSendKeepAlive = options.sendKeepAlive ?? true;
    // ... other initialization

    // Start keepalive interval if enabled
    this._shouldSendKeepAlive
        ? this._keepAliveInterval = setInterval(() => {
            this._sendKeepAlive()
        }, 5000)  // 5 second interval
        : this._keepAliveInterval = null;
}

_sendKeepAlive() {
    this._incomingAckId = this._incomingMsgId;
    const msg = new Che(9, 0, this._incomingAckId, k4e());  // Type 9 = KeepAlive
    this._socketWriter.write(msg);
}
```

### Socket Timeout Detection (Line ~795280)

```javascript
_recvAckCheck() {
    const oldestMsg = this._outgoingUnackMsg.peek();
    const timeSinceWrite = Date.now() - oldestMsg.writtenTime;
    const timeSinceRead = Date.now() - this._socketReader.lastReadTime;
    const timeSinceTimeout = Date.now() - this._lastSocketTimeoutTime;

    // Timeout if all conditions exceed 20 seconds and no high load
    if (timeSinceWrite >= 20000 &&
        timeSinceRead >= 20000 &&
        timeSinceTimeout >= 20000 &&
        !this._loadEstimator.hasHighLoad()) {
        this._onSocketTimeout.fire({
            unacknowledgedMsgCount: this._outgoingUnackMsg.length(),
            timeSinceOldestUnacknowledgedMsg: timeSinceWrite,
            timeSinceLastReceivedSomeData: timeSinceRead
        });
        return;
    }

    // Schedule next check
    const nextCheck = Math.max(
        20000 - timeSinceWrite,
        20000 - timeSinceRead,
        20000 - timeSinceTimeout,
        500  // minimum 500ms
    );
    this._outgoingAckTimeout = setTimeout(() => this._recvAckCheck(), nextCheck);
}
```

## HTTP/2 Ping Configuration

### Schema Definition (Line ~295077)

```javascript
http2_ping_config: ls.object({
    enabled: ls.array(ls.string()),       // Feature flags to enable for
    pingIdleConnection: ls.boolean().nullable(),
    pingIntervalMs: ls.number().nullable(),
    pingTimeoutMs: ls.number().nullable(),
    idleConnectionTimeoutMs: ls.number().nullable()
})
```

### Default Values (Line ~295389)

```javascript
http2_ping_config: {
    client: true,  // Client-side config
    fallbackValues: {
        enabled: [],           // Empty by default - feature gated
        pingIdleConnection: null,
        pingIntervalMs: null,
        pingTimeoutMs: null,
        idleConnectionTimeoutMs: null
    }
}
```

### Feature Flags (Line ~294141)

```javascript
http2_disable_pings: {
    client: true,
    default: false  // HTTP/2 pings enabled by default
}
```

## HTTP/1.1 Keepalive Configuration

### Schema Definition (Line ~295084)

```javascript
http1_keepalive_config: ls.object({
    keepAliveInitialDelayMs: ls.number().nullable()
})
```

### Default Values (Line ~295399)

```javascript
http1_keepalive_config: {
    client: true,
    fallbackValues: {
        keepAliveInitialDelayMs: null  // System default
    }
}
```

### Feature Flag (Line ~294153)

```javascript
http1_keepalive_disabled: {
    client: true,
    default: false  // HTTP/1.1 keepalive enabled by default
}
```

## Fetch API Keepalive

### Sentry Transport (Line ~504413)

```javascript
const fetchOptions = {
    body: request.body,
    method: "POST",
    referrerPolicy: "strict-origin",
    headers: headers,
    keepalive: totalBytes <= 60000 && pendingRequests < 15,  // Conditional keepalive
    ...options.fetchOptions
};
```

This implements the Fetch API `keepalive` flag which allows requests to outlive the page. The conditions:
- Total bytes <= 60KB (`6e4`)
- Pending requests < 15

## Debugging: Timeout Prevention Setting

### Configuration (Line ~450685)

```javascript
"cursor.debug.timeoutPrevention": {
    title: "Timeout Prevention",
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

### Policy Integration

The `NetworkDisableHttp2` policy (Line ~450680) allows enterprise admins to enforce HTTP/1.1 for all requests with minimum version "1.99".

## Agent Heartbeat Configuration

### Client Heartbeat Interval (Line ~466028)

```javascript
const heartbeatIntervalMs = 5000;  // 5 seconds
let heartbeatTimeout;

const scheduleHeartbeat = () => {
    heartbeatTimeout = setTimeout(() => {
        writer.write(new ClientMessage({
            message: {
                case: "clientHeartbeat",
                value: new ClientHeartbeat()
            }
        })).then(() => tracker.onClientSentHeartbeat());
        scheduleHeartbeat();
    }, heartbeatIntervalMs);
};
```

### Server Heartbeat Processing (Line ~465865)

```javascript
for await (const message of stream) {
    if (message.message.case === "interactionUpdate" &&
        message.message.value.message.case === "heartbeat") {
        tracker.onServerSentHeartbeat();
    } else {
        tracker.reset("inbound_message", messageType);
    }
}
```

### Background Composer Ping Interval (Line ~1143919)

```javascript
const pingIntervalMs = Math.max(
    serverConfig.backgroundComposerConfig?.windowInWindowPingIntervalMs ?? 10000,
    1000  // Minimum 1 second
);
await new Promise(resolve => setTimeout(resolve, pingIntervalMs));
```

## Retry Interceptor Configuration

### Schema (Line ~295122)

```javascript
retry_interceptor_config: ls.object({
    retriableErrors: ls.array(ls.object({
        code: ls.string(),
        errorMessage: ls.string().optional(),
        method: ls.string().optional()
    }))
})

retry_interceptor_params_config: ls.object({
    maxRetries: ls.number().optional(),
    baseDelayMs: ls.number().optional(),
    maxDelayMs: ls.number().optional()
})
```

### Default Retriable Errors (Line ~295470)

```javascript
retry_interceptor_config: {
    client: true,
    fallbackValues: {
        retriableErrors: [
            { code: "Unavailable" },
            { code: "Internal" },
            { code: "DeadlineExceeded" }
        ]
    }
}
```

### Headers (Line ~300964)

```javascript
function getRetryInterceptorHeaders(enabled, params) {
    const headers = {
        "X-Cursor-RetryInterceptor-Enabled": "true"
    };
    if (params?.maxRetries !== undefined) {
        headers["X-Cursor-RetryInterceptor-MaxRetries"] = String(params.maxRetries);
    }
    if (params?.baseDelayMs !== undefined) {
        headers["X-Cursor-RetryInterceptor-BaseDelayMs"] = String(params.baseDelayMs);
    }
    if (params?.maxDelayMs !== undefined) {
        headers["X-Cursor-RetryInterceptor-MaxDelayMs"] = String(params.maxDelayMs);
    }
    return headers;
}
```

## Idempotent Stream Configuration

### Retry Lookback Window (Line ~295144)

```javascript
idempotent_stream_config: ls.object({
    retry_lookback_window_ms: ls.number()
})

// Default: 7,200,000ms = 2 hours
idempotent_stream_config: {
    client: true,
    fallbackValues: {
        retry_lookback_window_ms: 7200000
    }
}
```

### Usage (Line ~945195)

```javascript
const retryLookbackMs = this.experimentService.getDynamicConfigParam(
    "idempotent_stream_config",
    "retry_lookback_window_ms"
) ?? 7200000;  // 2 hour default
```

## Composer Hang Detection

### Configuration (Line ~295090)

```javascript
composer_hang_detection_config: ls.object({
    thresholds_ms: ls.array(ls.number())
})

// Default thresholds (Line ~295414)
composer_hang_detection_config: {
    client: true,
    fallbackValues: {
        thresholds_ms: [2000, 4000, 6000, 8000, 10000, 12000, 14000, 16000, 32000]
    }
}
```

This provides escalating timeout thresholds for detecting unresponsive composer streams.

## Reliable Stream Fault Injection

### Configuration (Line ~295093)

```javascript
reliable_stream_fault_injection: ls.object({
    enabled: ls.boolean(),
    baseIntervalMs: ls.number(),
    exponentialFactor: ls.number()
})

// Defaults
reliable_stream_fault_injection: {
    client: true,
    fallbackValues: {
        enabled: false,
        baseIntervalMs: 1000,
        exponentialFactor: 0.05
    }
}
```

Used for testing stream reliability by injecting controlled failures.

## Sentry Idle Span Configuration

### Default Timeouts (Line ~3344)

```javascript
const idleSpanDefaults = {
    idleTimeout: 1000,     // 1 second - Mark span idle after 1s of no activity
    finalTimeout: 30000,   // 30 seconds - Maximum span duration
    childSpanTimeout: 15000  // 15 seconds - Timeout for child spans
};

const timeoutReasons = {
    heartbeatFailed: "heartbeatFailed",
    idleTimeout: "idleTimeout",
    finalTimeout: "finalTimeout",
    externalFinish: "externalFinish"
};
```

## Connection Timeout Summary

| Layer | Keepalive Interval | Timeout | Purpose |
|-------|-------------------|---------|---------|
| Internal Socket | 5 seconds | 20 seconds | IPC protocol liveness |
| HTTP/2 Ping | Configurable | Configurable | HTTP/2 connection health |
| Agent Heartbeat | 5 seconds | N/A | Agent stream liveness |
| Background Composer | 10 seconds (default) | N/A | Window visibility tracking |
| Fetch keepalive | N/A | N/A | Request outlives page |
| Reconnection Grace | N/A | 3 hours / 5 minutes | Reconnection window |
| Idle Span | N/A | 1 second | Sentry tracing |

## Key Source Locations

| Component | Line Range | Description |
|-----------|------------|-------------|
| Protocol Constants | 794916-794919 | Timeout and keepalive timing constants |
| Message Types | 794889-794915 | Protocol message type enum |
| Keepalive Implementation | 795150-795310 | Socket keepalive logic |
| HTTP/2 Ping Config | 295077-295083, 295389-295397 | HTTP/2 ping schema and defaults |
| HTTP/1 Keepalive Config | 295084-295086, 295399-295403 | HTTP/1.1 keepalive settings |
| Timeout Prevention | 450685-450692 | Debug setting for debugging timeouts |
| Agent Heartbeat | 466025-466043 | Client heartbeat scheduling |
| Retry Interceptor | 295122-295137, 300961-300967 | Retry configuration and headers |
| Hang Detection | 295090-295092, 295411-295416 | Composer hang detection thresholds |

## Implementation Notes

### Keepalive vs Heartbeat Distinction

- **Keepalive**: Low-level connection liveness (TCP/HTTP level)
- **Heartbeat**: Application-level message exchange for session/stream health

### Debugging Workflow

1. If experiencing timeout issues during debugging:
   - Set `cursor.debug.timeoutPrevention` to `"always"`
   - This disables HTTP/2 keepalive pings that can timeout during breakpoints

2. For corporate proxy issues:
   - Check if HTTP/2 pings are being blocked
   - Consider using `http2_disable_pings` feature flag
   - Fall back to HTTP/1.1 via `cursor.general.disableHttp2`

### Server-Side Control

The `http2_ping_config.enabled` array controls which features/services have HTTP/2 pings enabled. When empty (default), the feature is effectively disabled until server-side configuration enables it for specific use cases.

## Related Tasks

- TASK-43: SSE/Poll Fallback Mechanism - Protocol fallback hierarchy
- TASK-118: HTTP/2 Config - Server-side HTTP/2 configuration
- TASK-84: Idempotent Streams - Stream resumption and retry
- TASK-39: Stream Resumption - Reconnection handling
