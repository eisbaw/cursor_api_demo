# TASK-118: Server-Side Http2Config Enforcement Logic

## Executive Summary

Cursor implements server-side HTTP/2 protocol configuration through the `Http2Config` enum delivered via the `GetServerConfigResponse` protobuf message. This allows Cursor's backend to remotely control client HTTP protocol behavior, potentially overriding user preferences. The implementation includes a comprehensive HTTP/2 ping configuration system for connection health monitoring.

## Http2Config Enum Definition

### Protobuf Definition (Line 826343-826361)

```javascript
// Internal enum name: nbt
// Protobuf namespace: aiserver.v1.Http2Config
nbt = {
    UNSPECIFIED: 0,           // "HTTP2_CONFIG_UNSPECIFIED"
    FORCE_ALL_DISABLED: 1,    // "HTTP2_CONFIG_FORCE_ALL_DISABLED"
    FORCE_ALL_ENABLED: 2,     // "HTTP2_CONFIG_FORCE_ALL_ENABLED"
    FORCE_BIDI_DISABLED: 3,   // "HTTP2_CONFIG_FORCE_BIDI_DISABLED"
    FORCE_BIDI_ENABLED: 4     // "HTTP2_CONFIG_FORCE_BIDI_ENABLED"
}
```

### Enum Value Semantics

| Value | Name | Description |
|-------|------|-------------|
| 0 | UNSPECIFIED | Server does not enforce any protocol preference |
| 1 | FORCE_ALL_DISABLED | Force all connections to use HTTP/1.x (disable HTTP/2 entirely) |
| 2 | FORCE_ALL_ENABLED | Force all connections to use HTTP/2 |
| 3 | FORCE_BIDI_DISABLED | Allow HTTP/2 but disable bidirectional streaming (use SSE/poll fallback) |
| 4 | FORCE_BIDI_ENABLED | Force HTTP/2 with bidirectional streaming enabled |

## GetServerConfigResponse Structure

### Protobuf Message (Line 827785-827879)

```javascript
// Class name: M2s (rOn)
// Protobuf type: aiserver.v1.GetServerConfigResponse
{
    isDevDoNotUseForSecretThingsBecauseCanBeSpoofedByUsers: false,  // Field 2
    configVersion: "",                                               // Field 6
    http2Config: nbt.UNSPECIFIED,                                   // Field 7
    modelMigrations: [],                                            // Field 12
    useNlbForNal: false,                                            // Field 21+

    // Sub-configs
    bugConfigResponse: Jru,          // Field 1
    indexingConfig: Yru,             // Field 3
    clientTracingConfig: zOf,        // Field 4
    chatConfig: Xru,                 // Field 5
    profilingConfig: UOf,            // Field 8
    metricsConfig: KOf,              // Field 9
    backgroundComposerConfig: YOf,   // Field 10
    autoContextConfig: XOf,          // Field 11
    memoryMonitorConfig: QOf,        // Field 13
    folderSizeLimit: Qru,            // Field 14
    gitIndexingConfig: GOf,          // Field 15
    performanceEventsConfig: ???,    // Field 16
    onlineMetricsConfig: dOf         // Field 20
}
```

### Default ServerConfig Instance (Line 1144232-1144234)

```javascript
// Default config stored as dLu
dLu = new M2s({
    indexingConfig: uLu,
    http2Config: nbt.UNSPECIFIED  // Server doesn't override by default
});
```

## Server Config Fetching

### Service Configuration (Line 1144237-1144327)

```javascript
// Storage key: "cursorai/serverConfig"
// Refresh interval: 300 seconds (5 minutes)
// Timeout: 30 seconds

class K9o extends Ve {
    constructor() {
        this.serverConfigStore = dLu;  // Default config
        this.refreshPeriodicallyFromServer();
    }

    // Fetch from server
    async forceRefreshServerConfig() {
        const response = await serverConfigClient.getServerConfig({
            telemEnabled: canWeTrackTelem,
            osStats: { totalmem, freemem, loadavg },
            osProperties: { type, release, arch, platform, cpus },
            remoteAuthority: remoteAuthorityInfo,
            inAppAdTrigger: trigger
        });
        this.setCachedServerConfig(response);
    }

    // Persist to disk
    setCachedServerConfig(config) {
        this.storageService.store("cursorai/serverConfig", config.toJsonString(), -1, 1);
        this._onDidRefreshServerConfig.fire();
    }
}
```

## Client-Side Configuration Settings

### User Preferences (Line 268991, 450674-450697)

```javascript
// Config keys
Qdt = "cursor.general.disableHttp2"       // Disable HTTP/2 entirely
dHr = "cursor.general.disableHttp1SSE"    // Disable SSE fallback (forces polling)

// Settings schema
{
    "cursor.general.disableHttp2": {
        title: "Disable HTTP/2",
        type: "boolean",
        default: false,
        description: "Disable HTTP/2 for all requests, and use HTTP/1.1 instead...",
        policy: {
            name: "NetworkDisableHttp2",
            minimumVersion: "1.99"
        }
    },
    "cursor.general.disableHttp1SSE": {
        title: "Disable HTTP/1.1 SSE",
        type: "boolean",
        default: false,
        description: "Disable HTTP/1.1 SSE for agent chat..."
    }
}
```

## HTTP/2 Ping Configuration

### Dynamic Config Schema (Line 295077-295082)

```javascript
http2_ping_config: ls.object({
    enabled: ls.array(ls.string()),        // List of endpoints/services to enable pings for
    pingIdleConnection: ls.boolean().nullable(),
    pingIntervalMs: ls.number().nullable(),
    pingTimeoutMs: ls.number().nullable(),
    idleConnectionTimeoutMs: ls.number().nullable()
})
```

### Default Values (Line 295389-295396)

```javascript
http2_ping_config: {
    client: true,  // Client-side feature
    fallbackValues: {
        enabled: [],           // No services enabled by default
        pingIdleConnection: null,
        pingIntervalMs: null,
        pingTimeoutMs: null,
        idleConnectionTimeoutMs: null
    }
}
```

### Feature Flag (Line 294141-294143)

```javascript
http2_disable_pings: {
    client: true,
    default: false  // Pings enabled by default when not disabled
}
```

## HTTP/1.1 Keepalive Configuration

### Dynamic Config Schema (Line 295084-295085)

```javascript
http1_keepalive_config: ls.object({
    keepAliveInitialDelayMs: ls.number().nullable()
})
```

### Feature Flag (Line 294153-294155)

```javascript
http1_keepalive_disabled: {
    client: true,
    default: false  // Keepalive enabled by default
}
```

## Network Diagnostics Implementation

### Diagnostic Panel (Line 911491-911757)

The network diagnostics UI runs multiple protocol tests:

```javascript
function Mmu() {
    const [disableHttp2, setDisableHttp2] = H3(Qdt, configService, false);
    const [disableHttp1SSE, setDisableHttp1SSE] = H3(dHr, configService, false);

    // Diagnostic state
    const [results, setResults] = Be({
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

### HTTP/2 Protocol Test (Line 911556-911581)

```javascript
const runHttp2Ping = async () => {
    const startTime = Date.now();
    log("http2", "Start");

    const result = await everythingProvider.runCommand("connectDebug.http2Ping", {});

    if (result?.error) {
        log("http2", `Error: ${result.error}`);
        setResult({ http2: new Error(result.error) });
        return;
    }

    log("http2", `Protocol: ${result.protocol}`);

    // h2 = HTTP/2, otherwise error
    const success = result.protocol === "h2"
        ? true
        : new Error(`Unexpected protocol: ${result.protocol}`);

    log("http2", `Result: ${success} in ${Date.now() - startTime}ms`);
    setResult({ http2: success });
};
```

### Bidirectional Stream Test (Line 911719-911756)

```javascript
const runBidi = async () => {
    const client = await healthClient();
    const stream = await client.streamBidi(inputStream);

    let chunkCount = 0;
    let times = [];

    for await (const response of stream) {
        if (response.payload == "foo") chunkCount++;
        times.push(elapsed);

        if (chunkCount > 4) break;
        await sleep(500);
        inputStream.push({ payload: "foo" });
    }

    // Analyze results
    const result =
        (chunkCount == 0 || times.length == 0 || (chunkCount > 1 && chunkCount < 5))
            ? new Error(`Incomplete response (${chunkCount}/${times.length} valid chunks)`)
        : (chunkCount == 1 || times[0] > 2000)
            ? new Error(
                disableHttp2()
                    ? "HTTP/1.1 SSE responses are being buffered by a proxy"
                    : "Bidirectional streaming not supported by http2 proxy"
              )
        : true;
};
```

## HTTP Compatibility Mode UI

### Protocol Selection (Line 911765-911794)

```javascript
{
    label: "HTTP Compatibility Mode",
    description: "HTTP/2 is recommended for low-latency streaming...",

    get value() {
        return !disableHttp2() ? "http2"
             : disableHttp1SSE() ? "http1.0"
             : "http1.1";
    },

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

## Error Handling

### NGHTTP2 Protocol Error Detection (Line 465283)

```javascript
// Detect HTTP/2 protocol errors for fallback
if (error instanceof ConnectError && error.code === Code.Internal) {
    const cause = error.cause;
    if (cause instanceof Error && cause.message.includes("NGHTTP2_PROTOCOL_ERROR")) {
        throw new ProtocolError(error.message);
    }
}
```

## Interaction Matrix

| Server Http2Config | Client disableHttp2 | Client disableHttp1SSE | Effective Protocol |
|-------------------|---------------------|------------------------|-------------------|
| UNSPECIFIED | false | false | HTTP/2 BiDi |
| UNSPECIFIED | true | false | HTTP/1.1 SSE |
| UNSPECIFIED | true | true | HTTP/1.0 Poll |
| FORCE_ALL_DISABLED | any | any | HTTP/1.x (server override) |
| FORCE_ALL_ENABLED | any | any | HTTP/2 (server override) |
| FORCE_BIDI_DISABLED | false | any | HTTP/2 without BiDi |
| FORCE_BIDI_ENABLED | any | false | HTTP/2 BiDi (server override) |

## Current Implementation Status

Based on code analysis, the `http2Config` field is:

1. **Defined**: Complete protobuf enum and message field definitions exist
2. **Received**: The field is part of GetServerConfigResponse and stored in cachedServerConfig
3. **Not Actively Enforced**: No consumer code found that reads cachedServerConfig.http2Config to override client behavior

The server-side enforcement appears to be infrastructure that is defined but not actively used. The client respects user settings (`disableHttp2`, `disableHttp1SSE`) but doesn't appear to have logic that reads the server's `http2Config` to override these.

## Key Source Locations

| Component | Line Range | Description |
|-----------|------------|-------------|
| Http2Config Enum | 826343-826361 | Protocol control enum definition |
| ServerConfig Message | 827785-827879 | GetServerConfigResponse structure |
| Default Config | 1144232-1144234 | Default ServerConfig instance |
| Config Service | 1144238-1144327 | Server config fetching and caching |
| User Settings | 450674-450697 | disableHttp2 and disableHttp1SSE |
| HTTP/2 Ping Config | 295077-295082 | Ping configuration schema |
| Network Diagnostics | 911491-911757 | Protocol testing implementation |
| NGHTTP2 Error Handling | 465283 | Protocol error detection |

## Recommendations

1. **Server Override Logic**: The http2Config enum values suggest server-side control was planned but client enforcement may not be fully implemented
2. **Monitoring**: Use network diagnostics to verify protocol negotiation
3. **Configuration**: The http2_ping_config allows fine-tuning connection health monitoring
4. **Fallback**: NGHTTP2_PROTOCOL_ERROR triggers graceful protocol degradation

## Related Tasks

- TASK-43: SSE/Poll Fallback Mechanism (covers protocol fallback patterns)
- Investigation needed: http2Config enforcement in transport layer
