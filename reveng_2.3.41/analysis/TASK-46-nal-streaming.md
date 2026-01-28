# TASK-46: NAL (Native Agent Layer) vs Regular Backend Streaming Paths in Cursor

## Executive Summary

Cursor IDE version 2.3.41 implements two distinct streaming paths for AI-powered code generation:

1. **NAL (Native Agent Layer)** - A newer, more integrated agent-based architecture
2. **Regular Backend (Agentic Composer)** - The traditional composer-based streaming path

The NAL path uses `AgentService/Run` with bidirectional (BiDi) streaming, while the regular path uses `AiServerService/StreamComposer` with server-side streaming (SSE). The selection between these paths is controlled by the `isNAL` flag on composer data, which can be set through various feature gates and conditions.

## Architecture Overview

### Source File
- **File**: `/home/mpedersen/topics/cursor_decompiled_1.3_mini/reveng_2.3.41/beautified/workbench.desktop.main.js`

### Key Components

```
+-------------------+     +---------------------------+
|   Composer UI     |---->|   ComposerChatService     |
+-------------------+     +---------------------------+
                                    |
                    +---------------+---------------+
                    |                               |
                    v                               v
        +-------------------+           +-------------------+
        |  NAL Path         |           |  Regular Path     |
        |  (isNAL: true)    |           |  (isNAL: false)   |
        +-------------------+           +-------------------+
                    |                               |
                    v                               v
        +-------------------+           +-------------------+
        | ComposerAgent     |           |   AiService       |
        | Service           |           | streamResponse    |
        +-------------------+           +-------------------+
                    |                               |
                    v                               v
        +-------------------+           +-------------------+
        | AgentService/Run  |           | AiServerService/  |
        | BiDi Streaming    |           | StreamComposer    |
        +-------------------+           +-------------------+
```

## NAL (Native Agent Layer) Details

### Definition and Default State
Location: Line ~215140
```javascript
{
    // Default composer data includes:
    isNAL: false,
    conversationState: new U1  // Uses protobuf U1 for conversation state
}
```

### NAL Detection and Setting
The `isNAL` flag is set to `true` under several conditions:

1. **Background Composer Attachment** (Line ~487958-487960):
```javascript
n.data.isNAL !== !0 && this._composerDataService.updateComposerData(t, {
    isNAL: !0
})
```

2. **Worktree NAL-Only Gate** (Line ~489139-489145):
```javascript
const ae = this._experimentService.checkFeatureGate("worktree_nal_only");
// For worktree sessions, if gate enabled and new conversation:
ce && ne.isNAL !== !0 && ae && Le && this._composerDataService.updateComposerData(e, {
    isNAL: !0
})
```

### NAL vs Regular Path Selection (Line ~490068-490130)
```javascript
const No = ne.isNAL ?? !1;
if (No) {
    // NAL path: Uses ComposerAgentService
    const uu = this.convertCtxToContext(s) ?? fBc(lI(), this._structuredLogService, this._metricsService);
    oc = this._composerAgentService.getAgentStreamResponse(uu, {
        modelDetails: M,
        generationUUID: r,
        composerId: e,
        abortController: wn,
        startTime: p,
        // ... other params
    });
} else {
    // Regular path: Uses streamComposer
    oc = this._aiService.streamResponse({
        modelDetails: M,
        generationUUID: r,
        streamer: qu,
        streamerURL: fB.typeName + "/" + fB.methods.streamComposer.name,
        source: "composer",
        // ...
    });
}
```

### NAL Streaming Implementation
Location: Line ~950034-950130 (`streamFromAgentBackend` method)
```javascript
async * streamFromAgentBackend(e, t, n, s, r, o, a, l, d, h) {
    // Uses agent-client package
    // Connects to AgentService/Run endpoint
    // Returns async generator for streaming responses
}
```

### NAL Stall Detection
Location: Line ~465826 (`@anysphere/agent-client:stall-detector`)
```javascript
Sro.warn(this.ctx, "[NAL client stall detector] Bidirectional stream stall detected - no activity for threshold period", n)
```

The NAL client has a dedicated stall detector that monitors bidirectional stream activity with:
- Default threshold: 10 seconds (`thresholdMs: 1e4`)
- Heartbeat interval: 5 seconds (`ke = 5e3`)
- Metrics tracked: `agent_client.stream.stall.count`, `agent_client.stream.stall.duration_ms`

## Streaming Protocol Differences

### Service Type Enumeration (Line ~85839)
```javascript
i[i.Unary = 0] = "Unary"
i[i.ServerStreaming = 1] = "ServerStreaming"
i[i.ClientStreaming = 2] = "ClientStreaming"
i[i.BiDiStreaming = 3] = "BiDiStreaming"
```

### NAL Path Endpoints
| Service | Method | Type |
|---------|--------|------|
| AgentService | Run | BiDiStreaming |
| AgentService | RunSSE | ServerStreaming |
| UnifiedChatService | StreamUnifiedChatWithTools | BiDiStreaming |
| UnifiedChatService | StreamUnifiedChatWithToolsSSE | ServerStreaming |

### Regular Path Endpoints
| Service | Method | Type |
|---------|--------|------|
| AiServerService | StreamComposer | BiDiStreaming |
| AiServerService | StreamComposerSSE | ServerStreaming |
| HealthService | StreamBidi | BiDiStreaming |
| HealthService | StreamBidiSSE | ServerStreaming |

### SSE Fallback Pattern
Location: Line ~439104-439220 (`bidi_pb.js`)

Each BiDi streaming method has a corresponding SSE fallback:
```javascript
// SSE streaming request uses requestId for correlation
jre = class extends K {
    constructor(e) {
        super()
        this.requestId = ""  // Used for SSE session correlation
        v.util.initPartial(e, this)
    }
}
```

## HTTP Transport Configuration

### HTTP Mode Settings
Location: Line ~268991
```javascript
Qdt = "cursor.general.disableHttp2"      // Config key to disable HTTP/2
dHr = "cursor.general.disableHttp1SSE"   // Config key to disable HTTP/1.1 SSE
```

### Network Diagnostics Panel (Line ~911490-911800)
The settings panel provides HTTP compatibility mode selection:
- **HTTP/2** (default): Low-latency bidirectional streaming
- **HTTP/1.1**: SSE-based streaming with proxy compatibility
- **HTTP/1.0**: Maximum compatibility mode

Network diagnostic tests:
1. **DNS Lookup** - Verifies DNS resolution
2. **HTTP/2 Support** - Tests bidirectional capabilities
3. **TLS Inspection** - Checks TLS configuration
4. **Unary Request** - Tests basic connectivity
5. **Ping Test** - HTTP/2 ping for latency
6. **Stream Test** - Server streaming verification
7. **BiDi Test** - Full bidirectional streaming test

### BiDi vs SSE Detection (Line ~911746)
```javascript
const ce = te == 0 || ie.length == 0 || te > 1 && te < 5
    ? new Error(`Incomplete response (${te}/${ie.length} valid chunks)`)
    : te == 1 || ie[0] > 2e3
        ? new Error(e()
            ? "HTTP/1.1 SSE responses are being buffered by a proxy in your network environment"
            : "Bidirectional streaming is not supported by the http2 proxy in your network environment"
        )
        : !0;
```

## Performance Considerations

### NAL Path Advantages
1. **Direct BiDi Communication** - Lower latency for tool calls
2. **Heartbeat Mechanism** - 5-second client heartbeats maintain connection
3. **Stall Detection** - Built-in monitoring for stream health
4. **Conversation State Management** - Uses protobuf `U1` state object

### Regular Path Characteristics
1. **Code Block Based** - Uses `codeBlockData` for file tracking
2. **Checkpoint System** - File-based checkpoint recovery
3. **Broader Compatibility** - SSE fallback for restrictive networks

### Metrics Tracking
Both paths track performance metrics:
```javascript
// Time to first token (TTFT)
this._metricsService.distribution({
    stat: "composer.submitChat.ttftActual",
    value: uu,
    tags: {
        model: this.getModelNameForMetrics(M, this._aiSettingsService),
        chatService: ne.isNAL ? "agent" : "agentic-composer",
        // ...
    }
})
```

## Feature Gates and Experiments

### NAL-Related Feature Gates
| Gate Name | Purpose |
|-----------|---------|
| `worktree_nal_only` | Force NAL for worktree sessions |
| `composer_gc_handles` | Garbage collection for composer handles |
| `spec_mode` | Specification mode for planning |
| `auto_open_review_during_plan_build` | Auto-open review pane |

### Hang Detection Configuration
```javascript
const G = [2e3, 4e3, 6e3, 8e3, 1e4, 12e3, 14e3, 16e3, 32e3],
      Z = this._experimentService.getDynamicConfigParam("composer_hang_detection_config", "thresholds_ms") ?? G
```

## Abort Controller Handling

### NAL Path Abort Behavior (Line ~894637)
```javascript
for (const [G, Z] of this.streamingAbortControllers)
    if (!J.includes(G)) {
        const ee = B.find(ie => ie.generationUUID === G);
        // NAL streams are NOT aborted when removed from progress list
        ee?.metadata?.type === "composer" && ee?.metadata?.isNAL || Z.abort()
        this.streamingAbortControllers.delete(G)
    }
```

This is significant: NAL streams have different abort handling - they are not automatically aborted when their generation is removed from the in-progress list.

## File State Differences

### NAL Path (Line ~214857-214862)
```javascript
if (i.isNAL) {
    const o = i.conversationState.fileStatesV2;
    for (const a in o) {
        if (s.length >= e) break;
        adt(s, a)
    }
}
```

### Regular Path (Line ~214864-214867)
```javascript
else {
    const o = Object.keys(i.codeBlockData || {});
    for (const a of o) {
        // Uses codeBlockData for file tracking
    }
}
```

## Conclusions

1. **NAL is the newer architecture** - Designed for agent-style interactions with bidirectional streaming
2. **Automatic selection** - NAL is enabled for background composers and optionally for worktrees
3. **Fallback mechanisms** - Both paths support SSE fallback for HTTP/1.1 environments
4. **Different state management** - NAL uses `conversationState.fileStatesV2`, regular uses `codeBlockData`
5. **Abort handling differs** - NAL streams have special abort protection

## Recommendations for Further Investigation

1. **Agent Protocol Details** - Deep dive into `@anysphere/agent-client` package
2. **Conversation State Schema** - Document the `U1` protobuf message structure
3. **SSE Polling Mechanism** - Investigate `StreamBidiPoll` for polling fallback
4. **Background Composer Integration** - How NAL integrates with cloud agent workflows
